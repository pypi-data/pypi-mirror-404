"""General utilities"""

from __future__ import annotations

import base64
import datetime as dt
import gzip
import json
import os
import re
from collections import namedtuple
from collections.abc import KeysView
from contextlib import contextmanager
from copy import deepcopy
from enum import Enum
from pathlib import Path
from types import ModuleType
from typing import Any, Iterable, Sequence

from ionbus_utils.base_utils import (
    base_to_int,  # noqa: F401
    int_to_base,
    is_windows,
    uuid_baseN,
)
from ionbus_utils.file_utils import get_module_filepath
from ionbus_utils.group_utils import get_user_name
from ionbus_utils.logging_utils import logger

# pylint: disable=bare-except

# first group captures quoted strings (double or single)
# second group captures comments (//single-line or /* multi-line */)
comment_re = re.compile(
    r"(\".*?\"|\'.*?\')|(/\*.*?\*/|//[^\n]*$)", re.MULTILINE | re.DOTALL
)
trailing_comma_re = re.compile(r",(\s*[\}|\]])")
stupid_windows_re = re.compile(r"\r\n")
# https://stackoverflow.com/a/241506/821832
pattern_re = re.compile(
    r'//.*?$|/\*.*?\*/|\'(?:\\.|[^\\\'])*\'|"(?:\\.|[^\\"])*"',
    re.DOTALL | re.MULTILINE,
)
at_re = re.compile(r"@.+$")
comma_re = re.compile(r",")
gz_re = re.compile(r"\.gz", re.IGNORECASE)
factor_pair_list = [
    (re.compile(r"(.+?)k$", re.IGNORECASE), 1_000),
    (re.compile(r"(.+?)M{1,2}$", re.IGNORECASE), 1_000_000),
    (re.compile(r"(.+?)B$", re.IGNORECASE), 1_000_000_000),
]
DOMAIN = "gmail.com"
EOL = "\r\n" if is_windows() else "\n"


def load_json(filename: str | Path, verbose: bool = True) -> Any:
    """Reads json from filename, dealing with both comments and trailing
    commas"""
    with open(filename, encoding="UTF-8") as source:
        contents = source.read()
    try:
        return json.loads(remove_comments(contents))
    except:
        if verbose:
            logger.error(f"Cannot load JSON\n{remove_comments(contents)}")
        raise


def load_json_string(contents: str, verbose: bool = True) -> Any:
    """Reads json from string 'contents' dealing with both comments and
    trailing commas"""
    try:
        return json.loads(remove_comments(contents))
    except:
        if verbose:
            logger.error(f"Cannot load JSON\n{remove_comments(contents)}")
        raise


def remove_comments(string: str) -> str:
    """Removes comments and trailing commas from JSON string"""

    def replacer(match: re.Match) -> str:
        string = match.group(0)
        if string.startswith("/"):
            return " "  # note: a space and not an empty string
        return string

    string = stupid_windows_re.sub(r"\n", string)
    string = pattern_re.sub(replacer, string)
    return trailing_comma_re.sub(r"\1", pattern_re.sub(replacer, string))


def convert_string_to_float(number_as_str: str) -> float | None:
    """Converts a string into a float.
    * Commas are removed
    * k (1e3), MM (1e6), and B(1e9) suffixes are applied.

    Returns None if conversion not possible.
    """
    factor = 1
    # get rid of all commas
    number_as_str = comma_re.sub("", number_as_str)
    if not number_as_str:
        return None
    # loop over factor regexes and use factor when necessary
    for regex, this_factor in factor_pair_list:
        match = regex.search(number_as_str)
        if match:
            number_as_str = match.group(1)
            factor = this_factor
            break
    try:
        return float(number_as_str) * factor
    except:  # noqa: E722
        return None


def is_non_string_sequence(arg: Any) -> bool:
    """Returns true if it is a sequence (including dictionary keys) that is NOT
    a string"""
    # Note that sequence is too big and includes strings.
    if isinstance(arg, (str, bytes)):
        return False
    if isinstance(arg, KeysView):
        return True
    return isinstance(arg, Sequence)


def to_single_list(args: Sequence | Any) -> list:
    """Designed to convert * args into a single list.

    For args, it expects one of the following inputs:
    * A list/tuple of objects
    * A single non-list/tuple object
    * A list/tuple of length 1 that has a list/tuple

    These will all be converted to a list of objects
    """
    if args is None:
        return []
    if not is_non_string_sequence(args):
        return [args]
    if len(args) == 1 and is_non_string_sequence(args[0]):
        return list(args[0])  # type: ignore
    return list(args)


def cleanup_username(user: str | None) -> str:
    """Extracts user name from email"""
    if not user:
        return ""
    return at_re.sub("", user).lower()


def package_version_tuple(package: ModuleType) -> tuple:
    """Converts python package version into tuple of integers"""
    vers = package.__version__.split(".")
    # pylint: disable-next=consider-using-generator
    return tuple(int(i) for i in vers)


