"""Configuration from RMAPI_* environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    """rmapi configuration"""

    model_config = SettingsConfigDict(env_prefix="RMAPI_")

    dns: str = "localmaeher.dev.pvarki.fi"


config = Config()
