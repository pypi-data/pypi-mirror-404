"""Main SDK client with unified interface."""

from __future__ import annotations

import atexit
import logging
import signal
from collections.abc import Callable

from ._api.generated.services.enums import ServiceStatus
from ._config import UnrealonConfig, configure
from .exceptions import RegistrationError
from .services.commands import AsyncCommandService, CommandService
from .services.heartbeat import AsyncHeartbeatService, HeartbeatService
from .services.logger import AsyncLoggerService, LoggerService
from .services.registrar import AsyncRegistrarService, RegistrarService

logger = logging.getLogger(__name__)


class ServiceClient:
    """
    Main SDK client for service management.

    Provides unified interface for:
    - Registration and deregistration
    - Heartbeat (manual and automatic)
    - Logging (single and batched)
    - Command polling and execution

    Example:
        ```python
        # Initialize with config
        client = ServiceClient(
            api_key="pk_live_xxx",
            service_name="my-service",
        )

        # Start service lifecycle
        with client:
            client.info("Service started")
            # ... do work ...
            client.update_status(items_processed=100)

        # Or manual control
        client.start()
        # ... do work ...
        client.stop()
        ```
    """

    def __init__(
        self,
        api_key: str | None = None,
        service_name: str | None = None,
        *,
        api_url: str | None = None,
        source_code: str | None = None,
        heartbeat_interval: int | None = None,
        auto_heartbeat: bool = True,
        auto_commands: bool = True,
        auto_logging: bool = True,
        **kwargs,
    ):
        """
        Initialize service client.

        Args:
            api_key: API key (or UNREALON_API_KEY env var)
            service_name: Service name (or UNREALON_SERVICE_NAME env var)
            api_url: API URL (or UNREALON_API_URL env var)
            source_code: Source code identifier
            heartbeat_interval: Heartbeat interval in seconds
            auto_heartbeat: Auto-start heartbeat on registration
            auto_commands: Auto-start command polling on registration
            auto_logging: Auto-start log batching on registration
            **kwargs: Additional config options
        """
        # Build config kwargs
        config_kwargs = {}
        if api_key:
            config_kwargs["api_key"] = api_key
        if service_name:
            config_kwargs["service_name"] = service_name
        if api_url:
            config_kwargs["api_url"] = api_url
        if source_code:
            config_kwargs["source_code"] = source_code
        if heartbeat_interval:
            config_kwargs["heartbeat_interval"] = heartbeat_interval
        config_kwargs.update(kwargs)

        # Get or create config
        if config_kwargs:
            self._config = configure(**config_kwargs)
        else:
            from ._config import get_config

            self._config = get_config()

        # Settings
        self._auto_heartbeat = auto_heartbeat
        self._auto_commands = auto_commands
        self._auto_logging = auto_logging

        # State
        self._service_id: str | None = None
        self._is_started = False
        self._items_processed = 0
        self._errors_count = 0
        self._shutdown_requested = False

        # Services (lazy initialization)
        self._registrar: RegistrarService | None = None
        self._heartbeat: HeartbeatService | None = None
        self._logger: LoggerService | None = None
        self._commands: CommandService | None = None

        # Signal handling
        self._original_sigint = None
        self._original_sigterm = None

    @property
    def registrar(self) -> RegistrarService:
        """Get registrar service."""
        if self._registrar is None:
            self._registrar = RegistrarService(self._config)
        return self._registrar

    @property
    def heartbeat(self) -> HeartbeatService:
        """Get heartbeat service."""
        if self._heartbeat is None:
            self._heartbeat = HeartbeatService(self._config)
        return self._heartbeat

    @property
    def log(self) -> LoggerService:
        """Get logger service."""
        if self._logger is None:
            self._logger = LoggerService(self._config)
        return self._logger

    @property
    def commands(self) -> CommandService:
        """Get command service."""
        if self._commands is None:
            self._commands = CommandService(self._config)
        return self._commands

    @property
    def service_id(self) -> str | None:
        """Get registered service ID."""
        return self._service_id

    @property
    def is_started(self) -> bool:
        """Check if client is started."""
        return self._is_started

    @property
    def shutdown_requested(self) -> bool:
        """Check if shutdown was requested."""
        return self._shutdown_requested

    @property
    def items_processed(self) -> int:
        """Get total items processed."""
        return self._items_processed

    @property
    def errors_count(self) -> int:
        """Get total errors count."""
        return self._errors_count

    @property
    def config(self) -> UnrealonConfig:
        """Get configuration."""
        return self._config

    def start(
        self,
        *,
        description: str | None = None,
        metadata: dict | None = None,
    ) -> str:
        """
        Start service: register and start background services.

        Args:
            description: Service description
            metadata: Additional metadata

        Returns:
            Service ID
        """
        if self._is_started:
            logger.warning("Client already started")
            return self._service_id

        logger.info("Starting service client: name=%s", self._config.service_name)

        # Register
        try:
            response = self.registrar.register(
                description=description,
                metadata=metadata,
            )
            self._service_id = response.service_id
        except Exception as e:
            raise RegistrationError(
                message=f"Failed to register service: {e}",
                original_error=e,
            )

        # Start background services
        if self._auto_heartbeat:
            self.heartbeat.start_background(
                self._service_id,
                status=ServiceStatus.RUNNING,
            )

        if self._auto_commands:
            self.commands.start_polling(self._service_id)

        if self._auto_logging:
            self.log.start_batching(self._service_id)

        self._is_started = True

        # Setup shutdown handlers
        self._setup_signal_handlers()
        atexit.register(self._atexit_handler)

        logger.info("Service client started: service_id=%s", self._service_id)

        return self._service_id

    def stop(self) -> None:
        """Stop service: stop services and deregister."""
        if not self._is_started:
            return

        logger.info("Stopping service client...")

        # Update status
        if self._heartbeat and self._heartbeat.is_running:
            self._heartbeat.update_status(ServiceStatus.STOPPING)

        # Stop background services
        if self._commands:
            self._commands.stop_polling()

        if self._logger:
            self._logger.stop_batching()

        if self._heartbeat:
            self._heartbeat.stop_background()

        # Deregister
        if self._service_id:
            try:
                self.registrar.deregister(self._service_id)
                logger.info("Service deregistered")
            except Exception as e:
                logger.error("Failed to deregister: %s", e)

        # Close HTTP clients
        if self._registrar:
            self._registrar.close()
        if self._heartbeat:
            self._heartbeat.close()
        if self._logger:
            self._logger.close()
        if self._commands:
            self._commands.close()

        self._is_started = False
        self._service_id = None

        logger.info("Service client stopped")

    def update_status(
        self,
        *,
        status: ServiceStatus | None = None,
        items_processed: int | None = None,
        errors_count: int | None = None,
        extra_data: dict | None = None,
    ) -> None:
        """
        Update service status for heartbeat.

        Args:
            status: New service status
            items_processed: Total items processed
            errors_count: Total errors count
            extra_data: Additional metrics
        """
        if items_processed is not None:
            self._items_processed = items_processed
        if errors_count is not None:
            self._errors_count = errors_count

        if self._heartbeat and self._heartbeat.is_running:
            self._heartbeat.update_status(
                status=status or ServiceStatus.RUNNING,
                items_processed=self._items_processed,
                errors_count=self._errors_count,
                extra_data=extra_data,
            )

    def increment_processed(self, count: int = 1) -> None:
        """Increment processed items counter."""
        self._items_processed += count
        self.update_status(items_processed=self._items_processed)

    def increment_errors(self, count: int = 1) -> None:
        """Increment error counter."""
        self._errors_count += count
        self.update_status(errors_count=self._errors_count)

    # Logging shortcuts
    def debug(self, message: str, **kwargs) -> None:
        """Log debug message."""
        self.log.debug(message, **kwargs)

    def info(self, message: str, **kwargs) -> None:
        """Log info message."""
        self.log.info(message, **kwargs)

    def warning(self, message: str, **kwargs) -> None:
        """Log warning message."""
        self.log.warning(message, **kwargs)

    def error(self, message: str, **kwargs) -> None:
        """Log error message."""
        self.log.error(message, **kwargs)

    def critical(self, message: str, **kwargs) -> None:
        """Log critical message."""
        self.log.critical(message, **kwargs)

    # Command handlers
    def on_command(self, command_type: str, handler: Callable) -> None:
        """Register command handler."""
        self.commands.register_handler(command_type, handler)

    def on_any_command(self, handler: Callable) -> None:
        """Register default command handler."""
        self.commands.register_default_handler(handler)

    def request_shutdown(self) -> None:
        """Request graceful shutdown (sets flag for main loop to check)."""
        self._shutdown_requested = True
        logger.info("Shutdown requested")

    # Context manager
    def __enter__(self) -> ServiceClient:
        """Start client on context enter."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Stop client on context exit."""
        if exc_type is not None:
            logger.error("Service exiting with error: %s", exc_val)
            self.update_status(status=ServiceStatus.ERROR)
        self.stop()

    def _setup_signal_handlers(self) -> None:
        """Setup graceful shutdown signal handlers."""

        def signal_handler(signum, _frame):
            logger.info("Received signal %d, requesting shutdown...", signum)
            self._shutdown_requested = True

        try:
            self._original_sigint = signal.signal(signal.SIGINT, signal_handler)
            self._original_sigterm = signal.signal(signal.SIGTERM, signal_handler)
        except ValueError:
            # Signal handling not available (e.g., not in main thread)
            pass

    def _atexit_handler(self) -> None:
        """Handle process exit."""
        if self._is_started:
            self.stop()


