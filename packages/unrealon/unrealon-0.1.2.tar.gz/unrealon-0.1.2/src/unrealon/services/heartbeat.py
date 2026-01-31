"""Heartbeat service for maintaining service connection."""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable
from typing import TYPE_CHECKING

from .._api.client import AsyncBaseService, BaseService
from .._api.generated.services.enums import ServiceStatus
from .._api.generated.services.services__api__service_sdk.client import ServicesServiceSdkAPI
from .._api.generated.services.services__api__service_sdk.models import (
    ServiceHeartbeatRequest,
    ServiceHeartbeatResponse,
)

# Import generated API clients
from .._api.generated.services.services__api__service_sdk.sync_client import (
    SyncServicesServiceSdkAPI,
)
from ..exceptions import api_error_handler, async_api_error_handler
from ..utils.metrics import (
    get_cpu_percent,
    get_memory_mb,
    get_uptime_seconds,
)

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from .._config import UnrealonConfig


class HeartbeatService(BaseService):
    """
    Heartbeat service for maintaining service connection.

    Supports both manual heartbeats and automatic background heartbeats.

    Example:
        ```python
        heartbeat = HeartbeatService(config)

        # Manual heartbeat
        response = heartbeat.send(
            service_id="...",
            status=ServiceStatus.RUNNING,
        )

        # Background heartbeat
        heartbeat.start_background(service_id="...")
        # ... do work ...
        heartbeat.stop_background()
        ```
    """

    def __init__(self, config: UnrealonConfig):
        super().__init__(config)
        self._api = SyncServicesServiceSdkAPI(self._http_client)
        self._background_thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._service_id: str | None = None
        self._status: ServiceStatus = ServiceStatus.RUNNING
        self._items_processed: int = 0
        self._errors_count: int = 0
        self._extra_data: dict | None = None
        self._on_heartbeat: Callable[[ServiceHeartbeatResponse], None] | None = None

    @api_error_handler
    def send(
        self,
        service_id: str,
        *,
        status: ServiceStatus | None = None,
        items_processed: int | None = None,
        errors_count: int | None = None,
        extra_data: dict | None = None,
    ) -> ServiceHeartbeatResponse:
        """
        Send single heartbeat to server.

        Args:
            service_id: Service UUID from registration
            status: Current service status
            items_processed: Total items processed
            errors_count: Total errors count
            extra_data: Additional metrics data

        Returns:
            ServiceHeartbeatResponse with server time and pending commands count
        """
        data = ServiceHeartbeatRequest(
            service_id=service_id,
            status=status,
            memory_mb=get_memory_mb(),
            cpu_percent=get_cpu_percent(),
            uptime_seconds=get_uptime_seconds(),
            items_processed=items_processed,
            errors_count=errors_count,
            extra_data=extra_data,
        )

        logger.debug("Sending heartbeat: service_id=%s, status=%s", service_id, status)

        result = self._api.services_services_heartbeat_create(service_id, data)

        logger.debug(
            "Heartbeat response: received=%s, commands_pending=%d",
            result.received,
            result.commands_pending,
        )

        return result

    def start_background(
        self,
        service_id: str,
        *,
        interval: int | None = None,
        status: ServiceStatus = ServiceStatus.RUNNING,
        on_heartbeat: Callable[[ServiceHeartbeatResponse], None] | None = None,
    ) -> None:
        """
        Start background heartbeat thread.

        Args:
            service_id: Service UUID from registration
            interval: Heartbeat interval in seconds (default from config)
            status: Initial service status
            on_heartbeat: Optional callback for each heartbeat response
        """
        if self._background_thread is not None and self._background_thread.is_alive():
            logger.warning("Background heartbeat already running")
            return

        self._service_id = service_id
        self._status = status
        self._on_heartbeat = on_heartbeat
        self._stop_event.clear()

        interval = interval or self._config.heartbeat_interval

        self._background_thread = threading.Thread(
            target=self._heartbeat_loop,
            args=(interval,),
            daemon=True,
            name=f"heartbeat-{service_id[:8]}",
        )
        self._background_thread.start()

        logger.info(
            "Started background heartbeat: service_id=%s, interval=%ds", service_id, interval
        )

    def stop_background(self, timeout: float = 5.0) -> None:
        """
        Stop background heartbeat thread.

        Args:
            timeout: Maximum time to wait for thread to stop
        """
        if self._background_thread is None:
            return

        logger.info("Stopping background heartbeat...")
        self._stop_event.set()

        self._background_thread.join(timeout=timeout)
        if self._background_thread.is_alive():
            logger.warning("Heartbeat thread did not stop cleanly")

        self._background_thread = None
        self._service_id = None
        logger.info("Background heartbeat stopped")

    def update_status(
        self,
        status: ServiceStatus,
        *,
        items_processed: int | None = None,
        errors_count: int | None = None,
        extra_data: dict | None = None,
    ) -> None:
        """
        Update status for background heartbeat.

        Args:
            status: New service status
            items_processed: Total items processed
            errors_count: Total errors count
            extra_data: Additional metrics data
        """
        self._status = status
        if items_processed is not None:
            self._items_processed = items_processed
        if errors_count is not None:
            self._errors_count = errors_count
        if extra_data is not None:
            self._extra_data = extra_data

    @property
    def is_running(self) -> bool:
        """Check if background heartbeat is running."""
        return self._background_thread is not None and self._background_thread.is_alive()

    def _heartbeat_loop(self, interval: int) -> None:
        """Background heartbeat loop."""
        while not self._stop_event.wait(timeout=interval):
            if self._service_id is None:
                break

            try:
                response = self.send(
                    self._service_id,
                    status=self._status,
                    items_processed=self._items_processed,
                    errors_count=self._errors_count,
                    extra_data=self._extra_data,
                )

                if self._on_heartbeat:
                    try:
                        self._on_heartbeat(response)
                    except Exception as e:
                        logger.error("Error in heartbeat callback: %s", e)

            except Exception as e:
                logger.error("Heartbeat failed: %s", e)


class AsyncHeartbeatService(AsyncBaseService):
    """Async version of HeartbeatService (manual heartbeats only)."""

    def __init__(self, config: UnrealonConfig):
        super().__init__(config)
        self._api = ServicesServiceSdkAPI(self._http_client)

    @async_api_error_handler
    async def send(
        self,
        service_id: str,
        *,
        status: ServiceStatus | None = None,
        items_processed: int | None = None,
        errors_count: int | None = None,
        extra_data: dict | None = None,
    ) -> ServiceHeartbeatResponse:
        """Send single heartbeat (async)."""
        data = ServiceHeartbeatRequest(
            service_id=service_id,
            status=status,
            memory_mb=get_memory_mb(),
            cpu_percent=get_cpu_percent(),
            uptime_seconds=get_uptime_seconds(),
            items_processed=items_processed,
            errors_count=errors_count,
            extra_data=extra_data,
        )

        logger.debug("Sending heartbeat (async): service_id=%s", service_id)

        result = await self._api.services_services_heartbeat_create(service_id, data)

        logger.debug("Heartbeat response (async): received=%s", result.received)

        return result


__all__ = ["HeartbeatService", "AsyncHeartbeatService"]
