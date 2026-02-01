"""
Debug information formatters for HFortix

Provides formatters for displaying request information, connection stats,
and debug output in human-readable formats.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from hfortix_fortios import FortiOS

__all__ = [
    "format_request_info",
    "format_connection_stats",
    "print_debug_info",
]


def format_request_info(request_info: dict[str, Any] | None) -> str:
    """Format request info dictionary as human-readable string.

    Args:
        request_info: Request info from client.last_request

    Returns:
        Formatted string with request details

    Example:
        >>> info = fgt.last_request
        >>> print(format_request_info(info))
        GET /api/v2/cmdb/firewall/address
        Response Time: 123.4ms
        Status Code: 200
    """
    if not request_info:
        return "No request information available"

    lines = []

    method = request_info.get("method", "UNKNOWN")
    endpoint = request_info.get("endpoint", "UNKNOWN")
    lines.append(f"{method} {endpoint}")

    if request_info.get("params"):
        lines.append(f"Params: {json.dumps(request_info['params'])}")

    response_time = request_info.get("response_time_ms")
    if response_time is not None:
        lines.append(f"Response Time: {response_time:.1f}ms")

    status_code = request_info.get("status_code")
    if status_code is not None:
        lines.append(f"Status Code: {status_code}")

    return "\n".join(lines)


def format_connection_stats(stats: dict[str, Any] | None) -> str:
    """Format connection stats dictionary as human-readable string.

    Args:
        stats: Connection stats from client.connection_stats

    Returns:
        Formatted string with connection statistics

    Example:
        >>> stats = fgt.connection_stats
        >>> print(format_connection_stats(stats))
        Connection Pool Statistics
        ==========================
        Max Connections: 100
        Active Requests: 2
        Total Requests: 1543
        Pool Exhaustion Events: 0
    """
    if not stats:
        return "No connection statistics available"

    lines = ["Connection Pool Statistics", "=" * 50]

    if "max_connections" in stats:
        lines.append(f"Max Connections: {stats['max_connections']}")
    if "max_keepalive_connections" in stats:
        lines.append(f"Max Keepalive: {stats['max_keepalive_connections']}")
    if "active_requests" in stats:
        lines.append(f"Active Requests: {stats['active_requests']}")
    if "total_requests" in stats:
        lines.append(f"Total Requests: {stats['total_requests']}")
    if "pool_exhaustion_count" in stats:
        count = stats["pool_exhaustion_count"]
        lines.append(f"Pool Exhaustion Events: {count}")
        if count > 0 and "pool_exhaustion_timestamps" in stats:
            lines.append(
                f"  Last Exhaustion: {stats['pool_exhaustion_timestamps'][-1]}"
            )

    return "\n".join(lines)


def print_debug_info(
    client: FortiOS,
    include_last_request: bool = True,
    include_connection_stats: bool = True,
) -> None:
    """Print comprehensive debug information for a FortiOS client.

    Args:
        client: FortiOS client to inspect
        include_last_request: Include last request details
        include_connection_stats: Include connection pool statistics

    Example:
        >>> from hfortix_core.debug import print_debug_info
        >>> fgt = FortiOS(host="192.168.1.99", token="your-token")
        >>> fgt.cmdb.firewall.address.get()
        >>> print_debug_info(fgt)
    """
    print("\nFortiOS Client Debug Information")
    print("=" * 60)

    if include_last_request:
        print("\nLast Request:")
        print("-" * 60)
        print(format_request_info(client.last_request))

    if include_connection_stats:
        print("\n" + format_connection_stats(client.connection_stats))

    print()  # Final newline
