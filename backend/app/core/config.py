"""
Application configuration — reads from environment variables via pydantic-settings.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve .env from backend/ or project root (one level up)
_HERE = Path(__file__).resolve().parent.parent.parent  # backend/
_ROOT_ENV = _HERE.parent / ".env"  # project root
_ENV_FILE = str(_ROOT_ENV) if _ROOT_ENV.exists() else ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_ENV_FILE,
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # App
    APP_ENV: str = "development"
    SECRET_KEY: str = "change-me"
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    # JWT
    JWT_SECRET: str = "change-me-jwt"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 10080  # 1 week

    # Database
    DATABASE_URL: str

    # LLM
    GEMINI_API_KEY: str
    LLM_MODEL: str = "gemini-2.0-flash"

    # Embeddings
    EMBEDDING_MODEL: str = "models/text-embedding-004"
    EMBEDDING_DIMENSION: int = 768

    # Qdrant
    QDRANT_URL: str
    QDRANT_API_KEY: str
    QDRANT_RESUME_COLLECTION: str = "resume_chunks"
    QDRANT_JOB_COLLECTION: str = "job_chunks"

    # Sentry
    SENTRY_DSN: str = ""

    # Agent
    AGENT_MAX_ITERATIONS: int = 8


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
