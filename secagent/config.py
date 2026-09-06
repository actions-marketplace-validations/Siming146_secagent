"""Configuration settings for SecAgent using Pydantic Settings."""

import os
from functools import lru_cache
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """SecAgent system settings and environment variables."""

    # DeepSeek API Configuration
    deepseek_api_key: Optional[str] = Field(default=None, alias="DEEPSEEK_API_KEY")
    deepseek_base_url: str = Field(
        default="https://api.deepseek.com", alias="DEEPSEEK_BASE_URL"
    )
    deepseek_chat_model: str = Field(
        default="deepseek-chat", alias="DEEPSEEK_CHAT_MODEL"
    )
    deepseek_reasoner_model: str = Field(
        default="deepseek-reasoner", alias="DEEPSEEK_REASONER_MODEL"
    )

    # GitHub Integration
    github_token: Optional[str] = Field(default=None, alias="GITHUB_TOKEN")
    github_repository: Optional[str] = Field(default=None, alias="GITHUB_REPOSITORY")

    # Sandbox Limits
    sandbox_timeout_seconds: int = Field(default=60, alias="SANDBOX_TIMEOUT_SECONDS")
    sandbox_max_retries: int = Field(default=3, alias="SANDBOX_MAX_RETRIES")

    # Logging & Output
    secagent_log_level: str = Field(default="INFO", alias="SECAGENT_LOG_LEVEL")
    secagent_sarif_output: str = Field(
        default="results.sarif.json", alias="SECAGENT_SARIF_OUTPUT"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache()
def get_settings() -> Settings:
    """Return a cached singleton instance of Settings."""
    return Settings()
