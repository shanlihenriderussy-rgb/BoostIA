"""Client asynchrone vers Ollama — v2 : ajoute override `model` par requete."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator

import httpx
import structlog

from app.config import settings

logger = structlog.get_logger(__name__)


class OllamaError(RuntimeError):
    """Erreur remontee par le client Ollama."""


class OllamaClient:
    """Client async minimal pour l'endpoint `/api/chat` d'Ollama."""

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        timeout_seconds: int | None = None,
    ) -> None:
        self.base_url = (base_url or settings.ollama_base_url).rstrip("/")
        self.default_model = model or settings.model_name
        self.timeout_seconds = timeout_seconds or settings.request_timeout_seconds

    @property
    def model(self) -> str:
        """Compat retro : `client.model` continue de marcher pour le code existant."""
        return self.default_model

    async def chat_stream(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
    ) -> AsyncIterator[str]:
        """Stream la reponse d'Ollama, yield chaque fragment de texte.

        Args:
            messages: liste de messages au format OpenAI/Ollama.
            model: NOM du modele Ollama a utiliser pour CETTE requete uniquement
                (override le default). Si None, utilise `self.default_model`.
            temperature: sampling temperature.
            top_p: nucleus sampling.

        Yields:
            Les fragments de texte au fur et a mesure de la generation.

        Raises:
            OllamaError: si Ollama repond une erreur HTTP ou un payload invalide.
        """
        target_model = model or self.default_model
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": target_model,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": temperature if temperature is not None else settings.default_temperature,
                "top_p": top_p if top_p is not None else settings.default_top_p,
            },
        }

        timeout = httpx.Timeout(self.timeout_seconds, connect=10.0)

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                async with client.stream("POST", url, json=payload) as response:
                    if response.status_code >= 400:
                        body = await response.aread()
                        raise OllamaError(
                            f"Ollama HTTP {response.status_code}: {body.decode('utf-8', errors='replace')[:500]}"
                        )

                    async for raw_line in response.aiter_lines():
                        if not raw_line:
                            continue
                        try:
                            chunk = json.loads(raw_line)
                        except json.JSONDecodeError:
                            logger.warning("ollama_invalid_json_line", line=raw_line[:200])
                            continue

                        if "error" in chunk:
                            raise OllamaError(str(chunk["error"]))

                        if chunk.get("done"):
                            return

                        content = chunk.get("message", {}).get("content", "")
                        if content:
                            yield content
        except httpx.HTTPError as exc:
            raise OllamaError(f"Erreur reseau Ollama : {exc}") from exc
