from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """Application settings loaded from environment variables."""

    app_name: str = "ShopPilot API"
    app_version: str = "0.1.0"
    debug: bool = False
    log_level: str = "INFO"
    api_prefix: str = "/api"

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            app_name=os.getenv("APP_NAME", cls.app_name),
            app_version=os.getenv("APP_VERSION", cls.app_version),
            debug=os.getenv("DEBUG", "false").lower() == "true",
            log_level=os.getenv("LOG_LEVEL", cls.log_level).upper(),
            api_prefix=os.getenv("API_PREFIX", cls.api_prefix),
        )


settings = Settings.from_env()
