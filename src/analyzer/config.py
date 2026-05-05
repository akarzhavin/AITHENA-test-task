"""Application configuration via pydantic-settings."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All tunables live here; sourced from env / .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- LLM -----------------------------------------------------------------
    openai_api_key: str
    openai_model: str = "gpt-4o-mini"
    openai_temperature: float = 0.0
    openai_max_tokens: int = 4096

    # --- Paths ---------------------------------------------------------------
    data_dir: Path = Path("data")
    output_dir: Path = Path("output")

    # --- Feature flags -------------------------------------------------------
    copyleft_function_threshold: int = 2
    force_rewrite: bool = False
