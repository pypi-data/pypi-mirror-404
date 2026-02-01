"""
Built-in Audit Log Handlers

Provides common audit log handlers for various output destinations.
"""

from __future__ import annotations

import logging
import socket
import sys
from pathlib import Path
from typing import Any, Callable, TextIO

from .formatters import AuditFormatter, JSONFormatter

__all__ = [
    "SyslogHandler",
    "FileHandler",
    "StreamHandler",
    "CompositeHandler",
    "NullHandler",
]

logger = logging.getLogger("hfortix.audit")


class SyslogHandler:
    """
    Send audit logs to a syslog server

    Sends UDP packets to a syslog server in RFC 5424 format.
    Commonly used for SIEM integration (Splunk, ELK, QRadar, ArcSight).

    Example:
        >>> from hfortix_core.audit import SyslogHandler
        >>> handler = SyslogHandler("siem.company.com:514")
        >>> # Use with FortiOS client
        >>> fgt = FortiOS("192.168.1.99", token="...", audit_handler=handler)

    Note:
        Uses UDP protocol which is fire-and-forget. For guaranteed delivery,
        consider using FileHandler with external log shipping.
    """

    def __init__(
        self,
        server: str,
        formatter: AuditFormatter | None = None,
        timeout: float = 5.0,
    ):
        """
        Initialize Syslog handler

        Args:
            server: Syslog server in format "host:port" or "host" (default port 514)  # noqa: E501
            formatter: Custom formatter (default: SyslogFormatter)
            timeout: Socket timeout in seconds
        """
        # Parse server address
        if ":" in server:
            host, port_str = server.rsplit(":", 1)
            self.host = host
            self.port = int(port_str)
        else:
            self.host = server
            self.port = 514

        # Setup formatter
        if formatter is None:
            from .formatters import SyslogFormatter

            formatter = SyslogFormatter()
        self.formatter = formatter

        # Create UDP socket
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._socket.settimeout(timeout)

        logger.debug(
            f"SyslogHandler initialized: {self.host}:{self.port}",
            extra={"host": self.host, "port": self.port},
        )

    def log_operation(self, operation: dict[str, Any]) -> None:
        """
        Send operation to syslog server

        Args:
            operation: Operation data dictionary
        """
        try:
            # Format message
            message = self.formatter.format(operation)

            # Send via UDP (max 64KB for IPv4, but practical limit ~8KB for syslog)  # noqa: E501
            message_bytes = message.encode("utf-8")
            if len(message_bytes) > 8192:
                logger.warning(
                    f"Syslog message truncated (size: {len(message_bytes)} bytes)",  # noqa: E501
                    extra={"message_size": len(message_bytes)},
                )
                message_bytes = message_bytes[:8192]

            self._socket.sendto(message_bytes, (self.host, self.port))

        except Exception as e:
            # Don't let audit failures break the application
            logger.error(
                f"Failed to send audit log to syslog: {e}",
                extra={
                    "error": str(e),
                    "host": self.host,
                    "port": self.port,
                    "request_id": operation.get("request_id"),
                },
                exc_info=True,
            )

    def close(self) -> None:
        """Close the socket"""
        try:
            self._socket.close()
        except Exception:
            pass

    def __del__(self):
        """Cleanup on garbage collection"""
        self.close()


