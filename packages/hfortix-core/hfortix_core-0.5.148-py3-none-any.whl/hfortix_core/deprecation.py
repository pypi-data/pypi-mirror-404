"""
Deprecation warnings for FortiOS API fields.

Provides utilities to warn users about deprecated fields
and suggest migrations to newer alternatives.
"""

from __future__ import annotations

import warnings
from typing import Any


class DeprecationWarning(UserWarning):
    """Warning for deprecated API fields."""

    pass


def warn_deprecated_field(
    field_name: str,
    endpoint: str,
    reason: str | None = None,
    alternative: str | None = None,
    removal_version: str | None = None,
) -> None:
    """
    Emit a deprecation warning for a field.

    Args:
        field_name: Name of the deprecated field
        endpoint: API endpoint path (e.g., "firewall/address")
        reason: Optional reason for deprecation
        alternative: Optional suggested alternative field
        removal_version: Optional version when field will be removed
    """
    parts = [f"Field '{field_name}' in endpoint '{endpoint}' is deprecated"]

    if reason:
        parts.append(f"Reason: {reason}")

    if alternative:
        parts.append(f"Use '{alternative}' instead")

    if removal_version:
        parts.append(f"Will be removed in version {removal_version}")

    message = ". ".join(parts) + "."

    warnings.warn(message, DeprecationWarning, stacklevel=3)


def check_deprecated_fields(
    payload: dict[str, Any],
    deprecated_fields: dict[str, dict[str, str]],
    endpoint: str,
) -> None:
    """
    Check payload for deprecated fields and emit warnings.

    Args:
        payload: The data payload to check
        deprecated_fields: Dict mapping field names to deprecation info
            Format: {
                "field_name": {
                    "reason": "...",
                    "alternative": "...",
                    "removal_version": "..."
                }
            }
        endpoint: API endpoint path
    """
    for field_name in payload:
        if field_name in deprecated_fields:
            info = deprecated_fields[field_name]
            warn_deprecated_field(
                field_name=field_name,
                endpoint=endpoint,
                reason=info.get("reason"),
                alternative=info.get("alternative"),
                removal_version=info.get("removal_version"),
            )
