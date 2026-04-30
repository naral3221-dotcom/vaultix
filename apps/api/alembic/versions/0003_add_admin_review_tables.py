"""add admin review tables

Revision ID: 0003_add_admin_review_tables
Revises: 0002_add_auth_token_tables
Create Date: 2026-05-01
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0003_add_admin_review_tables"
down_revision: str | None = "0002_add_auth_token_tables"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("role", sa.String(length=32), nullable=False, server_default="member"),
    )
    op.create_check_constraint("ck_users_role", "users", "role IN ('member', 'admin')")
    op.create_index("idx_users_role", "users", ["role"])

    op.create_table(
        "asset_reports",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("asset_id", sa.BigInteger(), sa.ForeignKey("assets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("reporter_user_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("reason", sa.String(length=32), nullable=False),
        sa.Column("message", sa.Text()),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint(
            "reason IN ('copyright','inappropriate','broken_file','other')",
            name="ck_asset_reports_reason",
        ),
        sa.CheckConstraint("status IN ('open','resolved','dismissed')", name="ck_asset_reports_status"),
    )
    op.create_index("idx_asset_reports_status_created", "asset_reports", ["status", "created_at"])
    op.create_index("idx_asset_reports_asset", "asset_reports", ["asset_id"])

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("actor_user_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("action", sa.String(length=80), nullable=False),
        sa.Column("target_type", sa.String(length=40), nullable=False),
        sa.Column("target_id", sa.BigInteger(), nullable=False),
        sa.Column("metadata_json", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_audit_logs_actor_created", "audit_logs", ["actor_user_id", "created_at"])
    op.create_index("idx_audit_logs_target", "audit_logs", ["target_type", "target_id"])


def downgrade() -> None:
    op.drop_index("idx_audit_logs_target", table_name="audit_logs")
    op.drop_index("idx_audit_logs_actor_created", table_name="audit_logs")
    op.drop_table("audit_logs")
    op.drop_index("idx_asset_reports_asset", table_name="asset_reports")
    op.drop_index("idx_asset_reports_status_created", table_name="asset_reports")
    op.drop_table("asset_reports")
    op.drop_index("idx_users_role", table_name="users")
    op.drop_constraint("ck_users_role", "users", type_="check")
    op.drop_column("users", "role")
