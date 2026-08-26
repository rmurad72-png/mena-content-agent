from __future__ import annotations

import uuid
from enum import Enum

from sqlalchemy import (
    Enum as SAEnum,
    Boolean,
    CheckConstraint,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.organization import RoleScope


class BrandStatus(str, Enum):
    active = "active"
    inactive = "inactive"
    archived = "archived"


class BrandRuleSeverity(str, Enum):
    info = "info"
    warning = "warning"
    blocking = "blocking"


class BrandRuleType(str, Enum):
    preferred_term = "preferred_term"
    forbidden_term = "forbidden_term"
    required_phrase = "required_phrase"
    forbidden_topic = "forbidden_topic"
    required_disclaimer = "required_disclaimer"
    style_rule = "style_rule"
    legal_rule = "legal_rule"
    editorial_rule = "editorial_rule"


class Brand(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    SoftDeleteMixin,
    Base,
):
    __tablename__ = "brands"

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    mission: Mapped[str | None] = mapped_column(Text, nullable=True)
    vision: Mapped[str | None] = mapped_column(Text, nullable=True)
    positioning: Mapped[str | None] = mapped_column(Text, nullable=True)
    primary_language: Mapped[str] = mapped_column(
        String(10), nullable=False, default="ar", server_default="ar"
    )
    status: Mapped[BrandStatus] = mapped_column(
        SAEnum(BrandStatus, name="brand_status"), nullable=False, default=BrandStatus.active, server_default="active"
    )

    __table_args__ = (
        UniqueConstraint("workspace_id", "slug", name="uq_brands_workspace_slug"),
        UniqueConstraint("id", "workspace_id", name="uq_brands_id_workspace"),
        CheckConstraint("length(trim(name)) > 0", name="brand_name_not_blank"),
        CheckConstraint("length(trim(slug)) > 0", name="brand_slug_not_blank"),
        Index("ix_brands_workspace_status", "workspace_id", "status"),
    )


class BrandIdentity(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    __tablename__ = "brand_identities"

    brand_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("brands.id", ondelete="CASCADE"),
        nullable=False,
    )
    personality: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default="{}")
    values: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default="{}")
    visual_identity: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default="{}")
    verbal_identity: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default="{}")
    editorial_identity: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default="{}")

    __table_args__ = (
        UniqueConstraint("brand_id", name="uq_brand_identities_brand"),
    )


class BrandVoice(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    __tablename__ = "brand_voices"

    brand_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("brands.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    attributes: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default="{}")
    examples: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default="{}")
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")

    __table_args__ = (
        UniqueConstraint("brand_id", "name", name="uq_brand_voices_brand_name"),
        Index("ix_brand_voices_brand_default", "brand_id", "is_default"),
    )


class BrandAudience(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    __tablename__ = "brand_audiences"

    brand_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("brands.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    language: Mapped[str] = mapped_column(String(10), nullable=False, default="ar", server_default="ar")
    demographics: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default="{}")
    interests: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default="{}")
    pain_points: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default="{}")

    __table_args__ = (
        UniqueConstraint("brand_id", "name", name="uq_brand_audiences_brand_name"),
        Index("ix_brand_audiences_brand_language", "brand_id", "language"),
    )


class BrandRule(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    SoftDeleteMixin,
    Base,
):
    __tablename__ = "brand_rules"

    brand_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("brands.id", ondelete="CASCADE"),
        nullable=False,
    )
    rule_type: Mapped[BrandRuleType] = mapped_column(SAEnum(BrandRuleType, name="brand_rule_type"), nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    severity: Mapped[BrandRuleSeverity] = mapped_column(
        SAEnum(BrandRuleSeverity, name="brand_rule_severity"), nullable=False, default=BrandRuleSeverity.warning, server_default="warning"
    )
    rule_config: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default="{}")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")

    __table_args__ = (
        Index("ix_brand_rules_brand_type_active", "brand_id", "rule_type", "is_active"),
    )


class BrandTerm(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    __tablename__ = "brand_terms"

    brand_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("brands.id", ondelete="CASCADE"),
        nullable=False,
    )
    term: Mapped[str] = mapped_column(String(150), nullable=False)
    preferred_form: Mapped[str] = mapped_column(String(300), nullable=False)
    forbidden_forms: Mapped[list] = mapped_column(JSONB, nullable=False, default=list, server_default="[]")
    language: Mapped[str] = mapped_column(String(10), nullable=False, default="ar", server_default="ar")
    context: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        UniqueConstraint("brand_id", "term", "language", name="uq_brand_terms_brand_term_language"),
        Index("ix_brand_terms_brand_language", "brand_id", "language"),
    )


class BrandMemberRole(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    __tablename__ = "brand_member_roles"

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False
    )
    brand_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False
    )
    workspace_member_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False
    )
    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False
    )
    role_scope: Mapped[RoleScope] = mapped_column(
        SAEnum(RoleScope, name="role_scope"), nullable=False, default=RoleScope.brand, server_default="brand"
    )

    __table_args__ = (
        ForeignKeyConstraint(
            ["brand_id", "workspace_id"],
            ["brands.id", "brands.workspace_id"],
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["workspace_member_id", "workspace_id"],
            ["workspace_members.id", "workspace_members.workspace_id"],
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["role_id", "workspace_id", "role_scope"],
            ["roles.id", "roles.workspace_id", "roles.scope"],
            ondelete="CASCADE",
        ),
        CheckConstraint("role_scope = 'brand'", name="brand_member_role_scope_valid"),
        UniqueConstraint(
            "workspace_member_id",
            "brand_id",
            "role_id",
            name="uq_brand_member_roles_member_brand_role",
        ),
        Index("ix_brand_member_roles_brand_member", "brand_id", "workspace_member_id"),
    )