def list_to_comma_string(
    iter_list: list[str],
    quote_char: str = "",
) -> str:
    """Converts list to string.  Uses quote character if provided"""
    comma = f"{quote_char}, {quote_char}" if quote_char else ", "
    return quote_char + comma.join(iter_list) + quote_char


def multiline_comma_join(
    iter_list: list[str], spaces: int, use_quotes: bool = False
) -> str:
    """Does a multiline comma join"""
    if use_quotes:
        spacer = f'",\n{" " * spaces}"'
        return f'"{spacer.join(iter_list)}"'
    return f",\n{' ' * spaces}".join(iter_list)


def comma_join_list(items: list[Any]) -> str:
    """Returns a string representing the list using English syntax.
    Examples:
    [] -> ""
    [1] -> "1"
    [1, 2] -> "1 and 2"
    [1, 2, 3] -> "1, 2, and 3"
    [1, 2, 3, 4] -> "1, 2, 3, and 4"
    """
    if not items:
        return ""
    items = [str(x) for x in items]
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"
    return f"{', '.join(items[:-1])}, and {items[-1]}"


# pylint: disable-next=too-many-branches
def filter_string_rep_of_list(  # noqa: C901
    the_list: Iterable,
    *args: list | str | re.Pattern,
    ignore_case: bool = True,
    full_match: bool = False,
    inverted: bool = False,
    unmatched_at_end: bool = False,
    remove_dups: bool = True,
) -> list[str]:
    """Regex filtering of string representation of list.

    Parameters:
    * the_list         - input list to be filtered
    * *args            - string or regex to filter (or list of these)
        * If string, will be converted into regex paying attention to:
          * ignore_case
          * full_match (add ^ and $ to string before regex compilation)
    * inverted         - take everything EXCEPT what matches
    * remove_dups      - will remove duplicate entries in return values (either
                         because of duplicates passed in or because of multiple
                         regex matching a single entry)
    * unmatched_at_end - will put all unmatched values at end of returning
                         list

    Returns:  list of strings
    """

    def is_already_seen(element: str, the_set: set[str]) -> bool:
        """Returns whether or not an element has been seen adding
        it to the list if it has not been."""
        seen = element in the_set
        the_set.add(element)
        return seen

    # Convert args to list of regexes
    ignore = re.IGNORECASE if ignore_case else 0
    clean_args = to_single_list(args)
    regexes = []
    for arg in clean_args:
        if isinstance(arg, re.Pattern):
            regexes.append(arg)
            continue
        if full_match:
            arg = f"^{arg}$"  # noqa: PLW2901
        regexes.append(re.compile(arg, ignore))  # type: ignore
    ret_list = []
    for reg in regexes:
        for col in the_list:
            # column names can be integers, etc, so make sure it's looking
            # at a string.
            if reg.search(str(col)):
                ret_list.append(col)
                continue
    if remove_dups:
        the_set = set()
        ret_list = [x for x in ret_list if not is_already_seen(x, the_set)]
    if inverted:
        ret_list = [x for x in the_list if x not in ret_list]
    elif unmatched_at_end:
        ret_list.extend([x for x in the_list if x not in ret_list])
    return ret_list


def filter_string_rep_of_dict(
    the_dict: dict,
    *args,
    ignore_case: bool = True,
    full_match: bool = False,
    inverted: bool = False,
) -> dict:
    """Regex filtering of dictionary using string representation of keys.
    See filter_string_rep_of_list for full explanation.  Returns
    filtered and sorted dictionary.

    input:  dictionary and filters
    output: dictionary"""
    good_keys = filter_string_rep_of_list(
        the_dict.keys(),
        *args,
        remove_dups=True,
        ignore_case=ignore_case,
        full_match=full_match,
        inverted=inverted,
    )
    return {x: the_dict[x] for x in good_keys}


def dict_to_namedtuple(the_dict: dict, name: str = "GenericDict") -> namedtuple:  # type: ignore
    """Converts dictionary into named tuple.

    Warning: If values of dictionary are not hashable, the returned named
    tuple will not be hashalb and therefore will not work as a dictionary key.
    """
    # https://stackoverflow.com/a/69408076/821832
    return namedtuple(name, the_dict.keys())(**the_dict)


def recursively_uppercase_dict_keys(the_dict: dict) -> dict:
    """Input is nested dictionary with possible dictionary and other values.
    Any dictionary values will have their string recursively uppercased.
    Any dictionaries in lists will NOT be recursively uppercased."""
    ret_dict = {}
    for key, value in the_dict.items():
        if isinstance(key, str):
            # If this is a string key, make it upper case
            key = key.upper()  # noqa: PLW2901
        # Now add values to retDict
        if isinstance(value, dict):
            ret_dict[key] = recursively_uppercase_dict_keys(value)
        else:
            ret_dict[key] = deepcopy(value)
    return ret_dict


def get_user_email() -> str:
    """Returns current user email address.  Returns empty string if no user is
    found"""
    return f"{user}@{DOMAIN}".lower() if (user := get_user_name()) else ""