class FileHandler:
    """
    Write audit logs to a file

    Writes audit logs to a file in JSON Lines format (one JSON object per line).  # noqa: E501
    Supports automatic log rotation based on file size.

    Example:
        >>> from hfortix_core.audit import FileHandler
        >>> handler = FileHandler("/var/log/fortinet-audit.jsonl")
        >>> fgt = FortiOS("192.168.1.99", token="...", audit_handler=handler)

    File Format:
        Each line is a complete JSON object (JSON Lines format):
        {"timestamp":"2026-01-02T14:23:45Z","method":"POST",...}
        {"timestamp":"2026-01-02T14:23:46Z","method":"GET",...}

    This format is:
        - Easy to parse (one record per line)
        - Compatible with log shipping tools (Fluentd, Logstash, Filebeat)
        - Human-readable with tools like `jq`
    """

    def __init__(
        self,
        filepath: str | Path,
        max_bytes: int = 10_000_000,  # 10 MB default
        backup_count: int = 5,
        formatter: AuditFormatter | None = None,
        mode: str = "a",
    ):
        """
        Initialize File handler

        Args:
            filepath: Path to log file
            max_bytes: Maximum file size before rotation (bytes)
            backup_count: Number of backup files to keep
            formatter: Custom formatter (default: JSONFormatter)
            mode: File open mode ('a' for append, 'w' for overwrite)
        """
        self.filepath = Path(filepath)
        self.max_bytes = max_bytes
        self.backup_count = backup_count
        self.mode = mode

        # Setup formatter
        if formatter is None:
            formatter = JSONFormatter()
        self.formatter = formatter

        # Create directory if needed
        self.filepath.parent.mkdir(parents=True, exist_ok=True)

        # File handle (opened on first write)
        self._file: TextIO | None = None

        logger.debug(
            f"FileHandler initialized: {self.filepath}",
            extra={
                "filepath": str(self.filepath),
                "max_bytes": self.max_bytes,
            },
        )

    def log_operation(self, operation: dict[str, Any]) -> None:
        """
        Write operation to file

        Args:
            operation: Operation data dictionary
        """
        try:
            # Check if rotation needed
            self._rotate_if_needed()

            # Open file if not already open
            if self._file is None or self._file.closed:
                self._file = open(self.filepath, self.mode, encoding="utf-8")  # type: ignore[assignment]  # noqa: E501

            # Format and write
            message = self.formatter.format(operation)
            if self._file is not None:
                self._file.write(message + "\n")
                self._file.flush()  # Ensure written immediately

        except Exception as e:
            # Don't let audit failures break the application
            logger.error(
                f"Failed to write audit log to file: {e}",
                extra={
                    "error": str(e),
                    "filepath": str(self.filepath),
                    "request_id": operation.get("request_id"),
                },
                exc_info=True,
            )

    def _rotate_if_needed(self) -> None:
        """Rotate log file if size limit exceeded"""
        if not self.filepath.exists():
            return

        # Check file size
        if self.filepath.stat().st_size < self.max_bytes:
            return

        # Close current file
        if self._file is not None and not self._file.closed:
            self._file.close()

        # Rotate existing backups
        # file.log.4 -> file.log.5, file.log.3 -> file.log.4, etc.
        for i in range(self.backup_count - 1, 0, -1):
            old_file = Path(f"{self.filepath}.{i}")
            new_file = Path(f"{self.filepath}.{i + 1}")

            if old_file.exists():
                if new_file.exists():
                    new_file.unlink()  # Remove oldest if exists
                old_file.rename(new_file)

        # Rotate current file to .1
        backup_file = Path(f"{self.filepath}.1")
        if backup_file.exists():
            backup_file.unlink()
        self.filepath.rename(backup_file)

        logger.info(
            f"Rotated audit log file: {self.filepath}",
            extra={"filepath": str(self.filepath)},
        )

    def close(self) -> None:
        """Close the file"""
        if self._file is not None and not self._file.closed:
            try:
                self._file.close()
            except Exception:
                pass

    def __del__(self):
        """Cleanup on garbage collection"""
        self.close()


class StreamHandler:
    """
    Write audit logs to a stream (stdout/stderr)

    Useful for containerized applications where logs are captured by
    container orchestration (Docker, Kubernetes) and sent to centralized
    logging (CloudWatch, Datadog, etc.).

    Example:
        >>> from hfortix_core.audit import StreamHandler
        >>> import sys
        >>>
        >>> # Log to stdout (captured by Docker/Kubernetes)
        >>> handler = StreamHandler(sys.stdout, format="json")
        >>> fgt = FortiOS("192.168.1.99", token="...", audit_handler=handler)
    """

    def __init__(
        self,
        stream: TextIO | None = None,
        formatter: AuditFormatter | None = None,
    ):
        """
        Initialize Stream handler

        Args:
            stream: Output stream (default: sys.stdout)
            formatter: Custom formatter (default: JSONFormatter)
        """
        self.stream = stream or sys.stdout

        # Setup formatter
        if formatter is None:
            formatter = JSONFormatter()
        self.formatter = formatter

        stream_name = getattr(self.stream, "name", "<unnamed>")
        logger.debug(
            f"StreamHandler initialized: {stream_name}",
            extra={"stream": stream_name},
        )

    def log_operation(self, operation: dict[str, Any]) -> None:
        """
        Write operation to stream

        Args:
            operation: Operation data dictionary
        """
        try:
            message = self.formatter.format(operation)
            print(message, file=self.stream, flush=True)

        except Exception as e:
            # Don't let audit failures break the application
            logger.error(
                f"Failed to write audit log to stream: {e}",
                extra={
                    "error": str(e),
                    "stream": getattr(self.stream, "name", "<unnamed>"),
                    "request_id": operation.get("request_id"),
                },
                exc_info=True,
            )


