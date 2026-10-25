from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    aws_region: str = "us-east-1"
    aws_endpoint_url: str | None = None
    table_name: str = "metermind"
    bucket_name: str = "metermind-photos"

    models_dir: Path = Path("models")
    vision_url: str | None = None

    llm_provider: Literal["gemini", "bedrock", "none"] = "none"
    llm_timeout_seconds: float = 4.0
    gemini_api_key: SecretStr | None = None
    gemini_model: str = "gemini-2.5-flash"
    bedrock_model_id: str = "us.amazon.nova-lite-v1:0"

    timezone: str = "Asia/Kolkata"
    public_base_url: str = "http://localhost:8000"
    session_ttl_hours: int = 24
    max_photo_bytes: int = 15 * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()
