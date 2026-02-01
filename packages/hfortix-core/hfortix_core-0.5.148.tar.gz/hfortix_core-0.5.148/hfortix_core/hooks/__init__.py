"""
Request Hook Protocols

Defines protocols for before-request and after-request hooks that allow
intercepting and modifying API requests/responses.
"""

from __future__ import annotations

from typing import Any, Protocol, TypedDict, runtime_checkable

__all__ = ["BeforeRequestHook", "AfterRequestHook", "RequestContext"]


class RequestContext(TypedDict, total=False):
    """
    Request context passed to hooks

    Attributes:
        method: HTTP method (GET, POST, PUT, DELETE)
        api_type: API category (cmdb, monitor, log, service)
        path: Relative endpoint path
        data: Request payload (mutable)
        params: Query parameters (mutable)
        vdom: Virtual domain
        endpoint: Full endpoint path
        request_id: Unique request identifier
        user_context: User-provided context metadata
    """

    method: str
    api_type: str
    path: str
    data: dict[str, Any] | None
    params: dict[str, Any] | None
    vdom: str | None
    endpoint: str
    request_id: str
    user_context: dict[str, Any] | None


@runtime_checkable
class BeforeRequestHook(Protocol):
    """
    Protocol for before-request hooks

    Hooks implementing this protocol are called BEFORE sending API requests.
    They can:
    - Validate request data
    - Transform request data
    - Add headers or parameters
    - Cancel requests (raise exception)
    - Log/audit request details

    Example:
        >>> class ValidationHook:
        ...     def before_request(
        ...         self, context: dict[str, Any]
        ...     ) -> dict[str, Any]:
        ...         # Validate request
        ...         if 'ticket' not in context.get('user_context', {}):
        ...             raise ValueError("Change ticket required!")
        ...         return context
        ...
        >>> hook = ValidationHook()
        >>> fgt = FortiOS(
        ...     "192.168.1.99", token="...", before_request_hooks=[hook]
        ... )
    """

    def before_request(self, context: dict[str, Any]) -> dict[str, Any]:
        """
        Called before sending API request

        Args:
            context: Request context (see RequestContext)

        Returns:
            Modified context (changes apply to request)

        Raises:
            Any exception to cancel the request

        Note:
            - Modify context['data'] or context['params'] to change request
            - Raise exceptions to block requests
            - Keep execution fast - this runs in request path
        """
        ...


@runtime_checkable
class AfterRequestHook(Protocol):
    """
    Protocol for after-request hooks

    Hooks implementing this protocol are called AFTER receiving API responses.
    They can:
    - Validate responses
    - Transform response data
    - Log successful operations
    - Trigger side effects
    - Cache results

    Note: The existing audit_handler is a specialized after-request hook.

    Example:
        >>> class CacheHook:
        ...     def after_request(
        ...         self, context: dict[str, Any], response: dict[str, Any]
        ...     ) -> dict[str, Any]:
        ...         # Cache GET responses
        ...         if context['method'] == 'GET':
        ...             self.cache[context['endpoint']] = response
        ...         return response
    """

    def after_request(
        self, context: dict[str, Any], response: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Called after receiving API response (success only)

        Args:
            context: Request context (see RequestContext)
            response: API response (mutable)

        Returns:
            Modified response (changes apply to caller)

        Note:
            - Only called on successful requests (2xx status)
            - Exceptions in hooks don't cancel the response
            - Keep execution fast - this runs in response path
        """
        ...
