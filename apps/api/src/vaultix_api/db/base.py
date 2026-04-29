from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


# Import model modules so Base.metadata is populated for tests and Alembic.
from vaultix_api.models import core as _core  # noqa: E402,F401

