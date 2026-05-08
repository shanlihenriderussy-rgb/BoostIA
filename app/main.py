"""Application FastAPI v8 — fixe le system prompt cassé de /api/refine + sauvegarde history."""

from __future__ import annotations

import asyncio
import json
import sys
import time
import uuid
from collections import defaultdict, deque
from collections.abc import AsyncIterator
from pathlib import Path
from threading import Lock

import structlog
from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.config import AVAILABLE_MODELS, RECOMMENDED_MODELS, find_recommendation, settings
from app.history import HistoryDB
from app.llm_client import OllamaClient, OllamaError
from app.logging_config import configure_logging
from app.templates import Tone, build_messages, list_templates

# --- Initialisation ----------------------------------------------------------

configure_logging()
logger = structlog.get_logger(__name__)

app = FastAPI(
    title="BoostIA",
    description="Assistant de redaction professionnelle 100 % local.",
    version="0.5.0",
)

if settings.cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

llm = OllamaClient()
history_db = HistoryDB()

# --- Controles de protection -------------------------------------------------

_generation_semaphore = asyncio.Semaphore(settings.max_concurrent_generations)
_rate_lock = Lock()
_request_times: dict[str, deque[float]] = defaultdict(deque)


def _check_rate_limit(client_ip: str) -> bool:
    if settings.rate_limit_per_minute <= 0:
        return True
    now = time.time()
    window = 60.0
    with _rate_lock:
        times = _request_times[client_ip]
        while times and times[0] < now - window:
            times.popleft()
        if len(times) >= settings.rate_limit_per_minute:
            return False
        times.append(now)
        return True


def _get_client_ip(request: Request) -> str:
    fwd = request.headers.get("x-forwarded-for")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _verify_api_key(authorization: str | None = Header(default=None)) -> None:
    if not settings.api_key:
        return
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="API key manquante")
    token = authorization.split(" ", 1)[1].strip()
    if token != settings.api_key:
        raise HTTPException(status_code=403, detail="API key invalide")


_MODEL_ID_RE = __import__("re").compile(r"^[A-Za-z0-9._\-:/]+$")


def _is_valid_model_id(model_id: str) -> bool:
    """Valide le format du nom de modele Ollama (ex. 'phi4:latest', 'qwen2.5:7b').

    On n'impose plus de liste blanche cote serveur : tout modele installe
    dans Ollama est utilisable. Ollama renverra une erreur claire si le
    modele n'est pas present, et l'UI ne propose que les modeles installes.
    """
    return bool(model_id) and len(model_id) <= 200 and bool(_MODEL_ID_RE.match(model_id))


# --- Modeles d'entree --------------------------------------------------------


class GenerateRequest(BaseModel):
    template_id: str = Field(...)
    context: str = Field(..., min_length=1, max_length=8000)
    tone: Tone = Field(default="neutre")
    model: str | None = Field(default=None)


class RefineRequest(BaseModel):
    output: str = Field(..., min_length=1, max_length=20000)
    instruction: str = Field(..., description="plus_court | plus_formel | plus_neutre | plus_direct")
    model: str | None = Field(default=None)


# --- Routes API --------------------------------------------------------------


@app.get("/api/health")
async def health() -> dict[str, str | int | bool]:
    return {
        "status": "ok",
        "model": settings.model_name,
        "max_concurrent": settings.max_concurrent_generations,
        "rate_limit_per_minute": settings.rate_limit_per_minute,
        "auth_required": bool(settings.api_key),
    }


@app.get("/api/templates")
async def templates_endpoint() -> list[dict[str, str]]:
    return list_templates()


