"""Configuration centralisee — v7 : restaure qwen3:8b dans les modeles disponibles."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore",
    )

    # Ollama
    ollama_base_url: str = "http://localhost:11434"
    model_name: str = "qwen2.5:3b-instruct"

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
        "id": "qwen2.5:3b-instruct",
        "label": "Qwen 2.5 — 3B Instruct",
        "description": "Tres rapide (~50 tokens/s), qualite acceptable",
    },
    {
        "id": "deepseek-r1:8b",
        "label": "DeepSeek R1 — 8B",
        "description": "Reasoning model — raisonnement profond, qualite superieure",
    },
    {
        "id": "phi4:latest",
        "label": "Phi 4 — Latest",
        "description": "Modele puissant et equilibre (9.1 GB)",
    },
]
