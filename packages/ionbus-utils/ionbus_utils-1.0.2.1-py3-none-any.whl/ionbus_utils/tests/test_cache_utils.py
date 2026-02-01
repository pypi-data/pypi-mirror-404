"""Tests for cache_utils module."""

from __future__ import annotations

import datetime as dt
import site
from pathlib import Path

import pandas as pd
import pytest

parent_dir = Path(__file__).absolute().parent.parent.parent
site.addsitedir(str(parent_dir))

from ionbus_utils import cache_utils  # noqa: E402
from ionbus_utils.cache_utils import (  # noqa: E402
    InMemoryCache,
    cache_filename,
    get_latest_cache_filename,
    load_cache,
)


def test_cache_filename_defaults():
    """cache_filename returns expected path for today."""
    today = dt.date.today()
    name = cache_filename("prefix")
    assert str(today.year) in name
    assert "prefix_" in name
    assert name.endswith(".pkl.gz")


def test_cache_filename_keep_date_as_string():
    """When keep_date_as_string is True, date is used verbatim."""
    name = cache_filename("pref", "*", keep_date_as_string=True, directory="d")
    assert name == "d/pref_*.pkl.gz"


def test_get_latest_cache_filename(temp_dir, monkeypatch):
    """Returns most recent cache file."""
    fixed_date = dt.date(2024, 1, 1)
    # Subclass date so construction still works
    class FakeDate(dt.date):
        @classmethod
        def today(cls):
            return fixed_date

    monkeypatch.setattr(cache_utils.dt, "date", FakeDate)
    first = Path(cache_filename("pref", fixed_date, directory=str(temp_dir)))
    second = Path(cache_filename("pref", fixed_date + dt.timedelta(days=1), directory=str(temp_dir)))
    first.parent.mkdir(parents=True, exist_ok=True)
    first.touch()
    second.touch()
    latest = get_latest_cache_filename("pref", directory=str(temp_dir))
    assert latest.endswith(second.name)


def test_load_cache_prefers_today(temp_dir, monkeypatch):
    """load_cache returns today's cache and tomorrow's callback time when present."""
    fixed_now = dt.datetime(2024, 1, 1, 12, 0, 0)

    class FixedDateTime(dt.datetime):
        @classmethod
        def now(cls, tz=None):
            return fixed_now.replace(tzinfo=tz)

    monkeypatch.setattr(cache_utils.dt, "datetime", FixedDateTime)
    today_file = Path(cache_filename("pref", fixed_now.date(), directory=str(temp_dir)))
    today_file.parent.mkdir(parents=True, exist_ok=True)
    data = {"a": 1}
    pd.to_pickle(data, today_file)
    contents, next_time = load_cache(
        "pref", dt.time(9, 30), directory=str(temp_dir), allow_no_data=False
    )
    assert contents == data
    assert next_time.date() == fixed_now.date() + dt.timedelta(days=1)


def test_load_cache_uses_previous_when_missing_today(temp_dir, monkeypatch):
    """Falls back to previous cache file when today's cache is absent."""
    fixed_now = dt.datetime(2024, 1, 2, 8, 0, 0)

    class FixedDateTime(dt.datetime):
        @classmethod
        def now(cls, tz=None):
            return fixed_now.replace(tzinfo=tz)

    monkeypatch.setattr(cache_utils.dt, "datetime", FixedDateTime)
    yesterday = fixed_now.date() - dt.timedelta(days=1)
    prev_file = Path(cache_filename("pref", yesterday, directory=str(temp_dir)))
    prev_file.parent.mkdir(parents=True, exist_ok=True)
    data = {"prev": True}
    pd.to_pickle(data, prev_file)
    contents, next_time = load_cache(
        "pref", dt.time(9, 30), directory=str(temp_dir), allow_no_data=False
    )
    assert contents == data
    assert next_time.date() == fixed_now.date()


def test_load_cache_raises_when_no_data_and_not_allowed(temp_dir, monkeypatch):
    """Raises when no cache exists and allow_no_data is False."""
    fixed_now = dt.datetime(2024, 1, 3, 8, 0, 0)

    class FixedDateTime(dt.datetime):
        @classmethod
        def now(cls, tz=None):
            return fixed_now.replace(tzinfo=tz)

    monkeypatch.setattr(cache_utils.dt, "datetime", FixedDateTime)
    with pytest.raises(RuntimeError):
        load_cache("pref", dt.time(9, 30), directory=str(temp_dir), allow_no_data=False)


class TestInMemoryCache:
    """Tests for InMemoryCache class."""

    def test_put_and_get_returns_copy(self):
        payload = {"x": [1, 2, 3]}
        InMemoryCache.put(payload, "prefix", "key")
        returned = InMemoryCache.get("prefix", "key")
        assert returned == payload
        assert returned is not payload

    def test_put_state_and_get_state(self):
        state = {"val": 42}
        autogen = InMemoryCache.put_state(state, "pfx")
        fetched = InMemoryCache.get_state("pfx", autogen)
        assert fetched == state

    def test_put_many_and_get_many(self):
        InMemoryCache.put_many({"a": 1, "b": 2}, ["p"])
        result = InMemoryCache.get_many(["p"], ["a", "b"])
        assert result == {"a": 1, "b": 2}
