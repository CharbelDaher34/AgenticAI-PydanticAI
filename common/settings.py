"""Settings and configuration for PydanticAI Masterclass.

This module provides centralized configuration management using Pydantic Settings.
All environment variables are loaded from .env file automatically.
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.
    
    Create a .env file in the project root with:
        OPENAI_API_KEY=sk-your-key-here
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    # Required
    openai_api_key: str = Field(
        ...,
        description="OpenAI API key for accessing GPT models",
    )
    
    # Optional - Other LLM providers
    anthropic_api_key: str | None = Field(
        default=None,
        description="Anthropic API key for Claude models",
    )
    
    google_api_key: str | None = Field(
        default=None,
        description="Google API key for Gemini models",
    )
    
    groq_api_key: str | None = Field(
        default=None,
        description="Groq API key",
    )
    
    # Application settings
    debug: bool = Field(
        default=False,
        description="Enable debug mode",
    )
    
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR)",
    )


# Global settings instance
# This will be imported throughout the application
settings = Settings()
