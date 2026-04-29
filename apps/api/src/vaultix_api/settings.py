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


@lru_cache
def get_settings() -> Settings:
    return Settings()