@contextmanager
def open_using(  # noqa: ANN201
    filename: str, *args, encoding: str = "ascii", **kwargs
):
    """Function that returns either open or gzip open based on filename ending.
    To be used inside 'with' statement; close will be called automatically.
    'encoding' will only be applied to open, not gzip open.

    IMPORTANT: If gzip is used, you will get bytes and not string. User will
    need to check.
    """
    if gz_re.search(filename):
        resource = gzip.open(filename, *args, **kwargs)  # noqa: SIM115
    else:
        resource = open(  # noqa: SIM115
            filename, *args, **kwargs, encoding=encoding
        )
    try:
        yield resource
    finally:
        resource.close()


def as_string(string_or_bytes: str | bytes) -> str:
    """If string_or_bytes is bytes, will convert to string."""
    if isinstance(string_or_bytes, bytes):
        string_or_bytes = string_or_bytes.decode("ascii").strip()
    return string_or_bytes  # type: ignore


@contextmanager
def temporarily_change_dir(destination):
    """Context manager to temporarily change directory.

    Note: There is no concern about changing directories using os.chdir()
    inside this block.  It will still work as expected and get back to the
    original directory."""
    try:
        cwd = os.getcwd()
        os.chdir(destination)
        yield
    finally:
        os.chdir(cwd)


def compress_and_encode_as_base64(
    input_string: str,
    gzip_encode="utf-8",
) -> str:
    """
    Compresses a string using gzip and encodes it with base64.
    Returns The base64-encoded compressed string.
    """
    # Compress the string using gzip
    compressed_data = gzip.compress(input_string.encode(gzip_encode))

    # Encode the compressed data with base64
    return base64.b64encode(compressed_data).decode("utf-8")


def decompress_and_decode_from_base64(
    encoded_string: str,
    gzip_encode="utf-8",
) -> str:
    """
    Decompresses a base64-encoded string that was compressed with gzip.

    Returns The decompressed string.
    """
    # Decode the base64-encoded string
    compressed_data = base64.b64decode(encoded_string)

    # Decompress the data using gzip
    return gzip.decompress(compressed_data).decode(gzip_encode)


def string_to_enum_value(
    enum_class: Enum, key: str, throw_if_not_found: bool = False
) -> Any:
    """Given enum class and a string, will return value for enum where label
    matches string.
    Returns None if not found unless throw_if_not_found is True (in which case
    it throws).
    String matching is case insensitive"""
    key = key.upper()
    # First try enum names
    for enum_obj in enum_class:  # type: ignore
        if enum_obj.name.upper() == key:
            return enum_class(enum_obj.value)  # type: ignore
    # now try enum values
    # NOTE: Values do NOT have to be unique.  This function will
    # match the first value it finds regardless if it is the only value
    for enum_obj in enum_class:  # type: ignore
        if str(enum_obj.value).upper() == key:
            return enum_class(enum_obj.value)  # type: ignore

    # if we're still here
    if throw_if_not_found:
        raise RuntimeError(f"{key} not found in enum")
    return None


def timestamped_unique_id(prefix: str | None = "", base: int = 62) -> str:
    """Returns timestamped unique ID based on unique uuid"""
    if prefix:
        prefix = f"{prefix}_"
    else:
        prefix = ""
    microseconds = int(dt.datetime.now().timestamp() * 1e6 + 0.5)
    return (
        f"{prefix}{int_to_base(microseconds, base=base)}_"
        f"{uuid_baseN(base=base)}"
    )


def timestamped_id(
    prefix: str | None = "",
    base: int = 62,
    use_seconds: bool = False,
) -> str:
    """Returns timestamped ID.  This ID is NOT guaranteed to be unique.
    Uses microseconds since epoch by default, will use seconds since epoch when
    `use_seconds` is provided."""
    if prefix:
        prefix = f"{prefix}_"
    else:
        prefix = ""
    number = (
        int(dt.datetime.now().timestamp() + 0.5)
        if use_seconds
        else int(dt.datetime.now().timestamp() * 1e6 + 0.5)
    )
    return f"{prefix}{int_to_base(number, base=base)}"


def setup_requests_ca_bundle(ca_cert: str | None = None) -> None:
    """Sets up environment variable REQUESTS_CA_BUNDLE"""
    if not ca_cert:
        # But first see if we have a file
        if not (
            bundle := os.environ.get("REQUESTS_CA_BUNDLE")
        ) or not os.path.exists(bundle):
            os.environ["REQUESTS_CA_BUNDLE"] = get_https_cert_filename()
    elif ca_cert != "certifi":
        # Use a different certificate store path, unless the user specified
        # 'certifi'. In the latter case, don't set any value, and allow the
        # upstream default, which is to use the cert store provided by the
        # certifi library.
        os.environ["REQUESTS_CA_BUNDLE"] = ca_cert


def get_https_cert_filename() -> str:
    """Returns appropriate HTTPS certificate filename"""
    for filename in [
        "/etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem",
        r"C:\ProgramData\pip\tls-ca-bundle.pem",
        str(get_module_filepath().parent / "resources" / "tls-ca-bundle.pem"),
    ]:
        if os.path.exists(filename):
            logger.info(f"Using certificate file {filename}")
            return filename
    raise RuntimeError("No certificate PEM file found")
