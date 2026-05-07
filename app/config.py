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


# Modeles selectionnables depuis le menu deroulant de l'UI.
# Pour ajouter un modele : `ollama pull <id>` puis l'ajouter ici.
AVAILABLE_MODELS: list[dict[str, str]] = [
    {
        "id": "qwen2.5:7b-instruct",
        "label": "Qwen 2.5 — 7B Instruct",
        "description": "Recommande — bon equilibre qualite/vitesse (~15-25s par e-mail)",
    },
    {
        "id": "qwen2.5:3b-instruct",
        "label": "Qwen 2.5 — 3B Instruct",
        "description": "Tres rapide (~5s) mais qualite FR limitee",
    },
    {
        "id": "phi4:latest",
        "label": "Phi 4 — Latest",
        "description": "Meilleure qualite mais lent sur petite VRAM (~50-60s)",
    },
]
