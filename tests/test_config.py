import pytest

from app.core.config import PROJECT_ROOT, Settings

_ROOT_DB = "sqlite:///" + (PROJECT_ROOT / "data" / "app.db").as_posix()


@pytest.mark.parametrize("raw,expected", [
    ("postgres://u:p@h:5432/d", "postgresql+psycopg2://u:p@h:5432/d"),
    ("postgresql://u:p@h/d?sslmode=require", "postgresql+psycopg2://u:p@h/d?sslmode=require"),
    ("postgresql+psycopg2://u:p@h/d", "postgresql+psycopg2://u:p@h/d"),
    ("sqlite:///./data/app.db", _ROOT_DB),  # relative paths resolve against the project root
    ("sqlite:///:memory:", "sqlite:///:memory:"),
])
def test_database_url_is_normalised_for_sqlalchemy(raw, expected):
    assert Settings(database_url=raw).database_url == expected


def test_production_refuses_the_default_jwt_secret(monkeypatch):
    from app.core import config

    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.delenv("JWT_SECRET", raising=False)
    config.get_settings.cache_clear()
    try:
        with pytest.raises(RuntimeError):
            config.get_settings()
    finally:
        monkeypatch.setenv("APP_ENV", "test")
        config.get_settings.cache_clear()
