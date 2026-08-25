from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    bot_token: str
    admin_ids: list[int] = []
    environment: str = "production"
    telegram_channel_id: str

    model_config = SettingsConfigDict(
        case_sensitive=False,
        extra="ignore"
    )


settings = Settings()
