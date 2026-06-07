"""Configuration management for the Slack Adapter service."""

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Environment-driven settings loaded from .env file."""

    SLACK_SIGNING_SECRET: str = ""
    SLACK_BOT_TOKEN: str = ""
    AI_SERVICE_URL: str = "http://ai-service:8000"
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
