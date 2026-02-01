"""Utilities for converting integers to different bases"""

from __future__ import annotations

import uuid
import os
import sys

# The characters are arranged so they are in sorting order
_convert_numbers_list_64 = sorted(
    # digits 0 - 9
    [chr(ord("0") + x) for x in range(0, 9 + 1)]  # noqa: PIE808
    # letters A - Z
    + [chr(ord("A") + x) for x in range(26)]
    + ["^"]
    # letters a - z
    + [chr(ord("a") + x) for x in range(26)]
    + ["~"]
)
_convert_numbers_dict_64 = {
    x: idx for idx, x in enumerate(_convert_numbers_list_64)
}
_convert_numbers_list_62 = sorted(
    # digits 0 -9
    [chr(ord("0") + x) for x in range(0, 9 + 1)]  # noqa: PIE808
    # letters A - Z
    + [chr(ord("A") + x) for x in range(26)]
    # letters a - z
    + [chr(ord("a") + x) for x in range(26)]
)
_convert_numbers_dict_62 = {
    x: idx for idx, x in enumerate(_convert_numbers_list_62)
}


def is_windows() -> bool:
    """Returns true if windows else false (linux)"""
    return sys.platform.lower()[:3] == "win"


def is_wsl() -> bool:
    """Returns true if running in WSL (Windows Subsystem for Linux)"""
    return not is_windows() and bool(os.environ.get("WSL_DISTRO_NAME"))


def is_mac() -> bool:
    """Returns true if running on macOS"""
    return sys.platform == "darwin"


def int_to_base(number: int, base: int = 62) -> str:
    """Converts non-negative integer to string requested base.
    NOTE: bases bigger than 62 generate strings that are not URL safe."""
    if number < 0:
        raise RuntimeError("No negative numbers")
    if base > 64 or base < 2:  # noqa: PLR2004
        raise RuntimeError("base must be between 2 and 64 inclusive.")
    ret_str = ""
    convert_numbers_list = _convert_numbers_list_62
    if base > 62:  # noqa: PLR2004
        convert_numbers_list = _convert_numbers_list_64
    while True:
        number, digit = divmod(number, base)
        ret_str += convert_numbers_list[digit]
        if not number:
            break
    return ret_str[::-1]


def base_to_int(number_string: str, base: int = 62) -> int:
    """Converts string base representation back to integer"""
    if base > 64 or base < 2:  # noqa: PLR2004
        raise RuntimeError("base must be between 2 and 64 inclusive.")
    ret_int = 0
    convert_numbers_dict = _convert_numbers_dict_62
    if base > 62:  # noqa: PLR2004
        convert_numbers_dict = _convert_numbers_dict_64
    for char in number_string:
        ret_int *= base
        ret_int += convert_numbers_dict[char]
    return ret_int


def uuid_baseN(base: int = 62) -> str:
    """Returns a UUID encoded in the specified base (default is 62).
    This is (almost) guaranteed to be unique (1 in 2**122)."""
    return int_to_base(uuid.uuid4().int, base=base)  # type: ignore
