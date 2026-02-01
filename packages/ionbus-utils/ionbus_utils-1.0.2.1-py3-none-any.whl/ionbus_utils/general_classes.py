"""General Classes"""

from __future__ import annotations

import argparse
from typing import Any


class GenObject:
    """Very general class to create a dummy object"""


class DictClass(dict):
    """A generic class built off of a dictionary."""

    # https://stackoverflow.com/a/39375731/821832 and
    # https://stackoverflow.com/a/71954346/821832

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __getattr__(self, __name: str) -> Any:
        return super().__getitem__(__name)

    def __setattr__(self, __name: str, __value: Any) -> None:
        return super().__setitem__(__name, __value)

    def copy(self) -> DictClass:
        """returns shallow copy of self"""
        return DictClass(super().copy())

    def as_dict(self) -> dict:
        """Returns"""
        return super().copy()


class ArgParseRangeAction(argparse.Action):
    """An argparse action that requires a range of arguments in argparse.

    min_args defaults to 1.  max_args defaults to None (no maximum).
    One can call this class with only defaults, but that is effectively a no-op
    (e.g., the same as nargs='+').

    E.g.,
    parser.add_argument(
        "--pull-latest",
        type=str,
        action=ArgParseRangeAction,
        min_args=0,
        max_args=1,
        default=None,
    )
    """

    min_args: int = 1
    max_args: int | None

    def __init__(
        self,
        min_args: int = 1,
        max_args: int | None = None,
        *args,
        **kwargs,
    ):
        self.min_args = min_args
        self.max_args = max_args
        # Use '*' if min_args is 0, otherwise '+'
        kwargs["nargs"] = "*" if min_args == 0 else "+"
        super().__init__(*args, **kwargs)

    def __call__(
        self,
        parser: argparse.ArgumentParser,
        namespace: argparse.Namespace,
        values: list[str],
        option_string: str | None = None,
    ):
        num_args = len(values)

        # Check minimum
        if num_args < self.min_args:
            parser.error(
                f"{self.dest} requires at least {self.min_args} argument(s), "
                f"got {num_args}"
            )

        # Check maximum (if specified)
        if self.max_args and num_args > self.max_args:
            parser.error(
                f"{self.dest} requires at most {self.max_args} argument(s), "
                f"got {num_args}"
            )

        setattr(namespace, self.dest, values)