@app.get("/api/models")
async def models_endpoint() -> dict:
    """Liste les modeles utilisables.

    Strategie :
    1. Interroge Ollama pour les modeles deja telecharges (`ollama list`).
    2. Enrichit chaque modele installe avec les metadata du catalogue
       RECOMMENDED_MODELS (label lisible, description, flag recommended).
    3. Si Ollama est injoignable, fallback sur le catalogue (mode degrade).
    4. Choisit un modele par defaut sense :
       - Si le modele config par defaut est installe, on le garde.
       - Sinon, premier modele recommande installe.
       - Sinon, premier modele installe.
    """
    installed = await llm.list_installed_models()
    ollama_available = bool(installed)

    available: list[dict[str, object]] = []

    if ollama_available:
        for inst in installed:
            name = inst["name"]
            reco = find_recommendation(name)
            available.append(
                {
                    "id": name,
                    "label": reco["label"] if reco else name,
                    "description": reco["description"] if reco else "Modele installe localement",
                    "recommended": bool(reco["recommended"]) if reco else False,
                    "installed": True,
                    "size": inst.get("size", 0),
                }
            )
        # Trie : recommandes d'abord, puis ordre alpha
        available.sort(key=lambda m: (not m["recommended"], str(m["id"]).lower()))
    else:
        # Fallback : catalogue statique sans flag installed
        for m in RECOMMENDED_MODELS:
            available.append(
                {
                    "id": m["id"],
                    "label": m["label"],
                    "description": m["description"],
                    "recommended": m["recommended"],
                    "installed": False,
                    "size": 0,
                }
            )

    # Choix du default
    installed_ids = [m["id"] for m in available if m["installed"]]
    default_id: str = ""
    if settings.model_name in installed_ids:
        default_id = settings.model_name
    else:
        # Premier recommande installe
        for m in available:
            if m["recommended"] and m["installed"]:
                default_id = str(m["id"])
                break
        # Sinon premier installe
        if not default_id and installed_ids:
            default_id = installed_ids[0]
        # Sinon (Ollama down) premier du catalogue
        if not default_id and available:
            default_id = str(available[0]["id"])

    return {
        "default": default_id,
        "available": available,
        "ollama_available": ollama_available,
    }


@app.get("/api/history")
async def history_endpoint(limit: int = 20) -> list[dict]:
    """Recupere les dernieres generations sauvegardees."""
    entries = history_db.get_all(limit=limit)
    return [
        {
            "id": e.id,
            "created_at": e.created_at,
            "template_id": e.template_id,
            "template_label": e.template_label,
            "tone": e.tone,
            "context": e.context[:200] + "..." if len(e.context) > 200 else e.context,
            "output_chars": e.output_chars,
        }
        for e in entries
    ]


def _sse(payload: dict, event: str | None = None) -> bytes:
    body = json.dumps(payload, ensure_ascii=False)
    prefix = f"event: {event}\n" if event else ""
    return f"{prefix}data: {body}\n\n".encode("utf-8")


@app.post("/api/generate")
async def generate(
    req: GenerateRequest,
    request: Request,
    _: None = Depends(_verify_api_key),
) -> StreamingResponse:
    client_ip = _get_client_ip(request)

    if not _check_rate_limit(client_ip):
        raise HTTPException(status_code=429, detail=f"Trop de requetes (max {settings.rate_limit_per_minute}/min).")

    chosen_model: str | None = None
    if req.model:
        if not _is_valid_model_id(req.model):
            raise HTTPException(status_code=400, detail=f"Nom de modele invalide : {req.model!r}")
        chosen_model = req.model

    request_id = uuid.uuid4().hex[:12]
    log = logger.bind(
        request_id=request_id, client_ip=client_ip, template_id=req.template_id,
        tone=req.tone, context_len=len(req.context),
        model=chosen_model or settings.model_name,
    )

    try:
        messages = build_messages(req.template_id, req.context, req.tone)
    except KeyError as exc:
        log.warning("template_not_found")
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        log.warning("invalid_tone", error=str(exc))
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    log.info("generation_start")
    started = time.perf_counter()

    async def event_stream() -> AsyncIterator[bytes]:
        try:
            await asyncio.wait_for(_generation_semaphore.acquire(), timeout=2.0)
        except asyncio.TimeoutError:
            log.warning("generation_busy")
            yield _sse({"error": "Le modele est deja en train de generer."}, event="error")
            return

        total_chars = 0
        output_parts: list[str] = []
        try:
            async for delta in llm.chat_stream(messages, model=chosen_model):
                total_chars += len(delta)
                output_parts.append(delta)
                yield _sse({"delta": delta})
        except OllamaError as exc:
            log.error("ollama_error", error=str(exc))
            yield _sse({"error": str(exc)}, event="error")
            return
        except Exception as exc:  # noqa: BLE001
            log.exception("generation_error")
            yield _sse({"error": f"Erreur interne : {exc}"}, event="error")
            return
        finally:
            _generation_semaphore.release()

        elapsed = round(time.perf_counter() - started, 2)
        output_text = "".join(output_parts)

        try:
            from app.templates import get_template
            template = get_template(req.template_id)
            history_db.add_entry(
                template_id=req.template_id, template_label=template.label, tone=req.tone,
                context=req.context, output=output_text,
                output_chars=total_chars, elapsed_seconds=elapsed,
            )
        except Exception as exc:
            log.warning("history_save_failed", error=str(exc))

        log.info("generation_end", output_chars=total_chars, elapsed_seconds=elapsed)
        yield _sse(
            {"output_chars": total_chars, "elapsed_seconds": elapsed, "model": chosen_model or settings.model_name},
            event="done",
        )

    return StreamingResponse(
        event_stream(), media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no", "X-Content-Type-Options": "nosniff"},
    )


