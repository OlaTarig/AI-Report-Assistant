from functools import lru_cache
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    gemini_api_key: str
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/reports"
    max_file_size_mb: int = 20
    upload_dir: str = "./storage/uploads"
    app_password: str = "changeme"
    session_secret: str = "changeme-session-secret"
    cors_origins: list[str] = ["http://localhost:3000"]

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
    @field_validator("database_url")
    @classmethod
    def fix_async_driver(cls, v: str) -> str:
            if v.startswith("postgresql://"):
                return v.replace("postgresql://", "postgresql+asyncpg://", 1)
            return v


@lru_cache
def get_settings() -> Settings:
    return Settings()
