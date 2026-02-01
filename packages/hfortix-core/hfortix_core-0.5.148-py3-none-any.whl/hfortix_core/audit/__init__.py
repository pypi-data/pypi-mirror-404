"""
Enterprise Audit Logging for FortiOS API Operations

This module provides comprehensive audit logging capabilities for tracking
all API operations to FortiGate devices. Essential for compliance with
SOC 2, HIPAA, PCI-DSS, and other regulatory requirements.

Features:
- Protocol-based handler interface (bring your own handler)
- Built-in handlers for common use cases (Syslog, File, Stream)
- Configurable formatters (JSON, CEF, Syslog RFC 5424)
- Composite handlers for multi-destination logging
- Automatic data sanitization for sensitive fields
- Non-blocking error handling (audit failures don't break operations)

Basic Usage:
    >>> from hfortix import FortiOS
    >>> from hfortix_core.audit import SyslogHandler
    >>>
    >>> # Send audit logs to SIEM
    >>> fgt = FortiOS(
    ...     "192.168.1.99",
    ...     token="token",
    ...     audit_handler=SyslogHandler("siem.company.com:514")
    ... )
    >>>
    >>> # Now all API operations are automatically logged
    >>> fgt.api.cmdb.firewall.policy.create(data={...})

Advanced Usage:
    >>> from hfortix_core.audit import CompositeHandler, FileHandler, StreamHandler  # noqa: E501
    >>>
    >>> # Send to multiple destinations
    >>> handler = CompositeHandler([
    ...     SyslogHandler("siem.company.com:514"),  # Compliance
    ...     FileHandler("/var/log/fortinet.log"),   # Local backup
    ...     StreamHandler(format="json")             # Container logs
    ... ])
    >>>
    >>> fgt = FortiOS("192.168.1.99", token="token", audit_handler=handler)

Custom Handler:
    >>> def custom_audit(operation: dict):
    ...     # Send to Kafka, database, cloud logging, etc.
    ...     send_to_kafka(operation)
    ...
    >>> fgt = FortiOS("192.168.1.99", token="token", audit_callback=custom_audit)  # noqa: E501
"""

from .base import AuditHandler, AuditOperation
from .formatters import (
    AuditFormatter,
    CEFFormatter,
    JSONFormatter,
    SyslogFormatter,
)
from .handlers import (
    CompositeHandler,
    FileHandler,
    NullHandler,
    StreamHandler,
    SyslogHandler,
)

__all__ = [
    # Base protocol and types
    "AuditHandler",
    "AuditOperation",
    # Handlers
    "SyslogHandler",
    "FileHandler",
    "StreamHandler",
    "CompositeHandler",
    "NullHandler",
    # Formatters
    "AuditFormatter",
    "JSONFormatter",
    "SyslogFormatter",
    "CEFFormatter",
]
