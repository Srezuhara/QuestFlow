"""Application settings, loaded from environment variables / .env.

Every other module should import `settings` from here rather than reading
os.environ directly, so configuration stays centrally typed and validated.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    environment: str = "development"

    # Database
    database_url: str = (
        "postgresql+asyncpg://questflow:questflow_dev_password@localhost:5432/questflow"
    )

    # JWT
    jwt_secret_key: str = "change-me-dev-secret-access-do-not-use-in-prod"
    jwt_refresh_secret_key: str = "change-me-dev-secret-refresh-do-not-use-in-prod"
    jwt_access_token_expire_minutes: int = 15
    jwt_refresh_token_expire_days: int = 30
    jwt_algorithm: str = "HS256"

    # Web Push (VAPID)
    vapid_public_key: str = "placeholder-vapid-public-key"
    vapid_private_key: str = "placeholder-vapid-private-key"
    vapid_subject: str = "mailto:admin@questflow.local"

    # CORS
    cors_origin: str = "http://localhost:5173"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
