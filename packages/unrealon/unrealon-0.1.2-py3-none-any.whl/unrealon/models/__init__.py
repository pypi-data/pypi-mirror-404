"""
Re-exports of generated Pydantic models from OpenAPI.

Models are auto-generated from Django's OpenAPI schema.
Import from here for a stable public API.
"""

from __future__ import annotations

from .._api.generated.services.enums import (
    ApiKeyKeyType,
    CommandAckRequestStatus,
    CommandCommandType,
    CommandStatus,
    LogEntryRequestLevel,
    ServiceControlRequestAction,
    ServiceStatus,
)
from .._api.generated.services.services__api__service_commands.models import (
    Command,
    PaginatedCommandList,
)
from .._api.generated.services.services__api__service_sdk.models import (
    CommandAckRequest,
    CommandAckResponse,
    LogBatchRequest,
    LogBatchResponse,
    LogEntryRequest,
    Service,
    ServiceHeartbeatRequest,
    ServiceHeartbeatResponse,
    ServiceRegistrationRequest,
    ServiceRegistrationResponse,
    ServiceRequest,
)

__all__ = [
    # Registration
    "ServiceRegistrationRequest",
    "ServiceRegistrationResponse",
    "ServiceRequest",
    "Service",
    # Heartbeat
    "ServiceHeartbeatRequest",
    "ServiceHeartbeatResponse",
    # Logs
    "LogEntryRequest",
    "LogBatchRequest",
    "LogBatchResponse",
    # Commands
    "Command",
    "PaginatedCommandList",
    "CommandAckRequest",
    "CommandAckResponse",
    # Enums
    "ServiceStatus",
    "LogEntryRequestLevel",
    "CommandStatus",
    "CommandCommandType",
    "CommandAckRequestStatus",
    "ServiceControlRequestAction",
    "ApiKeyKeyType",
]
