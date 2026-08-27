"""Create Phase 1 workspace, brand, RBAC and platform-account schema.

Revision ID: 001_phase1
Revises:
Create Date: 2026-08-26
"""

from __future__ import annotations

import json
import uuid
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "001_phase1"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def uuid_type():
    return postgresql.UUID(as_uuid=True)


def jsonb():
    return postgresql.JSONB()


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    workspace_status = sa.Enum(
        "active", "suspended", "archived", name="workspace_status"
    )
    user_status = sa.Enum(
        "active", "invited", "suspended", "archived", name="user_status"
    )
    membership_status = sa.Enum(
        "invited", "active", "suspended", "removed", name="membership_status"
    )
    role_scope = sa.Enum("workspace", "brand", name="role_scope")
    brand_status = sa.Enum(
        "active", "inactive", "archived", name="brand_status"
    )
    brand_rule_severity = sa.Enum(
        "info", "warning", "blocking", name="brand_rule_severity"
    )
    brand_rule_type = sa.Enum(
        "preferred_term",
        "forbidden_term",
        "required_phrase",
        "forbidden_topic",
        "required_disclaimer",
        "style_rule",
        "legal_rule",
        "editorial_rule",
        name="brand_rule_type",
    )
    platform_account_status = sa.Enum(
        "active",
        "disconnected",
        "suspended",
        "archived",
        name="platform_account_status",
    )

    for enum_type in (
        workspace_status,
        user_status,
        membership_status,
        role_scope,
        brand_status,
        brand_rule_severity,
        brand_rule_type,
        platform_account_status,
    ):
        enum_type.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "workspaces",
        sa.Column("id", uuid_type(), primary_key=True, nullable=False),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("default_language", sa.String(10), nullable=False, server_default="ar"),
        sa.Column("timezone", sa.String(50), nullable=False, server_default="Asia/Riyadh"),
        sa.Column("status", workspace_status, nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("slug", name="uq_workspaces_slug"),
        sa.CheckConstraint("length(trim(name)) > 0", name="workspace_name_not_blank"),
        sa.CheckConstraint("length(trim(slug)) > 0", name="workspace_slug_not_blank"),
        sa.CheckConstraint("default_language IN ('ar','en')", name="workspace_language_allowed"),
    )
    op.create_index("ix_workspaces_status", "workspaces", ["status"])

    op.create_table(
        "users",
        sa.Column("id", uuid_type(), primary_key=True, nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("display_name", sa.String(150), nullable=False),
        sa.Column("username", sa.String(100), nullable=True),
        sa.Column("avatar_asset_id", uuid_type(), nullable=True),
        sa.Column("preferred_language", sa.String(10), nullable=False, server_default="ar"),
        sa.Column("status", user_status, nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("email", name="uq_users_email"),
        sa.UniqueConstraint("username", name="uq_users_username"),
        sa.CheckConstraint("length(trim(email)) > 0", name="user_email_not_blank"),
        sa.CheckConstraint("length(trim(display_name)) > 0", name="user_display_name_not_blank"),
        sa.CheckConstraint("preferred_language IN ('ar','en')", name="user_language_allowed"),
    )
    op.create_index("ix_users_status", "users", ["status"])

    op.create_table(
        "workspace_members",
        sa.Column("id", uuid_type(), primary_key=True, nullable=False),
        sa.Column("workspace_id", uuid_type(), nullable=False),
        sa.Column("user_id", uuid_type(), nullable=False),
        sa.Column("status", membership_status, nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("workspace_id", "user_id", name="uq_workspace_members_workspace_user"),
        sa.UniqueConstraint("id", "workspace_id", name="uq_workspace_members_id_workspace"),
    )
    op.create_index("ix_workspace_members_workspace_status", "workspace_members", ["workspace_id", "status"])

    op.create_table(
        "permissions",
        sa.Column("id", uuid_type(), primary_key=True, nullable=False),
        sa.Column("key", sa.String(120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("key", name="uq_permissions_key"),
        sa.CheckConstraint("length(trim(key)) > 0", name="permission_key_not_blank"),
    )

    op.create_table(
        "roles",
        sa.Column("id", uuid_type(), primary_key=True, nullable=False),
        sa.Column("workspace_id", uuid_type(), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("scope", role_scope, nullable=False, server_default="workspace"),
        sa.Column("is_system_role", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("workspace_id", "name", name="uq_roles_workspace_name"),
        sa.UniqueConstraint("id", "workspace_id", "scope", name="uq_roles_id_workspace_scope"),
        sa.CheckConstraint("length(trim(name)) > 0", name="role_name_not_blank"),
    )
    op.create_index("ix_roles_workspace_scope", "roles", ["workspace_id", "scope"])

    op.create_table(
        "role_permissions",
        sa.Column("id", uuid_type(), primary_key=True, nullable=False),
        sa.Column("role_id", uuid_type(), nullable=False),
        sa.Column("permission_id", uuid_type(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["permission_id"], ["permissions.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("role_id", "permission_id", name="uq_role_permissions_role_permission"),
    )

    op.create_table(
        "workspace_member_roles",
        sa.Column("id", uuid_type(), primary_key=True, nullable=False),
        sa.Column("workspace_id", uuid_type(), nullable=False),
        sa.Column("workspace_member_id", uuid_type(), nullable=False),
        sa.Column("role_id", uuid_type(), nullable=False),
        sa.Column("role_scope", role_scope, nullable=False, server_default="workspace"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(
            ["workspace_member_id", "workspace_id"],
            ["workspace_members.id", "workspace_members.workspace_id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["role_id", "workspace_id", "role_scope"],
            ["roles.id", "roles.workspace_id", "roles.scope"],
            ondelete="CASCADE",
        ),
        sa.CheckConstraint("role_scope = 'workspace'", name="workspace_member_role_scope_valid"),
        sa.UniqueConstraint("workspace_member_id", "role_id", name="uq_workspace_member_roles_member_role"),
    )
    op.create_index(
        "ix_workspace_member_roles_workspace_member",
        "workspace_member_roles",
        ["workspace_id", "workspace_member_id"],
    )

    op.create_table(
        "brands",
        sa.Column("id", uuid_type(), primary_key=True, nullable=False),
        sa.Column("workspace_id", uuid_type(), nullable=False),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("mission", sa.Text(), nullable=True),
        sa.Column("vision", sa.Text(), nullable=True),
        sa.Column("positioning", sa.Text(), nullable=True),
        sa.Column("primary_language", sa.String(10), nullable=False, server_default="ar"),
        sa.Column("status", brand_status, nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("workspace_id", "slug", name="uq_brands_workspace_slug"),
        sa.UniqueConstraint("id", "workspace_id", name="uq_brands_id_workspace"),
        sa.CheckConstraint("length(trim(name)) > 0", name="brand_name_not_blank"),
        sa.CheckConstraint("length(trim(slug)) > 0", name="brand_slug_not_blank"),
        sa.CheckConstraint("primary_language IN ('ar','en')", name="brand_language_allowed"),
    )
    op.create_index("ix_brands_workspace_status", "brands", ["workspace_id", "status"])

    op.create_table(
        "brand_identities",
        sa.Column("id", uuid_type(), primary_key=True, nullable=False),
        sa.Column("brand_id", uuid_type(), nullable=False),
        sa.Column("personality", jsonb(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("values", jsonb(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("visual_identity", jsonb(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("verbal_identity", jsonb(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("editorial_identity", jsonb(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["brand_id"], ["brands.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("brand_id", name="uq_brand_identities_brand"),
    )

    op.create_table(
        "brand_voices",
        sa.Column("id", uuid_type(), primary_key=True, nullable=False),
        sa.Column("brand_id", uuid_type(), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("attributes", jsonb(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("examples", jsonb(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["brand_id"], ["brands.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("brand_id", "name", name="uq_brand_voices_brand_name"),
        # Required by the composite FK from brand_platform_profiles.
        sa.UniqueConstraint("id", "brand_id", name="uq_brand_voices_id_brand"),
    )
    op.create_index("ix_brand_voices_brand_default", "brand_voices", ["brand_id", "is_default"])
    op.create_index(
        "uq_brand_voices_one_default_per_brand",
        "brand_voices",
        ["brand_id"],
        unique=True,
        postgresql_where=sa.text("is_default IS TRUE"),
    )

    op.create_table(
        "brand_audiences",
        sa.Column("id", uuid_type(), primary_key=True, nullable=False),
        sa.Column("brand_id", uuid_type(), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("language", sa.String(10), nullable=False, server_default="ar"),
        sa.Column("demographics", jsonb(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("interests", jsonb(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("pain_points", jsonb(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["brand_id"], ["brands.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("brand_id", "name", name="uq_brand_audiences_brand_name"),
        sa.CheckConstraint("language IN ('ar','en')", name="brand_audience_language_allowed"),
    )
    op.create_index("ix_brand_audiences_brand_language", "brand_audiences", ["brand_id", "language"])

    op.create_table(
        "brand_rules",
        sa.Column("id", uuid_type(), primary_key=True, nullable=False),
        sa.Column("brand_id", uuid_type(), nullable=False),
        sa.Column("rule_type", brand_rule_type, nullable=False),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("severity", brand_rule_severity, nullable=False, server_default="warning"),
        sa.Column("rule_config", jsonb(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["brand_id"], ["brands.id"], ondelete="CASCADE"),
    )
    op.create_index(
        "ix_brand_rules_brand_type_active",
        "brand_rules",
        ["brand_id", "rule_type", "is_active"],
    )

    op.create_table(
        "brand_terms",
        sa.Column("id", uuid_type(), primary_key=True, nullable=False),
        sa.Column("brand_id", uuid_type(), nullable=False),
        sa.Column("term", sa.String(150), nullable=False),
        sa.Column("preferred_form", sa.String(300), nullable=False),
        sa.Column("forbidden_forms", jsonb(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("language", sa.String(10), nullable=False, server_default="ar"),
        sa.Column("context", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["brand_id"], ["brands.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("brand_id", "term", "language", name="uq_brand_terms_brand_term_language"),
        sa.CheckConstraint("language IN ('ar','en')", name="brand_term_language_allowed"),
        sa.CheckConstraint("length(trim(term)) > 0", name="brand_term_not_blank"),
        sa.CheckConstraint("length(trim(preferred_form)) > 0", name="brand_term_preferred_not_blank"),
    )
    op.create_index("ix_brand_terms_brand_language", "brand_terms", ["brand_id", "language"])

    op.create_table(
        "platforms",
        sa.Column("id", uuid_type(), primary_key=True, nullable=False),
        sa.Column("key", sa.String(50), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("capabilities", jsonb(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("key", name="uq_platforms_key"),
        sa.CheckConstraint("length(trim(key)) > 0", name="platform_key_not_blank"),
    )

    op.create_table(
        "brand_platform_profiles",
        sa.Column("id", uuid_type(), primary_key=True, nullable=False),
        sa.Column("brand_id", uuid_type(), nullable=False),
        sa.Column("platform_id", uuid_type(), nullable=False),
        sa.Column("language", sa.String(10), nullable=False, server_default="ar"),
        sa.Column("voice_id", uuid_type(), nullable=True),
        sa.Column("tone", sa.String(150), nullable=True),
        sa.Column("style_config", jsonb(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("content_rules", jsonb(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("default_hashtags", jsonb(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("default_cta", sa.Text(), nullable=True),
        sa.Column("max_length", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["brand_id"], ["brands.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["platform_id"], ["platforms.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["voice_id", "brand_id"],
            ["brand_voices.id", "brand_voices.brand_id"],
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint(
            "brand_id", "platform_id", "language",
            name="uq_brand_platform_profiles_brand_platform_language",
        ),
        sa.CheckConstraint("language IN ('ar','en')", name="brand_platform_profile_language_allowed"),
        sa.CheckConstraint(
            "max_length IS NULL OR max_length > 0",
            name="brand_platform_profile_max_length_positive",
        ),
    )
    op.create_index(
        "ix_brand_platform_profiles_brand_platform_active",
        "brand_platform_profiles",
        ["brand_id", "platform_id", "is_active"],
    )

    op.create_table(
        "platform_accounts",
        sa.Column("id", uuid_type(), primary_key=True, nullable=False),
        sa.Column("workspace_id", uuid_type(), nullable=False),
        sa.Column("brand_id", uuid_type(), nullable=False),
        sa.Column("platform_id", uuid_type(), nullable=False),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("external_account_id", sa.String(255), nullable=False),
        sa.Column("username", sa.String(255), nullable=True),
        sa.Column("account_metadata", jsonb(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("credentials_reference", sa.String(500), nullable=True),
        sa.Column("status", platform_account_status, nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["platform_id"], ["platforms.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["brand_id", "workspace_id"],
            ["brands.id", "brands.workspace_id"],
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint(
            "platform_id", "external_account_id",
            name="uq_platform_accounts_platform_external_id",
        ),
        sa.CheckConstraint("length(trim(name)) > 0", name="platform_account_name_not_blank"),
        sa.CheckConstraint(
            "length(trim(external_account_id)) > 0",
            name="platform_account_external_id_not_blank",
        ),
    )
    op.create_index(
        "ix_platform_accounts_workspace_brand",
        "platform_accounts",
        ["workspace_id", "brand_id"],
    )
    op.create_index(
        "ix_platform_accounts_brand_platform_status",
        "platform_accounts",
        ["brand_id", "platform_id", "status"],
    )

    op.create_table(
        "brand_member_roles",
        sa.Column("id", uuid_type(), primary_key=True, nullable=False),
        sa.Column("workspace_id", uuid_type(), nullable=False),
        sa.Column("brand_id", uuid_type(), nullable=False),
        sa.Column("workspace_member_id", uuid_type(), nullable=False),
        sa.Column("role_id", uuid_type(), nullable=False),
        sa.Column("role_scope", role_scope, nullable=False, server_default="brand"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(
            ["brand_id", "workspace_id"],
            ["brands.id", "brands.workspace_id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["workspace_member_id", "workspace_id"],
            ["workspace_members.id", "workspace_members.workspace_id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["role_id", "workspace_id", "role_scope"],
            ["roles.id", "roles.workspace_id", "roles.scope"],
            ondelete="CASCADE",
        ),
        sa.CheckConstraint("role_scope = 'brand'", name="brand_member_role_scope_valid"),
        sa.UniqueConstraint(
            "workspace_member_id", "brand_id", "role_id",
            name="uq_brand_member_roles_member_brand_role",
        ),
    )
    op.create_index(
        "ix_brand_member_roles_brand_member",
        "brand_member_roles",
        ["brand_id", "workspace_member_id"],
    )

    permission_rows = [
        ("workspace.view", "View workspace"),
        ("workspace.manage", "Manage workspace settings"),
        ("team.view", "View workspace team"),
        ("team.manage", "Manage workspace team"),
        ("roles.view", "View roles"),
        ("roles.manage", "Create and manage roles"),
        ("brands.view", "View brands"),
        ("brands.manage", "Create and manage brands"),
        ("brand_identity.view", "View brand identity"),
        ("brand_identity.manage", "Manage brand identity"),
        ("content.create", "Create content"),
        ("content.view", "View content"),
        ("content.edit", "Edit content"),
        ("content.delete", "Delete content"),
        ("content.approve", "Approve content"),
        ("publication.create", "Create publication jobs"),
        ("publication.publish", "Publish content"),
        ("analytics.view", "View analytics"),
        ("agent.run", "Run agents"),
        ("agent.configure", "Configure agents"),
        ("settings.manage", "Manage system settings"),
    ]

    permission_values = []
    for key, description in permission_rows:
        permission_values.append(
            {
                "id": uuid.uuid5(uuid.NAMESPACE_URL, f"mena-content-agent:permission:{key}"),
                "key": key,
                "description": description,
            }
        )

    op.bulk_insert(
        sa.table(
            "permissions",
            sa.column("id", uuid_type()),
            sa.column("key", sa.String(120)),
            sa.column("description", sa.Text()),
        ),
        permission_values,
    )

    platform_rows = [
        ("telegram", "Telegram", {"text": True, "image": True, "video": True}),
        ("x", "X", {"text": True, "image": True, "video": True}),
        ("reddit", "Reddit", {"text": True, "image": True, "video": True}),
        ("youtube", "YouTube", {"text": True, "image": True, "video": True}),
        ("instagram", "Instagram", {"text": True, "image": True, "video": True}),
        ("linkedin", "LinkedIn", {"text": True, "image": True, "video": True}),
    ]

    platform_values = []
    for key, name, capabilities in platform_rows:
        platform_values.append(
            {
                "id": uuid.uuid5(uuid.NAMESPACE_URL, f"mena-content-agent:platform:{key}"),
                "key": key,
                "name": name,
                "capabilities": json.dumps(capabilities, separators=(",", ":")),
            }
        )

    op.bulk_insert(
        sa.table(
            "platforms",
            sa.column("id", uuid_type()),
            sa.column("key", sa.String(50)),
            sa.column("name", sa.String(100)),
            sa.column("capabilities", sa.Text()),
        ),
        platform_values,
    )


def downgrade() -> None:
    for table in (
        "brand_member_roles",
        "platform_accounts",
        "brand_platform_profiles",
        "platforms",
        "brand_terms",
        "brand_rules",
        "brand_audiences",
        "brand_voices",
        "brand_identities",
        "brands",
        "workspace_member_roles",
        "role_permissions",
        "roles",
        "permissions",
        "workspace_members",
        "users",
        "workspaces",
    ):
        op.drop_table(table)

    for enum_name in (
        "platform_account_status",
        "brand_rule_type",
        "brand_rule_severity",
        "brand_status",
        "role_scope",
        "membership_status",
        "user_status",
        "workspace_status",
    ):
        sa.Enum(name=enum_name).drop(op.get_bind(), checkfirst=True)
