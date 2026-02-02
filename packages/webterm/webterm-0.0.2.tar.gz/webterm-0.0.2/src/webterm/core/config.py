"""Configuration settings for webterm."""

import os
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    host: str = "127.0.0.1"
    port: int = 8000
    reload: bool = False
    shell: Optional[str] = None
    max_sessions: int = 10
    session_timeout: int = 3600  # 1 hour in seconds
    log_level: str = "INFO"
    token: Optional[str] = None  # Authentication token (if set, auth is required)

    class Config:
        env_prefix = "WEBTERM_"
        env_file = ".env"
        env_file_encoding = "utf-8"

    def get_shell(self) -> str:
        """Get the shell to use, defaulting to user's shell or /bin/bash."""
        if self.shell:
            return self.shell
        return os.environ.get("SHELL", "/bin/bash")


settings = Settings()
