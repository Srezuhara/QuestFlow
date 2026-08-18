from app.core.config import Settings, get_settings


def test_settings_loads_defaults() -> None:
    s = Settings()
    assert s.jwt_algorithm == "HS256"
    assert s.database_url.startswith("postgresql+asyncpg://")


def test_get_settings_is_cached() -> None:
    assert get_settings() is get_settings()
