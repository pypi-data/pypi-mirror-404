"""Module to help with both in memory and on disk caching"""

from __future__ import annotations

# pylint: disable=C0411
import datetime as dt
import os
import threading
from collections.abc import KeysView
from glob import glob
from typing import Any, ClassVar, Union

import pandas as pd

import ionbus_utils.time_utils as tu
from ionbus_utils.date_utils import to_date_isoformat
from ionbus_utils.general import timestamped_id, to_single_list
from ionbus_utils.logging_utils import logger
from ionbus_utils.time_utils import TimeType

PrefixKeyType = Union[list[str], tuple[str], KeysView[str], str]


def cache_filename(
    prefix: str,
    the_date: dt.date | dt.datetime | pd.Timestamp | str | None = None,
    keep_date_as_string: bool = False,
    directory: str = "data",
) -> str:
    """Returns cache filename.  Use keep_date_as_string=True to
    get glob string.  Passing in no date uses today as the date."""
    directory = directory.rstrip("/\\")
    if the_date is None:
        the_date = dt.date.today()
    date_str = (
        the_date
        if keep_date_as_string
        else to_date_isoformat(the_date, no_symbols=True)
    )
    if date_str is None:
        raise RuntimeError("No date passed in")
    return f"{directory}/{prefix}_{date_str}.pkl.gz"


def get_latest_cache_filename(prefix: str, directory: str = "") -> str | None:
    """Assumes the latest file is the last when sorted alphabetically."""
    files = sorted(
        glob(
            cache_filename(
                prefix, "*", keep_date_as_string=True, directory=directory
            )
        )
    )
    return files[-1] if files else None


def load_cache(
    prefix: str,
    cb_time: TimeType,
    directory: str = "data",
    allow_no_data: bool = False,
    alias: str | None = None,
) -> tuple[dict, dt.datetime | None]:
    """Loads a cache file returning dictionary of information and next timestamp
    to load new data."""
    try:
        # Get today
        now = dt.datetime.now()
        today = now.date()
        today_cb = tu.datetime_from_date_and_time(today, cb_time)
        tomorrow_cb = today_cb + dt.timedelta(days=1)
        today_cache_name = cache_filename(prefix, today, directory=directory)
        if os.path.exists(today_cache_name):
            # we've got what we need today, come back tomorrow
            logger.info(f"Loading today's cache file {today_cache_name}")
            return pd.read_pickle(today_cache_name), tomorrow_cb
        # We don't have today, so the load data callback time should be today.
        latest_cache_name = get_latest_cache_filename(prefix, directory)
        if not latest_cache_name:
            if not allow_no_data:
                raise RuntimeError(f"Unable to get data for {prefix}")
            logger.warning("No cache file found.")
            return {}, today_cb
        logger.warning(f"Loading previous cache file {latest_cache_name}")
        return pd.read_pickle(latest_cache_name), today_cb
    except Exception as excp:
        if allow_no_data:
            return {}, today_cb
        raise excp


class InMemoryCache:
    """In memory cache singleton class"""

    _lock: ClassVar[threading.Lock] = threading.Lock()
    _cache_data: ClassVar[dict] = {}
    _stash_id: ClassVar[int] = 0

    @classmethod
    def get(
        cls,
        prefix_keys: PrefixKeyType,
        *keys,
        default_copy: bool = True,
    ) -> Any:
        """Gets requested item"""
        with cls._lock:
            return cls._assume_locked_get(
                cls._combine_prefix_with_keys(prefix_keys, keys, True),
                default_copy,
            )

    @classmethod
    def get_many(
        cls,
        prefix_keys: PrefixKeyType,
        list_or_dict: list | dict,
        default_copy: bool = True,
    ) -> dict:
        """Gets multiple requested items"""
        if isinstance(list_or_dict, dict):
            ret_dict = list_or_dict
            list_or_dict = list(list_or_dict.keys())
        else:
            ret_dict = {}
        prefix_keys = to_single_list(prefix_keys)
        with cls._lock:
            for key in list_or_dict:
                ret_dict[key] = cls._assume_locked_get(
                    cls._combine_prefix_with_keys(prefix_keys, key, False),
                    default_copy,
                )
        return ret_dict

    @classmethod
    def get_state(cls, prefix_keys: PrefixKeyType, autogen_key: str) -> Any:
        """Gets state dictionary"""
        return cls.get(prefix_keys, autogen_key, default_copy=False)

    @classmethod
    def put(
        cls,
        data: Any,
        prefix_keys: PrefixKeyType,
        *keys,
    ) -> None:
        """puts single item"""
        with cls._lock:
            cls._assume_locked_put(
                data,
                cls._combine_prefix_with_keys(prefix_keys, keys),
            )

    @classmethod
    def put_many(
        cls,
        data_dict: dict,
        prefix_keys: PrefixKeyType,
    ) -> None:
        """Pushes many pieces of data into cache.  If prefix_keys are given,
        should be list, tuple, or string."""
        prefix_keys = to_single_list(prefix_keys)
        with cls._lock:
            for key, value in data_dict.items():
                cls._assume_locked_put(
                    value,
                    cls._combine_prefix_with_keys(prefix_keys, key),
                )

    @classmethod
    def put_state(
        cls,
        state: dict,
        prefix_keys: PrefixKeyType,
        autogen_key: str | None = None,
    ) -> str:
        """puts multiple state items.  Returns autogen_key"""
        with cls._lock:
            if autogen_key is None:
                cls._stash_id += 1
                autogen_key = f"{timestamped_id('agk_')}_{cls._stash_id:03}"
            # I could use put(), but I didn't want to unlock and immediately
            # lock again, so I chose to be more verbose instead.
            cls._assume_locked_put(
                state,
                cls._combine_prefix_with_keys(prefix_keys, autogen_key),
            )
        return autogen_key

    @classmethod
    def _assume_locked_get(
        cls, keys: PrefixKeyType, default_copy: bool = True
    ) -> Any:
        data = cls._cache_data.get(tuple(keys))
        if default_copy:
            if isinstance(data, (pd.DataFrame, pd.Series, dict)):
                return data.copy()
            if isinstance(data, list):
                return data[:]
        return data

    @classmethod
    def _assume_locked_put(
        cls,
        data: Any,
        keys: PrefixKeyType,
    ) -> None:
        cls._cache_data.update({tuple(keys): data})

    @classmethod
    def _combine_prefix_with_keys(
        cls,
        prefix_keys: PrefixKeyType,
        keys: PrefixKeyType,
        prepare_prefix_keys: bool = False,
    ) -> list[str]:
        if prepare_prefix_keys or not isinstance(prefix_keys, list):
            prefix_keys = to_single_list(prefix_keys)
        elif prefix_keys is None:
            raise RuntimeError(
                "Cannot have None for prefix keys if not preparing prefix keys"
            )
        return prefix_keys + to_single_list(keys)
