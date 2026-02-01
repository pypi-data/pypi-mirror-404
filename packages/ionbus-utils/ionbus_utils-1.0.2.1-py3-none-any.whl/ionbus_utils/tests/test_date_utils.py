"""Tests for date_utils.py module."""

from __future__ import annotations

import datetime as dt
import site
from pathlib import Path

import pandas as pd
import pytest

parent_dir = Path(__file__).absolute().parent.parent.parent
site.addsitedir(str(parent_dir))

from ionbus_utils.date_utils import (
    ensure_date_is_iso_string,
    first_day_of_month,
    first_day_of_next_month,
    last_day_of_month,
    to_date,
    to_date_isoformat,
    yyyymmdd_to_date,
)


class TestYyyymmddToDate:
    """Tests for yyyymmdd_to_date function."""

    def test_parses_dashed_format(self):
        """Test parsing YYYY-MM-DD format."""
        result = yyyymmdd_to_date("2024-07-23")
        assert result == dt.date(2024, 7, 23)

    def test_parses_no_dash_format(self):
        """Test parsing YYYYMMDD format."""
        result = yyyymmdd_to_date("20240723")
        assert result == dt.date(2024, 7, 23)

    def test_parses_slashed_format(self):
        """Test parsing format with slashes."""
        result = yyyymmdd_to_date("2024/07/23")
        assert result == dt.date(2024, 7, 23)

    def test_returns_none_for_empty_string(self):
        """Test returns None for empty string."""
        result = yyyymmdd_to_date("")
        assert result is None

    def test_returns_none_for_none(self):
        """Test returns None for None input."""
        result = yyyymmdd_to_date(None)
        assert result is None


class TestToDate:
    """Tests for to_date function."""

    def test_converts_date(self):
        """Test converting date object."""
        d = dt.date(2024, 7, 23)
        result = to_date(d)
        assert result == d

    def test_converts_datetime(self):
        """Test converting datetime object."""
        d = dt.datetime(2024, 7, 23, 14, 30, 0)
        result = to_date(d)
        assert result == dt.date(2024, 7, 23)

    def test_converts_timestamp(self):
        """Test converting pandas Timestamp."""
        ts = pd.Timestamp("2024-07-23 14:30:00")
        result = to_date(ts)
        assert result == dt.date(2024, 7, 23)

    def test_converts_string(self):
        """Test converting string."""
        result = to_date("2024-07-23")
        assert result == dt.date(2024, 7, 23)

    def test_returns_none_for_none(self):
        """Test returns None for None input."""
        result = to_date(None)
        assert result is None

    def test_returns_none_for_empty_string(self):
        """Test returns None for empty string."""
        result = to_date("")
        assert result is None


class TestToDateIsoformat:
    """Tests for to_date_isoformat function."""

    def test_returns_isoformat(self):
        """Test returns ISO format string."""
        d = dt.date(2024, 7, 23)
        result = to_date_isoformat(d)
        assert result == "2024-07-23"

    def test_returns_no_symbols_format(self):
        """Test returns format without symbols."""
        d = dt.date(2024, 7, 23)
        result = to_date_isoformat(d, no_symbols=True)
        assert result == "20240723"

    def test_converts_datetime(self):
        """Test converts datetime to date isoformat."""
        d = dt.datetime(2024, 7, 23, 14, 30, 0)
        result = to_date_isoformat(d)
        assert result == "2024-07-23"

    def test_returns_none_for_none(self):
        """Test returns None for None input."""
        result = to_date_isoformat(None)
        assert result is None


class TestFirstDayOfMonth:
    """Tests for first_day_of_month function."""

    def test_returns_first_day(self):
        """Test returns first day of month."""
        d = dt.date(2024, 7, 23)
        result = first_day_of_month(d)
        assert result == dt.date(2024, 7, 1)

    def test_already_first_day(self):
        """Test when input is already first day."""
        d = dt.date(2024, 7, 1)
        result = first_day_of_month(d)
        assert result == dt.date(2024, 7, 1)

    def test_with_datetime(self):
        """Test with datetime input."""
        d = dt.datetime(2024, 7, 23, 14, 30)
        result = first_day_of_month(d)
        assert result == dt.date(2024, 7, 1)

    def test_with_string(self):
        """Test with string input."""
        result = first_day_of_month("2024-07-23")
        assert result == dt.date(2024, 7, 1)


class TestFirstDayOfNextMonth:
    """Tests for first_day_of_next_month function."""

    def test_returns_first_of_next_month(self):
        """Test returns first day of next month."""
        d = dt.date(2024, 7, 23)
        result = first_day_of_next_month(d)
        assert result == dt.date(2024, 8, 1)

    def test_december_to_january(self):
        """Test December rolls to January of next year."""
        d = dt.date(2024, 12, 15)
        result = first_day_of_next_month(d)
        assert result == dt.date(2025, 1, 1)

    def test_with_datetime(self):
        """Test with datetime input."""
        d = dt.datetime(2024, 7, 23, 14, 30)
        result = first_day_of_next_month(d)
        assert result == dt.date(2024, 8, 1)


class TestLastDayOfMonth:
    """Tests for last_day_of_month function."""

    def test_returns_last_day_31(self):
        """Test returns last day for 31-day month."""
        d = dt.date(2024, 7, 15)
        result = last_day_of_month(d)
        assert result == dt.date(2024, 7, 31)

    def test_returns_last_day_30(self):
        """Test returns last day for 30-day month."""
        d = dt.date(2024, 6, 15)
        result = last_day_of_month(d)
        assert result == dt.date(2024, 6, 30)

    def test_february_leap_year(self):
        """Test February in leap year."""
        d = dt.date(2024, 2, 15)
        result = last_day_of_month(d)
        assert result == dt.date(2024, 2, 29)

    def test_february_non_leap_year(self):
        """Test February in non-leap year."""
        d = dt.date(2023, 2, 15)
        result = last_day_of_month(d)
        assert result == dt.date(2023, 2, 28)


class TestEnsureDateIsIsoString:
    """Tests for ensure_date_is_iso_string function."""

    def test_converts_date(self):
        """Test converts date to ISO string."""
        d = dt.date(2024, 7, 23)
        result = ensure_date_is_iso_string(d)
        assert result == "2024-07-23"

    def test_converts_datetime(self):
        """Test converts datetime to ISO string."""
        d = dt.datetime(2024, 7, 23, 14, 30)
        result = ensure_date_is_iso_string(d)
        assert result == "2024-07-23"

    def test_converts_timestamp(self):
        """Test converts Timestamp to ISO string."""
        ts = pd.Timestamp("2024-07-23")
        result = ensure_date_is_iso_string(ts)
        assert result == "2024-07-23"

    def test_returns_none_for_none(self):
        """Test returns None for None input."""
        result = ensure_date_is_iso_string(None)
        assert result is None
