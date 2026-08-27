from __future__ import annotations

import uuid
from enum import Enum

from sqlalchemy import (
    Boolean, CheckConstraint, Enum as SAEnum, ForeignKey, ForeignKeyConstraint,
    Index, String, Text, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin


class WorkspaceStatus(str, Enum):
    active = "active"
    suspended = "suspended"
    archived = "archived"


class UserStatus(str, Enum):
    active = "active"
    invited = "invited"
    suspended = "suspended"
    archived = "archived"


class MembershipStatus(str, Enum):
    invited = "invited"
    active = "active"
    suspended = "suspended"
    removed = "removed"


class RoleScope(str, Enum):
    workspace = "workspace"
    brand = "brand"


class Workspace(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "workspaces"
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    default_language: Mapped[str] = mapped_column(String(10), nullable=False, default="ar", server_default="ar")
    timezone: Mapped[str] = mapped_column(String(50), nullable=False, default="Asia/Riyadh", server_default="Asia/Riyadh")
    status: Mapped[WorkspaceStatus] = mapped_column(SAEnum(WorkspaceStatus, name="workspace_status"), nullable=False, default=WorkspaceStatus.active, server_default="active")
    __table_args__ = (
        UniqueConstraint("slug", name="uq_workspaces_slug"),
        CheckConstraint("length(trim(name)) > 0", name="workspace_name_not_blank"),
        CheckConstraint("length(trim(slug)) > 0", name="workspace_slug_not_blank"),
        CheckConstraint("default_language IN ('ar','en')", name="workspace_language_allowed"),
        Index("ix_workspaces_status", "status"),
    )


class User(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "users"
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(150), nullable=False)
    username: Mapped[str | None] = mapped_column(String(100))
    avatar_asset_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    preferred_language: Mapped[str] = mapped_column(String(10), nullable=False, default="ar", server_default="ar")
    status: Mapped[UserStatus] = mapped_column(SAEnum(UserStatus, name="user_status"), nullable=False, default=UserStatus.active, server_default="active")
    __table_args__ = (
        UniqueConstraint("email", name="uq_users_email"),
        UniqueConstraint("username", name="uq_users_username"),
        CheckConstraint("length(trim(email)) > 0", name="user_email_not_blank"),
        CheckConstraint("length(trim(display_name)) > 0", name="user_display_name_not_blank"),
        CheckConstraint("preferred_language IN ('ar','en')", name="user_language_allowed"),
        Index("ix_users_status", "status"),
    )


class WorkspaceMember(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "workspace_members"
    workspace_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[MembershipStatus] = mapped_column(SAEnum(MembershipStatus, name="membership_status"), nullable=False, default=MembershipStatus.active, server_default="active")
    __table_args__ = (
        UniqueConstraint("workspace_id", "user_id", name="uq_workspace_members_workspace_user"),
        UniqueConstraint("id", "workspace_id", name="uq_workspace_members_id_workspace"),
        Index("ix_workspace_members_workspace_status", "workspace_id", "status"),
    )


class Permission(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "permissions"
    key: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    __table_args__ = (
        UniqueConstraint("key", name="uq_permissions_key"),
        CheckConstraint("length(trim(key)) > 0", name="permission_key_not_blank"),
    )


class Role(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "roles"
    workspace_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    scope: Mapped[RoleScope] = mapped_column(SAEnum(RoleScope, name="role_scope"), nullable=False, default=RoleScope.workspace, server_default="workspace")
    is_system_role: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    __table_args__ = (
        UniqueConstraint("workspace_id", "name", name="uq_roles_workspace_name"),
        UniqueConstraint("id", "workspace_id", "scope", name="uq_roles_id_workspace_scope"),
        CheckConstraint("length(trim(name)) > 0", name="role_name_not_blank"),
        Index("ix_roles_workspace_scope", "workspace_id", "scope"),
    )


class RolePermission(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "role_permissions"
    role_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), nullable=False)
    permission_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("permissions.id", ondelete="CASCADE"), nullable=False)
    __table_args__ = (UniqueConstraint("role_id", "permission_id", name="uq_role_permissions_role_permission"),)


class WorkspaceMemberRole(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "workspace_member_roles"
    workspace_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    workspace_member_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    role_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    role_scope: Mapped[RoleScope] = mapped_column(SAEnum(RoleScope, name="role_scope"), nullable=False, default=RoleScope.workspace, server_default="workspace")
    __table_args__ = (
        ForeignKeyConstraint(["workspace_member_id", "workspace_id"], ["workspace_members.id", "workspace_members.workspace_id"], ondelete="CASCADE"),
        ForeignKeyConstraint(["role_id", "workspace_id", "role_scope"], ["roles.id", "roles.workspace_id", "roles.scope"], ondelete="CASCADE"),
        CheckConstraint("role_scope = 'workspace'", name="workspace_member_role_scope_valid"),
        UniqueConstraint("workspace_member_id", "role_id", name="uq_workspace_member_roles_member_role"),
        Index("ix_workspace_member_roles_workspace_member", "workspace_id", "workspace_member_id"),
    )
