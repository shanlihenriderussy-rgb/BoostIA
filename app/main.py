"""Application FastAPI v6 — ajoute /api/models + override modele par requete."""

from __future__ import annotations

import asyncio
import json
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

from app.config import AVAILABLE_MODELS, settings
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
    version="0.4.0",
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


def _allowed_model_ids() -> set[str]:
    return {m["id"] for m in AVAILABLE_MODELS}


# --- Modeles d'entree --------------------------------------------------------


class GenerateRequest(BaseModel):
    template_id: str = Field(...)
    context: str = Field(..., min_length=1, max_length=8000)
    tone: Tone = Field(default="neutre")
    model: str | None = Field(
        default=None,
        description="Nom du modele Ollama a utiliser (override le default). "
        "Doit etre dans la liste AVAILABLE_MODELS.",
    )


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
    """Liste les modeles selectionnables + indique le defaut."""
    return {
        "default": settings.model_name,
        "available": AVAILABLE_MODELS,
    }


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
    """Genere un texte en streaming SSE.

    Le champ optionnel `model` permet d'override le modele par defaut pour
    cette requete. Doit etre dans `AVAILABLE_MODELS`.
    """
    client_ip = _get_client_ip(request)

    if not _check_rate_limit(client_ip):
        raise HTTPException(
            status_code=429,
            detail=f"Trop de requetes (max {settings.rate_limit_per_minute}/min). Reessayez plus tard.",
        )

    # Validation du modele (whitelist)
    chosen_model: str | None = None
    if req.model:
        if req.model not in _allowed_model_ids():
            raise HTTPException(
                status_code=400,
                detail=f"Modele non autorise : {req.model!r}. "
                f"Choix possibles : {sorted(_allowed_model_ids())}",
            )
        chosen_model = req.model

    request_id = uuid.uuid4().hex[:12]
    log = logger.bind(
        request_id=request_id,
        client_ip=client_ip,
        template_id=req.template_id,
        tone=req.tone,
        context_len=len(req.context),
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
            yield _sse(
                {"error": "Le modele est deja en train de generer. Reessayez dans quelques secondes."},
                event="error",
            )
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

        # Sauvegarde dans l'historique (SQLite)
        try:
            from app.templates import get_template
            template = get_template(req.template_id)
            history_db.add_entry(
                template_id=req.template_id,
                template_label=template.label,
                tone=req.tone,
                context=req.context,
                output=output_text,
                output_chars=total_chars,
                elapsed_seconds=elapsed,
            )
        except Exception as exc:
            log.warning("history_save_failed", error=str(exc))

        log.info("generation_end", output_chars=total_chars, elapsed_seconds=elapsed)
        yield _sse(
            {"output_chars": total_chars, "elapsed_seconds": elapsed, "model": chosen_model or settings.model_name},
            event="done",
        )

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "X-Content-Type-Options": "nosniff",
        },
    )


# --- Frontend statique (monte en dernier) -----------------------------------

WEB_DIR = Path(__file__).parent.parent / "web"
if WEB_DIR.is_dir():
    app.mount("/", StaticFiles(directory=str(WEB_DIR), html=True), name="web")
