# ionbus_utils

A collection of Python utilities for common development tasks including
logging, cryptography, file operations, date/time handling, caching,
pandas operations, subprocess management, and configuration management.

## Installation

```bash
pip install ionbus-utils
```

Or install from source:

```bash
pip install -e .
```

## Modules

| Module | Description |
|--------|-------------|
| `base_utils` | Base conversion (2-64) and platform detection |
| `cache_utils` | File-based and in-memory caching with thread-safe operations |
| `crypto_utils` | AES-128-GCM encryption and authentication file management |
| `date_utils` | Date conversion, month boundaries, ISO formatting |
| `enumerate` | C++-style enumerations with bit flags and key-value support |
| `exceptions` | Exception formatting and logging helpers |
| `file_utils` | File operations, hashing, compression, log file management |
| `general_classes` | Generic utility classes (DictClass, ArgParseRangeAction) |
| `general` | JSON loading, string/list utilities, compression helpers |
| `git_utils` | Git repository management, tagging, submodule handling |
| `group_utils` | User and group utilities (cross-platform) |
| `logging_utils` | Enhanced logging with timestamps, custom levels, and `warn_once()` |
| `pandas_utils` | DataFrame manipulation, rollup operations, markdown export |
| `regex_utils` | Pre-compiled regex patterns for common string operations |
| `subprocess_utils` | Cross-platform subprocess management and process control |
| `time_utils` | DateTime/Timestamp utilities, timezone handling, time rounding |
| `yaml_utils` | `PDYaml` class extending Pydantic with YAML support |

Full [documentation on github](https://github.com/ionbus/ionbus_utils/tree/main?tab=readme-ov-file#ionbus_utils).

## Requirements

- Python >= 3.9
- See `requirements.txt` for dependencies

## License

MIT License
