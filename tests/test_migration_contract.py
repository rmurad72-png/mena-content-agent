from pathlib import Path

MIGRATION = Path(__file__).resolve().parents[1] / "alembic" / "versions" / "001_phase1_workspace_brand_rbac.py"


def test_authoritative_migration_contains_brand_voice_composite_unique_key():
    text = MIGRATION.read_text()
    assert '"uq_brand_voices_id_brand"' in text
    assert 'sa.UniqueConstraint("id", "brand_id", name="uq_brand_voices_id_brand")' in text


def test_authoritative_migration_contains_brand_scoped_voice_fk():
    text = MIGRATION.read_text()
    assert '["voice_id", "brand_id"]' in text
    assert '["brand_voices.id", "brand_voices.brand_id"]' in text
    assert 'ondelete="RESTRICT"' in text


def test_authoritative_migration_contains_default_voice_partial_unique_index():
    text = MIGRATION.read_text()
    assert '"uq_brand_voices_one_default_per_brand"' in text
    assert 'postgresql_where=sa.text("is_default IS TRUE")' in text


def test_authoritative_migration_contains_language_constraints():
    text = MIGRATION.read_text()
    for name in (
        "workspace_language_allowed",
        "user_language_allowed",
        "brand_language_allowed",
        "brand_audience_language_allowed",
        "brand_term_language_allowed",
        "brand_platform_profile_language_allowed",
    ):
        assert name in text
