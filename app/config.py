from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    bot_token: str
    telegram_webhook_secret: str
    admin_user_ids: str = ""
    environment: str = "production"

    @property
    def admin_ids(self) -> set[int]:
        return {
            int(value.strip())
            for value in self.admin_user_ids.split(",")
            if value.strip()
        }


settings = Settings()
