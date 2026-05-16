"""Configuration centralisee — v9 : qwen2.5:7b par defaut (sweet spot qualite/vitesse)."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore",
    )

    # Ollama
    ollama_base_url: str = "http://localhost:11434"
    model_name: str = "qwen2.5:7b-instruct"

    # Generation
    request_timeout_seconds: int = 120
    default_temperature: float = 0.4
    default_top_p: float = 0.9

    # Observabilite
    log_level: str = "INFO"

    # Reseau / CORS
    cors_origins: list[str] = []

    # Securite
    max_concurrent_generations: int = 1
    rate_limit_per_minute: int = 10
    api_key: str = ""
    ollama_keep_alive: str = "5m"


settings = Settings()


# Modeles RECOMMANDES par BoostIA.
# Sert de base de connaissance pour enrichir l'UI :
# - label/description plus lisibles que le nom brut Ollama
# - flag `recommended` pour le badge "Recommande" dans le dropdown
# - flag `is_default` pour pre-selectionner si le modele est present
#
# La liste reelle des modeles affiches dans l'UI vient de `/api/tags` (Ollama).
# Ce catalogue ne sert QU'A enrichir/decorer ces modeles installes.
RECOMMENDED_MODELS: list[dict[str, object]] = [
    {
        "id": "phi4:latest",
        "label": "Phi 4",
        "description": "Recommande - meilleure qualite FR, ~50-60s sur petite VRAM",
        "recommended": True,
        "is_default": True,
    },
    {
        "id": "qwen2.5:7b-instruct",
        "label": "Qwen 2.5 7B",
        "description": "Bon equilibre qualite/vitesse (~15-25s par e-mail)",
        "recommended": True,
        "is_default": False,
    },
    {
        "id": "qwen2.5:3b-instruct",
        "label": "Qwen 2.5 3B",
        "description": "Tres rapide (~5s) mais qualite FR limitee",
        "recommended": False,
        "is_default": False,
    },
]

# Compatibilite retro : ancien import garde l'ID/label/description simple
AVAILABLE_MODELS: list[dict[str, str]] = [
    {"id": m["id"], "label": m["label"], "description": m["description"]}
    for m in RECOMMENDED_MODELS
]


def find_recommendation(model_id: str) -> dict[str, object] | None:
    """Cherche un modele dans le catalogue par son id (ex. 'phi4:latest')."""
    return next((m for m in RECOMMENDED_MODELS if m["id"] == model_id), None)
