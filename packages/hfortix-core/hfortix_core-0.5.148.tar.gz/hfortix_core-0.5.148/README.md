# HFortix Core

Core foundation for HFortix - Python SDK for Fortinet products.

[![PyPI version](https://badge.fury.io/py/hfortix-core.svg)](https://pypi.org/project/hfortix-core/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

> **⚠️ BETA STATUS - Version 0.5.57 (January 14, 2026)**
>
> Production-ready but in beta. All packages remain in beta until v1.0 with comprehensive unit tests.

## Overview

`hfortix-core` provides the shared foundation for all HFortix Fortinet SDKs. It includes exception handling, HTTP client framework, formatting utilities, and common types used across FortiOS, FortiManager, and FortiAnalyzer clients.

**This package is typically used as a dependency.** For most users, install a product-specific package like `hfortix-fortios` or the meta-package `hfortix[all]`.

## Installation

```bash
pip install hfortix-core
```

## What's Included

### Formatting Utilities (`fmt` module) - NEW in v0.5.44!

13 data formatting functions for converting FortiOS data:

```python
from hfortix_core import fmt

# Convert to various formats
fmt.to_json(data)           # Formatted JSON string
fmt.to_csv(data)            # Comma-separated string  
fmt.to_dict(data)           # Dictionary
fmt.to_list(data)           # List (auto-splits "80 443" → ['80', '443'])
fmt.to_multiline(data)      # Newline-separated string
fmt.to_quoted(data)         # Quoted string representation
fmt.to_table(data)          # ASCII table format
fmt.to_yaml(data)           # YAML-like output (no dependencies)
fmt.to_xml(data)            # Simple XML format
fmt.to_key_value(data)      # Config file format
fmt.to_markdown_table(data) # Markdown table
fmt.to_dictlist(data)       # Columnar → row format
fmt.to_listdict(data)       # Row → columnar format
```

**Features:**
- Zero external dependencies
- Handles any input gracefully (never raises exceptions)
- Auto-split for space-delimited strings (perfect for FortiOS `tcp_portrange`)
- Works with objects, dicts, lists, primitives

### Exception System

Comprehensive exception hierarchy with 403+ FortiOS error codes:

```python
from hfortix_core import (
    FortinetError,      # Base exception
    APIError,           # API-specific errors
    AuthenticationError,
    ResourceNotFoundError,
    DuplicateEntryError,
    # ... and 380+ more
)

try:
    # Your Fortinet API code
    pass
except DuplicateEntryError as e:
    print(f"Object already exists: {e}")
except ResourceNotFoundError as e:
    print(f"Not found: {e}")
except APIError as e:
    print(f"API Error: {e.message} (code: {e.error_code})")
```

**Features:**
- 403+ specific error codes with detailed descriptions
- Intelligent error classification
- Built-in recovery suggestions
- Request correlation tracking

### Type Definitions

Shared TypedDict definitions and protocols for type safety:

```python
from hfortix_core import (
    APIResponse,
    MutationResponse,
    RawAPIResponse,
    ListResponse,
    ObjectResponse,
    ErrorResponse,
    ConnectionStats,
    RequestInfo,
)

# Protocol interface for extensibility
from hfortix_core.http.interface import IHTTPClient

class MyCustomClient:
    def get(self, api_type: str, path: str, **kwargs) -> dict: ...
    def post(self, api_type: str, path: str, data: dict, **kwargs) -> dict: ...
    # ... implement IHTTPClient protocol
```

## When to Use This Package

**Use `hfortix-core` directly if:**
- Building custom Fortinet integrations
- Creating specialized HTTP clients
- Extending exception handling
- Implementing custom protocols

**For most users:**
```bash
# Install FortiOS client (includes core automatically)
pip install hfortix-fortios

# Or install everything
pip install hfortix[all]
```

## Product Packages

This core is used by:
- **hfortix-fortios** - FortiOS/FortiGate API client (1,348 endpoints)
- **hfortix-fortimanager** - FortiManager client (planned)
- **hfortix-fortianalyzer** - FortiAnalyzer client (planned)

## Key Features

- 🔒 **Type-Safe**: Full PEP 561 compliance with type hints
- ⚡ **High Performance**: HTTP/2 support with connection pooling
- 🔄 **Resilient**: Automatic retry logic and circuit breaker
- 🎯 **Async Ready**: Full async/await support
- 📊 **Observable**: Request tracking and structured logging
- 🛡️ **Enterprise Grade**: Production-ready reliability features
- 📝 **Formatting**: 13 data conversion utilities in `fmt` module

## Requirements

- Python 3.10+
- httpx[http2] >= 0.27.0

## Documentation

For complete documentation, see the [main repository](https://github.com/hermanwjacobsen/hfortix):

- [Quick Start Guide](https://github.com/hermanwjacobsen/hfortix/blob/main/QUICKSTART.md)
- [API Reference](https://github.com/hermanwjacobsen/hfortix/blob/main/docs/fortios/ENDPOINT_METHODS.md)
- [Async Guide](https://github.com/hermanwjacobsen/hfortix/blob/main/docs/fortios/ASYNC_GUIDE.md)

## License

Proprietary - See LICENSE file

## Support

- 📖 [Documentation](https://github.com/hermanwjacobsen/hfortix)
- 🐛 [Report Issues](https://github.com/hermanwjacobsen/hfortix/issues)
- 💬 [Discussions](https://github.com/hermanwjacobsen/hfortix/discussions)
