"""init users assets

Revision ID: 0001_init_users_assets
Revises:
Create Date: 2026-04-29
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0001_init_users_assets"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("email_lower", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255)),
        sa.Column("display_name", sa.String(length=60)),
        sa.Column("locale", sa.String(length=10), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("email_verified_at", sa.DateTime(timezone=True)),
        sa.Column("last_login_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint("status IN ('active', 'suspended', 'deleted')", name="ck_users_status"),
    )
    op.create_index("idx_users_created_at", "users", ["created_at"])
    op.create_index("idx_users_status", "users", ["status"])
    op.create_index("uq_users_email_lower", "users", ["email_lower"], unique=True)

    op.create_table(
        "categories",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("parent_id", sa.BigInteger(), sa.ForeignKey("categories.id", ondelete="SET NULL")),
        sa.Column("slug", sa.String(length=80), nullable=False, unique=True),
        sa.Column("name_ko", sa.String(length=80), nullable=False),
        sa.Column("name_en", sa.String(length=80)),
        sa.Column("name_ja", sa.String(length=80)),
        sa.Column("description_ko", sa.Text()),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_categories_parent", "categories", ["parent_id", "sort_order"])
    op.create_index("idx_categories_active", "categories", ["is_active"])

    op.create_table(
        "tags",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("slug", sa.String(length=80), nullable=False, unique=True),
        sa.Column("name_ko", sa.String(length=80), nullable=False),
        sa.Column("name_en", sa.String(length=80)),
        sa.Column("name_ja", sa.String(length=80)),
        sa.Column("use_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_tags_use_count", "tags", ["use_count"])

    op.create_table(
        "sessions",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("session_token", sa.String(length=255), nullable=False, unique=True),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("expires", sa.DateTime(timezone=True), nullable=False),
        sa.Column("user_agent", sa.String(length=500)),
        sa.Column("ip", sa.String(length=64)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_sessions_user", "sessions", ["user_id"])
    op.create_index("idx_sessions_expires", "sessions", ["expires"])

    op.create_table(
        "assets",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("slug", sa.String(length=120), nullable=False, unique=True),
        sa.Column("asset_type", sa.String(length=32), nullable=False),
        sa.Column("category_id", sa.BigInteger(), sa.ForeignKey("categories.id", ondelete="SET NULL")),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("title_ko", sa.String(length=200), nullable=False),
        sa.Column("description_ko", sa.Text()),
        sa.Column("alt_text_ko", sa.String(length=500)),
        sa.Column("file_path", sa.String(length=500)),
        sa.Column("thumbnail_path", sa.String(length=500)),
        sa.Column("preview_path", sa.String(length=500)),
        sa.Column("file_size_bytes", sa.BigInteger()),
        sa.Column("mime_type", sa.String(length=80)),
        sa.Column("checksum", sa.String(length=64)),
        sa.Column("download_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint(
            "asset_type IN ('image','pptx','svg','docx','xlsx','html','lottie','colorbook','icon_set')",
            name="ck_assets_asset_type",
        ),
        sa.CheckConstraint(
            "status IN ('inbox','approved','published','rejected','archived','taken_down')",
            name="ck_assets_status",
        ),
    )
    op.create_index("idx_assets_status_created", "assets", ["status", "created_at"])
    op.create_index("idx_assets_category", "assets", ["category_id"])

    op.create_table(
        "asset_files",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("asset_id", sa.BigInteger(), sa.ForeignKey("assets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("file_role", sa.String(length=32), nullable=False),
        sa.Column("file_path", sa.String(length=500), nullable=False),
        sa.Column("mime_type", sa.String(length=80), nullable=False),
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("checksum", sa.String(length=64)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "asset_tags",
        sa.Column("asset_id", sa.BigInteger(), sa.ForeignKey("assets.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("tag_id", sa.BigInteger(), sa.ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
    )


def downgrade() -> None:
    op.drop_table("asset_tags")
    op.drop_table("asset_files")
    op.drop_index("idx_assets_category", table_name="assets")
    op.drop_index("idx_assets_status_created", table_name="assets")
    op.drop_table("assets")
    op.drop_index("idx_sessions_expires", table_name="sessions")
    op.drop_index("idx_sessions_user", table_name="sessions")
    op.drop_table("sessions")
    op.drop_index("idx_tags_use_count", table_name="tags")
    op.drop_table("tags")
    op.drop_index("idx_categories_active", table_name="categories")
    op.drop_index("idx_categories_parent", table_name="categories")
    op.drop_table("categories")
    op.drop_index("uq_users_email_lower", table_name="users")
    op.drop_index("idx_users_status", table_name="users")
    op.drop_index("idx_users_created_at", table_name="users")
    op.drop_table("users")
