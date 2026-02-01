"""
Internal Async HTTP Client for FortiOS API

This module contains the AsyncHTTPClient class which handles all async HTTP
communication
with FortiGate devices. It mirrors HTTPClient but uses async/await with
httpx.AsyncClient.

This is an internal implementation detail and not part of the public API.
"""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from typing import Any, Callable, Optional, TypeAlias, Union
from urllib.parse import quote

import httpx
from hfortix_core.http.base import BaseHTTPClient

logger = logging.getLogger("hfortix.http.async")

# Type alias for API responses
HTTPResponse: TypeAlias = dict[str, Any]

__all__ = ["AsyncHTTPClient", "HTTPResponse"]


class AsyncHTTPClient(BaseHTTPClient):
    """
    Internal async HTTP client for FortiOS API requests (Async Implementation)

    Implements the IHTTPClient protocol for asynchronous HTTP operations.

    Async version of HTTPClient using httpx.AsyncClient. Handles all HTTP
    communication
    with FortiGate devices including:
    - Async session management
    - Authentication headers
    - SSL verification
    - Request/response handling
    - Error handling
    - Automatic retry with exponential backoff
    - Async context manager support (use with 'async with' statement)

    Protocol Implementation:
        This class implements the IHTTPClient protocol, allowing it to be used
        interchangeably with other HTTP client implementations (e.g.,
        HTTPClient,
        custom user-provided async clients). All methods return coroutines that
        must be awaited.

    This class is internal and not exposed to users directly, but users can
    provide
    their own async IHTTPClient implementations to FortiOS.__init__().
    """

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
        session_idle_timeout: Optional[float] = 300.0,
        read_only: bool = False,
        track_operations: bool = False,
        adaptive_retry: bool = False,
        retry_strategy: str = "exponential",
        retry_jitter: bool = False,
        audit_handler: Optional[Any] = None,
        audit_callback: Optional[Any] = None,
        user_context: Optional[dict[str, Any]] = None,
    ) -> None:
        """
        Initialize async HTTP client

        Args:
            url: Base URL for API (e.g., "https://192.0.2.10")
            verify: Verify SSL certificates
            token: API authentication token (if using token auth)
            username: Username for authentication (if using username/password
            auth)
            password: Password for authentication (if using username/password
            auth)
            vdom: Default virtual domain
            max_retries: Maximum number of retry attempts on transient failures
            (default: 3)
            connect_timeout: Timeout for establishing connection in seconds
            (default: 10.0)
            read_timeout: Timeout for reading response in seconds (default:
            300.0)
            user_agent: Custom User-Agent header
            circuit_breaker_threshold: Number of consecutive failures before
            opening circuit (default: 10)
            circuit_breaker_timeout: Seconds to wait before transitioning to
            half-open (default: 30.0)
            circuit_breaker_auto_retry: When True, automatically wait and retry
            when circuit breaker
                                       opens instead of raising error
                                       immediately (default: False).
                                       WARNING: Not recommended for test
                                       environments - may cause long delays.
            circuit_breaker_max_retries: Maximum number of auto-retry attempts
            when circuit breaker
                                        opens (default: 3). Only used when
                                        circuit_breaker_auto_retry=True.
            circuit_breaker_retry_delay: Delay in seconds between retry
            attempts when auto-retry enabled (default: 5.0).
                                        Separate from circuit_breaker_timeout,
                                        which controls when the circuit
                                        transitions from open to half-open.
            max_connections: Maximum number of connections in the pool
            (default: 100)
            max_keepalive_connections: Maximum number of keepalive connections
            (default: 20)
            session_idle_timeout: For username/password auth only. Idle timeout
            in seconds before
                       proactively re-authenticating (default: 300 = 5
                       minutes). Set to None or
                       False to disable. Note: Async client does not yet
                       implement proactive
                       re-auth; this parameter is accepted for API
                       compatibility.
            read_only: Enable read-only mode - simulate write operations
            without executing (default: False)
            track_operations: Enable operation tracking - maintain audit log of
            all API calls (default: False)
            adaptive_retry: Enable adaptive retry with backpressure detection
            (default: False).
                          When enabled, monitors response times and adjusts
                          retry delays based on
                          FortiGate health signals (slow responses, 503
                          errors).
            retry_strategy: Retry backoff strategy - 'exponential' (default)
                          or 'linear'. Exponential: 1s, 2s, 4s, 8s, 16s, 30s.
                          Linear: 1s, 2s, 3s, 4s, 5s.
            retry_jitter: Add random jitter (0-25% of delay) to retry delays
                         to prevent thundering herd problem (default: False).
            audit_handler: Handler for audit logging (implements AuditHandler
            protocol).
                          Use built-in handlers: SyslogHandler, FileHandler,
                          StreamHandler,
                          CompositeHandler. Essential for compliance (SOC 2,
                          HIPAA, PCI-DSS).
            audit_callback: Custom callback function for audit logging.
                           Alternative to audit_handler. Receives operation
                           dict as parameter.
            user_context: Optional dict with user/application context to
            include in audit logs.
                         Example: {"username": "admin", "app": "automation",
                         "ticket": "CHG-12345"}

        Raises:
            ValueError: If parameters are invalid or both token and
            username/password provided
        """
        # Validate authentication parameters
        if token and (username or password):
            raise ValueError(
                "Cannot specify both token and username/password authentication"  # noqa: E501
            )
        if (username and not password) or (password and not username):
            raise ValueError(
                "Both username and password must be provided together"
            )

        # Call parent class constructor (handles validation and common
        # initialization)
        super().__init__(
            url=url,
            verify=verify,
            vdom=vdom,
            max_retries=max_retries,
            connect_timeout=connect_timeout,
            read_timeout=read_timeout,
            circuit_breaker_threshold=circuit_breaker_threshold,
            circuit_breaker_timeout=circuit_breaker_timeout,
            max_connections=max_connections,
            max_keepalive_connections=max_keepalive_connections,
            adaptive_retry=adaptive_retry,
            retry_strategy=retry_strategy,
            retry_jitter=retry_jitter,
        )

        # Store circuit breaker auto-retry settings
        self._circuit_breaker_auto_retry = circuit_breaker_auto_retry
        self._circuit_breaker_max_retries = circuit_breaker_max_retries
        self._circuit_breaker_retry_delay = circuit_breaker_retry_delay

        # Store connection pool settings for monitoring
        self._max_connections = max_connections
        self._max_keepalive_connections = max_keepalive_connections

        # Set default User-Agent if not provided
        if user_agent is None:
            from hfortix_core import __version__

            user_agent = f"hfortix/{__version__} (async)"

        # Initialize httpx AsyncClient
        self._client = httpx.AsyncClient(
            headers={"User-Agent": user_agent},
            timeout=httpx.Timeout(
                connect=connect_timeout,
                read=read_timeout,
                write=30.0,
                pool=10.0,
            ),
            verify=verify,
            http2=True,  # Enable HTTP/2 support
            limits=httpx.Limits(
                max_connections=max_connections,
                max_keepalive_connections=max_keepalive_connections,
            ),
        )

        # Store authentication credentials
        self._token = token
        self._username = username
        self._password = password
        self._session_token: Optional[str] = None  # For username/password auth
        self._using_token_auth = token is not None
        self._login_task: Optional[asyncio.Task] = None  # Track login task

        # Read-only mode and operation tracking
        self._read_only = read_only
        self._track_operations = track_operations
        self._operations: list[dict[str, Any]] = [] if track_operations else []

        # Audit logging
        self._audit_handler = audit_handler
        self._audit_callback = audit_callback
        self._user_context = user_context or {}

        # Connection pool monitoring
        self._active_requests = 0
        self._total_requests = 0
        self._pool_exhaustion_count = 0
        self._pool_exhaustion_timestamps: list[float] = []

        # Request inspection for debugging
        self._last_request: Optional[dict[str, Any]] = None
        self._last_response: Optional[dict[str, Any]] = None
        self._last_response_time: Optional[float] = None

        # Set token if provided
        if token:
            self._client.headers["Authorization"] = f"Bearer {token}"

        # Note: For async, we can't login in __init__ because it's not async
        # User should call await client.login() or use async context manager

        logger.debug(
            "Async HTTP client initialized for %s (max_retries=%d, connect_timeout=%.1fs, read_timeout=%.1fs, "  # noqa: E501
            "http2=enabled, user_agent='%s', circuit_breaker_threshold=%d, max_connections=%d)",  # noqa: E501
            self._url,
            max_retries,
            connect_timeout,
            read_timeout,
            user_agent,
            circuit_breaker_threshold,
            max_connections,
        )

    async def login(self) -> None:
        """
        Authenticate using username/password and obtain session token (async)

        Must be called manually for async clients (cannot be called in
        __init__).
        Alternatively, use async context manager which handles login/logout
        automatically.

        Raises:
            ValueError: If username/password not configured
            AuthenticationError: If login fails

        Example:
            >>> client = AsyncHTTPClient(url, username="admin",
            password="password")
            >>> await client.login()
        """
        if not self._username or not self._password:
            raise ValueError("Username and password required for login")

        logger.debug(
            "Authenticating with username/password for %s (async)", self._url
        )

        try:
            # FortiOS login endpoint
            login_url = f"{self._url}/logincheck"
            login_data = {
                "username": self._username,
                "password": self._password,
            }

            # Make login request
            response = await self._client.post(
                login_url,
                data=login_data,
                follow_redirects=False,
            )

            # Check for successful login
            if response.status_code == 200:
                # Extract CSRF token from cookies
                csrf_token = None
                for cookie_name, cookie_value in response.cookies.items():
                    if "ccsrftoken" in cookie_name.lower():
                        csrf_token = cookie_value
                        break

                if csrf_token:
                    self._session_token = csrf_token
                    self._client.headers["X-CSRFTOKEN"] = csrf_token
                    logger.info(
                        "Successfully authenticated via username/password (async)"  # noqa: E501
                    )
                else:
                    raise ValueError(
                        "Login succeeded but no CSRF token found in response"
                    )
            else:
                raise ValueError(
                    f"Login failed with status code {response.status_code}"
                )

        except httpx.HTTPError as e:
            logger.error("Login failed (async): %s", str(e))
            raise ValueError(f"Login failed: {str(e)}") from e

    async def logout(self) -> None:
        """
        Logout and invalidate session token (async)

        This method is called automatically when using async context manager.
        Can also be called manually to explicitly logout.

        Note:
            Only applicable when using username/password authentication.
            Token-based authentication doesn't require logout.
        """
        if not self._session_token:
            logger.debug(
                "No active session to logout (using token auth or not logged in) (async)"  # noqa: E501
            )
            return

        logger.debug("Logging out from %s (async)", self._url)

        try:
            logout_url = f"{self._url}/logout"
            response = await self._client.post(logout_url)

            if response.status_code == 200:
                logger.info("Successfully logged out (async)")
            else:
                logger.warning(
                    "Logout returned status code %d (async)",
                    response.status_code,
                )

        except httpx.HTTPError as e:
            logger.warning("Logout failed (async): %s", str(e))
        finally:
            # Clear session token and header regardless of logout result
            self._session_token = None
            if "X-CSRFTOKEN" in self._client.headers:
                del self._client.headers["X-CSRFTOKEN"]

    def get_connection_stats(self) -> dict[str, Any]:
        """
        Get HTTP connection pool statistics (async client)

        Returns:
            dict: Connection statistics including:
                - http2_enabled: Whether HTTP/2 is enabled
                - max_connections: Maximum number of connections allowed
                - max_keepalive_connections: Maximum keepalive connections
                - active_requests: Current number of active requests
                - total_requests: Total requests made since initialization
                - pool_exhaustion_count: Times pool reached capacity
                - circuit_breaker_state: Current circuit breaker state
                - consecutive_failures: Number of consecutive failures

        Example:
            >>> stats = client.get_connection_stats()
            >>> print(f"Circuit breaker: {stats['circuit_breaker_state']}")
            >>> print(f"Active requests: {stats['active_requests']}")
        """
        return {
            "http2_enabled": True,
            "max_connections": self._max_connections,
            "max_keepalive_connections": self._max_keepalive_connections,
            "active_requests": self._active_requests,
            "total_requests": self._total_requests,
            "pool_exhaustion_count": self._pool_exhaustion_count,
            "circuit_breaker_state": self._circuit_breaker["state"],
            "consecutive_failures": self._circuit_breaker[
                "consecutive_failures"
            ],
            "last_failure_time": self._circuit_breaker["last_failure_time"],
        }

    def inspect_last_request(self) -> dict[str, Any]:
        """
        Get details of last API request for debugging

        Returns:
            dict: Request information including:
                - method: HTTP method used
                - endpoint: API endpoint path
                - params: Query parameters
                - response_time_ms: Response time in milliseconds
                - status_code: HTTP status code
                - error: Error message if no requests made

        Example:
            >>> await client.get("/api/v2/cmdb/firewall/address")
            >>> info = client.inspect_last_request()
            >>> print(f"Last request took {info['response_time_ms']:.2f}ms")
        """
        if not self._last_request:
            return {"error": "No requests have been made yet"}

        result: dict[str, Any] = {
            "method": self._last_request.get("method"),
            "endpoint": self._last_request.get("endpoint"),
            "params": self._last_request.get("params"),
            "response_time_ms": (
                round(self._last_response_time * 1000, 2)
                if self._last_response_time
                else None
            ),
        }

        if self._last_response:
            result["status_code"] = self._last_response.get("status_code")

        return result

    async def _check_circuit_breaker(  # type: ignore[override]
        self, endpoint: str
    ) -> None:
        """
        Override base class circuit breaker check with optional auto-retry

        Args:
            endpoint: API endpoint being checked

        Raises:
            CircuitBreakerOpenError: If circuit breaker is open and
                auto-retry is disabled or max retries exceeded
        """
        if not self._circuit_breaker_auto_retry:
            # Use default fail-fast behavior (call base class method,
            # not async)
            super()._check_circuit_breaker(endpoint)
            return

        # Auto-retry enabled - wait and retry when circuit breaker opens
        retry_count = 0
        while retry_count < self._circuit_breaker_max_retries:
            if self._circuit_breaker["state"] == "open":
                retry_count += 1
                logger.info(
                    "Circuit breaker OPEN - auto-retry %d/%d after %.1fs",
                    retry_count,
                    self._circuit_breaker_max_retries,
                    self._circuit_breaker_retry_delay,
                )
                await asyncio.sleep(self._circuit_breaker_retry_delay)

                # Check if enough time has elapsed for circuit to transition
                elapsed = time.time() - (
                    self._circuit_breaker["last_failure_time"] or 0
                )
                if elapsed >= self._circuit_breaker["timeout"]:
                    # Timeout elapsed, transition to half_open
                    self._circuit_breaker["state"] = "half_open"
                    logger.info(
                        "Circuit breaker transitioning to HALF_OPEN " "state"
                    )
                # If timeout not elapsed, circuit stays open but we
                # retry anyway (the request will fail-fast again if
                # service still down)
                return
            else:
                # Circuit breaker is closed or half_open, proceed
                return

        # Max retries exceeded, raise error
        from hfortix_core.exceptions import CircuitBreakerOpenError

        raise CircuitBreakerOpenError(
            f"Circuit breaker is OPEN for {endpoint}. "
            f"Max retries ({self._circuit_breaker_max_retries}) exceeded. "
            "Service appears to be down."
        )

    def _handle_response_errors(
        self,
        response: httpx.Response,
        endpoint: Optional[str] = None,
        method: Optional[str] = None,
        params: Optional[dict[str, Any]] = None,
    ) -> None:
        """
        Handle HTTP response errors using FortiOS error handling

        Args:
            response: httpx.Response object
            endpoint: API endpoint path for better error context
            method: HTTP method (GET, POST, PUT, DELETE)
            params: Request parameters (will be sanitized in error messages)
        """
        if not response.is_success:
            try:
                from hfortix_core.exceptions import (
                    get_error_description,
                    raise_for_status,
                )

                json_response = response.json()

                # Add error description if error code present
                error_code = json_response.get("error")
                if error_code and "error_description" not in json_response:
                    json_response["error_description"] = get_error_description(
                        error_code
                    )

                # Log the error
                status = json_response.get("status")
                http_status = json_response.get(
                    "http_status", response.status_code
                )
                error_desc = json_response.get(
                    "error_description", "Unknown error"
                )

                logger.error(
                    "Request failed: HTTP %d, status=%s, error=%s, description='%s'",  # noqa: E501
                    http_status,
                    status,
                    error_code,
                    error_desc,
                )

                # Use FortiOS-specific error handling with enhanced context
                raise_for_status(
                    json_response,
                    endpoint=endpoint,
                    method=method,
                    params=params,
                )

            except ValueError:
                logger.error(
                    "Request failed: HTTP %d (non-JSON response, %d bytes)",
                    response.status_code,
                    len(response.content),
                )
                response.raise_for_status()

    def _log_audit(
        self,
        method: str,
        endpoint: str,
        api_type: str,
        path: str,
        data: Optional[dict[str, Any]],
        params: Optional[dict[str, Any]],
        status_code: int,
        success: bool,
        duration_ms: int,
        request_id: str,
        error: Optional[str] = None,
    ) -> None:
        """
        Log API operation to audit handlers (sync for async client)

        Note: This is intentionally synchronous to avoid async complexity
        in audit logging. If async audit is needed, use audit_callback
        with async function.

        Args:
            method: HTTP method
            endpoint: Full API endpoint
            api_type: API type (cmdb, monitor, etc.)
            path: Relative path
            data: Request data (will be sanitized)
            params: Request params (will be sanitized)
            status_code: HTTP status code
            success: Whether operation succeeded
            duration_ms: Duration in milliseconds
            request_id: Request ID
            error: Error message if failed
        """
        # Skip if no audit handler or callback configured
        if not self._audit_handler and not self._audit_callback:
            return

        try:
            from datetime import datetime, timezone

            # Determine action from method and path
            action = self._infer_action(method, path)

            # Extract object type and name from path
            object_type, object_name = self._extract_object_info(path, data)

            # Build operation dict
            operation: dict[str, Any] = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "request_id": request_id,
                "method": method.upper(),
                "endpoint": endpoint,
                "api_type": api_type,
                "path": path,
                "vdom": params.get("vdom") if params else None,
                "action": action,
                "object_type": object_type,
                "object_name": object_name,
                "data": self._sanitize_data(data) if data else None,
                "params": self._sanitize_data(params) if params else None,
                "status_code": status_code,
                "success": success,
                "duration_ms": duration_ms,
                "host": self._url.replace("https://", "").replace(
                    "http://", ""
                ),
                "read_only_mode": self._read_only
                and method in ("POST", "PUT", "DELETE"),
            }

            # Add error if present
            if error:
                operation["error"] = error

            # Add user context if provided
            if self._user_context:
                operation["user_context"] = self._user_context

            # Call audit handler if configured
            if self._audit_handler:
                try:
                    self._audit_handler.log_operation(operation)
                except Exception as e:
                    logger.error(
                        f"Audit handler failed: {e}",
                        extra={
                            "error": str(e),
                            "request_id": request_id,
                        },
                        exc_info=True,
                    )

            # Call audit callback if configured
            if self._audit_callback:
                try:
                    self._audit_callback(operation)
                except Exception as e:
                    logger.error(
                        f"Audit callback failed: {e}",
                        extra={
                            "error": str(e),
                            "request_id": request_id,
                        },
                        exc_info=True,
                    )

        except Exception as e:
            # Don't let audit failures break API operations
            logger.error(
                f"Audit logging failed: {e}",
                extra={"error": str(e), "request_id": request_id},
                exc_info=True,
            )

    @staticmethod
    def _infer_action(method: str, path: str) -> str:
        """Infer high-level action from method and path"""
        method = method.upper()

        if method == "GET":
            parts = path.strip("/").split("/")
            if len(parts) > 0 and parts[-1] and not parts[-1].startswith("?"):
                return "read"
            return "list"
        elif method == "POST":
            return "create"
        elif method == "PUT":
            return "update"
        elif method == "DELETE":
            return "delete"
        else:
            return "unknown"

    @staticmethod
    def _extract_object_info(
        path: str, data: Optional[dict[str, Any]]
    ) -> tuple[str, Optional[str]]:
        """
        Extract object type and name from path and data

        Returns:
            Tuple of (object_type, object_name)
        """
        path = path.strip("/")
        object_type = path.replace("/", ".")
        object_name = None

        parts = path.split("/")
        if len(parts) > 0:
            last_part = parts[-1]
            if last_part and not last_part.startswith("?"):
                object_name = last_part

        if data:
            if "name" in data:
                object_name = str(data["name"])
            elif "mkey" in data:
                object_name = str(data["mkey"])

        return object_type, object_name

    async def request(
        self,
        method: str,
        api_type: str,
        path: str,
        data: Optional[dict[str, Any]] = None,
        params: Optional[dict[str, Any]] = None,
        vdom: Optional[Union[str, bool]] = None,
        raw_json: bool = False,
        request_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Generic async request method for all API calls

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            api_type: API type (cmdb, monitor, log, service)
            path: API endpoint path
            data: Request body data (for POST/PUT)
            params: Query parameters dict
            vdom: Virtual domain
            raw_json: If False, return only 'results' field. If True, return
            full response
            request_id: Optional correlation ID for tracking requests

        Returns:
            dict: API response (results or full response based on raw_json)
        """
        # Generate request ID if not provided
        if request_id is None:
            request_id = str(uuid.uuid4())[:8]

        # Normalize and encode path
        path = self._normalize_path(path)
        encoded_path = (
            quote(str(path), safe="/%") if isinstance(path, str) else path
        )
        url = f"{self._url}/api/v2/{api_type}/{encoded_path}"
        params = params or {}

        # Handle vdom parameter
        if vdom is not None:
            params["vdom"] = vdom
        elif self._vdom is not None and "vdom" not in params:
            params["vdom"] = self._vdom

        # Build endpoint key
        full_path = f"/api/v2/{api_type}/{path}"
        endpoint_key = f"{api_type}/{path}"

        # Check circuit breaker
        try:
            await self._check_circuit_breaker(endpoint_key)
        except RuntimeError:
            logger.error(
                "Circuit breaker blocked request",
                extra=self._log_context(
                    request_id=request_id,
                    method=method,
                    endpoint=full_path,
                    circuit_state=self._circuit_breaker["state"],
                ),
            )
            raise

        # Get endpoint-specific timeout if configured
        endpoint_timeout = self._get_endpoint_timeout(endpoint_key)

        # Log request start
        logger.debug(
            "Async request started",
            extra=self._log_context(
                request_id=request_id,
                method=method.upper(),
                endpoint=full_path,
                has_data=bool(data),
                has_params=bool(params),
            ),
        )

        # Track timing
        start_time = time.time()

        # Track total requests
        self._retry_stats["total_requests"] += 1

        # Retry loop with exponential backoff
        last_error = None
        for attempt in range(self._max_retries + 1):
            try:
                # Track active requests and total requests
                self._active_requests += 1
                self._total_requests += 1

                # Store request details for debugging
                self._last_request = {
                    "method": method.upper(),
                    "endpoint": full_path,
                    "params": params,
                    "data": data,
                    "timestamp": time.time(),
                }

                try:
                    # Make async request
                    res = await self._client.request(
                        method=method,
                        url=url,
                        json=data if data else None,
                        params=params if params else None,
                        timeout=endpoint_timeout if endpoint_timeout else None,
                    )

                    # Store response details for debugging
                    self._last_response = {
                        "status_code": res.status_code,
                        "headers": dict(res.headers),
                    }

                except httpx.PoolTimeout:
                    # Track pool exhaustion
                    self._pool_exhaustion_count += 1
                    self._pool_exhaustion_timestamps.append(time.time())
                    logger.warning(
                        "Connection pool exhausted (async)",
                        extra={
                            "request_id": request_id,
                            "endpoint": full_path,
                            "active_requests": self._active_requests,
                            "max_connections": self._max_connections,
                        },
                    )
                    raise
                finally:
                    # Always decrement active requests
                    self._active_requests -= 1

                # Calculate duration
                duration = time.time() - start_time
                self._last_response_time = duration

                # Record response time for adaptive backpressure (if enabled)
                self._record_response_time(endpoint_key, duration)

                # Handle errors
                self._handle_response_errors(
                    res,
                    endpoint=full_path,
                    method=method.upper(),
                    params=params,
                )

                # Record success
                self._record_circuit_breaker_success()
                self._retry_stats["successful_requests"] += 1

                # Log successful response
                logger.info(
                    "Async request completed successfully",
                    extra=self._log_context(
                        request_id=request_id,
                        method=method.upper(),
                        endpoint=full_path,
                        status_code=res.status_code,
                        duration_seconds=round(duration, 3),
                        attempts=attempt + 1,
                    ),
                )

                # Audit logging for successful operations
                self._log_audit(
                    method=method,
                    endpoint=full_path,
                    api_type=api_type,
                    path=path,
                    data=data,
                    params=params,
                    status_code=res.status_code,
                    success=True,
                    duration_ms=int(duration * 1000),
                    request_id=request_id,
                )

                # Parse JSON response
                json_response = res.json()
                
                # Inject http_status into response if not present
                # FortiOS API doesn't always include http_status in JSON body
                if "http_status" not in json_response:
                    json_response["http_status"] = res.status_code

                # Normalize keys: FortiOS returns hyphenated keys (tcp-portrange)
                # but Python/TypedDict requires underscores (tcp_portrange)
                from hfortix_core.utils import normalize_keys

                json_response = normalize_keys(json_response)

                # Return based on raw_json flag
                if raw_json:
                    return json_response
                else:
                    return json_response.get("results", json_response)

            except Exception as e:
                last_error = e

                # Record failure
                self._record_circuit_breaker_failure(endpoint_key)

                # Check if we should retry
                if self._should_retry(e, attempt, endpoint_key):
                    response_obj = (
                        getattr(e, "response", None)
                        if isinstance(e, httpx.HTTPStatusError)
                        else None
                    )
                    delay = self._get_retry_delay(
                        attempt, response_obj, endpoint_key
                    )

                    logger.info(
                        "Retrying async request after delay",
                        extra=self._log_context(
                            request_id=request_id,
                            method=method.upper(),
                            endpoint=full_path,
                            error_type=type(e).__name__,
                            attempt=attempt + 1,
                            max_attempts=self._max_retries + 1,
                            delay_seconds=delay,
                            adaptive_retry=self._adaptive_retry,
                        ),
                    )

                    # Wait before retry (async sleep)
                    await asyncio.sleep(delay)
                    continue
                else:
                    raise

        # If we've exhausted all retries
        if last_error:
            self._retry_stats["failed_requests"] += 1
            logger.error(
                "Async request failed after all retries",
                extra=self._log_context(
                    request_id=request_id,
                    method=method.upper(),
                    endpoint=full_path,
                    total_attempts=self._max_retries + 1,
                    error_type=type(last_error).__name__,
                ),
            )

            # Audit log the failure
            duration = time.time() - start_time
            error_message = str(last_error)
            status_code = 0

            # Try to extract status code from error
            if hasattr(last_error, "response"):
                response_obj = getattr(last_error, "response", None)
                if response_obj and hasattr(response_obj, "status_code"):
                    status_code = response_obj.status_code

            self._log_audit(
                method=method,
                endpoint=full_path,
                api_type=api_type,
                path=path,
                data=data,
                params=params,
                status_code=status_code,
                success=False,
                duration_ms=int(duration * 1000),
                request_id=request_id,
                error=error_message,
            )

            raise last_error

        raise RuntimeError("Request loop completed without success or error")

    async def get(
        self,
        api_type: str,
        path: str,
        params: Optional[dict[str, Any]] = None,
        vdom: Optional[Union[str, bool]] = None,
        raw_json: bool = False,
    ) -> dict[str, Any]:
        """Async GET request"""
        return await self.request(
            "GET", api_type, path, params=params, vdom=vdom, raw_json=raw_json
        )

    async def get_binary(
        self,
        api_type: str,
        path: str,
        params: Optional[dict[str, Any]] = None,
        vdom: Optional[Union[str, bool]] = None,
    ) -> bytes:
        """Async GET request returning binary data"""
        path = path.lstrip("/") if isinstance(path, str) else path
        url = f"{self._url}/api/v2/{api_type}/{path}"
        params = params or {}

        # Add vdom
        if vdom is not None:
            params["vdom"] = vdom
        elif self._vdom is not None and "vdom" not in params:
            params["vdom"] = self._vdom

        # Make async request
        res = await self._client.get(url, params=params if params else None)

        # Build full endpoint path for error context
        full_path = f"/api/v2/{api_type}/{path}"

        # Handle errors
        self._handle_response_errors(
            res,
            endpoint=full_path,
            method="GET",
            params=params,
        )

        return res.content

    async def post(
        self,
        api_type: str,
        path: str,
        data: dict[str, Any],
        params: Optional[dict[str, Any]] = None,
        vdom: Optional[Union[str, bool]] = None,
        raw_json: bool = False,
    ) -> dict[str, Any]:
        """Async POST request - Create new object"""
        return await self.request(
            "POST",
            api_type,
            path,
            data=data,
            params=params,
            vdom=vdom,
            raw_json=raw_json,
        )

    async def put(
        self,
        api_type: str,
        path: str,
        data: dict[str, Any],
        params: Optional[dict[str, Any]] = None,
        vdom: Optional[Union[str, bool]] = None,
        raw_json: bool = False,
    ) -> dict[str, Any]:
        """Async PUT request - Update existing object"""
        return await self.request(
            "PUT",
            api_type,
            path,
            data=data,
            params=params,
            vdom=vdom,
            raw_json=raw_json,
        )

    async def delete(
        self,
        api_type: str,
        path: str,
        params: Optional[dict[str, Any]] = None,
        vdom: Optional[Union[str, bool]] = None,
        raw_json: bool = False,
    ) -> dict[str, Any]:
        """Async DELETE request - Delete object"""
        return await self.request(
            "DELETE",
            api_type,
            path,
            params=params,
            vdom=vdom,
            raw_json=raw_json,
        )

    # Validation helpers (same as sync - these are static methods)
    @staticmethod
    def validate_mkey(mkey: Any, parameter_name: str = "mkey") -> str:
        """Validate and convert mkey to string"""
        if mkey is None:
            raise ValueError(
                f"{parameter_name} is required and cannot be None"
            )
        mkey_str = str(mkey).strip()
        if not mkey_str:
            raise ValueError(f"{parameter_name} cannot be empty")
        return mkey_str

    @staticmethod
    def validate_required_params(
        params: dict[str, Any], required: list[str]
    ) -> None:
        """Validate that required parameters are present"""
        if not params:
            if required:
                raise ValueError(
                    f"Missing required parameters: {', '.join(required)}"
                )
            return
        missing = [
            param
            for param in required
            if param not in params or params[param] is None
        ]
        if missing:
            raise ValueError(
                f"Missing required parameters: {', '.join(missing)}"
            )

    @staticmethod
    def validate_range(
        value: Union[int, float],
        min_val: Union[int, float],
        max_val: Union[int, float],
        parameter_name: str = "value",
    ) -> None:
        """Validate that a numeric value is within a specified range"""
        if not isinstance(value, (int, float)):
            raise ValueError(f"{parameter_name} must be a number")
        if not (min_val <= value <= max_val):
            raise ValueError(
                f"{parameter_name} must be between {min_val} and {max_val}, got {value}"  # noqa: E501
            )

    @staticmethod
    def validate_choice(
        value: Any, choices: list[Any], parameter_name: str = "value"
    ) -> None:
        """Validate that a value is one of the allowed choices"""
        if value not in choices:
            raise ValueError(
                f"{parameter_name} must be one of {choices}, got '{value}'"
            )

    @staticmethod
    def build_params(**kwargs: Any) -> dict[str, Any]:
        """Build parameters dict, filtering out None values"""
        return {k: v for k, v in kwargs.items() if v is not None}

    async def __aenter__(self) -> "AsyncHTTPClient":
        """
        Async context manager entry - auto-login if using username/password
        """
        # Auto-login for username/password authentication
        if self._username and self._password and not self._session_token:
            await self.login()
        return self

    async def __aexit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[Any],
    ) -> None:
        """
        Async context manager exit - ensures session is closed

        This method is called automatically when exiting an async with block.
        It ensures that all network connections and sessions are properly
        closed.

        Example:
            async with AsyncHTTPClient(...) as client:
                ...
            # Session is closed automatically here
        """
        await self.close()

    async def close(self) -> None:
        """
        Close the async HTTP session and release resources

        This method should be called to properly clean up resources when using
        AsyncHTTPClient.
        It ensures that all network connections and sessions are closed.

        Usage:
            - Call `await client.close()` when you are done with the client in
            async mode.
            - Prefer using the async context manager (`async with`) for
            automatic cleanup.

        Example:
            client = AsyncHTTPClient(...)
            try:
                ...
            finally:
                await client.close()
        """
        # Logout if using username/password authentication
        if self._session_token:
            await self.logout()

        if self._client:
            await self._client.aclose()
            logger.debug("Async HTTP client session closed")

    def get_operations(self) -> list[dict[str, Any]]:
        """
        Get audit log of all tracked API operations

        Returns all tracked operations (GET/POST/PUT/DELETE) in chronological
        order.
        Only available when track_operations=True was passed to constructor.

        Returns:
            List of operation dictionaries (same format as
            HTTPClient.get_operations())
        """
        return self._operations.copy()

    def get_write_operations(self) -> list[dict[str, Any]]:
        """
        Get audit log of write operations only (POST/PUT/DELETE)

        Filters tracked operations to return only write operations, excluding
        GET requests.

        Returns:
            List of write operation dictionaries (same format as
            HTTPClient.get_write_operations())
        """
        return [
            op
            for op in self._operations
            if op["method"] in ("POST", "PUT", "DELETE")
        ]

    @staticmethod
    def make_exists_method(
        get_method: Callable[..., Any],
    ) -> Callable[..., bool]:
        """
        Create an exists() helper that works with both sync and async modes.

        This utility wraps a get() method and returns a function that:
        - Returns True if the object exists
        - Returns False if ResourceNotFoundError is raised
        - Works transparently with both sync and async clients

        Args:
            get_method: The get() method to wrap (bound method from endpoint
            instance)

        Returns:
            A function that returns bool (sync) or Coroutine[bool] (async)

        Example:
            class Address:
                def __init__(self, client):
                    self._client = client

                def get(self, name, **kwargs):
                    return self._client.get("cmdb",
                    f"/firewall/address/{name}", **kwargs)

                # Create exists method using the helper
                exists = AsyncHTTPClient.make_exists_method(get)
        """
        import inspect

        def exists_wrapper(*args: Any, **kwargs: Any) -> Union[bool, Any]:
            """Check if an object exists."""
            from hfortix_core.exceptions import ResourceNotFoundError

            # Call the get method
            result = get_method(*args, **kwargs)

            # Check if we got a coroutine (async mode)
            if inspect.iscoroutine(result):
                # Return async version
                async def _exists_async():
                    try:
                        # Type ignore justified: Runtime check
                        # (inspect.iscoroutine) confirms
                        # result is awaitable, but mypy sees Union[dict,
                        # Coroutine] from protocol
                        # and cannot narrow the type. This is safe and
                        # necessary for dual-mode design.
                        await result
                        return True
                    except ResourceNotFoundError:
                        return False

                return _exists_async()
            else:
                # Sync mode - we already called get(), it succeeded
                # If it raised ResourceNotFoundError, we wouldn't be here
                return True

        return exists_wrapper