class CompositeHandler:
    """
    Send audit logs to multiple handlers with advanced routing

    Features:
    - Multiple destination routing
    - Priority-based ordering
    - Conditional routing with filters
    - Error aggregation and reporting
    - Individual handler enable/disable

    Example (Basic):
        >>> from hfortix_core.audit import CompositeHandler, SyslogHandler, FileHandler  # noqa: E501
        >>>
        >>> # Send to both SIEM and local file
        >>> handler = CompositeHandler([
        ...     SyslogHandler("siem.company.com:514"),  # Compliance
        ...     FileHandler("/var/log/fortinet.log"),   # Debugging/backup
        ... ])
        >>>
        >>> fgt = FortiOS("192.168.1.99", token="...", audit_handler=handler)

    Example (Priority and Filtering):
        >>> # Higher priority handlers execute first
        >>> handler = CompositeHandler([
        ...     (critical_handler, 10, lambda op: op['action'] == 'delete'),
        ...     (normal_handler, 5, lambda op: op['success']),
        ...     (all_handler, 1, None),  # No filter, always executes
        ... ])

    Error Handling:
        If one handler fails, others continue. Errors are aggregated and
        can be retrieved via error_summary property.
    """

    def __init__(
        self,
        handlers: list[Any],
        aggregate_errors: bool = True,
        error_threshold: int = 10,
    ):
        """
        Initialize Composite handler

        Args:
            handlers: List of handlers or tuples (handler, priority, filter_fn)
                - handler: Implements AuditHandler protocol
                - priority: Int (higher = executes first), default: 0
                - filter_fn: Callable[[dict], bool] or None, default: None
            aggregate_errors: Track errors for reporting
            error_threshold: Max errors to track per handler
        """
        self.aggregate_errors = aggregate_errors
        self.error_threshold = error_threshold
        self.error_counts: dict[str, int] = {}
        self.error_samples: dict[str, list[str]] = {}

        # Parse and sort handlers by priority
        self._handlers: list[tuple[Any, int, Any]] = []

        for item in handlers:
            if isinstance(item, tuple):
                if len(item) == 2:
                    # (handler, priority)
                    handler, priority = item
                    filter_fn = None
                elif len(item) == 3:
                    # (handler, priority, filter_fn)
                    handler, priority, filter_fn = item
                else:
                    raise ValueError(
                        f"Invalid handler tuple: {item}. "
                        "Expected (handler, priority[, filter_fn])"
                    )
            else:
                # Just handler - use defaults
                handler = item
                priority = 0
                filter_fn = None

            self._handlers.append((handler, priority, filter_fn))

        # Sort by priority (highest first)
        self._handlers.sort(key=lambda x: x[1], reverse=True)

        logger.debug(
            (
                f"CompositeHandler initialized with "
                f"{len(self._handlers)} handlers"
            ),
            extra={
                "handler_count": len(self._handlers),
                "priorities": [p for _, p, _ in self._handlers],
            },
        )

    def log_operation(self, operation: dict[str, Any]) -> None:
        """
        Send operation to all matching handlers

        Args:
            operation: Operation data dictionary
        """
        for handler, priority, filter_fn in self._handlers:
            # Apply filter if present
            if filter_fn is not None:
                try:
                    if not filter_fn(operation):
                        continue  # Skip this handler
                except Exception as e:
                    logger.error(
                        f"Filter function failed: {e}",
                        extra={
                            "handler_type": type(handler).__name__,
                            "error": str(e),
                            "request_id": operation.get("request_id"),
                        },
                    )
                    continue  # Skip on filter error

            # Execute handler
            try:
                handler.log_operation(operation)
            except Exception as e:
                # Track error if aggregation enabled
                if self.aggregate_errors:
                    self._record_error(handler, e, operation)

                # Log error but continue to other handlers
                logger.error(
                    f"Handler failed in CompositeHandler: {e}",
                    extra={
                        "error": str(e),
                        "handler_type": type(handler).__name__,
                        "priority": priority,
                        "request_id": operation.get("request_id"),
                    },
                    exc_info=True,
                )

    def _record_error(
        self, handler: Any, error: Exception, operation: dict[str, Any]
    ) -> None:
        """Record error for aggregation"""
        handler_key = f"{type(handler).__module__}.{type(handler).__name__}"

        # Increment error count
        self.error_counts[handler_key] = (
            self.error_counts.get(handler_key, 0) + 1
        )

        # Store error sample (limited)
        if handler_key not in self.error_samples:
            self.error_samples[handler_key] = []

        if len(self.error_samples[handler_key]) < self.error_threshold:
            error_msg = (
                f"[{operation.get('request_id')}] {type(error).__name__}: "
                f"{str(error)}"
            )
            self.error_samples[handler_key].append(error_msg)

    @property
    def error_summary(self) -> dict[str, Any]:
        """
        Get summary of handler errors

        Returns:
            Dictionary with error counts and samples per handler
        """
        return {
            "total_errors": sum(self.error_counts.values()),
            "errors_by_handler": {
                handler: {
                    "count": count,
                    "samples": self.error_samples.get(handler, []),
                }
                for handler, count in self.error_counts.items()
            },
        }

    def reset_errors(self) -> None:
        """Clear error tracking"""
        self.error_counts.clear()
        self.error_samples.clear()

    def add_handler(
        self, handler: Any, priority: int = 0, filter_fn: Any = None
    ) -> None:
        """
        Add handler dynamically

        Args:
            handler: Handler implementing AuditHandler protocol
            priority: Execution priority (higher = first)
            filter_fn: Optional filter function
        """
        self._handlers.append((handler, priority, filter_fn))
        # Re-sort by priority
        self._handlers.sort(key=lambda x: x[1], reverse=True)

        logger.debug(
            f"Handler added to CompositeHandler: {type(handler).__name__}",
            extra={"priority": priority, "has_filter": filter_fn is not None},
        )

    def remove_handler(self, handler: Any) -> bool:
        """
        Remove handler

        Args:
            handler: Handler to remove

        Returns:
            True if handler was found and removed
        """
        original_count = len(self._handlers)
        self._handlers = [
            (h, p, f) for h, p, f in self._handlers if h is not handler
        ]

        removed = len(self._handlers) < original_count
        if removed:
            logger.debug(
                f"Handler removed from CompositeHandler: "
                f"{type(handler).__name__}"
            )

        return removed

    def get_handlers(self) -> list[tuple[Any, int, Any]]:
        """
        Get list of all handlers with their priority and filters

        Returns:
            List of (handler, priority, filter_fn) tuples
        """
        return self._handlers.copy()

    def close(self) -> None:
        """Close all handlers that support it"""
        for handler, _, _ in self._handlers:
            if hasattr(handler, "close"):
                try:
                    handler.close()
                except Exception:
                    pass

    def __del__(self):
        """Cleanup on garbage collection"""
        self.close()


