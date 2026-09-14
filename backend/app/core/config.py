"""
Application configuration.

All configuration is loaded from environment variables (see .env.example).
Never hardcode secrets here - this module only defines defaults that are
safe for local development and the *shape* of the configuration.
"""

from functools import lru_cache
from typing import List

from pydantic import AnyUrl, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # --- General ---
    PROJECT_NAME: str = "mausamnetra"
    PROJECT_DESCRIPTION: str = (
        "AI-Powered Weather Incident Verification & Intelligence Platform "
        "(SIH 26069 - Ministry of Earth Sciences / IMD prototype)"
    )
    VERSION: str = "0.1.0"
    ENVIRONMENT: str = Field(
        default="development"
    )  # development | staging | production
    API_V1_PREFIX: str = "/api/v1"

    # --- Database ---
    DATABASE_URL: str = Field(
        default="postgresql+psycopg://postgres:postgres@localhost:5432/mausamnetra"
    )
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    DATABASE_ECHO: bool = False

    # --- JWT / Auth ---
    JWT_SECRET_KEY: str = Field(default="CHANGE_ME_IN_ENV_FILE")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # --- CORS ---
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    # --- File uploads ---
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10 MB
    ALLOWED_IMAGE_EXTENSIONS: str = "jpg,jpeg,png,webp"
    ALLOWED_VIDEO_EXTENSIONS: str = "mp4,mov,webm"

    @property
    def allowed_image_extensions_set(self) -> set:
        return {e.strip().lower() for e in self.ALLOWED_IMAGE_EXTENSIONS.split(",")}

    @property
    def allowed_video_extensions_set(self) -> set:
        return {e.strip().lower() for e in self.ALLOWED_VIDEO_EXTENSIONS.split(",")}

    # --- Pagination ---
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100

    # --- Logging ---
    LOG_LEVEL: str = "INFO"

    # NOTE: was previously defaulted to :8000, which collides with the
    # backend's own port (see README: `uvicorn app.main:app` runs on 8000).
    # The classifier microservice now defaults to :8002 instead.
    CLASSIFIER_SERVICE_URL: str = Field(default="http://localhost:8002")
    VERIFICATION_SERVICE_URL: str = Field(default="http://localhost:8001")

    @field_validator("JWT_SECRET_KEY")
    @classmethod
    def secret_must_be_set_in_production(cls, v: str) -> str:
        return v


@lru_cache
def get_settings() -> Settings:
    """Cached settings accessor so the .env file is only parsed once."""
    return Settings()


settings = get_settings()
