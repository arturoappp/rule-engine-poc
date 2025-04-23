"""
Application configuration settings.
"""
import os

from pydantic import Field
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings."""

    # Base config
    PROJECT_NAME: str = "Rule Engine API"
    PROJECT_DESCRIPTION: str = "A flexible rule engine for evaluating conditions against data"
    VERSION: str = "1.0.0"
    API_PREFIX: str = "/api/v1"
    PORT: int = int("8080")

    # CORS settings
    ALLOWED_ORIGINS: List[str] = Field(default_factory=lambda: ["*"])

    # Rule engine settings
    DEFAULT_ENTITY_TYPE: str = "generic"
    MAX_RULES_PER_REQUEST: int = 100

    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        case_sensitive = True


settings = Settings()