class NullHandler:
    """
    Null handler that does nothing

    Useful for disabling audit logging without changing code.

    Example:
        >>> from hfortix_core.audit import NullHandler
        >>>
        >>> # Disable audit logging
        >>> handler = NullHandler()
        >>> fgt = FortiOS("192.168.1.99", token="...", audit_handler=handler)
    """

    def log_operation(self, operation: dict[str, Any]) -> None:
        """Do nothing"""
        pass


class CallbackHandler:
    """
    Handler that wraps a callback function

    Allows using a simple function as an audit handler without
    creating a class.

    Example:
        >>> def my_audit_func(operation: dict):
        ...     send_to_kafka(operation)
        ...
        >>> handler = CallbackHandler(my_audit_func)
        >>> fgt = FortiOS("192.168.1.99", token="...", audit_handler=handler)

    Note:
        This is primarily for internal use. Users can pass callbacks
        directly to the audit_callback parameter.
    """

    def __init__(
        self,
        callback: Callable[[dict[str, Any]], None],
        propagate_errors: bool = False,
    ):
        """
        Initialize Callback handler

        Args:
            callback: Function that takes an operation dict
            propagate_errors: If True, re-raise exceptions from callback.
                              If False (default), log and swallow exceptions.
                              Set to True when used inside CompositeHandler
                              to enable error aggregation.
        """
        self.callback = callback
        self.propagate_errors = propagate_errors

    def log_operation(self, operation: dict[str, Any]) -> None:
        """Call the callback function"""
        try:
            self.callback(operation)
        except Exception as e:
            logger.error(
                f"Audit callback failed: {e}",
                extra={
                    "error": str(e),
                    "request_id": operation.get("request_id"),
                },
                exc_info=True,
            )
            if self.propagate_errors:
                raise
