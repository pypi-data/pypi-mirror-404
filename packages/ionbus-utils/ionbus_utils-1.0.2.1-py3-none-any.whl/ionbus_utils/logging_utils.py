"""Provide easy logging."""

from __future__ import annotations

import inspect
import logging
import os
import sys
from threading import Lock


# cSpell: ignore msecs
setup_already_called = False
DEFAULT_LOGGER_NAME = "DEFAULT_LOGGER"
LOG_ONCE_LOCK = Lock()
_log_once_locations = set()

# Add custom NOTICE level between INFO (20) and WARNING (30)
NOTICE_LEVEL = 25


def _notice(self, message, *args, **kwargs):
    """Log a message with severity 'NOTICE'."""
    if self.isEnabledFor(NOTICE_LEVEL):
        self._log(NOTICE_LEVEL, message, args, **kwargs)


def _ensure_notice_level() -> None:
    """Ensure NOTICE level and Logger.notice are registered."""
    if logging.getLevelName(NOTICE_LEVEL) != "NOTICE":
        logging.addLevelName(NOTICE_LEVEL, "NOTICE")
    if not hasattr(logging.Logger, "notice"):
        setattr(logging.Logger, "notice", _notice)


_ensure_notice_level()


class BadLogConfigError(RuntimeError):
    """An error that is thrown when a functionality of the logger is used that
    doesn't exist."""


def setup_logger_format(
    logger_name: str = DEFAULT_LOGGER_NAME,
    level: int = logging.INFO,
    module_width: int = 25,
    func_width: int = 30,
    thread_width: int = 6,
    thread_info: bool = False,
    update_format: bool = False,
    multiprocessing_info: bool = False,
    extra_info: str | None = None,
) -> logging.Logger:
    """Sets format for the default logger"""
    # https://stackoverflow.com/a/11927374/821832
    global setup_already_called  # noqa: PLW0603
    _ensure_notice_level()
    logger_instance = logging.getLogger(logger_name)
    # If we are updating format and the logger already existed,
    # we need to update the logger itself.
    if update_format or not setup_already_called:
        setup_already_called = True
        format_str = ""
        base_str = "%(asctime)s.%(msecs)03d %(levelname)-8s"
        tail_str = (
            f" [%(module)-{module_width}s:%(funcName)-{func_width}s "
            f"(%(lineno)4d)] %(message)s"
        )
        if thread_info:
            base_str += f" %(thread){thread_width}d"
        elif multiprocessing_info:
            # Add process and process name
            base_str += f" %(process){thread_width}d %(processName)-20s"
        elif extra_info:
            base_str += extra_info
        format_str = base_str + tail_str
        formatter = logging.Formatter(format_str, datefmt="%Y-%m-%d %H:%M:%S")
        if not logger_instance.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(formatter)
            logger_instance.addHandler(handler)
        else:
            for handler in logger_instance.handlers:
                handler.setFormatter(formatter)
        logger_instance.setLevel(level)
    return logger_instance


def get_logger(logger_name: str = DEFAULT_LOGGER_NAME) -> logging.Logger:
    """Get logger"""
    if not setup_already_called:
        return setup_logger_format(logger_name, update_format=True)
    return logging.getLogger(logger_name)


def set_log_level(log_level: int | str) -> None:
    """Sets the current log level. Supply log_level as either a string or an
    int - the proper value will be used based on the active logger type."""
    if isinstance(logger, logging.Logger):
        log_level = _get_log_level_int(log_level)
        logger.setLevel(log_level)
    else:
        log_level = _get_log_level_str(log_level)
        logger.remove()
        logger.add(sys.stderr, level=log_level)


def add_log_file(
    log_prefix: str, *, level: int | str | None = None, log_dir: str = "."
) -> str:
    """Attach a file handler/sink to the module logger using its current format.
    returns the path of the log file."""
    # import here to avoid circular dependencies
    from ionbus_utils.file_utils import get_logfile_name

    log_path = get_logfile_name(prefix=log_prefix, log_dir=log_dir)
    if not log_path:
        raise BadLogConfigError("Unable to determine logfile path.")
    log_path = os.path.abspath(log_path)

    formatter = None
    for existing_handler in logger.handlers:
        formatter = getattr(existing_handler, "formatter", None)
        if formatter is not None:
            break
    if formatter is None:
        raise BadLogConfigError(
            f"No formatter configured for logger '{logger.name}'."
        )

    converted_level = _get_log_level_int(level) if level is not None else None

    for existing_handler in logger.handlers:
        handler_path = getattr(existing_handler, "baseFilename", None)
        if handler_path and os.path.abspath(handler_path) == log_path:
            if converted_level is not None:
                existing_handler.setLevel(converted_level)
            return log_path

    file_handler = logging.FileHandler(log_path, mode="w", encoding="utf-8")
    file_handler.setFormatter(formatter)
    if converted_level is not None:
        file_handler.setLevel(converted_level)
    logger.addHandler(file_handler)
    return log_path


