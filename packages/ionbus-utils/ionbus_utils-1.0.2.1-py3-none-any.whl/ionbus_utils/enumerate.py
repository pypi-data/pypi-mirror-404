"""C++ style enum with more functionality than Python 3's enum.  Also
includes 3.11's StrEnum class"""

from __future__ import annotations

# cSpell: ignore integerized
import re
import sys
from typing import Any

if sys.version_info >= (3, 11):
    from enum import StrEnum  # noqa: F401
else:
    from backports.strenum import StrEnum  # noqa: F401

equal_re = re.compile(r"(\w+)=(.+)")


class Enumerate:
    """Similar to C++'s 'enum', but with a few extra toys.  Takes a
    string with spaces in between the different 'enum' names (keys).

    If names_or_dict is a dictionary, the dictionary is used to set the
    key/value pairs.

    * as_int=True   -> values will be integers (useful for array indices
    * as_bit=True   -> values will be ints with incremental bits set
    * key_value     -> expects string of format key1=val1 key2=val2
        * if as_int is True, values will be converted to integerized
    # name_as_value -> value is same as key (with prefix if any prepended)"""

    # pylint: disable=R0912
    def __init__(  # noqa: C901, PLR0913, PLR0917, PLR0912
        self,
        names_or_dict: str | dict | list,
        prefix: str = "",
        as_int: bool = False,
        int_offset: int = 0,
        key_value: bool = False,
        as_bit: bool = False,
        name_only: bool = False,
        name_as_value: bool = False,
    ):
        self._keys = []
        self._value_dict = {}
        # If we have a dictionary, then just loop over it setting everything
        # up and be done with it.
        if isinstance(names_or_dict, dict):
            self._as_bit = False
            for key, value in names_or_dict.items():
                object.__setattr__(self, key, value)
                self._value_dict[value] = key
                self._keys.append(key)
            return
        self._as_bit = as_bit
        if isinstance(names_or_dict, str):
            # turn string into list
            names_or_dict = names_or_dict.strip().split()
        for count, name in enumerate(names_or_dict):
            key = f"{prefix}_{name}"
            if name_only:
                key = f"{prefix}{name}"
            if key_value:
                match = equal_re.match(name)
                if match:
                    name = match.group(1)  # noqa: PLW2901
                    key = match.group(2)
                    if as_int:
                        key = int(key)
                else:
                    key = name
            if name_as_value:
                key = f"{prefix}{name}"
            if self.is_valid_key(name):
                raise RuntimeError(f"You cannot duplicate Enum Names '{name}'")
            if as_bit:
                key = 1 << count + int_offset
            if as_int and not key_value:
                key = count + int_offset
            object.__setattr__(self, name, key)
            self._value_dict[key] = name
            self._keys.append(name)
        self.__slots__ = tuple(self._keys)

    def __str__(self) -> str:
        retval = ""
        for value, key in sorted(self._value_dict.items()):
            if retval:
                retval += ", "
            if self._as_bit:
                value = f"0x{value:x}"  # noqa: PLW2901
            retval += f"{key}:{value}"
        return retval

    def is_valid_value(self, value: Any) -> bool:
        """Returns true if this value is a valid enum value"""
        return value in self._value_dict

    def is_valid_key(self, key: str) -> bool:
        """Returns true if this value is a valid enum key"""
        return key in self.__dict__

    def value_to_key(self, value: Any) -> str | None:
        """Returns the key (if it exists) for a given enum value"""
        return self._value_dict.get(value, None)

    def keys(self) -> list:
        """Returns copy of valid keys"""
        return self._keys[:]

    def values(self) -> list:
        """returns copy of values"""
        return list(self._value_dict.keys())

    def __setattr__(self, name: str, value: Any):
        """Lets me set internal values, but throws an error if any of
        the enum values are changed"""
        if not name.startswith("_"):
            raise RuntimeError("You cannot modify Enum values.")
        object.__setattr__(self, name, value)

    def __getattr__(self, name: str):
        """This only gets called for undefined attributes.
        So this function won't usually get used, but it stops pylint from a lot
        of complaining, so...."""
        if name not in self.__dict__:
            raise RuntimeError(f'"{name} not found in this class.')
        return self.__dict__[name]

    def __call__(self, key: str) -> Any:
        return self.__dict__.get(key, None)

    def __iter__(self):
        yield from self._keys
