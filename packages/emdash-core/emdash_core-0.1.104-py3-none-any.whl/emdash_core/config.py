"""Server configuration."""

import os
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


def _get_default_model() -> str:
    """Get the default model from emdash_core or fallback."""
    try:
        from .agent.providers.factory import DEFAULT_MODEL
        return DEFAULT_MODEL
    except ImportError:
        # Fallback if not available
        return os.getenv("EMDASH_DEFAULT_MODEL", "fireworks:accounts/fireworks/models/minimax-m2p1")


class ServerConfig(BaseSettings):
    """Configuration for the emdash-core server."""

    # Server settings
    host: str = Field(default="127.0.0.1", description="Host to bind to")
    port: int = Field(default=8765, description="Port to bind to")

    # Repository settings
    repo_root: Optional[str] = Field(default=None, description="Repository root path")

    # Database settings
    database_path: str = Field(
        default=".emdash/index/kuzu_db",
        description="Path to Kuzu database relative to repo root"
    )

    # Agent settings
    default_model: str = Field(default_factory=_get_default_model, description="Default LLM model")
    max_iterations: int = Field(default=100, description="Max agent iterations")
    context_threshold: float = Field(default=0.6, description="Context window threshold for summarization")

    # SSE settings
    sse_ping_interval: int = Field(default=15, description="SSE ping interval in seconds")

    class Config:
        env_prefix = "EMDASH_"
        env_file = ".env"
        extra = "ignore"

    @property
    def database_full_path(self) -> Path:
        """Get full path to database."""
        if self.repo_root:
            return Path(self.repo_root) / self.database_path
        return Path(self.database_path)


# Global config instance
_config: Optional[ServerConfig] = None


def get_config() -> ServerConfig:
    """Get or create server configuration."""
    global _config
    if _config is None:
        _config = ServerConfig()
    return _config


def set_config(**kwargs) -> ServerConfig:
    """Set server configuration with overrides."""
    global _config
    _config = ServerConfig(**kwargs)
    return _config
