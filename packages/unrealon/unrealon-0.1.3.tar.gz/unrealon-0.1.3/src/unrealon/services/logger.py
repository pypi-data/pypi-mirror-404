"""Logger service for sending logs to Django backend."""

from __future__ import annotations

import logging
import threading
import traceback
import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from .._api.client import AsyncBaseService, BaseService
from .._api.generated.services.enums import LogEntryRequestLevel
from .._api.generated.services.services__api__service_sdk.client import ServicesServiceSdkAPI
from .._api.generated.services.services__api__service_sdk.models import (
    LogBatchRequest,
    LogBatchResponse,
    LogEntryRequest,
)

# Import generated API clients
from .._api.generated.services.services__api__service_sdk.sync_client import (
    SyncServicesServiceSdkAPI,
)
from ..exceptions import api_error_handler, async_api_error_handler

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from .._config import UnrealonConfig


class LoggerService(BaseService):
    """
    Logger service for sending logs to Django backend.

    Supports batching and automatic flushing.

    Example:
        ```python
        logger_svc = LoggerService(config)

        # Single log
        logger_svc.log(
            service_id="...",
            level="info",
            message="Processing started",
        )

        # Batch mode with auto-flush
        logger_svc.start_batching(service_id="...")
        logger_svc.info("Step 1 complete")
        logger_svc.info("Step 2 complete")
        logger_svc.error("Step 3 failed", exception=e)
        logger_svc.flush()  # or wait for auto-flush
        ```
    """

    def __init__(self, config: UnrealonConfig):
        super().__init__(config)
        self._api = SyncServicesServiceSdkAPI(self._http_client)
        self._batch: list[LogEntryRequest] = []
        self._lock = threading.Lock()
        self._service_id: str | None = None
        self._run_id: str = str(uuid.uuid4())  # Auto-generate run_id at start
        self._flush_thread: threading.Thread | None = None
        self._stop_event = threading.Event()

    @api_error_handler
    def send_batch(
        self,
        service_id: str,
        entries: list[LogEntryRequest],
        *,
        run_id: str | None = None,
    ) -> LogBatchResponse:
        """
        Send batch of log entries.

        Args:
            service_id: Service UUID
            entries: List of log entries
            run_id: Optional run identifier

        Returns:
            LogBatchResponse with accepted/rejected counts
        """
        batch_id = str(uuid.uuid4())

        data = LogBatchRequest(
            service_id=service_id,
            batch_id=batch_id,
            entries=entries,
            run_id=run_id,
            created_at=datetime.now(timezone.utc).isoformat(),
        )

        logger.debug(
            "Sending log batch: service_id=%s, entries=%d",
            service_id,
            len(entries),
        )

        result = self._api.services_services_logs_batch_create(service_id, data)

        logger.debug(
            "Log batch response: accepted=%d, rejected=%d",
            result.accepted,
            result.rejected,
        )

        return result

    def log(
        self,
        service_id: str,
        level: str,
        message: str,
        *,
        extra: dict | None = None,
        exception: Exception | None = None,
        function: str | None = None,
        module: str | None = None,
        line_number: int | None = None,
        run_id: str | None = None,
    ) -> LogBatchResponse:
        """
        Send single log entry immediately.

        Args:
            service_id: Service UUID
            level: Log level (debug, info, warning, error, critical)
            message: Log message
            extra: Additional data
            exception: Exception to include
            function: Function name
            module: Module name
            line_number: Line number
            run_id: Optional run identifier

        Returns:
            LogBatchResponse
        """
        entry = self._create_entry(
            level=level,
            message=message,
            extra=extra,
            exception=exception,
            function=function,
            module=module,
            line_number=line_number,
        )

        return self.send_batch(service_id, [entry], run_id=run_id)

    def start_batching(
        self,
        service_id: str,
        *,
        run_id: str | None = None,
        auto_flush: bool = True,
    ) -> None:
        """
        Start batching mode.

        Args:
            service_id: Service UUID
            run_id: Optional run identifier (auto-generated if not provided)
            auto_flush: Whether to auto-flush periodically
        """
        self._service_id = service_id
        if run_id is not None:
            self._run_id = run_id
        # else keep the auto-generated run_id
        self._batch.clear()
        self._stop_event.clear()

        if auto_flush:
            self._flush_thread = threading.Thread(
                target=self._flush_loop,
                daemon=True,
                name=f"log-flush-{service_id[:8]}",
            )
            self._flush_thread.start()

        logger.info("Started log batching: service_id=%s", service_id)

    def stop_batching(self) -> None:
        """Stop batching mode and flush remaining logs."""
        if self._flush_thread:
            self._stop_event.set()
            self._flush_thread.join(timeout=5.0)
            self._flush_thread = None

        # Final flush
        self.flush()
        self._service_id = None
        # Generate new run_id for next session
        self._run_id = str(uuid.uuid4())
        logger.info("Stopped log batching")

    def set_run_id(self, run_id: str) -> None:
        """
        Set run ID for log correlation.

        Args:
            run_id: Run identifier string
        """
        self._run_id = run_id

    @property
    def run_id(self) -> str:
        """Get current run ID."""
        return self._run_id

    def add(
        self,
        level: str,
        message: str,
        *,
        extra: dict | None = None,
        exception: Exception | None = None,
        function: str | None = None,
        module: str | None = None,
        line_number: int | None = None,
    ) -> None:
        """
        Add log entry to batch (requires batching mode).

        Args:
            level: Log level
            message: Log message
            extra: Additional data
            exception: Exception to include
            function: Function name
            module: Module name
            line_number: Line number
        """
        entry = self._create_entry(
            level=level,
            message=message,
            extra=extra,
            exception=exception,
            function=function,
            module=module,
            line_number=line_number,
        )

        with self._lock:
            self._batch.append(entry)

            # Auto-flush if batch is full
            if len(self._batch) >= self._config.log_batch_size:
                self._flush_batch()

    def debug(self, message: str, **kwargs) -> None:
        """Add debug log entry."""
        self.add("debug", message, **kwargs)

    def info(self, message: str, **kwargs) -> None:
        """Add info log entry."""
        self.add("info", message, **kwargs)

    def warning(self, message: str, **kwargs) -> None:
        """Add warning log entry."""
        self.add("warning", message, **kwargs)

    def error(self, message: str, **kwargs) -> None:
        """Add error log entry."""
        self.add("error", message, **kwargs)

    def critical(self, message: str, **kwargs) -> None:
        """Add critical log entry."""
        self.add("critical", message, **kwargs)

    def flush(self) -> LogBatchResponse | None:
        """Flush pending log entries."""
        with self._lock:
            return self._flush_batch()

    def _flush_batch(self) -> LogBatchResponse | None:
        """Internal flush (must hold lock)."""
        if not self._batch or not self._service_id:
            return None

        entries = self._batch.copy()
        self._batch.clear()

        try:
            return self.send_batch(
                self._service_id,
                entries,
                run_id=self._run_id,
            )
        except Exception as e:
            logger.error("Failed to flush logs: %s", e)
            # Put entries back on failure
            self._batch.extend(entries)
            return None

    def _flush_loop(self) -> None:
        """Background flush loop."""
        while not self._stop_event.wait(timeout=self._config.log_flush_interval):
            with self._lock:
                if self._batch:
                    self._flush_batch()

    def _create_entry(
        self,
        level: str,
        message: str,
        *,
        extra: dict | None = None,
        exception: Exception | None = None,
        function: str | None = None,
        module: str | None = None,
        line_number: int | None = None,
    ) -> LogEntryRequest:
        """Create log entry from parameters."""
        # Map level string to enum
        level_map = {
            "debug": LogEntryRequestLevel.DEBUG,
            "info": LogEntryRequestLevel.INFO,
            "warning": LogEntryRequestLevel.WARNING,
            "error": LogEntryRequestLevel.ERROR,
            "critical": LogEntryRequestLevel.CRITICAL,
        }
        level_enum = level_map.get(level.lower(), LogEntryRequestLevel.INFO)

        entry = LogEntryRequest(
            level=level_enum,
            message=message,
            timestamp=datetime.now(timezone.utc).isoformat(),
            extra=extra,
            function=function,
            module=module,
            line_number=line_number,
        )

        if exception:
            entry.exception_type = type(exception).__name__
            entry.exception_message = str(exception)
            entry.traceback = "".join(
                traceback.format_exception(type(exception), exception, exception.__traceback__)
            )

        return entry

    @property
    def pending_count(self) -> int:
        """Number of pending log entries."""
        with self._lock:
            return len(self._batch)


