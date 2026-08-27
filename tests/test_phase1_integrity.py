from sqlalchemy import CheckConstraint, Index, UniqueConstraint

from app.models import Base


def _constraints(table_name):
    return Base.metadata.tables[table_name].constraints


def test_language_checks_are_declared_on_all_language_scoped_tables():
    expected = {
        "workspaces": "workspace_language_allowed",
        "users": "user_language_allowed",
        "brands": "brand_language_allowed",
        "brand_audiences": "brand_audience_language_allowed",
        "brand_terms": "brand_term_language_allowed",
        "brand_platform_profiles": "brand_platform_profile_language_allowed",
    }
    for table_name, name in expected.items():
        assert any(isinstance(c, CheckConstraint) and c.name.endswith(name) for c in _constraints(table_name))


def test_brand_voice_has_one_default_per_brand_contract():
    table = Base.metadata.tables["brand_voices"]
    indexes = [i for i in table.indexes if i.name == "uq_brand_voices_one_default_per_brand"]
    assert len(indexes) == 1
    assert indexes[0].unique is True
    assert str(indexes[0].dialect_options["postgresql"].get("where")) == "brand_voices.is_default IS true"


def test_brand_platform_profile_voice_is_brand_scoped():
    table = Base.metadata.tables["brand_platform_profiles"]
    fks = {tuple(f.column_keys) for f in table.foreign_key_constraints}
    assert ("voice_id", "brand_id") in fks


def test_brand_platform_profile_platform_is_restricted_on_delete():
    table = Base.metadata.tables["brand_platform_profiles"]
    fk = next(f for f in table.foreign_key_constraints if tuple(f.column_keys) == ("platform_id",))
    assert fk.ondelete == "RESTRICT"


def test_platform_account_identity_is_unique_per_platform():
    table = Base.metadata.tables["platform_accounts"]
    assert any(
        isinstance(c, UniqueConstraint)
        and tuple(c.columns.keys()) == ("platform_id", "external_account_id")
        for c in table.constraints
    )


def test_all_authoritative_tables_compile_for_postgresql():
    from sqlalchemy.schema import CreateTable
    from sqlalchemy.dialects.postgresql import dialect

    pg = dialect()
    for table in Base.metadata.sorted_tables:
        sql = str(CreateTable(table).compile(dialect=pg))
        assert f'CREATE TABLE {table.name}' in sql
