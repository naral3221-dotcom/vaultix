from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="VAULTIX_", env_file=".env")

    app_name: str = "Vaultix API"
    env: str = "development"
    version: str = "0.1.0"


@lru_cache
def get_settings() -> Settings:
    return Settings()

