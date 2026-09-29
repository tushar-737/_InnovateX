"""Application settings. Secrets live in .env only — never in frontend code."""

from functools import lru_cache

from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Kaushal Saathi"
    app_version: str = "0.1.0"
    # SQLite for the demo. Any PostgreSQL DSN works here — schema is portable.
    database_url: str = "sqlite:///./kaushal_saathi.db"

    # LLM (Anthropic Claude). If absent, a deterministic rule-based dialogue
    # engine is used automatically so the demo always works.
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-5"
    llm_max_tokens: int = 700

    # CORS: Vite dev server + common preview hosts.
    cors_origins: str = "*"

    model_config = ConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
