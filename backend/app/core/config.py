from functools import lru_cache
from pathlib import Path

from pydantic import AnyHttpUrl, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Open Source Contributor Agent"
    app_env: str = Field(default="development", alias="APP_ENV")
    database_url: str = Field(
        default="postgresql+asyncpg://osca:osca@postgres:5432/osca",
        alias="DATABASE_URL",
    )
    redis_url: str = Field(default="redis://redis:6379/0", alias="REDIS_URL")
    allowed_origins: list[AnyHttpUrl] | list[str] = Field(
        default=["http://localhost:3000"],
        alias="ALLOWED_ORIGINS",
    )
    workspace_root: Path = Field(default=Path("/workspace"), alias="OSCA_WORKSPACE_ROOT")
    max_command_seconds: int = Field(default=120, alias="MAX_COMMAND_SECONDS")
    audit_stdout_limit: int = 12_000

    google_api_key: str | None = Field(default=None, alias="GOOGLE_API_KEY")
    anthropic_api_key: str | None = Field(default=None, alias="ANTHROPIC_API_KEY")
    openrouter_api_key: str | None = Field(default=None, alias="OPENROUTER_API_KEY")
    ollama_base_url: str = Field(default="http://ollama:11434", alias="OLLAMA_BASE_URL")
    github_token: str | None = Field(default=None, alias="GITHUB_TOKEN")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @field_validator("workspace_root")
    @classmethod
    def normalize_workspace_root(cls, value: Path) -> Path:
        return value.expanduser().resolve()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
