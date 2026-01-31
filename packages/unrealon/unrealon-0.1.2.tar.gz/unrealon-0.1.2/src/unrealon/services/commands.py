"""Command service for receiving and executing commands from Django backend."""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from .._api.client import AsyncBaseService, BaseService
from .._api.generated.services.enums import CommandAckRequestStatus
from .._api.generated.services.services__api__service_commands.models import (
    Command,
)
from .._api.generated.services.services__api__service_sdk.client import ServicesServiceSdkAPI
from .._api.generated.services.services__api__service_sdk.models import (
    CommandAckRequest,
    CommandAckResponse,
)

# Import generated API clients
from .._api.generated.services.services__api__service_sdk.sync_client import (
    SyncServicesServiceSdkAPI,
)
from ..exceptions import api_error_handler, async_api_error_handler

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from .._config import UnrealonConfig


# Type alias for command handler
CommandHandler = Callable[[Command], Any]


class CommandService(BaseService):
    """
    Command service for receiving and executing commands from Django backend.

    Supports both manual polling and automatic background polling with handlers.

    Example:
        ```python
        commands = CommandService(config)

        # Manual mode
        pending = commands.poll(service_id)
        for cmd in pending:
            result = execute_command(cmd)
            commands.acknowledge(cmd.id, status="completed", result=result)

        # Automatic mode with handlers
        commands.register_handler("restart", lambda cmd: restart_service())
        commands.start_polling(service_id)
        # ... commands are automatically executed ...
        commands.stop_polling()
        ```
    """

    def __init__(self, config: UnrealonConfig):
        super().__init__(config)
        self._sdk_api = SyncServicesServiceSdkAPI(self._http_client)
        self._handlers: dict[str, CommandHandler] = {}
        self._default_handler: CommandHandler | None = None
        self._poll_thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._service_id: str | None = None

    def poll(self, service_id: str) -> list[Command]:
        """
        Poll for pending commands.

        Args:
            service_id: Service UUID

        Returns:
            List of pending commands
        """
        logger.debug("Polling for commands: service_id=%s", service_id)

        try:
            url = f"/api/services/services/{service_id}/commands/"
            response = self._http_client.get(url)
            response.raise_for_status()
            data = response.json()

            # Handle paginated response
            if isinstance(data, dict) and "results" in data:
                commands = [Command.model_validate(cmd) for cmd in data["results"]]
            elif isinstance(data, list):
                commands = [Command.model_validate(cmd) for cmd in data]
            else:
                commands = []

            logger.debug("Found %d pending commands", len(commands))
            return commands
        except Exception as e:
            logger.error("Failed to poll commands: %s", e)
            return []

    @api_error_handler
    def acknowledge(
        self,
        command_id: str,
        status: str,
        *,
        result: dict | None = None,
        error: str | None = None,
    ) -> CommandAckResponse:
        """
        Acknowledge command execution.

        Args:
            command_id: Command UUID
            status: Status (acknowledged, executing, completed, failed)
            result: Command execution result
            error: Error message if failed

        Returns:
            CommandAckResponse
        """
        # Map status string to enum
        status_map = {
            "acknowledged": CommandAckRequestStatus.ACKNOWLEDGED,
            "executing": CommandAckRequestStatus.EXECUTING,
            "completed": CommandAckRequestStatus.COMPLETED,
            "failed": CommandAckRequestStatus.FAILED,
        }
        status_enum = status_map.get(status.lower(), CommandAckRequestStatus.ACKNOWLEDGED)

        data = CommandAckRequest(
            command_id=command_id,
            status=status_enum,
            result=result,
            error=error,
            executed_at=datetime.now(timezone.utc).isoformat()
            if status in ("completed", "failed")
            else None,
        )

        logger.debug("Acknowledging command: id=%s, status=%s", command_id, status)

        response = self._sdk_api.services_commands_ack_create(command_id, data)

        logger.debug("Command acknowledged: success=%s", response.success)

        return response

    def register_handler(
        self,
        command_type: str,
        handler: CommandHandler,
    ) -> None:
        """
        Register handler for specific command type.

        Args:
            command_type: Command type (start, stop, restart, pause, resume, update_config, custom)
            handler: Function to call when command is received
        """
        self._handlers[command_type] = handler
        logger.info("Registered handler for command type: %s", command_type)

    def register_default_handler(self, handler: CommandHandler) -> None:
        """
        Register default handler for unhandled command types.

        Args:
            handler: Function to call for unhandled commands
        """
        self._default_handler = handler
        logger.info("Registered default command handler")

    def start_polling(
        self,
        service_id: str,
        *,
        interval: int | None = None,
    ) -> None:
        """
        Start background command polling.

        Args:
            service_id: Service UUID
            interval: Poll interval in seconds (default from config)
        """
        if self._poll_thread is not None and self._poll_thread.is_alive():
            logger.warning("Command polling already running")
            return

        self._service_id = service_id
        self._stop_event.clear()
        interval = interval or self._config.command_poll_interval

        self._poll_thread = threading.Thread(
            target=self._poll_loop,
            args=(interval,),
            daemon=True,
            name=f"cmd-poll-{service_id[:8]}",
        )
        self._poll_thread.start()

        logger.info("Started command polling: service_id=%s, interval=%ds", service_id, interval)

    def stop_polling(self, timeout: float = 5.0) -> None:
        """
        Stop background command polling.

        Args:
            timeout: Maximum time to wait for thread to stop
        """
        if self._poll_thread is None:
            return

        logger.info("Stopping command polling...")
        self._stop_event.set()

        self._poll_thread.join(timeout=timeout)
        if self._poll_thread.is_alive():
            logger.warning("Polling thread did not stop cleanly")

        self._poll_thread = None
        self._service_id = None
        logger.info("Command polling stopped")

    @property
    def is_polling(self) -> bool:
        """Check if background polling is running."""
        return self._poll_thread is not None and self._poll_thread.is_alive()

    def execute(self, command: Command) -> Any:
        """
        Execute command using registered handler.

        Args:
            command: Command to execute

        Returns:
            Handler result
        """
        command_type = (
            command.command_type.value
            if hasattr(command.command_type, "value")
            else str(command.command_type)
        )

        # Find handler
        handler = self._handlers.get(command_type) or self._default_handler

        if handler is None:
            logger.warning("No handler for command type: %s", command_type)
            return None

        logger.info("Executing command: id=%s, type=%s", command.id, command_type)

        try:
            result = handler(command)
            return result
        except Exception as e:
            logger.error("Command execution failed: %s", e)
            raise

    def _poll_loop(self, interval: int) -> None:
        """Background polling loop."""
        while not self._stop_event.wait(timeout=interval):
            if self._service_id is None:
                break

            try:
                commands = self.poll(self._service_id)

                for command in commands:
                    self._process_command(command)

            except Exception as e:
                logger.error("Polling failed: %s", e)

    def _process_command(self, command: Command) -> None:
        """Process single command."""
        command_id = str(command.id)

        try:
            # Acknowledge receipt
            self.acknowledge(command_id, "acknowledged")

            # Execute
            self.acknowledge(command_id, "executing")
            result = self.execute(command)

            # Mark completed
            self.acknowledge(
                command_id,
                "completed",
                result={"result": result} if result else None,
            )

        except Exception as e:
            logger.error("Failed to process command %s: %s", command_id, e)
            try:
                self.acknowledge(command_id, "failed", error=str(e))
            except Exception as ack_error:
                logger.error("Failed to acknowledge error: %s", ack_error)


