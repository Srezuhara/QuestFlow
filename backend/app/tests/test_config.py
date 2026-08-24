from app.core.config import Settings, get_settings


def test_settings_loads_defaults() -> None:
    s = Settings()
    assert s.jwt_algorithm == "HS256"
    assert s.database_url.startswith("postgresql+asyncpg://")


def test_get_settings_is_cached() -> None:
    assert get_settings() is get_settings()


def test_push_enabled_false_for_placeholder_key() -> None:
    s = Settings(vapid_private_key="placeholder-vapid-private-key")
    assert s.push_enabled is False


def test_push_enabled_true_for_a_realistic_key() -> None:
    s = Settings(vapid_private_key="2gcYxWRA5xB6N1NgHC63oVIlFmLSvKUqWzAAzfzdjhA")
    assert s.push_enabled is True
