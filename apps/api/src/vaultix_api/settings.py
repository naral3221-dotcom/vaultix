from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="VAULTIX_", env_file=".env")

    app_name: str = "Vaultix API"
    env: str = "development"
    version: str = "0.1.0"
    database_url: str = Field(
        default="postgresql+psycopg://vaultix:change-me@localhost:5440/vaultix",
        validation_alias="DATABASE_URL",
    )
    redis_url: str = Field(default="redis://localhost:6380/0", validation_alias="REDIS_URL")
    public_site_url: str = Field(
        default="http://127.0.0.1:8301", validation_alias="PUBLIC_SITE_URL"
    )
    resend_api_key: str = Field(default="", validation_alias="RESEND_API_KEY")
    mail_from: str = Field(default="", validation_alias="MAIL_FROM")
    turnstile_secret_key: str = Field(default="", validation_alias="TURNSTILE_SECRET_KEY")
    admin_emails: str = Field(default="", validation_alias="ADMIN_EMAILS")


@lru_cache
def get_settings() -> Settings:
    return Settings()
