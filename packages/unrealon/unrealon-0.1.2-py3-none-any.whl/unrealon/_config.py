"""SDK configuration with environment variable support."""


from pydantic_settings import BaseSettings, SettingsConfigDict

from ._constants import (
    DEFAULT_API_URL,
    DEFAULT_COMMAND_POLL_INTERVAL,
    DEFAULT_HEARTBEAT_INTERVAL,
    DEFAULT_HEARTBEAT_TIMEOUT,
    DEFAULT_LOG_BATCH_SIZE,
    DEFAULT_LOG_FLUSH_INTERVAL,
    DEFAULT_MAX_RETRIES,
    DEFAULT_TIMEOUT,
)


class UnrealonConfig(BaseSettings):
    """
    SDK configuration with environment variable support.

    All settings can be configured via environment variables with UNREALON_ prefix.

    Example:
        UNREALON_API_KEY=pk_live_xxx
        UNREALON_SERVICE_NAME=my-service
        UNREALON_API_URL=http://127.0.0.1:8000
    """

    model_config = SettingsConfigDict(
        env_prefix="UNREALON_",
        env_file=".env",
        extra="ignore",
    )

    # Required credentials
    api_key: str
    service_name: str

    # API URL
    api_url: str = DEFAULT_API_URL

    # Heartbeat settings
    heartbeat_interval: int = DEFAULT_HEARTBEAT_INTERVAL
    heartbeat_timeout: float = DEFAULT_HEARTBEAT_TIMEOUT

    # Logging settings
    log_batch_size: int = DEFAULT_LOG_BATCH_SIZE
    log_flush_interval: float = DEFAULT_LOG_FLUSH_INTERVAL

    # Command settings
    command_poll_interval: int = DEFAULT_COMMAND_POLL_INTERVAL

    # HTTP settings
    timeout: float = DEFAULT_TIMEOUT
    max_retries: int = DEFAULT_MAX_RETRIES

    # Optional metadata
    service_version: str | None = None
    source_code: str | None = None


# Global config instance
_config: UnrealonConfig | None = None


def get_config() -> UnrealonConfig:
    """Get or create SDK configuration."""
    global _config
    if _config is None:
        _config = UnrealonConfig()
    return _config


def configure(**kwargs) -> UnrealonConfig:
    """Configure SDK with custom settings."""
    global _config
    _config = UnrealonConfig(**kwargs)
    return _config


def reset_config() -> None:
    """Reset configuration to defaults."""
    global _config
    _config = None