def warn_once(
    log_str: str,
    stack_level: int = 1,
    log_level: int | str = "WARNING",
) -> None:
    """Logs a warning message once per location in code."""
    # Get the caller's frame info
    frame = inspect.currentframe()
    if frame is None or frame.f_back is None:
        return
    caller_frame = frame.f_back
    caller_info = inspect.getframeinfo(caller_frame)

    # Create a unique identifier for this call location Using filename,
    # line number, and function name to identify unique locations
    location_key = (
        caller_info.filename,
        caller_info.lineno,
        caller_info.function,
        log_str,  # Include message to allow different warnings from same line
    )
    with LOG_ONCE_LOCK:
        if location_key in _log_once_locations:
            # we've already logged this warning
            return
        _log_once_locations.add(location_key)
    if isinstance(logger, logging.Logger):
        log_level = _get_log_level_int(log_level)
        logger.log(log_level, log_str, stacklevel=(stack_level + 1))
    else:
        log_level = _get_log_level_str(log_level)
        try:
            logger.opt(depth=stack_level).log(log_level, log_str, False)  # type: ignore
        except AttributeError as excp:
            raise BadLogConfigError(
                f"Logger of type {logger.__class__} "
                "is not compatible with logging_utils."
            ) from excp


def log_if(
    log_str: str,
    verbosity: int | bool,
    flags: int | None = None,
    stack_level: int = 1,
    log_level: int | str = "INFO",
) -> None:
    """Logs a message, if verbosity contains at least one flag bit set by
    "flags" (verbosity & flags > 0). Supply a boolean instead for verbosity to
    override and always log."""
    do_log = False
    if isinstance(verbosity, bool):  # boolean True/False
        do_log = verbosity
    elif isinstance(verbosity, int):  # config flag with specific bits set
        do_log = bool(verbosity) if flags is None else (verbosity & flags)
    if do_log:
        log_level = _get_log_level_int(log_level)
        logger.log(log_level, log_str, stacklevel=(stack_level + 1))


def log_info_if(
    log_str,
    config_or_bool,
    flags=None,
    level=1,  # noqa: ANN001
) -> None:
    """log_ifs at the INFO level."""
    log_if(
        log_str,
        config_or_bool,
        flags=flags,
        stack_level=(level + 1),
        log_level="INFO",
    )


def log_notice_if(
    log_str,
    config_or_bool,
    flags=None,
    level=1,  # noqa: ANN001
) -> None:
    """log_ifs at the NOTICE level."""
    log_if(
        log_str,
        config_or_bool,
        flags=flags,
        stack_level=(level + 1),
        log_level="NOTICE",
    )


def log_warning_if(
    log_str,
    config_or_bool,
    flags=None,
    level=1,  # noqa: ANN001
) -> None:
    """log_ifs at the WARNING level."""
    log_if(
        log_str,
        config_or_bool,
        flags=flags,
        stack_level=(level + 1),
        log_level="WARNING",
    )


def log_error_if(
    log_str,
    config_or_bool,
    flags=None,
    level=1,  # noqa: ANN001
) -> None:
    """log_ifs at the ERROR level."""
    log_if(
        log_str,
        config_or_bool,
        flags=flags,
        stack_level=(level + 1),
        log_level="ERROR",
    )


def log_debug_if(
    log_str,
    config_or_bool,
    flags=None,
    level=1,  # noqa: ANN001
) -> None:
    """log_ifs at the DEBUG level."""
    log_if(
        log_str,
        config_or_bool,
        flags=flags,
        stack_level=(level + 1),
        log_level="DEBUG",
    )


def log_critical_if(
    log_str,
    config_or_bool,
    flags=None,
    level=1,  # noqa: ANN001
) -> None:
    """log_ifs at the CRITICAL level."""
    log_if(
        log_str,
        config_or_bool,
        flags=flags,
        stack_level=(level + 1),
        log_level="CRITICAL",
    )


def _get_log_level_int(log_level: str | int) -> int:
    if isinstance(log_level, str):
        level = logging._nameToLevel.get(log_level.upper())
        if level is None:
            raise BadLogConfigError(f"Logging level not defined: {log_level}")
        return level
    return log_level


def _get_log_level_str(log_level: str | int) -> str:
    if isinstance(log_level, int):
        level = logging._levelToName.get(log_level)
        if level is None:
            raise BadLogConfigError(f"Logging level not defined: {log_level}")
        return level
    return log_level.upper()


logger = get_logger()

if __name__ == "__main__":
    logger.info("hello")
