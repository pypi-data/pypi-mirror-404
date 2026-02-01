"""ionbus_utils - A collection of Python utilities for common development tasks.

Modules:
    base_utils: Base conversion and platform detection
    logging_utils: Enhanced logging with custom levels
    file_utils: File operations, hashing, compression
    enumerate: C++-style enumerations
    group_utils: User and group utilities
    exceptions: Exception formatting and logging

Subpackages:
    crypto_utils: Cryptographic utilities and authentication
    yaml_utils: PDYaml class extending Pydantic with YAML support
"""

from __future__ import annotations

from ionbus_utils import base_utils
from ionbus_utils import crypto_utils
from ionbus_utils import enumerate
from ionbus_utils import exceptions
from ionbus_utils import file_utils
from ionbus_utils import group_utils
from ionbus_utils import logging_utils
from ionbus_utils import yaml_utils
try:
    from ionbus_utils._version import __version__  # type: ignore
except ImportError:
    __version__ = "unknown"

__all__ = [
    "base_utils",
    "crypto_utils",
    "enumerate",
    "exceptions",
    "file_utils",
    "group_utils",
    "logging_utils",
    "yaml_utils",
]
