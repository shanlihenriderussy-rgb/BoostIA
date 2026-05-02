"""Configuration centralisee — v6 : ajoute la liste des modeles disponibles dans l'UI."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Parametres de l'application BoostIA.

    Surchargeables via variables d'environnement ou `.env`.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ----- Ollama -----
    ollama_base_url: str = "http://localhost:11434"
    model_name: str = "qwen2.5:7b-instruct"

    # ----- Generation -----
    request_timeout_seconds: int = 120
    default_temperature: float = 0.4
    default_top_p: float = 0.9

    # ----- Observabilite -----
    log_level: str = "INFO"

    # ----- Reseau / CORS -----
    cors_origins: list[str] = []

    # ----- Securite et protection des ressources -----
    max_concurrent_generations: int = 1
    rate_limit_per_minute: int = 10
    api_key: str = ""
    ollama_keep_alive: str = "5m"


settings = Settings()


# ----- Modeles selectionnables depuis l'UI -----
# Liste affichee dans le menu deroulant en haut a droite de l'interface.
# Ajouter un modele : `ollama pull <id>` puis ajouter une entree ici.
# Le `id` doit correspondre exactement au nom Ollama (ex. "qwen3:8b").
AVAILABLE_MODELS: list[dict[str, str]] = [
    {
        "id": "phi4",
        "label": "Phi 4",
        "description": "Microsoft, recent, meilleur francais meme petit",
    },
    {
        "id": "qwen2.5:3b-instruct",
        "label": "Qwen 2.5 — 3B Instruct",
        "description": "Tres rapide (~50 tokens/s), qualite acceptable",
    },
]
