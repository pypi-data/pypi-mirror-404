# Logging Documentation

<!-- TOC start (generated with https://bitdowntoc.derlin.ch/) -->

- [Introduction](#introduction)
- [Basic Usage](#basic-usage)
- [More Advanced Topics](#more-advanced-topics)
    * [Helper Functions](#helper-functions)
    * [Logging directly to a file](#logging-directly-to-a-file)
    * [Changing information that is logged](#changing-information-that-is-logged)
    * [Loguru Integration](#loguru-integration)
    * [Logging Levels](#logging-levels)
    * [`warn_once` Function](#warn_once-function)
    * [`log_if` Functions (Advanced approach)](#log_if-functions-advanced-approach)
        + [`log_if` Code](#log_if-code)
    * [Logging Exceptions](#logging-exceptions)
<!-- TOC end -->

## Introduction

The ionbus_utils [logging_utils.py](logging_utils.py) module contains easy ways to set up a Python logger.  

A Python logger is an method to write messages to the console with improved control and other features. In almost all cases, it is considered best practices to use a logger instead of simple `print` statements when running production code.

- **Logging Levels** allow for control over the severity of messages that should be printed to the console. More information about Logging Levels is available in the section on [Logging Levels](#logging-levels) below.
- **Timestamps** are automatically provided in every message logged, which allows for easier traversal of log files.
- **Function Traces** are provided in each message as `function-name:line-number`. This makes it much easier to tell why a message was logged and improves debugging efficiency.

The following is an example of a logger message:

```
2024-07-17 16:27:13.877 ERROR    [log_if_tests_manual :test_log_if          (  38)] Some statement here
```

## Basic Usage

To use the logger, import it and use it.

```python
from ionbus_utils.logging_utils import logger

def some_func():
    logger.info("starting")
    if problem:
        logger.warning("uh oh")
```

## More Advanced Topics

### Helper Functions

It is important to note that the additional functions below will only work if you use the logger from logging utils. If you setup a logger yourself, these functions will not work with your logger. (To be clear: It is very much preferable to setup your own logger as opposed to using print statements.)

### Logging directly to a file

You can tell the logger to not only write to the screen (STDOUT), but also write to a file.  This can be useful when running in multiprocesssing or threading where you do not want the log statements from different threads to get confused.

```python
from ionbus_utils.logging_utils import add_log_file, logger

add_log_file("prefix_of_log_file")
logger.info("Hello!")
```

This tells it to pick the prefix log file `prefix_of_log_file`.

### Changing information that is logged

In general the logging information as setup works well enough for most use cases.  

To do this, call `setup_logger_format()` and pass in `update_format=True` and either:

- `thread_info=True` (prints out thread ID for different threads)
-  `multiprocessing_info=True` (prints out process ID for different process), 
or 
- `extra_info=some_string` to pass in whatever standard logger format you want added.

For example [`test_logging.py`](tests/test_logging.py) runs this in `test_single_threaded_logging()`:

```python
from ionbus_utils.logging_utils import (
    logger,
    setup_logger_format,
)

    setup_logger_format(update_format=True, extra_info="%(name)s")

```

which has the log looking like:

```bash
2025-10-13 15:44:11.126 INFO     [test_logging        :<module>             ( 141)] Running single-process test...
2025-10-13 15:44:12.994 INFO    DEFAULT_LOGGER [test_logging        :func                 (  20)] info message
2025-10-13 15:44:13.269 WARNING DEFAULT_LOGGER [test_logging        :func                 (  21)] warn once message
2025-10-13 15:44:13.269 INFO    DEFAULT_LOGGER [test_logging        :func                 (  20)] info message
2025-10-13 15:44:13.269 INFO    DEFAULT_LOGGER [test_logging        :func                 (  20)] info message
```

In [`test_logging.py`](tests/test_logging.py) runs this in `workder_process()`  you can find 

```python
    setup_logger_format(multiprocessing_info=True, update_format=True)
```

which has output like:

```bash
2025-10-13 15:44:15.587 INFO      29848 SpawnPoolWorker-2    [test_logging        :worker_process       (  82)] Process 1 started (PID: 29848)
2025-10-13 15:44:15.589 INFO      29848 SpawnPoolWorker-2    [test_logging        :worker_process       (  84)] Process 1 - Message 1
2025-10-13 15:44:15.591 INFO      29848 SpawnPoolWorker-2    [test_logging        :worker_process       (  85)] Process 1 completed
2025-10-13 15:44:15.604 INFO      12116 SpawnPoolWorker-1    [test_logging        :worker_process       (  82)] Process 0 started (PID: 12116)
2025-10-13 15:44:15.610 INFO      12116 SpawnPoolWorker-1    [test_logging        :worker_process       (  84)] Process 0 - Message 1
```


### Loguru Integration

By default, the `logging_utils` sets up everything using the standard python logger.  If it is running in an environment where the optional `loguru` package is installed, it will use that logger by default.

```
2024-07-17 16:27:13.882 | WARNING  | __main__:test_log_if:48 - Some message here
```

Console messages using loguru are also colored to make it easier to distinguish between messages at different severity levels.  Installing `loguru` is not necessary, but considered a nice option by many.

### Logging Levels

Logging levels allow a developer to provide a "severity" level to their messages, which can be filtered out at runtime. Logging levels follow a hierarchical structure, and setting a specific level ignores any levels that are "less severe". As an example, using

```python
from ionbus_utils.logging_utils import logger, set_log_level
set_log_level("WARNING")
logger.info("Info Message") # not displayed
logger.warning("Warning Message") # displayed
logger.error("Error Message) # displayed
```

will only print the latter two messages, as `INFO` messages are considered "less severe" than `WARNING` level messages. 

The logging level hierarchy is as follows:

```
DEBUG < INFO < WARNING < ERROR < CRITICAL
```

**Note**: `set_log_level()` takes either strings (e.g., `"WARNING"`) or default logger integer values.  Either works regardless of whether one is using default python logger or `loguru`.

### `warn_once` Function

`warn_once()` allows you to put in deprecation and other warnings that you want to show up, but only once.  You can pass in `log_level` as with [`log_if()` below](#log_if-functions-advanced-approach)

```python
from logging_utils import warn_once

def some_function_to_be_deprecated() -> None:
    """deprecated function"""
    warn_once(
        "Do not use this function anymore.  Use `new_function() instead."
    )
```

###  `log_if` Functions (Advanced approach)

It is often the case that being able to specify loging level is not enough granular control to turn on and off different logging messages.  To provide more granular functionality,`logging_utils.py` provides a number of functions for logging which allow greater control over which logs to output.

* `log_if()` function allows logging to any level, and logs to the `INFO` level by default. 
* `log_LEVEL-if()` functions allow logging to a specified level without using the `logger` object. Supported `LEVEL` values include: `debug`, `info`, `warning`, `error`, `critical`.

The basic idea is to provide to these functions a message and information to make the boolean decision of whether or not to print the log message.

Making the boolean decision can happen several different ways:

* Passing in a True/False boolean value

    ```python
    verbose = True
    log_if("some message", verbose)
    ```

* Doing bit arithmetic between an integer and one or more bits.
    * One can specify doing all of the bit arithmetic

    ```python
    verbose_int = 0x5
    # compares 0x5 to 0x2 and does not prints since zero overlap
    log_if("some_message", verbose_int & 0x2)
    ```

* One can specify passing in the pieces separately

    ```python
    verbose_int = 0x5
    # compares 0x5 to 0x3 and prints since non-zero overlap
    log_if("some_message", verbose_int, 0x1 | 0x2) 
    ```

#### `log_if` Code
The following is an example of using the log_if functionality, which allows for greater control with custom log flags. Log flag checking uses bit comparison to check if a message should be logged:

```python
from enum import IntEnum
from ionbus_utils.logging_utils import log_if, log_warning_if

class Flags(intEnum):
    """This class holds bit flags to be used with verbose int
    to determine what log statements are printed."""
    ALPHA = 0x1
    BETA = 0x2
    GAMMA = 0x4
    WARNING = 0x8
    NEXT_ITEM = 0x10
    LAST_ITEM = 0x20
    # ...

def main(verbose_int: int) -> None:
    """Main routine"""
    alpha = task_alpha()
    beta = task_beta(alpha)
    gamma = task_gamma(alpha, beta)

    # When verbose_int = 5:
    # this is printed
    log_if("{alpha=}", verbose_int, Flags.ALPHA)
    # this is not
    log_if("{beta=}", verbose_int, Flags.BETA)
    # this is printed
    log_if("{gamma=}", verbose_int, Flags.GAMMA)
    # This is printed
    log_if("{beta - alpha=}", verbose_int, Flags.ALPHA | Flags.BETA)

    if gamma > alpha:    
        # Even if gamma > alpha, this is NOT printed when verbose_int = 5
        log_warning_if(f"{gamma=}> {alpha=}", verbose_int, Flags.WARNING)

if __name__ == "__main__":
    # enable logging for flags in bit position 2 and 4
    verbose_int = 0x5 # = 0x1 | 0x4
```

**Note:** In general, we recommendusing `log_if()`.  But when using this functionality and a lot of different logging levels, using `log_warning_if()`, `log_info_if()` make a lot of sense.

### Logging Exceptions

When catching exceptions, it is often a good idea to log the exception before continuing.

```python
from ionbus_utils.exceptions import log_exception
from ionbus_utils.logging_utils import logger

if __name__ == "__main__":
    try:
        main(args_obj)
    except Exception as excp:
        log_exception(excp)
        raise excp
```
