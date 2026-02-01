"""
Debug handlers for HFortix SDK

Provides context managers and handlers for debugging API sessions
and measuring performance.
"""

from __future__ import annotations

import json
import time
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, Iterator, Literal

if TYPE_CHECKING:
    from hfortix_fortios import FortiOS

__all__ = [
    "DebugSession",
    "debug_timer",
]


class DebugSession:
    """Context manager for debugging FortiOS API sessions.

    Captures detailed information about all API requests made within the session,  # noqa: E501
    including timing, connection stats, and request/response details.

    Args:
        client: FortiOS client instance to debug
        capture_response_data: Whether to capture full response bodies (default: False)  # noqa: E501
        print_on_exit: Whether to print summary when exiting context (default: True)  # noqa: E501

    Example:
        >>> with DebugSession(fgt, capture_response_data=True) as session:
        ...     fgt.cmdb.firewall.address.get()
        ...     fgt.cmdb.firewall.policy.create(data={...})
        ...     session.print_summary()

        Session Summary:
        ================
        Duration: 1.234s
        Total Requests: 2
        Successful: 2
        Failed: 0
        Average Response Time: 617ms
        ...
    """

    def __init__(
        self,
        client: FortiOS,
        capture_response_data: bool = False,
        print_on_exit: bool = True,
    ) -> None:
        """Initialize debug session.

        Args:
            client: FortiOS client to monitor
            capture_response_data: Capture full response bodies
            print_on_exit: Auto-print summary on context exit
        """
        self.client = client
        self.capture_response_data = capture_response_data
        self.print_on_exit = print_on_exit

        # Session tracking
        self._start_time: float | None = None
        self._end_time: float | None = None
        self._initial_stats: dict[str, Any] | None = None
        self._final_stats: dict[str, Any] | None = None
        self._requests: list[dict[str, Any]] = []

    def __enter__(self) -> DebugSession:
        """Start debug session."""
        self._start_time = time.time()
        self._initial_stats = self.client.connection_stats
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """End debug session and optionally print summary."""
        self._end_time = time.time()
        self._final_stats = self.client.connection_stats

        if self.print_on_exit:
            self.print_summary()

    @property
    def duration(self) -> float | None:
        """Session duration in seconds."""
        if self._start_time is None:
            return None
        end = self._end_time or time.time()
        return end - self._start_time

    @property
    def request_count(self) -> int:
        """Total number of requests captured."""
        return len(self._requests)

    @property
    def stats_delta(self) -> dict[str, Any] | None:
        """Difference in connection stats from start to end."""
        if not self._initial_stats or not self._final_stats:
            return None

        return {
            "requests_made": (
                self._final_stats["total_requests"]
                - self._initial_stats["total_requests"]
            ),
            "pool_exhaustions": (
                self._final_stats["pool_exhaustion_count"]
                - self._initial_stats["pool_exhaustion_count"]
            ),
            "active_requests_delta": (
                self._final_stats["active_requests"]
                - self._initial_stats["active_requests"]
            ),
        }

    def capture_request(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
        response_time_ms: float | None = None,
        status_code: int | None = None,
        response_data: Any = None,
        error: str | None = None,
    ) -> None:
        """Capture information about an API request.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            params: Request parameters
            response_time_ms: Response time in milliseconds
            status_code: HTTP status code
            response_data: Response body (if capture_response_data=True)
            error: Error message if request failed
        """
        request_info = {
            "timestamp": time.time(),
            "method": method,
            "endpoint": endpoint,
            "params": params,
            "response_time_ms": response_time_ms,
            "status_code": status_code,
            "error": error,
        }

        if self.capture_response_data and response_data is not None:
            request_info["response_data"] = response_data

        self._requests.append(request_info)

    def get_summary(self) -> dict[str, Any]:
        """Get session summary as dictionary.

        Returns:
            Dictionary with session metrics and statistics
        """
        if not self._requests:
            successful = failed = 0
            avg_response_time = max_response_time = min_response_time = None
        else:
            successful = sum(1 for r in self._requests if not r.get("error"))
            failed = len(self._requests) - successful

            response_times = [
                r["response_time_ms"]
                for r in self._requests
                if r.get("response_time_ms") is not None
            ]

            if response_times:
                avg_response_time = sum(response_times) / len(response_times)
                max_response_time = max(response_times)
                min_response_time = min(response_times)
            else:
                avg_response_time = max_response_time = min_response_time = (
                    None
                )

        return {
            "duration_seconds": self.duration,
            "total_requests": len(self._requests),
            "successful_requests": successful,
            "failed_requests": failed,
            "avg_response_time_ms": avg_response_time,
            "max_response_time_ms": max_response_time,
            "min_response_time_ms": min_response_time,
            "stats_delta": self.stats_delta,
            "initial_stats": self._initial_stats,
            "final_stats": self._final_stats,
        }

    def print_summary(self, format: Literal["text", "json"] = "text") -> None:
        """Print session summary.

        Args:
            format: Output format - 'text' for human-readable, 'json' for structured  # noqa: E501
        """
        summary = self.get_summary()

        if format == "json":
            print(json.dumps(summary, indent=2))
            return

        # Text format
        print("\nDebug Session Summary")
        print("=" * 60)

        if summary["duration_seconds"] is not None:
            print(f"Duration: {summary['duration_seconds']:.3f}s")

        print(f"Total Requests: {summary['total_requests']}")
        print(f"Successful: {summary['successful_requests']}")
        print(f"Failed: {summary['failed_requests']}")

        if summary["avg_response_time_ms"] is not None:
            print(
                f"Average Response Time: {summary['avg_response_time_ms']:.1f}ms"  # noqa: E501
            )
            print(
                f"Max Response Time: {summary['max_response_time_ms']:.1f}ms"
            )
            print(
                f"Min Response Time: {summary['min_response_time_ms']:.1f}ms"
            )

        if summary["stats_delta"]:
            print("\nConnection Pool Delta:")
            print(
                f"  Requests Made: {summary['stats_delta']['requests_made']}"
            )
            print(
                f"  Pool Exhaustions: {summary['stats_delta']['pool_exhaustions']}"  # noqa: E501
            )
            print(
                f"  Active Requests Change: {summary['stats_delta']['active_requests_delta']}"  # noqa: E501
            )

        if summary["final_stats"]:
            print("\nFinal Connection Stats:")
            print(
                f"  Active Requests: {summary['final_stats']['active_requests']}"  # noqa: E501
            )
            print(
                f"  Total Requests: {summary['final_stats']['total_requests']}"
            )
            print(
                f"  Pool Exhaustion Count: {summary['final_stats']['pool_exhaustion_count']}"  # noqa: E501
            )

    def print_requests(self, verbose: bool = False) -> None:
        """Print detailed information about captured requests.

        Args:
            verbose: Include full request/response details
        """
        if not self._requests:
            print("\nNo requests captured")
            return

        print(f"\nCaptured Requests ({len(self._requests)} total)")
        print("=" * 60)

        for i, req in enumerate(self._requests, 1):
            print(f"\n{i}. {req['method']} {req['endpoint']}")
            print(f"   Time: {req.get('response_time_ms', 'N/A')}ms")
            print(f"   Status: {req.get('status_code', 'N/A')}")

            if req.get("error"):
                print(f"   Error: {req['error']}")

            if verbose:
                if req.get("params"):
                    print(f"   Params: {json.dumps(req['params'], indent=6)}")
                if req.get("response_data"):
                    print(
                        f"   Response: {json.dumps(req['response_data'], indent=6)}"  # noqa: E501
                    )


@contextmanager
def debug_timer(operation: str = "Operation") -> Iterator[dict[str, Any]]:
    """Context manager for timing operations.

    Args:
        operation: Name of the operation being timed

    Yields:
        Dictionary that will be populated with timing information

    Example:
        >>> with debug_timer("Get firewall addresses") as timing:
        ...     result = fgt.cmdb.firewall.address.get()
        >>> print(f"Took {timing['duration_ms']:.1f}ms")
    """
    timing: dict[str, Any] = {"operation": operation}
    start_time = time.time()

    try:
        yield timing
    finally:
        end_time = time.time()
        timing["duration_seconds"] = end_time - start_time
        timing["duration_ms"] = (end_time - start_time) * 1000

        print(f"{operation}: {timing['duration_ms']:.1f}ms")
