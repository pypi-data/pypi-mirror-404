"""Service registration service."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from .._api.client import AsyncBaseService, BaseService
from .._api.generated.services.services__api__service_sdk.client import ServicesServiceSdkAPI
from .._api.generated.services.services__api__service_sdk.models import (
    Service,
    ServiceRegistrationRequest,
    ServiceRegistrationResponse,
    ServiceRequest,
)

# Import generated API clients
from .._api.generated.services.services__api__service_sdk.sync_client import (
    SyncServicesServiceSdkAPI,
)
from .._version import __version__
from ..exceptions import api_error_handler, async_api_error_handler
from ..utils.system import (
    get_executable_path,
    get_hostname,
    get_pid,
    get_python_version,
    get_working_directory,
)

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from .._config import UnrealonConfig


class RegistrarService(BaseService):
    """
    Handles service registration and deregistration.

    Example:
        ```python
        registrar = RegistrarService(config)
        response = registrar.register()
        print(f"Registered: {response.service_id}")

        # Later...
        registrar.deregister(response.service_id)
        ```
    """

    def __init__(self, config: UnrealonConfig):
        super().__init__(config)
        self._api = SyncServicesServiceSdkAPI(self._http_client)

    @api_error_handler
    def register(
        self,
        *,
        description: str | None = None,
        metadata: dict | None = None,
    ) -> ServiceRegistrationResponse:
        """
        Register service with Django backend.

        Args:
            description: Service description
            metadata: Additional metadata dict

        Returns:
            ServiceRegistrationResponse with service_id and status
        """
        # Build registration data
        data = ServiceRegistrationRequest(
            name=self._config.service_name,
            hostname=get_hostname(),
            pid=get_pid(),
            description=description or "",
            source_code=self._config.source_code or "",
            executable_path=get_executable_path(),
            working_directory=get_working_directory(),
            sdk_version=__version__,
            python_version=get_python_version(),
            metadata=metadata or {},
        )

        logger.info(
            "Registering service: name=%s, hostname=%s, pid=%d",
            data.name,
            data.hostname,
            data.pid,
        )

        # Call API
        result = self._api.services_services_register_create(data)

        logger.info(
            "Service registered: service_id=%s, message=%s",
            result.service_id,
            result.message,
        )

        return result

    @api_error_handler
    def deregister(self, service_id: str) -> Service:
        """
        Deregister service from backend.

        Args:
            service_id: Service UUID from registration

        Returns:
            Service object
        """
        logger.info("Deregistering service: id=%s", service_id)

        data = ServiceRequest(
            name=self._config.service_name,
        )

        result = self._api.services_services_deregister_create(service_id, data)

        logger.info("Service deregistered: id=%s", service_id)

        return result


class AsyncRegistrarService(AsyncBaseService):
    """Async version of RegistrarService."""

    def __init__(self, config: UnrealonConfig):
        super().__init__(config)
        self._api = ServicesServiceSdkAPI(self._http_client)

    @async_api_error_handler
    async def register(
        self,
        *,
        description: str | None = None,
        metadata: dict | None = None,
    ) -> ServiceRegistrationResponse:
        """Register service (async)."""
        data = ServiceRegistrationRequest(
            name=self._config.service_name,
            hostname=get_hostname(),
            pid=get_pid(),
            description=description,
            source_code=self._config.source_code,
            executable_path=get_executable_path(),
            working_directory=get_working_directory(),
            sdk_version=__version__,
            python_version=get_python_version(),
            metadata=metadata,
        )

        logger.info("Registering service (async): name=%s", data.name)

        result = await self._api.services_services_register_create(data)

        logger.info("Service registered (async): service_id=%s", result.service_id)

        return result

    @async_api_error_handler
    async def deregister(self, service_id: str) -> Service:
        """Deregister service (async)."""
        logger.info("Deregistering service (async): id=%s", service_id)

        data = ServiceRequest(name=self._config.service_name)
        result = await self._api.services_services_deregister_create(service_id, data)

        logger.info("Service deregistered (async): id=%s", service_id)

        return result


__all__ = ["RegistrarService", "AsyncRegistrarService"]
