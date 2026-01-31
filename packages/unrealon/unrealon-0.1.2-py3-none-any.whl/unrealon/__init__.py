"""
Unrealon SDK - Service management SDK for Django backend.

Example:
    ```python
    from unrealon import ServiceClient

    # Using context manager (recommended)
    with ServiceClient(api_key="...", service_name="my-service") as client:
        client.info("Processing started")
        for item in items:
            process(item)
            client.increment_processed()
        client.info("Processing complete")

    # Manual control
    client = ServiceClient(api_key="...", service_name="my-service")
    client.start()
    # ... do work ...
    client.stop()

    # Async client
    async with AsyncServiceClient(api_key="...", service_name="my-service") as client:
        await client.send_heartbeat()
    ```
"""

# Re-export enums for convenience
from ._api.generated.services.enums import (
    CommandCommandType,
    CommandStatus,
    LogEntryRequestLevel,
    ServiceStatus,
)
from ._client import AsyncParserClient, AsyncServiceClient, ParserClient, ServiceClient
from ._config import UnrealonConfig, configure, get_config, reset_config
from ._version import __version__

# Core components
from .core import (
    LifecycleConfig,
    LifecycleEvent,
    LifecycleManager,
    ServiceState,
    SignalHandler,
    SignalHandlerConfig,
    StateMachine,
    StateTransitionError,
)
from .exceptions import (
    APIError,
    AuthenticationError,
    HeartbeatError,
    NetworkError,
    NotFoundError,
    RateLimitError,
    RegistrationError,
    TimeoutError,
    UnrealonError,
    ValidationError,
)
from .services import (
    AsyncCommandService,
    AsyncHeartbeatService,
    AsyncLoggerService,
    AsyncRegistrarService,
    CommandService,
    HeartbeatService,
    LoggerService,
    RegistrarService,
)

__all__ = [
    # Version
    "__version__",
    # Config
    "UnrealonConfig",
    "configure",
    "get_config",
    "reset_config",
    # Main clients
    "ServiceClient",
    "AsyncServiceClient",
    # Backward compatibility
    "ParserClient",
    "AsyncParserClient",
    # Services
    "RegistrarService",
    "AsyncRegistrarService",
    "HeartbeatService",
    "AsyncHeartbeatService",
    "LoggerService",
    "AsyncLoggerService",
    "CommandService",
    "AsyncCommandService",
    # Exceptions
    "UnrealonError",
    "APIError",
    "AuthenticationError",
    "RegistrationError",
    "HeartbeatError",
    "ValidationError",
    "TimeoutError",
    "NetworkError",
    "NotFoundError",
    "RateLimitError",
    # Enums
    "ServiceStatus",
    "CommandCommandType",
    "CommandStatus",
    "LogEntryRequestLevel",
    # Core
    "LifecycleManager",
    "LifecycleConfig",
    "LifecycleEvent",
    "SignalHandler",
    "SignalHandlerConfig",
    "ServiceState",
    "StateMachine",
    "StateTransitionError",
]
