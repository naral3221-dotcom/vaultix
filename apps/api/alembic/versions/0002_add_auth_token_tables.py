"""add auth token tables

Revision ID: 0002_add_auth_token_tables
Revises: 0001_init_users_assets
Create Date: 2026-04-30
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0002_add_auth_token_tables"
down_revision: str | None = "0001_init_users_assets"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "email_verifications",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("uq_email_verifications_token", "email_verifications", ["token"], unique=True)
    op.create_index("idx_email_verifications_user", "email_verifications", ["user_id", "used_at"])

    op.create_table(
        "password_resets",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(length=255), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_password_resets_user", "password_resets", ["user_id", "used_at"])


def downgrade() -> None:
    op.drop_index("idx_password_resets_user", table_name="password_resets")
    op.drop_table("password_resets")
    op.drop_index("idx_email_verifications_user", table_name="email_verifications")
    op.drop_index("uq_email_verifications_token", table_name="email_verifications")
    op.drop_table("email_verifications")
