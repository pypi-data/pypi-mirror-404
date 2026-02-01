"""Tests for time_utils module."""

from __future__ import annotations

import datetime as dt
import site
from pathlib import Path

import pandas as pd
import pytest

parent_dir = Path(__file__).absolute().parent.parent.parent
site.addsitedir(str(parent_dir))

from ionbus_utils import time_utils as tu  # noqa: E402


def test_ensure_time_parses_string_and_int():
    """ensure_time handles strings and minute counts."""
    assert tu.ensure_time("09:30") == dt.time(9, 30)
    assert tu.ensure_time(150) == dt.time(2, 30)
    with pytest.raises(RuntimeError):
        tu.ensure_time("bad")


def test_ensure_time_with_timedelta_unit():
    """Numeric with timedelta_number_unit is relative to now."""
    t = tu.ensure_time(1, timedelta_number_unit="hours")
    assert isinstance(t, dt.time)


def test_datetime_from_date_and_time():
    """Combines date and time respecting timezone optionality."""
    result = tu.datetime_from_date_and_time("2024-01-01", "12:00")
    assert result.date() == dt.date(2024, 1, 1)
    assert result.time() == dt.time(12, 0)


def test_datetime_from_time_and_date_start_time_rolls_forward():
    """Target time on same trade date when before start time."""
    start = "16:00"
    target = "15:00"
    now = dt.datetime(2024, 1, 2, 10, 0)
    ts = tu.datetime_from_time_and_date_start_time(
        target, start, _now=now, zone=tu.utc_timezone
    )
    assert ts.date() == dt.date(2024, 1, 2)


def test_ensure_time_invalid_string_raises():
    """Invalid time strings raise RuntimeError."""
    with pytest.raises(ValueError):
        tu.ensure_time("25:00")


def test_ensure_timezone_unknown_raises():
    """ensure_timezone raises when zone cannot be resolved."""
    with pytest.raises(RuntimeError):
        tu.ensure_timezone("Not/AZone")


def test_ensure_timezone_or_none_handles_known_codes():
    """Known codes resolve to ZoneInfo objects."""
    assert tu.ensure_timezone_or_none("ET") is tu.nyc_timezone
    assert tu.ensure_timezone_or_none("UTC") is tu.utc_timezone


def test_time_priority_queue(monkeypatch):
    """TimePriorityQueue orders items by time and uses now_func."""
    fixed_now = dt.datetime(2024, 1, 1, 0, 0, 0)
    queue = tu.TimePriorityQueue(now_func=lambda: fixed_now)
    queue.add(dt.timedelta(seconds=10), "a")
    queue.add(dt.timedelta(seconds=5), "b")
    assert len(queue) == 2
    assert queue.time_until_next_item() == 5
    ready = queue.next_ready_item()
    assert ready is None
    # Advance time
    queue.now_func = lambda: fixed_now + dt.timedelta(seconds=6)
    ready = queue.next_ready_item()
    assert ready[1] == "b"
