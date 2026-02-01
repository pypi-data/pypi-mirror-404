"""Type stubs for hfortix_core package."""

from typing import Any, Callable, TypeVar, ParamSpec, Literal, Generator, TypedDict
from typing_extensions import NotRequired
from contextlib import contextmanager

# Type variables for decorators
_T = TypeVar("_T")
_P = ParamSpec("_P")

# Cache utilities
class TTLCache:
    """Thread-safe TTL cache implementation."""
    def __init__(self, ttl: float = 300.0, maxsize: int = 128) -> None: ...
    def get(self, key: str) -> Any | None: ...
    def set(self, key: str, value: Any) -> None: ...
    def delete(self, key: str) -> None: ...
    def clear(self) -> None: ...
    def __contains__(self, key: str) -> bool: ...

def readonly_cache(ttl: float = 300.0) -> Callable[[Callable[_P, _T]], Callable[_P, _T]]: ...

# Deprecation utilities
def check_deprecated_fields(
    payload: dict[str, Any],
    deprecated_fields: dict[str, dict[str, str]],
    endpoint: str,
) -> None:
    """Check payload for deprecated fields and emit warnings."""
    ...
def warn_deprecated_field(field_name: str, replacement: str | None = None) -> None: ...

# Debug utilities
class DebugSession:
    """Context manager for debug sessions."""
    def __init__(
        self,
        client: Any,
        enabled: bool = True,
        show_headers: bool = False,
        show_body: bool = True,
        max_body_length: int = 1000,
    ) -> None: ...
    def __enter__(self) -> "DebugSession": ...
    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None: ...

@contextmanager
def debug_timer(name: str) -> Generator[None, None, None]: ...

def format_connection_stats(client: Any) -> str:
    """Format connection statistics from a FortiOS client for display."""
    ...

def format_request_info(client: Any) -> str:
    """Format request information from a FortiOS client for display."""
    ...

def print_debug_info(client: Any) -> None:
    """Print debug information about a FortiOS client."""
    ...

# Exceptions
class FortinetError(Exception):
    """Base exception for all Fortinet SDK errors."""
    message: str
    def __init__(self, message: str = "") -> None: ...

class APIError(FortinetError):
    """Base exception for API-related errors."""
    status_code: int | None
    response: dict[str, Any] | None
    def __init__(
        self,
        message: str = "",
        status_code: int | None = None,
        response: dict[str, Any] | None = None,
    ) -> None: ...

class AuthenticationError(APIError):
    """Authentication failed."""
    ...

class AuthorizationError(APIError):
    """Authorization/permission denied."""
    ...

class ValidationError(FortinetError):
    """Validation error."""
    ...

class RetryableError(APIError):
    """Error that can be retried."""
    ...

class NonRetryableError(APIError):
    """Error that should not be retried."""
    ...

class ConfigurationError(FortinetError):
    """Configuration error."""
    ...

class VDOMError(FortinetError):
    """VDOM-related error."""
    ...

class OperationNotSupportedError(FortinetError):
    """Operation not supported."""
    ...

class ReadOnlyModeError(FortinetError):
    """Client is in read-only mode."""
    ...

class BadRequestError(APIError):
    """Bad request (400)."""
    ...

class ResourceNotFoundError(APIError):
    """Resource not found (404)."""
    ...

class MethodNotAllowedError(APIError):
    """Method not allowed (405)."""
    ...

class RateLimitError(RetryableError):
    """Rate limit exceeded (429)."""
    ...

class ServerError(RetryableError):
    """Server error (5xx)."""
    ...

class ServiceUnavailableError(RetryableError):
    """Service unavailable (503)."""
    ...

class CircuitBreakerOpenError(NonRetryableError):
    """Circuit breaker is open."""
    ...

class TimeoutError(RetryableError):
    """Request timeout."""
    ...

class DuplicateEntryError(APIError):
    """Duplicate entry error."""
    ...

class EntryInUseError(APIError):
    """Entry is in use and cannot be deleted."""
    ...

class InvalidValueError(APIError):
    """Invalid value error."""
    ...

class PermissionDeniedError(AuthorizationError):
    """Permission denied."""
    ...

# Logging utilities
class RequestLogger:
    """Logger for API requests."""
    def __init__(self, logger_name: str = "hfortix") -> None: ...
    def log_request(self, method: str, url: str, **kwargs: Any) -> None: ...
    def log_response(self, status_code: int, **kwargs: Any) -> None: ...

class StructuredFormatter:
    """Structured log formatter (JSON)."""
    def format(self, record: Any) -> str: ...

class TextFormatter:
    """Text log formatter."""
    def format(self, record: Any) -> str: ...

def log_operation(
    logger_name: str,
    operation: str,
    level: str = "INFO",
    **kwargs: Any,
) -> None:
    """
    Log an operation with structured data.

    Args:
        logger_name: Name of the logger to use (e.g., "hfortix.http")
        operation: Operation being performed (logged as message)
        level: Log level (DEBUG, INFO, WARNING, ERROR)
        **kwargs: Additional context to log as extra fields
    """
    ...

# Type definitions

class ConnectionStats(TypedDict):
    """Connection statistics."""
    requests_made: int
    requests_failed: int
    retries: int
    avg_response_time: float

class RequestInfo(TypedDict):
    """Request information."""
    method: str
    url: str
    status_code: int
    response_time: float

class CircuitBreakerState(TypedDict):
    """Circuit breaker state."""
    state: Literal["closed", "open", "half-open"]
    failure_count: int
    last_failure_time: float | None

class APIResponse(TypedDict, total=False):
    """Generic API response."""
    status: str
    http_status: int
    results: Any

class ErrorResponse(TypedDict):
    """Error response."""
    error: int
    message: str
    http_status: int

class ListResponse(TypedDict):
    """List response."""
    results: list[dict[str, Any]]
    http_status: int
    status: str

class ObjectResponse(TypedDict):
    """Object response."""
    results: dict[str, Any]
    http_status: int
    status: str

# Version
__version__: str

__all__: list[str]
