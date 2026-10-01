"""Configuration from RMAPI_* environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    """rmapi configuration"""

    model_config = SettingsConfigDict(env_prefix="RMAPI_")
    user_cert_duration: str = "8760h"
    dns: str = "localmaeher.dev.pvarki.fi"


config = Config()
