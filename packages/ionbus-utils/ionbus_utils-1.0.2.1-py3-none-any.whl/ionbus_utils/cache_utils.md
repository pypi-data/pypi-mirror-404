# cache_utils.py Documentation

## Overview
Module providing both in-memory and on-disk caching functionality for data persistence and retrieval, with support for date-based file caching and thread-safe in-memory caching.

## File-Based Caching Functions

### `cache_filename(prefix, the_date=None, keep_date_as_string=False, directory="data")`
Generates standardized cache filename with date-based naming.
- **Parameters:**
  - `prefix`: File prefix identifier
  - `the_date`: Date for filename (date, datetime, Timestamp, str, or None for today)
  - `keep_date_as_string`: Keep date as wildcard "*" for glob patterns (default: False)
  - `directory`: Cache directory path (default: "data")
- **Returns:** Filename in format: `{directory}/{prefix}_{YYYYMMDD}.pkl.gz`
- **Example:** `data/users_20240115.pkl.gz`

### `get_latest_cache_filename(prefix, directory="")`
Finds the most recent cache file for given prefix.
- **Parameters:**
  - `prefix`: File prefix to search for
  - `directory`: Directory to search in
- **Returns:** Path to latest file or None if no files found
- **Note:** Relies on alphabetical sorting (date format ensures chronological order)

### `load_cache(prefix, cb_time, directory="data", allow_no_data=False, alias=None)`
Loads cache file with intelligent date-based selection and callback scheduling.
- **Parameters:**
  - `prefix`: Cache file prefix
  - `cb_time`: Callback time for cache refresh (TimeType)
  - `directory`: Cache directory (default: "data")
  - `allow_no_data`: Return empty dict if no cache found (default: False)
  - `alias`: Optional alias for OpsGenie alerts
- **Returns:** Tuple of (data_dict, next_callback_datetime)
- **Behavior:**
  - Loads today's cache if exists, schedules tomorrow's callback
  - Falls back to latest available cache if today's missing
  - Returns empty dict if `allow_no_data=True` and no cache exists
- **Raises:** RuntimeError if no data and `allow_no_data=False`

## In-Memory Caching Class

### `InMemoryCache`
Thread-safe singleton class for in-memory data caching.

#### Class Variables
- `_lock`: Threading lock for thread-safe operations
- `_cache_data`: Internal dictionary storing cached data
- `_stash_id`: Counter for auto-generated keys

#### Methods

##### `get(prefix_keys, *keys, default_copy=True)` (classmethod)
Retrieves single cached item.
- **Parameters:**
  - `prefix_keys`: Key prefix (string, list, or tuple)
  - `*keys`: Additional key components
  - `default_copy`: Return copy of data (default: True)
- **Returns:** Cached data or None if not found
- **Thread-Safe:** Yes

##### `get_many(prefix_keys, list_or_dict, default_copy=True)` (classmethod)
Retrieves multiple cached items.
- **Parameters:**
  - `prefix_keys`: Key prefix
  - `list_or_dict`: List of keys or dict to populate
  - `default_copy`: Return copies of data (default: True)
- **Returns:** Dictionary with requested items
- **Thread-Safe:** Yes

##### `get_state(prefix_keys, autogen_key)` (classmethod)
Retrieves state dictionary without copying.
- **Parameters:**
  - `prefix_keys`: Key prefix
  - `autogen_key`: Auto-generated state key
- **Returns:** State dictionary (no copy)
- **Thread-Safe:** Yes

##### `put(data, prefix_keys, *keys)` (classmethod)
Stores single item in cache.
- **Parameters:**
  - `data`: Data to cache
  - `prefix_keys`: Key prefix
  - `*keys`: Additional key components
- **Thread-Safe:** Yes

##### `put_many(data_dict, prefix_keys)` (classmethod)
Stores multiple items in cache.
- **Parameters:**
  - `data_dict`: Dictionary of key-value pairs to cache
  - `prefix_keys`: Common key prefix
