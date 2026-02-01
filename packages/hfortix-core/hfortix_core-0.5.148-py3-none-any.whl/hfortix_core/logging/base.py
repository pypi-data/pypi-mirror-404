"""
Base logging protocol and types for HFortix

Defines core types and protocols for structured logging.
"""

from __future__ import annotations

from typing import Any, Protocol, TypedDict, runtime_checkable

__all__ = ["LogRecord", "LogFormatter"]


class LogRecord(TypedDict, total=False):
    """
    Type definition for structured log record data

    Attributes:
        timestamp: ISO 8601 UTC timestamp
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        logger: Logger name (e.g., "hfortix.http.client")
        message: Log message
        request_id: Unique request identifier for correlation
        method: HTTP method (GET, POST, PUT, DELETE)
        endpoint: API endpoint path
        status_code: HTTP status code
        duration_s: Request duration in seconds
        duration_ms: Request duration in milliseconds
        vdom: FortiOS Virtual Domain
        event: Event type (request_start, request_completed, request_failed)
        error: Error message (if applicable)
        error_type: Exception class name
        attempt: Current retry attempt number
        max_attempts: Maximum retry attempts
        source: Source location (file, line, function)
    """

    timestamp: str
    level: str
    logger: str
    message: str
    request_id: str
    method: str
    endpoint: str
    status_code: int
    duration_s: float
    duration_ms: float
    vdom: str
    event: str
    error: str
    error_type: str
    attempt: int
    max_attempts: int
    source: dict[str, Any]


@runtime_checkable
class LogFormatter(Protocol):
    """
    Protocol for log formatters

    Any class implementing this protocol can be used as a formatter
    for HFortix logging.
    """

    def format(self, record: Any) -> str:
        """
        Format a log record

        Args:
            record: logging.LogRecord instance

        Returns:
            Formatted string
        """
        ...
