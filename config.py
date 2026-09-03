from __future__ import annotations

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    bot_token: str = Field(
        validation_alias=AliasChoices("BOT_TOKEN", "TELEGRAM_BOT_TOKEN")
    )
    admin_ids: list[int] = Field(default_factory=list)
    environment: str = "production"
    telegram_channel_id: str = Field(
        validation_alias=AliasChoices("TELEGRAM_CHANNEL_ID", "CHANNEL_ID")
    )
    database_url: str | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "DATABASE_URL",
            "DATABASE_PRIVATE_URL",
            "POSTGRES_PRIVATE_URL",
        ),
    )

    model_config = SettingsConfigDict(
        case_sensitive=False,
        extra="ignore",
        populate_by_name=True,
    )

    @field_validator("database_url")
    @classmethod
    def reject_unresolved_railway_reference(cls, value: str | None) -> str | None:
        if value is not None and value.strip().startswith("${{"):
            raise ValueError(
                "database_url contains an unresolved Railway variable reference. "
                "Link PostgreSQL to the service and expose the resolved value as "
                "DATABASE_URL (or DATABASE_PRIVATE_URL)."
            )
        return value


settings = Settings()