class AsyncCommandService(AsyncBaseService):
    """Async version of CommandService (manual polling only)."""

    def __init__(self, config: UnrealonConfig):
        super().__init__(config)
        self._sdk_api = ServicesServiceSdkAPI(self._http_client)

    async def poll(self, service_id: str) -> list[Command]:
        """Poll for pending commands (async)."""
        logger.debug("Polling for commands (async): service_id=%s", service_id)

        try:
            url = f"/api/services/services/{service_id}/commands/"
            response = await self._http_client.get(url)
            response.raise_for_status()
            data = response.json()

            if isinstance(data, dict) and "results" in data:
                commands = [Command.model_validate(cmd) for cmd in data["results"]]
            elif isinstance(data, list):
                commands = [Command.model_validate(cmd) for cmd in data]
            else:
                commands = []

            return commands
        except Exception as e:
            logger.error("Failed to poll commands: %s", e)
            return []

    @async_api_error_handler
    async def acknowledge(
        self,
        command_id: str,
        status: str,
        *,
        result: dict | None = None,
        error: str | None = None,
    ) -> CommandAckResponse:
        """Acknowledge command execution (async)."""
        status_map = {
            "acknowledged": CommandAckRequestStatus.ACKNOWLEDGED,
            "executing": CommandAckRequestStatus.EXECUTING,
            "completed": CommandAckRequestStatus.COMPLETED,
            "failed": CommandAckRequestStatus.FAILED,
        }
        status_enum = status_map.get(status.lower(), CommandAckRequestStatus.ACKNOWLEDGED)

        data = CommandAckRequest(
            command_id=command_id,
            status=status_enum,
            result=result,
            error=error,
            executed_at=datetime.now(timezone.utc).isoformat()
            if status in ("completed", "failed")
            else None,
        )

        logger.debug("Acknowledging command (async): id=%s, status=%s", command_id, status)

        return await self._sdk_api.services_commands_ack_create(command_id, data)


__all__ = ["CommandService", "AsyncCommandService"]