# Instructions de reformulation pour /api/refine (en clair, en francais)
_REFINE_INSTRUCTIONS = {
    "plus_court": "Raccourcis ce texte d'environ 30 % en gardant tous les faits importants. Coupe les redondances et les phrases de politesse trop longues. Garde le meme ton.",
    "plus_formel": "Reformule ce texte dans un registre plus formel : vouvoiement systematique, vocabulaire soutenu, formules de politesse completes. Garde tout le sens.",
    "plus_neutre": "Reformule ce texte dans un registre neutre et courtois : ni trop formel, ni trop familier. Garde tout le sens.",
    "plus_direct": "Reformule ce texte plus direct et factuel : phrases courtes, va droit au but, sans fioritures. Garde tout le sens.",
}


@app.post("/api/refine")
async def refine(
    req: RefineRequest,
    request: Request,
    _: None = Depends(_verify_api_key),
) -> StreamingResponse:
    """Reformule un texte deja genere selon une instruction (plus_court, plus_formel, etc.)."""
    client_ip = _get_client_ip(request)

    if not _check_rate_limit(client_ip):
        raise HTTPException(status_code=429, detail=f"Trop de requetes (max {settings.rate_limit_per_minute}/min).")

    chosen_model: str | None = None
    if req.model:
        if not _is_valid_model_id(req.model):
            raise HTTPException(status_code=400, detail=f"Nom de modele invalide : {req.model!r}")
        chosen_model = req.model

    consigne = _REFINE_INSTRUCTIONS.get(req.instruction, req.instruction)
    messages = [
        {
            "role": "system",
            "content": (
                "Tu es BoostIA, un assistant de reformulation. Tu modifies le texte "
                "fourni selon l'instruction donnee. Tu produis UNIQUEMENT le texte "
                "modifie, sans preambule, sans explication, sans guillemets autour. "
                "Tu n'ajoutes JAMAIS d'information absente du texte source."
            ),
        },
        {
            "role": "user",
            "content": f"INSTRUCTION : {consigne}\n\nTEXTE A MODIFIER :\n---\n{req.output}\n---",
        },
    ]

    request_id = uuid.uuid4().hex[:12]
    log = logger.bind(
        request_id=request_id, client_ip=client_ip,
        instruction=req.instruction, source_chars=len(req.output),
        model=chosen_model or settings.model_name,
    )
    log.info("refine_start")
    started = time.perf_counter()

    async def event_stream() -> AsyncIterator[bytes]:
        try:
            await asyncio.wait_for(_generation_semaphore.acquire(), timeout=2.0)
        except asyncio.TimeoutError:
            log.warning("refine_busy")
            yield _sse({"error": "Le modele est occupe."}, event="error")
            return

        total_chars = 0
        try:
            async for delta in llm.chat_stream(messages, model=chosen_model):
                total_chars += len(delta)
                yield _sse({"delta": delta})
        except OllamaError as exc:
            log.error("ollama_error", error=str(exc))
            yield _sse({"error": str(exc)}, event="error")
            return
        except Exception as exc:  # noqa: BLE001
            log.exception("refine_error")
            yield _sse({"error": f"Erreur : {exc}"}, event="error")
            return
        finally:
            _generation_semaphore.release()

        elapsed = round(time.perf_counter() - started, 2)
        log.info("refine_end", output_chars=total_chars, elapsed_seconds=elapsed)
        yield _sse({"output_chars": total_chars, "elapsed_seconds": elapsed}, event="done")

    return StreamingResponse(
        event_stream(), media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no", "X-Content-Type-Options": "nosniff"},
    )


# --- Frontend statique (compat dev + .exe PyInstaller) -----------------------

def _get_web_dir() -> Path:
    if getattr(sys, "frozen", False):
        base = Path(sys._MEIPASS)  # type: ignore[attr-defined]
    else:
        base = Path(__file__).parent.parent
    return base / "web"


WEB_DIR = _get_web_dir()
if WEB_DIR.is_dir():
    app.mount("/", StaticFiles(directory=str(WEB_DIR), html=True), name="web")
