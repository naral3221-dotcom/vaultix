from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from vaultix_api.db.session import get_engine, get_sessionmaker
from vaultix_api.settings import Settings


def test_get_engine_uses_configured_database_url():
    engine = get_engine("sqlite+pysqlite:///:memory:")

    assert isinstance(engine, Engine)
    assert str(engine.url) == "sqlite+pysqlite:///:memory:"


def test_get_sessionmaker_binds_to_engine():
    engine = get_engine("sqlite+pysqlite:///:memory:")
    maker = get_sessionmaker(engine)

    assert isinstance(maker, sessionmaker)
    with maker() as session:
        assert isinstance(session, Session)


def test_settings_accept_database_url_environment_name(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite+pysqlite:///runtime.db")

    settings = Settings()

    assert settings.database_url == "sqlite+pysqlite:///runtime.db"
