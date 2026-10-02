"""Configuration from RMAPI_* environment variables."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    """rmapi configuration"""

    model_config = SettingsConfigDict(env_prefix="RMAPI_")
    dns: str = "localmaeher.dev.pvarki.fi"

    # JWT
    jwt_key_path: Path  # PEM private key
    jwt_lifetime: int = 60 * 60 * 4  # 4 hours, in seconds
    jwt_issuer: str = "rmapi"

    invite_code_length: int = 8

    @property
    def deployment(self) -> str:
        """First DNS label, e.g. localmaeher."""
        return self.dns.split(".", maxsplit=1)[0]


config = Config()
