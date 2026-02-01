from __future__ import annotations

from typing import Any

import httpx

from .helpers import APILogger, LoggerConfig
from .services__api__api_keys.sync_client import SyncServicesApiKeysAPI
from .services__api__process_control.sync_client import SyncServicesProcessControlAPI
from .services__api__process_jobs.sync_client import SyncServicesProcessJobsAPI
from .services__api__service_commands.sync_client import SyncServicesServiceCommandsAPI
from .services__api__service_control.sync_client import SyncServicesServiceControlAPI
from .services__api__service_logs.sync_client import SyncServicesServiceLogsAPI
from .services__api__service_sdk.sync_client import SyncServicesServiceSdkAPI
from .services__api__services.sync_client import SyncServicesServicesAPI


class SyncAPIClient:
    """
    Synchronous API client for Unrealon API.

    Usage:
        >>> with SyncAPIClient(base_url='https://api.example.com') as client:
        ...     users = client.users.list()
        ...     post = client.posts.create(data=new_post)
    """

    def __init__(
        self,
        base_url: str,
        logger_config: LoggerConfig | None = None,
        **kwargs: Any,
    ):
        """
        Initialize sync API client.

        Args:
            base_url: Base API URL (e.g., 'https://api.example.com')
            logger_config: Logger configuration (None to disable logging)
            **kwargs: Additional httpx.Client kwargs
        """
        self.base_url = base_url.rstrip('/')
        self._client = httpx.Client(
            base_url=self.base_url,
            **kwargs,
        )

        # Initialize logger
        self.logger: APILogger | None = None
        if logger_config is not None:
            self.logger = APILogger(logger_config)

        # Initialize sub-clients
        self.services_api_keys = SyncServicesApiKeysAPI(self._client)
        self.services_process_control = SyncServicesProcessControlAPI(self._client)
        self.services_process_jobs = SyncServicesProcessJobsAPI(self._client)
        self.services_service_commands = SyncServicesServiceCommandsAPI(self._client)
        self.services_service_control = SyncServicesServiceControlAPI(self._client)
        self.services_service_logs = SyncServicesServiceLogsAPI(self._client)
        self.services_service_sdk = SyncServicesServiceSdkAPI(self._client)
        self.services_services = SyncServicesServicesAPI(self._client)

    def __enter__(self) -> SyncAPIClient:
        return self

    def __exit__(self, *args: Any) -> None:
        self._client.close()

    def close(self) -> None:
        """Close HTTP client."""
        self._client.close()