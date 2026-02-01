"""Common utilities."""

from typing import Any


def normalize_keys(data: Any) -> Any:
    """
    Recursively normalize dictionary keys from hyphen to underscore format.

    FortiOS API returns keys with hyphens (e.g., 'tcp-portrange'), but Python
    identifiers cannot contain hyphens. This function converts all keys to use
    underscores (e.g., 'tcp_portrange') to match TypedDict definitions.

    Args:
        data: Data to normalize (dict, list, or other types)

    Returns:
        Normalized data with hyphenated keys converted to underscored keys

    Examples:
        >>> normalize_keys({"tcp-portrange": "8080", "name": "test"})
        {"tcp_portrange": "8080", "name": "test"}

        >>> normalize_keys([{"srcaddr": [{"name": "test-addr"}]}])
        [{"srcaddr": [{"name": "test-addr"}]}]
    """
    if isinstance(data, dict):
        return {
            key.replace("-", "_"): normalize_keys(value)
            for key, value in data.items()
        }
    elif isinstance(data, list):
        return [normalize_keys(item) for item in data]
    else:
        return data


__all__ = ["normalize_keys"]
