from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]
    allowed_hosts: list[str] = ["localhost", "127.0.0.1"]
    app_name: str = "CareReady API"
    environment: Literal["development", "test", "production"] = "development"
    database_url: str = (
        "postgresql+asyncpg://careready:local-development-only@127.0.0.1:5434/careready"
    )
    redis_url: str = "redis://127.0.0.1:6382/0"
    jwt_secret_key: SecretStr | None = Field(default=None, min_length=32)
    jwt_algorithm: Literal["HS256"] = "HS256"
    access_token_minutes: int = Field(default=15, gt=0)
    refresh_token_days: int = Field(default=2, gt=0)
