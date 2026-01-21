from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _default_data_dir() -> str:
    return str(Path(__file__).resolve().parents[2] / "data")


def _normalize_database_url(database_url: str) -> str:
    if database_url.startswith("postgres://"):
        return database_url.replace("postgres://", "postgresql+psycopg://", 1)
    if database_url.startswith("postgresql://") and "postgresql+" not in database_url:
        return database_url.replace("postgresql://", "postgresql+psycopg://", 1)
    return database_url


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str | None = None
    data_dir: str = Field(default_factory=_default_data_dir)

    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "iu_project"
    db_user: str = "postgres"
    db_password: str = "postgres"

    @model_validator(mode="after")
    def _build_database_url(self) -> "Settings":
        if self.database_url:
            self.database_url = _normalize_database_url(self.database_url)
            return self
        self.database_url = (
            f"postgresql+psycopg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