class AsyncLoggerService(AsyncBaseService):
    """Async version of LoggerService (no batching, immediate sends)."""

    def __init__(self, config: UnrealonConfig):
        super().__init__(config)
        self._api = ServicesServiceSdkAPI(self._http_client)

    @async_api_error_handler
    async def send_batch(
        self,
        service_id: str,
        entries: list[LogEntryRequest],
        *,
        run_id: str | None = None,
    ) -> LogBatchResponse:
        """Send batch of log entries (async)."""
        batch_id = str(uuid.uuid4())

        data = LogBatchRequest(
            service_id=service_id,
            batch_id=batch_id,
            entries=entries,
            run_id=run_id,
            created_at=datetime.now(timezone.utc).isoformat(),
        )

        logger.debug("Sending log batch (async): service_id=%s", service_id)

        result = await self._api.services_services_logs_batch_create(service_id, data)

        return result

    async def log(
        self,
        service_id: str,
        level: str,
        message: str,
        *,
        extra: dict | None = None,
        exception: Exception | None = None,
        run_id: str | None = None,
    ) -> LogBatchResponse:
        """Send single log entry (async)."""
        # Map level string to enum
        level_map = {
            "debug": LogEntryRequestLevel.DEBUG,
            "info": LogEntryRequestLevel.INFO,
            "warning": LogEntryRequestLevel.WARNING,
            "error": LogEntryRequestLevel.ERROR,
            "critical": LogEntryRequestLevel.CRITICAL,
        }
        level_enum = level_map.get(level.lower(), LogEntryRequestLevel.INFO)

        entry = LogEntryRequest(
            level=level_enum,
            message=message,
            timestamp=datetime.now(timezone.utc).isoformat(),
            extra=extra,
        )

        if exception:
            entry.exception_type = type(exception).__name__
            entry.exception_message = str(exception)

        return await self.send_batch(service_id, [entry], run_id=run_id)


__all__ = ["LoggerService", "AsyncLoggerService"]
