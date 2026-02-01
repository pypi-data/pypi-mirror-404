# file_utils.py Documentation

## Overview
File utilities module providing helper functions for file operations, including file manipulation, hashing, gzipping, and logging file management.

## Functions

### `touch_file(path, file_perms=None)`
Updates the modification time of a file, creating it if necessary.
- **Parameters:**
  - `path`: File path (str, os.PathLike, or None)
  - `file_perms`: Optional file permissions to set (int)
- **Returns:** None
- **Note:** If path is None, function performs no operation

### `file_modify_time(path, with_tz=False)`
Returns the last modification datetime of a file.
- **Parameters:**
  - `path`: File path (str or os.PathLike)
  - `with_tz`: If True, returns datetime with NYC timezone
- **Returns:** datetime object or None if file doesn't exist

### `get_module_filepath(filename=None, level=2)`
Returns the absolute pathname of a file.
- **Parameters:**
  - `filename`: File path (optional)
  - `level`: Stack frame level for inspection (default: 2)
- **Returns:** Path object with absolute path
- **Note:** If filename is None, uses the calling function's file

### `get_module_name(filename=None)`
Returns the module name (parent directory name) of a file.
- **Parameters:**
  - `filename`: File path (optional)
- **Returns:** str - Module name
- **Note:** If filename is None, uses the calling function's file

### `move_single_file(orig_name, new_name)`
Moves a single file, removing destination if it exists.
- **Parameters:**
  - `orig_name`: Source file path
  - `new_name`: Destination file path
- **Returns:** None

### `gzip_file(filename, unlink_orig=True, verbose=False)`
Compresses a file using gzip.
- **Parameters:**
  - `filename`: File to compress
  - `unlink_orig`: If True, removes original file after compression (default: True)
  - `verbose`: If True, logs compression statistics
- **Returns:** None
- **Note:** Preserves original file's modification time on compressed file

### `get_file_hash(filename, use_md5=False, chunk_size=65536, as_base62=False)`
Calculates and returns a file's hash.
- **Parameters:**
  - `filename`: File to hash
  - `use_md5`: If True, uses MD5; otherwise uses blake2b (default: False)
  - `chunk_size`: Size of chunks to read (default: 65536)
  - `as_base62`: If True, returns hash as base62 string (default: False)
- **Returns:** str - Hexadecimal hash or base62 string

### `get_logfile_name(prefix="process", log_dir=".", gzip_old_logfiles=True, old_age_days=1, add_uuid=False, ignore_env=False)`
Generates a log file name with date-based directory structure.
- **Parameters:**
  - `prefix`: Prefix for log filename (default: "process")
  - `log_dir`: Root directory for logs (default: ".")
  - `gzip_old_logfiles`: If True, compresses old log files (default: True)
  - `old_age_days`: Age threshold for compressing logs (default: 1)
  - `add_uuid`: If True, adds UUID suffix to filename (default: False)
  - If the environment variable `IBU_LOG_DIR` is set, then all logs will be sent to this directory **unless** `ignore_env=True` is passed in.
- **Returns:** str - Full path to log file (format: `{log_dir}/YYYY/MM/{prefix}_YYYYMMDD_HHMMSS[_uuid].log`)
- **Note:** Automatically creates directory structure and compresses logs older than threshold

## Dependencies
- `ionbus_utils.base_utils`: For `int_to_base`, `is_windows`, and `uuid_baseN` functions
- `ionbus_utils.logging_utils`: For logger
- `ionbus_utils.time_utils`: For NYC timezone support

## Usage Examples

```python
from file_utils import touch_file, file_exists_robust, get_file_hash

# Update file modification time
touch_file("/path/to/file.txt", file_perms=0o644)

# Check if file exists robustly
if file_exists_robust("/network/path/file.txt"):
    print("File exists")

# Get file hash
hash_value = get_file_hash("/path/to/file.bin")
hash_base62 = get_file_hash("/path/to/file.bin", as_base62=True)

# Generate log filename with automatic old log compression
log_path = get_logfile_name(prefix="myapp", log_dir="/var/log/myapp")
```