- **Thread-Safe:** Yes

##### `put_state(state, prefix_keys, autogen_key=None)` (classmethod)
Stores state dictionary with optional auto-generated key.
- **Parameters:**
  - `state`: State dictionary to store
  - `prefix_keys`: Key prefix
  - `autogen_key`: Optional key (auto-generated if None)
- **Returns:** The autogen_key used
- **Key Format:** `agk_<timestamp>_<id>` when auto-generated
- **Thread-Safe:** Yes

#### Internal Methods

##### `_assume_locked_get(keys, default_copy=True)` (classmethod)
Internal getter assuming lock is held.
- **Copies:** DataFrames, Series, dicts, and lists when `default_copy=True`

##### `_assume_locked_put(data, keys)` (classmethod)
Internal setter assuming lock is held.

##### `_combine_prefix_with_keys(prefix_keys, keys, prepare_prefix_keys=False)` (classmethod)
Combines prefix and keys into single list.

## Usage Examples

### File-Based Caching
```python
from cache_utils import cache_filename, load_cache, get_latest_cache_filename
import pandas as pd
import datetime as dt

# Generate cache filename for today
filename = cache_filename("sales_data")
# "data/sales_data_20240115.pkl.gz"

# Generate filename for specific date
filename = cache_filename("sales_data", dt.date(2024, 1, 10))
# "data/sales_data_20240110.pkl.gz"

# Save data to cache
data = pd.DataFrame({"sales": [100, 200, 300]})
data.to_pickle(filename)

# Load cache with callback scheduling
data, next_callback = load_cache(
    "sales_data",
    cb_time=dt.time(9, 0),  # 9:00 AM
    directory="data",
    allow_no_data=False
)

# Find latest cache file
latest = get_latest_cache_filename("sales_data", directory="data")
```

### In-Memory Caching
```python
from cache_utils import InMemoryCache

# Store single item
InMemoryCache.put({"user": "john"}, "users", "john_id")

# Retrieve single item
user_data = InMemoryCache.get("users", "john_id")

# Store multiple items
users = {
    "john": {"name": "John", "age": 30},
    "jane": {"name": "Jane", "age": 25}
}
InMemoryCache.put_many(users, "users")

# Retrieve multiple items
retrieved = InMemoryCache.get_many("users", ["john", "jane"])

# Store and retrieve state
state = {"counter": 0, "status": "running"}
state_key = InMemoryCache.put_state(state, "process", "state_1")
# or auto-generate key
auto_key = InMemoryCache.put_state(state, "process")

# Retrieve state (no copy for performance)
current_state = InMemoryCache.get_state("process", auto_key)
```

### Complex Key Example
```python
from cache_utils import InMemoryCache

# Multi-level key hierarchy
InMemoryCache.put(
    data={"price": 150.50},
    prefix_keys=["market_data", "stocks"],
    "AAPL", "2024-01-15"
)

# Retrieve with same hierarchy
price_data = InMemoryCache.get(
    ["market_data", "stocks"],
    "AAPL", "2024-01-15"
)
```

## Key Features

### Thread Safety
- All InMemoryCache operations are thread-safe
- Uses single class-level lock for all operations
- Safe for concurrent read/write from multiple threads

### Data Copying
- By default, returns copies of mutable objects (DataFrame, Series, dict, list)
- Prevents unintended mutations of cached data
- Can disable copying with `default_copy=False` for performance

### Date-Based File Caching
- Standardized filename format ensures chronological sorting
- Automatic fallback to most recent cache
- Intelligent callback scheduling for cache refresh

### Flexible Key Structure
- Supports hierarchical key structures
- Keys can be strings, lists, or tuples
- Automatic key normalization and combination

## Notes
- Cache files use `.pkl.gz` format (compressed pickle)
    - This allows for easy saving of multiple items in a single file.
- In-memory cache persists for process lifetime
- State management includes auto-generated unique keys
- OpsGenie integration for error alerting in production environments