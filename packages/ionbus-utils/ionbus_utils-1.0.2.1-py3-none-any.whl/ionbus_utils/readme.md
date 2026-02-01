# ionbus_utils

A collection of Python utilities for common development tasks including
logging, cryptography, file operations, date/time handling, caching,
pandas operations, subprocess management, and configuration management.

<!-- TOC start (generated with https://bitdowntoc.derlin.ch/) -->

- [Installation](#installation)
- [Modules](#modules)
- [Running Tests](#running-tests)
- [Requirements](#requirements)
- [License](#license)
- [Module Details](#module-details)
   * [base_utils](#base_utils)
   * [enumerate](#enumerate)
   * [group_utils](#group_utils)
   * [exceptions](#exceptions)
   * [regex_utils](#regex_utils)
   * [date_utils](#date_utils)
   * [general](#general)
   * [general_classes](#general_classes)
   * [git_utils](#git_utils)

<!-- TOC end -->

## Installation

```bash
pip install ionbus-utils
```

Or install from source:

```bash
pip install -e .
```

## Modules

| Module | Description | Documentation |
|--------|-------------|---------------|
| `base_utils` | Base conversion (2-64) and platform detection | [Details](#base_utils) |
| `cache_utils` | File-based and in-memory caching with thread-safe operations | [cache_utils.md](cache_utils.md) |
| `crypto_utils` | AES-128-GCM encryption and authentication file management | [crypto_utils/readme.md](crypto_utils/readme.md) |
| `date_utils` | Date conversion, month boundaries, ISO formatting | [Details](#date_utils) |
| `enumerate` | C++-style enumerations with bit flags and key-value support | [Details](#enumerate) |
| `exceptions` | Exception formatting and logging helpers | [Details](#exceptions) |
| `file_utils` | File operations, hashing, compression, log file management | [file_utils.md](file_utils.md) |
| `general_classes` | Generic utility classes (DictClass, ArgParseRangeAction) | [Details](#general_classes) |
| `general` | JSON loading, string/list utilities, compression helpers | [Details](#general) |
| `git_utils` | Git repository management, tagging, submodule handling | [git_utils/readme.md](git_utils/readme.md) |
| `group_utils` | User and group utilities (cross-platform) | [Details](#group_utils) |
| `logging_utils` | Enhanced logging with timestamps, custom levels, and `warn_once()` | [logging.md](logging.md) |
| `pandas_utils` | DataFrame manipulation, rollup operations, markdown export | [pandas_utils.md](pandas_utils.md) |
| `regex_utils` | Pre-compiled regex patterns for common string operations | [Details](#regex_utils) |
| `subprocess_utils` | Cross-platform subprocess management and process control | [subprocess_utils.md](subprocess_utils.md) |
| `time_utils` | DateTime/Timestamp utilities, timezone handling, time rounding | [time_utils.md](time_utils.md) |
| `yaml_utils` | `PDYaml` class extending Pydantic with YAML support | [yaml_utils/readme.md](yaml_utils/readme.md) |

## Running Tests

With the correct Python environment activated, run:

```bash
pytest tests/ -v
```

To run a specific test file:

```bash
pytest tests/test_base_utils.py -v
```

To run tests with coverage:

```bash
pytest tests/ --cov=ionbus_utils --cov-report=term-missing
```

## Requirements

- Python >= 3.9
- See `requirements.txt` for dependencies

## License

MIT License

---

## Module Details

### base_utils

Base conversion utilities and platform detection.

```python
from ionbus_utils.base_utils import int_to_base, base_to_int, uuid_baseN
from ionbus_utils.base_utils import is_windows, is_mac, is_wsl

# Convert integers to compact string representations
encoded = int_to_base(12345, base=62)  # "3d7"
decoded = base_to_int("3d7", base=62)  # 12345

# Generate short unique identifiers
unique_id = uuid_baseN(base=62)  # e.g., "5KmV8f1gH2jN"

# Platform detection
if is_windows():
    # Windows-specific code
elif is_wsl():
    # WSL-specific code
```

**Functions:**
- `int_to_base(num, base)` - Convert integer to string in base 2-64
- `base_to_int(string, base)` - Convert string back to integer
- `uuid_baseN(base)` - Generate UUID encoded in specified base
- `is_windows()`, `is_mac()`, `is_wsl()` - Platform detection

### enumerate

C++-style enumerations with extended functionality.

```python
from ionbus_utils.enumerate import Enumerate, StrEnum

# Integer values (useful for array indices)
colors = Enumerate("RED GREEN BLUE", as_int=True)
print(colors.RED)    # 0
print(colors.GREEN)  # 1

# With offset
colors = Enumerate("RED GREEN BLUE", as_int=True, int_offset=10)
print(colors.RED)  # 10

# Bit flags (useful for permissions)
perms = Enumerate("READ WRITE EXECUTE", as_bit=True)
print(perms.READ)               # 1
print(perms.WRITE)              # 2
print(perms.READ | perms.WRITE) # 3

# Key-value pairs
status = Enumerate("OK=200 NOT_FOUND=404 ERROR=500", key_value=True, as_int=True)
print(status.OK)         # 200
print(status.NOT_FOUND)  # 404

# From dictionary
colors = Enumerate({"RED": 1, "GREEN": 2, "BLUE": 3})

# Utility methods
colors.is_valid_key("RED")      # True
colors.is_valid_value(1)        # True
colors.value_to_key(1)          # "RED"
colors.keys()                   # ["RED", "GREEN", "BLUE"]
```

Also exports `StrEnum` (backported for Python < 3.11).

### group_utils

User and group utilities with cross-platform support (Windows/Linux).

```python
from ionbus_utils.group_utils import get_user_name, get_groups_for_user
from ionbus_utils.group_utils import get_group_members

# Get current username
username = get_user_name()              # "JSMITH" (uppercase by default)
username = get_user_name(upper_case=False)  # "jsmith"

# Get groups for a user
groups = get_groups_for_user("jsmith")  # ["developers", "users", ...]

# Get members of a group
members = get_group_members("developers")  # ["jsmith", "asmith", ...]
```

### exceptions

Exception formatting and logging helpers.

```python
from ionbus_utils.exceptions import exception_to_string, log_exception

try:
    risky_operation()
except Exception as e:
    # Log exception with full context (file, function, hostname)
    log_exception(e)

    # Or get formatted string for custom handling
    error_text = exception_to_string(e)
    print(error_text)
```

`log_exception()` automatically includes:
- Exception type and message
- Full traceback
- File and function where the exception occurred
- Hostname information

### regex_utils

Pre-compiled regex patterns for common string operations.

```python
from ionbus_utils.regex_utils import (
    NEWLINE_RE,
    SPACE_RE,
    COMMA_SEMI_RE,
    NON_LETTER_LIKE_RE,
    NON_DIGIT_RE,
    LEADING_UNDER_RE,
)

# Split by newlines (handles \r\n and \n)
lines = NEWLINE_RE.split(text)

# Split/replace whitespace
normalized = SPACE_RE.sub(" ", text)

# Split on commas or semicolons (with surrounding whitespace)
items = COMMA_SEMI_RE.split("a, b; c")  # ["a", "b", "c"]

# Remove non-letter characters
clean = NON_LETTER_LIKE_RE.sub("", text)

# Remove non-digits
digits_only = NON_DIGIT_RE.sub("", "abc123")  # "123"

# Remove leading underscores
name = LEADING_UNDER_RE.sub("", "_private")  # "private"
```

### date_utils

Date conversion and manipulation utilities.

```python
from ionbus_utils.date_utils import (
    yyyymmdd_to_date,
    to_date,
    to_date_isoformat,
    first_day_of_month,
    first_day_of_next_month,
    last_day_of_month,
)

# Parse date strings (punctuation ignored)
d = yyyymmdd_to_date("2024-07-23")  # date(2024, 7, 23)
d = yyyymmdd_to_date("20240723")    # date(2024, 7, 23)

# Convert various types to date
to_date(datetime.now())    # date object
to_date(pd.Timestamp(...)) # date object
to_date("2024-07-23")      # date object

# ISO format conversion
to_date_isoformat(date(2024, 7, 23))                    # "2024-07-23"
to_date_isoformat(date(2024, 7, 23), no_symbols=True)  # "20240723"

# Month boundary calculations
first_day_of_month(date(2024, 7, 15))      # date(2024, 7, 1)
last_day_of_month(date(2024, 7, 15))       # date(2024, 7, 31)
first_day_of_next_month(date(2024, 7, 15)) # date(2024, 8, 1)
```

### general

General-purpose utilities for JSON, strings, lists, and more.

```python
from ionbus_utils.general import (
    load_json,
    load_json_string,
    remove_comments,
    convert_string_to_float,
    to_single_list,
    filter_string_rep_of_list,
    filter_string_rep_of_dict,
    dict_to_namedtuple,
    list_to_comma_string,
    comma_join_list,
    open_using,
    compress_and_encode_as_base64,
    decompress_and_decode_from_base64,
    timestamped_unique_id,
)

# Load JSON with comments and trailing commas
config = load_json("config.json")  # Handles // and /* */ comments

# Convert strings with suffixes to floats
convert_string_to_float("1.5k")   # 1500.0
convert_string_to_float("2.5MM")  # 2500000.0
convert_string_to_float("1B")     # 1000000000.0

# Flatten args into single list
to_single_list((["a", "b"],))  # ["a", "b"]
to_single_list("single")       # ["single"]

# Filter lists/dicts by regex
cols = ["id", "name", "created_at", "updated_at"]
filter_string_rep_of_list(cols, r".*_at$")  # ["created_at", "updated_at"]

# English-style list joining
comma_join_list([1, 2, 3])  # "1, 2, and 3"

# Open regular or gzip files transparently
with open_using("data.txt.gz", "rb") as f:
    content = f.read()

# Generate unique timestamped IDs
timestamped_unique_id("task")  # "task_2Kj5x_8fGh1mN..."
```

### general_classes

Generic utility classes.

```python
from ionbus_utils.general_classes import (
    GenObject,
    DictClass,
    ArgParseRangeAction,
)

# GenObject: Simple object for ad-hoc attributes
obj = GenObject()
obj.value = 42

# DictClass: Dictionary with attribute access
d = DictClass({"name": "Alice", "age": 30})
print(d.name)      # "Alice"
print(d["name"])   # "Alice"
d.city = "NYC"     # Set via attribute
print(d["city"])   # "NYC"

# ArgParseRangeAction: Enforce argument count ranges
import argparse
parser = argparse.ArgumentParser()
parser.add_argument(
    "--files",
    action=ArgParseRangeAction,
    min_args=1,
    max_args=3,
    help="Provide 1-3 files"
)
```

