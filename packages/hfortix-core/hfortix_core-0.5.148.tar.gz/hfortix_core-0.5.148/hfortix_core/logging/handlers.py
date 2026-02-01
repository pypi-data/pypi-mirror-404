"""
Logging utilities for structured request/response logging.

Provides context managers and helpers for consistent logging across the SDK.
"""

import logging
import time
from typing import Any, Optional

__all__ = ["RequestLogger", "log_operation"]

logger = logging.getLogger("hfortix.http")


class RequestLogger:
    """
    Context manager for logging API requests with timing and status

    Automatically logs request start/completion and calculates duration.
    Logs errors with full context if the request fails.

    Example:
        >>> with RequestLogger("POST", "/api/v2/cmdb/firewall/address", extra={"vdom": "root"}):  # noqa: E501
        ...     response = make_request()
        # Logs: ✓ POST /api/v2/cmdb/firewall/address (0.234s) {vdom: root}
    """

    def __init__(
        self,
        method: str,
        endpoint: str,
        extra: Optional[dict[str, Any]] = None,
    ):
        """
        Initialize request logger

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint path
            extra: Additional context to include in logs
        """
        self.method = method.upper()
        self.endpoint = endpoint
        self.extra = extra or {}
        self.start_time: Optional[float] = None

    def __enter__(self):
        self.start_time = time.time()
        logger.debug(
            "→ %s %s",
            self.method,
            self.endpoint,
            extra={**self.extra, "event": "request_start"},
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time is None:
            return False

        duration = time.time() - self.start_time

        if exc_type:
            logger.error(
                "✗ %s %s failed (%.3fs): %s",
                self.method,
                self.endpoint,
                duration,
                exc_val,
                extra={
                    **self.extra,
                    "duration_s": duration,
                    "error": str(exc_val),
                    "error_type": exc_type.__name__,
                    "event": "request_failed",
                },
            )
        else:
            logger.info(
                "✓ %s %s (%.3fs)",
                self.method,
                self.endpoint,
                duration,
                extra={
                    **self.extra,
                    "duration_s": duration,
                    "event": "request_completed",
                },
            )

        return False  # Don't suppress exceptions


def log_operation(
    logger_name: str, operation: str, level: str = "INFO", **kwargs
) -> None:
    """
    Log an operation with structured data

    Args:
        logger_name: Name of the logger to use (e.g., "hfortix.http")
        operation: Operation being performed (logged as message)
        level: Log level (DEBUG, INFO, WARNING, ERROR)
        **kwargs: Additional context to log as extra fields

    Example:
        >>> log_operation(
        ...     "hfortix.client",
        ...     "Creating firewall address",
        ...     level="INFO",
        ...     address_name="server1",
        ...     subnet="10.0.0.1/32",
        ...     vdom="root"
        ... )
        # Logs: Creating firewall address {address_name: server1, subnet: 10.0.0.1/32, vdom: root}  # noqa: E501
    """
    op_logger = logging.getLogger(logger_name)
    log_level = getattr(logging, level.upper(), logging.INFO)
    op_logger.log(log_level, operation, extra=kwargs)
