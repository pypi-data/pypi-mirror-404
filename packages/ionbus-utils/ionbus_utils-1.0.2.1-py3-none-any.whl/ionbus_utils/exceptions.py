"""Utilities for working with exceptions"""

import getpass
import inspect
import socket
import traceback

from ionbus_utils.logging_utils import logger


def exception_to_string(excp: Exception) -> str:
    """Converts exception to a string"""
    return "".join(
        traceback.format_exception(type(excp), excp, excp.__traceback__)
    )


def log_exception(excp: Exception, level: int = 1) -> None:
    """Logs an exception"""
    # https://docs.python.org/3.8/library/inspect.html
    frame = inspect.stack()[level][0]
    func = frame.f_code
    computer = socket.getfqdn()
    try:
        as_user = f"as {getpass.getuser()}"
    except:  # noqa: E722
        as_user = ""
    info = (
        #     filename            function name   line number
        f"at {func.co_filename} ({func.co_name}: {frame.f_lineno}) "
        f"running {as_user} on {computer}:"
    )
    logger.error(f"Exception caught {info}\n{exception_to_string(excp)}")
