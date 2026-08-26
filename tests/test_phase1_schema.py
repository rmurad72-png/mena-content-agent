from app.models import Base


EXPECTED_TABLES = {
    "workspaces",
    "users",
    "workspace_members",
    "permissions",
    "roles",
    "role_permissions",
    "workspace_member_roles",
    "brands",
    "brand_identities",
    "brand_voices",
    "brand_audiences",
    "brand_rules",
    "brand_terms",
    "brand_member_roles",
    "platforms",
    "brand_platform_profiles",
    "platform_accounts",
}


def test_phase1_expected_tables_registered():
    assert EXPECTED_TABLES.issubset(Base.metadata.tables.keys())


def test_brand_platform_profile_unique_constraint():
    table = Base.metadata.tables["brand_platform_profiles"]
    constraints = {
        tuple(constraint.columns.keys())
        for constraint in table.constraints
        if constraint.__class__.__name__ == "UniqueConstraint"
    }
    assert ("brand_id", "platform_id", "language") in constraints


def test_platform_account_has_cross_tenant_brand_foreign_key():
    table = Base.metadata.tables["platform_accounts"]
    foreign_keys = {
        tuple(foreign_key.column_keys)
        for foreign_key in table.foreign_key_constraints
    }
    assert ("brand_id", "workspace_id") in foreign_keys
