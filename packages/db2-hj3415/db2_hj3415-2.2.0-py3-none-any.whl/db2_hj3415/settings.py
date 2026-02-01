# db2_hj3415/settings.py
from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    MONGO_URI: str = "mongodb://192.168.100.172:27017"
    DB_NAME: str = "hj3415"

    # timeouts
    MONGO_CONNECT_TIMEOUT_MS: int = 5_000
    MONGO_SERVER_SELECTION_TIMEOUT_MS: int = 5_000

    # ✅ snapshot 보관 정책
    SNAPSHOT_TTL_DAYS: int | None = 730
    # - None 이면 TTL 인덱스 생성 안 함
    # - 0 이하도 비활성으로 간주해도 됨

def get_settings() -> Settings:
    return Settings()