class AsyncServiceClient:
    """Async version of ServiceClient."""

    def __init__(
        self,
        api_key: str | None = None,
        service_name: str | None = None,
        *,
        api_url: str | None = None,
        source_code: str | None = None,
        **kwargs,
    ):
        """Initialize async service client."""
        config_kwargs = {}
        if api_key:
            config_kwargs["api_key"] = api_key
        if service_name:
            config_kwargs["service_name"] = service_name
        if api_url:
            config_kwargs["api_url"] = api_url
        if source_code:
            config_kwargs["source_code"] = source_code
        config_kwargs.update(kwargs)

        if config_kwargs:
            self._config = configure(**config_kwargs)
        else:
            from ._config import get_config

            self._config = get_config()

        self._service_id: str | None = None
        self._is_started = False

        # Services
        self._registrar: AsyncRegistrarService | None = None
        self._heartbeat: AsyncHeartbeatService | None = None
        self._logger: AsyncLoggerService | None = None
        self._commands: AsyncCommandService | None = None

    @property
    def registrar(self) -> AsyncRegistrarService:
        """Get async registrar service."""
        if self._registrar is None:
            self._registrar = AsyncRegistrarService(self._config)
        return self._registrar

    @property
    def heartbeat(self) -> AsyncHeartbeatService:
        """Get async heartbeat service."""
        if self._heartbeat is None:
            self._heartbeat = AsyncHeartbeatService(self._config)
        return self._heartbeat

    @property
    def log(self) -> AsyncLoggerService:
        """Get async logger service."""
        if self._logger is None:
            self._logger = AsyncLoggerService(self._config)
        return self._logger

    @property
    def commands(self) -> AsyncCommandService:
        """Get async command service."""
        if self._commands is None:
            self._commands = AsyncCommandService(self._config)
        return self._commands

    @property
    def service_id(self) -> str | None:
        """Get registered service ID."""
        return self._service_id

    @property
    def is_started(self) -> bool:
        """Check if client is started."""
        return self._is_started

    async def start(
        self,
        *,
        description: str | None = None,
        metadata: dict | None = None,
    ) -> str:
        """Start service (async)."""
        if self._is_started:
            return self._service_id

        logger.info("Starting async service client: name=%s", self._config.service_name)

        try:
            response = await self.registrar.register(
                description=description,
                metadata=metadata,
            )
            self._service_id = response.service_id
        except Exception as e:
            raise RegistrationError(
                message=f"Failed to register service: {e}",
                original_error=e,
            )

        self._is_started = True
        logger.info("Async service client started: service_id=%s", self._service_id)

        return self._service_id

    async def stop(self) -> None:
        """Stop service (async)."""
        if not self._is_started:
            return

        logger.info("Stopping async service client...")

        if self._service_id:
            try:
                await self.registrar.deregister(self._service_id)
            except Exception as e:
                logger.error("Failed to deregister: %s", e)

        # Close HTTP clients
        if self._registrar:
            await self._registrar.close()
        if self._heartbeat:
            await self._heartbeat.close()
        if self._logger:
            await self._logger.close()
        if self._commands:
            await self._commands.close()

        self._is_started = False
        self._service_id = None

        logger.info("Async service client stopped")

    async def send_heartbeat(
        self,
        *,
        status: ServiceStatus | None = None,
        items_processed: int | None = None,
        errors_count: int | None = None,
        extra_data: dict | None = None,
    ):
        """Send manual heartbeat (async)."""
        if not self._service_id:
            raise RuntimeError("Client not started")

        return await self.heartbeat.send(
            self._service_id,
            status=status,
            items_processed=items_processed,
            errors_count=errors_count,
            extra_data=extra_data,
        )

    async def __aenter__(self) -> AsyncServiceClient:
        """Start client on async context enter."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Stop client on async context exit."""
        await self.stop()


# Backward compatibility aliases
ParserClient = ServiceClient
AsyncParserClient = AsyncServiceClient


__all__ = ["ServiceClient", "AsyncServiceClient", "ParserClient", "AsyncParserClient"]
