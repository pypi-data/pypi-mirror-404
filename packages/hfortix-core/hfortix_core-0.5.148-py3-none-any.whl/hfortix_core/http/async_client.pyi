"""Type stubs for hfortix_core.http.async_client module."""

from __future__ import annotations

from typing import Any, Callable, Literal, Optional, TypeAlias, Union

HTTPResponse: TypeAlias = dict[str, Any]

class AsyncHTTPClient:
    """Internal async HTTP client for FortiOS API requests."""

    # Connection tracking attributes
    _active_requests: int
    _total_requests: int
    _pool_exhaustion_count: int
    _pool_exhaustion_timestamps: list[float]
    _max_connections: int
    _max_keepalive_connections: int

    # Debug tracking attributes
    _last_request: dict[str, Any] | None
    _last_response: dict[str, Any] | None
    _last_response_time: float | None

    def __init__(
        self,
        url: str,
        verify: bool = True,
        token: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        vdom: Optional[str] = None,
        max_retries: int = 3,
        connect_timeout: float = 10.0,
        read_timeout: float = 300.0,
        user_agent: Optional[str] = None,
        circuit_breaker_threshold: int = 10,
        circuit_breaker_timeout: float = 30.0,
        circuit_breaker_auto_retry: bool = False,
        circuit_breaker_max_retries: int = 3,
        circuit_breaker_retry_delay: float = 5.0,
        max_connections: int = 100,
        max_keepalive_connections: int = 20,
        session_idle_timeout: Union[int, float, None] = 300,
        read_only: bool = False,
        track_operations: bool = False,
        adaptive_retry: bool = False,
        retry_strategy: str = "exponential",
        retry_jitter: bool = False,
        audit_handler: Optional[Any] = None,
        audit_callback: Optional[Any] = None,
        user_context: Optional[dict[str, Any]] = None,
    ) -> None: ...
    async def request(
        self,
        method: Literal["GET", "POST", "PUT", "DELETE"],
        endpoint: str,
        params: Optional[dict[str, Any]] = None,
        data: Optional[dict[str, Any]] = None,
        vdom: Optional[str] = None,
        validate: bool = True,
        skip_validation: bool = False,
    ) -> HTTPResponse:
        """Make async HTTP request to FortiOS API."""
        ...

    async def get(
        self,
        api_type: str,
        path: str,
        params: Optional[dict[str, Any]] = None,
        vdom: Optional[Union[str, bool]] = None,
        raw_json: bool = False,
    ) -> HTTPResponse:
        """Make async GET request."""
        ...

    async def post(
        self,
        api_type: str,
        path: str,
        data: dict[str, Any],
        params: Optional[dict[str, Any]] = None,
        vdom: Optional[Union[str, bool]] = None,
        raw_json: bool = False,
    ) -> HTTPResponse:
        """Make async POST request."""
        ...

    async def put(
        self,
        api_type: str,
        path: str,
        data: dict[str, Any],
        params: Optional[dict[str, Any]] = None,
        vdom: Optional[Union[str, bool]] = None,
        raw_json: bool = False,
    ) -> HTTPResponse:
        """Make async PUT request."""
        ...

    async def delete(
        self,
        api_type: str,
        path: str,
        params: Optional[dict[str, Any]] = None,
        vdom: Optional[Union[str, bool]] = None,
        raw_json: bool = False,
    ) -> HTTPResponse:
        """Make async DELETE request."""
        ...

    def get_connection_stats(self) -> dict[str, Any]:
        """Get real-time connection pool statistics.

        Returns:
            Dictionary with connection metrics including:
            - max_connections: Maximum allowed connections
            - max_keepalive_connections: Maximum keepalive connections
            - active_requests: Currently active requests
            - total_requests: Total requests made
            - pool_exhaustion_count: Number of pool exhaustion events
            - pool_exhaustion_timestamps: Timestamps of exhaustion events
        """
        ...

    def inspect_last_request(self) -> dict[str, Any] | None:
        """Get detailed information about the last API request.

        Returns:
            Dictionary with request details including:
            - method: HTTP method (GET, POST, etc.)
            - endpoint: API endpoint path
            - params: Request parameters
            - response_time_ms: Response time in milliseconds
            - status_code: HTTP status code
            Returns None if no requests have been made yet.
        """
        ...

    def get_operations(self) -> list[dict[str, Any]]:
        """Get list of all operations performed (requires track_operations=True)."""
        ...

    def get_write_operations(self) -> list[dict[str, Any]]:
        """Get list of write operations only (requires track_operations=True)."""
        ...

    def get_retry_stats(self) -> dict[str, Any]:
        """Get retry statistics and metrics."""
        ...

    def get_circuit_breaker_state(self) -> dict[str, Any]:
        """Get current circuit breaker state and metrics."""
        ...

    def get_health_metrics(self) -> dict[str, Any]:
        """Get comprehensive health metrics."""
        ...

    async def close(self) -> None:
        """Close async HTTP client and release resources."""
        ...

    async def __aenter__(self) -> AsyncHTTPClient: ...
    async def __aexit__(
        self, exc_type: Any, exc_val: Any, exc_tb: Any
    ) -> None: ...
