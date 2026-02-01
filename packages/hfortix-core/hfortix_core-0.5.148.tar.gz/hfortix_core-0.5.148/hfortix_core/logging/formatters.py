"""
Logging utilities for HFortix

Provides structured logging formatters and configuration helpers
for enterprise observability.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any


class StructuredFormatter(logging.Formatter):
    """
    Format log records as structured JSON

    Useful for log aggregation systems like ELK, Splunk, CloudWatch
    that can parse JSON logs for better searching and analysis.

    Standard Fields (always present):
        - timestamp: ISO 8601 UTC timestamp
        - level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        - logger: Logger name (e.g., "hfortix.http.client")
        - message: Log message

    Common Extra Fields (added via extra={...}):
        - request_id: Unique request identifier for correlation
        - method: HTTP method (GET, POST, PUT, DELETE, PATCH)
        - endpoint: API endpoint path
        - status_code: HTTP status code
        - duration_seconds: Request duration in seconds
        - vdom: FortiOS Virtual Domain (multi-tenant environments)
        - adom: FortiManager/FortiAnalyzer Administrative Domain
        - error_type: Exception class name (for errors)
        - attempt: Current retry attempt number
        - max_attempts: Maximum retry attempts

    Example:
        >>> import logging
        >>> from hfortix_core.logging import StructuredFormatter
        >>>
        >>> handler = logging.StreamHandler()
        >>> handler.setFormatter(StructuredFormatter())
        >>> logger = logging.getLogger("hfortix")
        >>> logger.addHandler(handler)
        >>>
        >>> # Basic usage
        >>> logger.info("API request completed",
        ...            extra={"endpoint": "/api/v2/cmdb/firewall/policy",
        ...                   "duration_seconds": 0.145})

        Output:
        {"timestamp":"2026-01-02T14:23:45.123Z","level":"INFO",
         "logger":"hfortix","message":"API request completed",
         "endpoint":"/api/v2/cmdb/firewall/policy","duration_seconds":0.145}

        >>> # Multi-tenant usage
        >>> logger.info("Policy created",
        ...            extra={"vdom": "customer_a", "endpoint": "/api/v2/cmdb/firewall/policy",  # noqa: E501
        ...                   "request_id": "req-123", "status_code": 200})

        Output:
        {"timestamp":"2026-01-02T14:23:45.456Z","level":"INFO",
         "logger":"hfortix","message":"Policy created","vdom":"customer_a",
         "endpoint":"/api/v2/cmdb/firewall/policy","request_id":"req-123",
         "status_code":200}
    """

    def __init__(
        self,
        include_fields: list[str] | None = None,
        exclude_fields: list[str] | None = None,
    ):
        """
        Initialize structured formatter

        Args:
            include_fields: List of extra fields to include (None = all)
            exclude_fields: List of fields to exclude from output
        """
        super().__init__()
        self.include_fields = include_fields
        self.exclude_fields = exclude_fields or []

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON

        Args:
            record: LogRecord to format

        Returns:
            JSON string with log data
        """
        # Build base log structure
        log_data: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add extra fields from record
        if hasattr(record, "__dict__"):
            # Get extra fields (those not in standard LogRecord)
            standard_fields = {
                "name",
                "msg",
                "args",
                "created",
                "filename",
                "funcName",
                "levelname",
                "levelno",
                "lineno",
                "module",
                "msecs",
                "message",
                "pathname",
                "process",
                "processName",
                "relativeCreated",
                "thread",
                "threadName",
                "exc_info",
                "exc_text",
                "stack_info",
            }

            for key, value in record.__dict__.items():
                if key in standard_fields:
                    continue
                if key in self.exclude_fields:
                    continue
                if (
                    self.include_fields is not None
                    and key not in self.include_fields
                ):
                    continue

                # Add extra field
                log_data[key] = value

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add source location for DEBUG level
        if record.levelno <= logging.DEBUG:
            log_data["source"] = {
                "file": record.filename,
                "line": record.lineno,
                "function": record.funcName,
            }

        # Return compact JSON
        return json.dumps(log_data, separators=(",", ":"), default=str)


class TextFormatter(logging.Formatter):
    """
    Format log records as human-readable text

    Provides colorized output for terminal and clean formatting
    for log files.

    Example:
        >>> import logging
        >>> from hfortix_core.logging import TextFormatter
        >>>
        >>> handler = logging.StreamHandler()
        >>> handler.setFormatter(TextFormatter(use_color=True))
        >>> logger = logging.getLogger("hfortix")
        >>> logger.addHandler(handler)
        >>> logger.info("API request completed")

        Output:
        2026-01-02 14:23:45 [INFO] hfortix: API request completed
    """

    # ANSI color codes
    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
        "RESET": "\033[0m",  # Reset
    }

    def __init__(self, use_color: bool = False):
        """
        Initialize text formatter

        Args:
            use_color: Whether to use ANSI color codes
        """
        super().__init__()
        self.use_color = use_color

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as text

        Args:
            record: LogRecord to format

        Returns:
            Formatted text string
        """
        # Format timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        # Format level with optional color
        level = record.levelname
        if self.use_color:
            color = self.COLORS.get(level, "")
            reset = self.COLORS["RESET"]
            level = f"{color}{level}{reset}"

        # Build message
        message = f"{timestamp} [{level}] {record.name}: {record.getMessage()}"

        # Add exception if present
        if record.exc_info:
            message += "\n" + self.formatException(record.exc_info)

        return message


__all__ = ["StructuredFormatter", "TextFormatter"]
