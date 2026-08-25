from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "MENA Content Agent"
    environment: str = "production"
    bot_token: str
    telegram_webhook_secret: str
    admin_user_ids: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )

    @property
    def admin_ids(self) -> set[int]:
        if not self.admin_user_ids.strip():
            return set()

        return {
            int(value.strip())
            for value in self.admin_user_ids.split(",")
            if value.strip()
        }


settings = Settings()
