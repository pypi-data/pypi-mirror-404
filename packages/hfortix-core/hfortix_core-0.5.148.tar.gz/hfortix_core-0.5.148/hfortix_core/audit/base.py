"""
Base Audit Protocol and Interfaces

Defines the core protocol and types for audit logging.
"""

from __future__ import annotations

from typing import Any, Protocol, TypedDict, runtime_checkable

__all__ = ["AuditHandler", "AuditOperation"]


class AuditOperation(TypedDict, total=False):
    """
    Type definition for audit operation data

    Attributes:
        timestamp: ISO 8601 timestamp when operation occurred
        request_id: Unique identifier for correlating related operations
        method: HTTP method (GET, POST, PUT, DELETE)
        endpoint: Full API endpoint path (e.g., '/api/v2/cmdb/firewall/policy')
        api_type: API category (cmdb, monitor, log, service)
        path: Relative path within api_type
        vdom: Virtual domain name (if applicable)
        action: High-level action (create, update, delete, read, list)
        object_type: Type of object being operated on (e.g., 'firewall.policy')
        object_name: Name/identifier of specific object (if available)
        data: Request payload (sanitized)
        params: Query parameters (sanitized)
        status_code: HTTP response status code
        success: Whether operation succeeded
        duration_ms: Operation duration in milliseconds
        error: Error message (if operation failed)
        user_context: Optional user-provided context dict
        host: FortiGate device IP/hostname
        read_only_mode: Whether operation was simulated in read-only mode
    """

    timestamp: str
    request_id: str
    method: str
    endpoint: str
    api_type: str
    path: str
    vdom: str | None
    action: str
    object_type: str
    object_name: str | None
    data: dict[str, Any] | None
    params: dict[str, Any] | None
    status_code: int
    success: bool
    duration_ms: int
    error: str | None
    user_context: dict[str, Any] | None
    host: str
    read_only_mode: bool


@runtime_checkable
class AuditHandler(Protocol):
    """
    Protocol for audit log handlers

    Any class implementing this protocol can be used as an audit handler.
    This allows for maximum flexibility - users can provide custom handlers
    for their specific logging infrastructure.

    The handler receives sanitized operation data and is responsible for:
    - Formatting the data as needed
    - Sending to destination (file, syslog, database, etc.)
    - Handling errors gracefully (should not raise exceptions)

    Example:
        >>> class CustomHandler:
        ...     def log_operation(self, operation: dict[str, Any]) -> None:
        ...         # Send to your logging infrastructure
        ...         send_to_kafka(operation)
        ...         update_database(operation)
        ...
        >>> handler = CustomHandler()
        >>> fgt = FortiOS("192.168.1.99", token="...", audit_handler=handler)
    """

    def log_operation(self, operation: dict[str, Any]) -> None:
        """
        Log an API operation

        Args:
            operation: Dictionary containing operation details (see AuditOperation)  # noqa: E501

        Note:
            This method should handle errors internally and not raise exceptions,  # noqa: E501
            as audit logging failures should not break API operations.
        """
        ...
