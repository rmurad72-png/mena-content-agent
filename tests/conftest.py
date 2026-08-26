import os

# Provide harmless test-only settings before app.config is imported.
os.environ.setdefault("BOT_TOKEN", "test-token")
os.environ.setdefault("TELEGRAM_CHANNEL_ID", "-1000000000000")
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+psycopg://test:test@localhost:5432/testdb",
)
