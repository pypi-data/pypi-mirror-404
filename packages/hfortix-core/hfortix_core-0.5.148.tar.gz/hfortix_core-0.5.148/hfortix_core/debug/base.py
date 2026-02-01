"""
Base debug protocol and types for HFortix

Defines core types and protocols for debugging utilities.
"""

from __future__ import annotations

from typing import Any, Protocol, TypedDict, runtime_checkable

__all__ = [
    "DebugInfo",
    "RequestInfo",
    "SessionSummary",
    "DebugFormatter",
]


class RequestInfo(TypedDict, total=False):
    """
    Type definition for request debugging information

    Attributes:
        timestamp: Unix timestamp when request was made
        method: HTTP method (GET, POST, PUT, DELETE)
        endpoint: API endpoint path
        params: Request query parameters
        response_time_ms: Response time in milliseconds
        status_code: HTTP status code
        error: Error message if request failed
        response_data: Full response body (if captured)
    """

    timestamp: float
    method: str
    endpoint: str
    params: dict[str, Any] | None
    response_time_ms: float
    status_code: int
    error: str
    response_data: Any


class DebugInfo(TypedDict, total=False):
    """
    Type definition for comprehensive debug information

    Attributes:
        last_request: Information about the last API request
        connection_stats: Connection pool statistics
        session_active: Whether a debug session is active
        capture_enabled: Whether response capture is enabled
    """

    last_request: RequestInfo | None
    connection_stats: dict[str, Any]
    session_active: bool
    capture_enabled: bool


class SessionSummary(TypedDict, total=False):
    """
    Type definition for debug session summary

    Attributes:
        duration_seconds: Total session duration in seconds
        total_requests: Total number of requests made
        successful_requests: Number of successful requests
        failed_requests: Number of failed requests
        avg_response_time_ms: Average response time in milliseconds
        max_response_time_ms: Maximum response time in milliseconds
        min_response_time_ms: Minimum response time in milliseconds
        stats_delta: Change in connection stats during session
        initial_stats: Connection stats at session start
        final_stats: Connection stats at session end
    """

    duration_seconds: float | None
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_response_time_ms: float | None
    max_response_time_ms: float | None
    min_response_time_ms: float | None
    stats_delta: dict[str, Any] | None
    initial_stats: dict[str, Any] | None
    final_stats: dict[str, Any] | None


@runtime_checkable
class DebugFormatter(Protocol):
    """
    Protocol for debug information formatters

    Any class implementing this protocol can be used to format
    debug information for display.
    """

    def format_request(
        self, request_info: RequestInfo | dict[str, Any] | None
    ) -> str:
        """
        Format request information as string

        Args:
            request_info: Request information dictionary

        Returns:
            Formatted string
        """
        ...

    def format_stats(self, stats: dict[str, Any] | None) -> str:
        """
        Format connection statistics as string

        Args:
            stats: Connection statistics dictionary

        Returns:
            Formatted string
        """
        ...
