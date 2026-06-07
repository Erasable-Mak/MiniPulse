"""Configuration management for the AI Service."""

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Environment-driven settings loaded from .env file."""

    HUBSPOT_ACCESS_TOKEN: str = ""
    GROQ_API_KEY: str = ""
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
