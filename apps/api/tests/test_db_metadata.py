from pathlib import Path

from vaultix_api.db.base import Base


def test_phase_one_core_tables_are_registered():
    assert {
        "users",
        "email_verifications",
        "password_resets",
        "sessions",
        "categories",
        "tags",
        "assets",
        "asset_files",
        "asset_tags",
    }.issubset(Base.metadata.tables)


def test_alembic_initial_revision_exists():
    api_root = Path(__file__).resolve().parents[1]

    assert (api_root / "alembic.ini").exists()
    assert (api_root / "alembic" / "env.py").exists()
    assert (api_root / "alembic" / "versions" / "0001_init_users_assets.py").exists()
    assert (api_root / "alembic" / "versions" / "0002_add_auth_token_tables.py").exists()
