from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from vaultix_api.settings import get_settings


def get_engine(database_url: str | None = None) -> Engine:
    url = database_url or get_settings().database_url
    return create_engine(url, pool_pre_ping=True)


def get_sessionmaker(engine: Engine | None = None) -> sessionmaker[Session]:
    bind = engine or get_engine()
    return sessionmaker(bind=bind, autoflush=False, expire_on_commit=False)

