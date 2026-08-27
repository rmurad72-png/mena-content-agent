from __future__ import annotations

import uuid
from enum import Enum

from sqlalchemy import Boolean, CheckConstraint, Enum as SAEnum, ForeignKey, ForeignKeyConstraint, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class PlatformAccountStatus(str, Enum):
    active = "active"
    disconnected = "disconnected"
    suspended = "suspended"
    archived = "archived"


class Platform(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "platforms"
    key: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    capabilities: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default="{}")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    __table_args__ = (
        UniqueConstraint("key", name="uq_platforms_key"),
        CheckConstraint("length(trim(key)) > 0", name="platform_key_not_blank"),
    )


class BrandPlatformProfile(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "brand_platform_profiles"
    brand_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    platform_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("platforms.id", ondelete="RESTRICT"), nullable=False)
    language: Mapped[str] = mapped_column(String(10), nullable=False, default="ar", server_default="ar")
    voice_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    tone: Mapped[str | None] = mapped_column(String(150))
    style_config: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default="{}")
    content_rules: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default="{}")
    default_hashtags: Mapped[list] = mapped_column(JSONB, nullable=False, default=list, server_default="[]")
    default_cta: Mapped[str | None] = mapped_column(Text)
    max_length: Mapped[int | None] = mapped_column(Integer)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    __table_args__ = (
        ForeignKeyConstraint(["brand_id"], ["brands.id"], ondelete="CASCADE"),
        ForeignKeyConstraint(["voice_id", "brand_id"], ["brand_voices.id", "brand_voices.brand_id"], ondelete="RESTRICT"),
        UniqueConstraint("brand_id", "platform_id", "language", name="uq_brand_platform_profiles_brand_platform_language"),
        CheckConstraint("language IN ('ar','en')", name="brand_platform_profile_language_allowed"),
        CheckConstraint("max_length IS NULL OR max_length > 0", name="brand_platform_profile_max_length_positive"),
        Index("ix_brand_platform_profiles_brand_platform_active", "brand_id", "platform_id", "is_active"),
    )


class PlatformAccount(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "platform_accounts"
    workspace_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    brand_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    platform_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("platforms.id", ondelete="RESTRICT"), nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    external_account_id: Mapped[str] = mapped_column(String(255), nullable=False)
    username: Mapped[str | None] = mapped_column(String(255))
    account_metadata: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default="{}")
    credentials_reference: Mapped[str | None] = mapped_column(String(500))
    status: Mapped[PlatformAccountStatus] = mapped_column(SAEnum(PlatformAccountStatus, name="platform_account_status"), nullable=False, default=PlatformAccountStatus.active, server_default="active")
    __table_args__ = (
        ForeignKeyConstraint(["brand_id", "workspace_id"], ["brands.id", "brands.workspace_id"], ondelete="CASCADE"),
        UniqueConstraint("platform_id", "external_account_id", name="uq_platform_accounts_platform_external_id"),
        CheckConstraint("length(trim(name)) > 0", name="platform_account_name_not_blank"),
        CheckConstraint("length(trim(external_account_id)) > 0", name="platform_account_external_id_not_blank"),
        Index("ix_platform_accounts_workspace_brand", "workspace_id", "brand_id"),
        Index("ix_platform_accounts_brand_platform_status", "brand_id", "platform_id", "status"),
    )
