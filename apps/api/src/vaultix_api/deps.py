from collections.abc import Iterator

from sqlalchemy.orm import Session

from vaultix_api.db.session import get_sessionmaker


def get_db() -> Iterator[Session]:
    maker = get_sessionmaker()
    with maker() as session:
        yield session

