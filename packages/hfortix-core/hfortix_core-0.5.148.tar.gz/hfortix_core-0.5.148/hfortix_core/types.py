"""
Type definitions for HFortix SDK

Provides TypedDict definitions for API responses and common data structures.
These improve IDE autocomplete and type checking.
"""

from typing import Any, Literal, TypedDict

__all__ = [
    "APIResponse",
    "RawAPIResponse",
    "MutationResponse",
    "ListResponse",
    "ObjectResponse",
    "ErrorResponse",
    "ConnectionStats",
    "RequestInfo",
    "CircuitBreakerState",
]


class APIResponse(TypedDict, total=False):
    """
    Base API response structure from FortiOS

    Not all fields are present in every response. Use total=False to make
    all fields optional.
    """

    http_status: int
    results: Any  # Can be list, dict, or string depending on endpoint
    revision: str
    revision_changed: bool
    old_revision: str
    vdom: str
    path: str
    name: str
    status: str
    http_method: str
    serial: str
    version: str
    build: int
    mkey: str  # Key of created/modified/deleted object


class RawAPIResponse(TypedDict):
    """
    Raw FortiOS API response envelope returned when raw_json=True.

    This is the complete response from the FortiOS API before any unwrapping.
    Use this for type checking raw_json=True calls.

    All fields are marked as required to provide autocomplete without warnings.
    The primary purpose is to catch typos - accessing undefined fields will
    show an error.

    Note: Not all fields are present in every response. GET responses include
    results, serial, version, build. Mutation responses include mkey, revision.
    Use .get() for fields that may not be present.

    Example GET response:
        {
            "http_method": "GET",
            "results": [...],
            "status": "success",
            "http_status": 200,
            "vdom": "root",
            "path": "firewall",
            "serial": "FGT...",
            "version": "v7.4.8",
            "build": 3636
        }

    Example POST/PUT/DELETE response:
        {
            "http_method": "POST",
            "revision": "1234567890",
            "mkey": "object_name",
            "status": "success",
            "http_status": 200,
            "vdom": "root"
        }
    """

    # Common to all responses
    http_method: str
    http_status: int
    status: str
    vdom: str

    # GET responses
    results: Any  # list[dict] for collection, dict for single item
    path: str
    name: str  # Only for single object queries
    serial: str
    version: str
    build: int

    # Mutation responses (POST/PUT/DELETE)
    mkey: str  # Key of created/modified/deleted object
    revision: str
    revision_changed: bool
    old_revision: str


class MutationResponse(TypedDict):
    """
    Response structure from POST/PUT/DELETE operations.

    This TypedDict validates that only known API response fields are accessed.
    These fields are always present in FortiOS API mutation responses.
    """

    http_status: int
    status: str


class MutationResponseFull(TypedDict, total=False):
    """
    Extended response structure from POST/PUT/DELETE operations.

    Includes optional fields that may be present in some responses.
    """

    http_status: int
    status: str
    vdom: str
    mkey: str  # Key of created/modified/deleted object
    revision: str
    serial: str
    version: str
    build: int


class ListResponse(TypedDict):
    """Response from list/get operations that return multiple items"""

    http_status: int
    results: list[dict[str, Any]]
    vdom: str
    path: str
    name: str
    status: str
    serial: str
    version: str
    build: int


class ObjectResponse(TypedDict):
    """Response from get operations that return a single item"""

    http_status: int
    results: dict[str, Any]  # Single object, not a list
    vdom: str
    path: str
    name: str
    status: str
    serial: str
    version: str
    build: int


class ErrorResponse(TypedDict):
    """Error response structure from FortiOS API"""

    http_status: int
    error: int
    errorcode: int
    message: str
    vdom: str


CircuitBreakerState = Literal["closed", "open", "half-open"]
"""Circuit breaker state: closed (normal), open (failing), half-open (testing)"""  # noqa: E501


class ConnectionStats(TypedDict):
    """
    Connection pool statistics

    Returned by HTTPClient.get_connection_stats()
    """

    http2_enabled: bool
    max_connections: int
    max_keepalive_connections: int
    active_requests: int
    total_requests: int
    pool_exhaustion_count: int
    circuit_breaker_state: CircuitBreakerState
    consecutive_failures: int
    last_failure_time: float | None


class RequestInfo(TypedDict, total=False):
    """
    Information about a request (for debugging)

    Returned by HTTPClient.inspect_last_request()
    """

    method: str
    endpoint: str
    params: dict[str, Any] | None
    data: dict[str, Any] | None
    response_time_ms: float | None
    status_code: int | None
    timestamp: float
    error: str
