from datetime import datetime

from sqlalchemy import BigInteger, Boolean, CheckConstraint, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from sqlalchemy.types import DateTime

from vaultix_api.db.base import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class User(TimestampMixin, Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("status IN ('active', 'suspended', 'deleted')", name="ck_users_status"),
        CheckConstraint("role IN ('member', 'admin')", name="ck_users_role"),
        Index("idx_users_created_at", "created_at"),
        Index("idx_users_status", "status"),
        Index("idx_users_role", "role"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    email_lower: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    password_hash: Mapped[str | None] = mapped_column(String(255))
    display_name: Mapped[str | None] = mapped_column(String(60))
    locale: Mapped[str] = mapped_column(String(10), nullable=False, default="ko")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    role: Mapped[str] = mapped_column(String(32), nullable=False, default="member")
    email_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class EmailVerification(Base):
    __tablename__ = "email_verifications"
    __table_args__ = (
        Index("uq_email_verifications_token", "token", unique=True),
        Index("idx_email_verifications_user", "user_id", "used_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token: Mapped[str] = mapped_column(String(64), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PasswordReset(Base):
    __tablename__ = "password_resets"
    __table_args__ = (Index("idx_password_resets_user", "user_id", "used_at"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Session(Base):
    __tablename__ = "sessions"
    __table_args__ = (
        Index("idx_sessions_user", "user_id"),
        Index("idx_sessions_expires", "expires"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    session_token: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    expires: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    user_agent: Mapped[str | None] = mapped_column(String(500))
    ip: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Category(TimestampMixin, Base):
    __tablename__ = "categories"
    __table_args__ = (
        Index("idx_categories_parent", "parent_id", "sort_order"),
        Index("idx_categories_active", "is_active"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id", ondelete="SET NULL"))
    slug: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    name_ko: Mapped[str] = mapped_column(String(80), nullable=False)
    name_en: Mapped[str | None] = mapped_column(String(80))
    name_ja: Mapped[str | None] = mapped_column(String(80))
    description_ko: Mapped[str | None] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column(default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class Tag(Base):
    __tablename__ = "tags"
    __table_args__ = (Index("idx_tags_use_count", "use_count"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    slug: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    name_ko: Mapped[str] = mapped_column(String(80), nullable=False)
    name_en: Mapped[str | None] = mapped_column(String(80))
    name_ja: Mapped[str | None] = mapped_column(String(80))
    use_count: Mapped[int] = mapped_column(nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Asset(TimestampMixin, Base):
    __tablename__ = "assets"
    __table_args__ = (
        CheckConstraint(
            "asset_type IN ('image','pptx','svg','docx','xlsx','html','lottie','colorbook','icon_set')",
            name="ck_assets_asset_type",
        ),
        CheckConstraint(
            "status IN ('inbox','approved','published','rejected','archived','taken_down')",
            name="ck_assets_status",
        ),
        Index("idx_assets_status_created", "status", "created_at"),
        Index("idx_assets_category", "category_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    slug: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    asset_type: Mapped[str] = mapped_column(String(32), nullable=False, default="image")
    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id", ondelete="SET NULL"))
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="inbox")
    title_ko: Mapped[str] = mapped_column(String(200), nullable=False)
    description_ko: Mapped[str | None] = mapped_column(Text)
    alt_text_ko: Mapped[str | None] = mapped_column(String(500))
    file_path: Mapped[str | None] = mapped_column(String(500))
    thumbnail_path: Mapped[str | None] = mapped_column(String(500))
    preview_path: Mapped[str | None] = mapped_column(String(500))
    file_size_bytes: Mapped[int | None] = mapped_column(BigInteger)
    mime_type: Mapped[str | None] = mapped_column(String(80))
    checksum: Mapped[str | None] = mapped_column(String(64))
    download_count: Mapped[int] = mapped_column(nullable=False, default=0)


class AssetFile(TimestampMixin, Base):
    __tablename__ = "asset_files"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id", ondelete="CASCADE"), nullable=False)
    file_role: Mapped[str] = mapped_column(String(32), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(80), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    checksum: Mapped[str | None] = mapped_column(String(64))


class AssetTag(Base):
    __tablename__ = "asset_tags"

    asset_id: Mapped[int] = mapped_column(
        ForeignKey("assets.id", ondelete="CASCADE"), primary_key=True
    )
    tag_id: Mapped[int] = mapped_column(ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True)


class AssetReport(TimestampMixin, Base):
    __tablename__ = "asset_reports"
    __table_args__ = (
        CheckConstraint(
            "reason IN ('copyright','inappropriate','broken_file','other')",
            name="ck_asset_reports_reason",
        ),
        CheckConstraint("status IN ('open','resolved','dismissed')", name="ck_asset_reports_status"),
        Index("idx_asset_reports_status_created", "status", "created_at"),
        Index("idx_asset_reports_asset", "asset_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id", ondelete="CASCADE"), nullable=False)
    reporter_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    reason: Mapped[str] = mapped_column(String(32), nullable=False)
    message: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="open")


class AssetGenerationRequest(TimestampMixin, Base):
    __tablename__ = "asset_generation_requests"
    __table_args__ = (
        CheckConstraint(
            "asset_type IN ('image','pptx','svg','docx','xlsx','html','lottie','colorbook','icon_set')",
            name="ck_asset_generation_requests_asset_type",
        ),
        CheckConstraint(
            "status IN ('queued','processing','completed','failed','canceled')",
            name="ck_asset_generation_requests_status",
        ),
        Index("idx_asset_generation_requests_status_created", "status", "created_at"),
        Index("idx_asset_generation_requests_requester", "requester_user_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    requester_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    asset_type: Mapped[str] = mapped_column(String(32), nullable=False, default="image")
    provider_preference: Mapped[str | None] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="queued")
    admin_notes: Mapped[str | None] = mapped_column(Text)
    result_asset_id: Mapped[int | None] = mapped_column(ForeignKey("assets.id", ondelete="SET NULL"))


class AuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("idx_audit_logs_actor_created", "actor_user_id", "created_at"),
        Index("idx_audit_logs_target", "target_type", "target_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    actor_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    action: Mapped[str] = mapped_column(String(80), nullable=False)
    target_type: Mapped[str] = mapped_column(String(40), nullable=False)
    target_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    metadata_json: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
