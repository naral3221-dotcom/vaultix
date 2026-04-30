"""add generation requests

Revision ID: 0004_add_generation_requests
Revises: 0003_add_admin_review_tables
Create Date: 2026-05-01
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0004_add_generation_requests"
down_revision: str | None = "0003_add_admin_review_tables"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "asset_generation_requests",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("requester_user_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("asset_type", sa.String(length=32), nullable=False),
        sa.Column("provider_preference", sa.String(length=40)),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("admin_notes", sa.Text()),
        sa.Column("result_asset_id", sa.BigInteger(), sa.ForeignKey("assets.id", ondelete="SET NULL")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint(
            "asset_type IN ('image','pptx','svg','docx','xlsx','html','lottie','colorbook','icon_set')",
            name="ck_asset_generation_requests_asset_type",
        ),
        sa.CheckConstraint(
            "status IN ('queued','processing','completed','failed','canceled')",
            name="ck_asset_generation_requests_status",
        ),
    )
    op.create_index(
        "idx_asset_generation_requests_status_created",
        "asset_generation_requests",
        ["status", "created_at"],
    )
    op.create_index(
        "idx_asset_generation_requests_requester",
        "asset_generation_requests",
        ["requester_user_id"],
    )


def downgrade() -> None:
    op.drop_index("idx_asset_generation_requests_requester", table_name="asset_generation_requests")
    op.drop_index("idx_asset_generation_requests_status_created", table_name="asset_generation_requests")
    op.drop_table("asset_generation_requests")
