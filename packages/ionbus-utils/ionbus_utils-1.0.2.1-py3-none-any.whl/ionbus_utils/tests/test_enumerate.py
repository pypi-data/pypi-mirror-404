"""Tests for enumerate.py module."""

from __future__ import annotations

import site
from pathlib import Path

import pytest

parent_dir = Path(__file__).absolute().parent.parent.parent
site.addsitedir(str(parent_dir))

from ionbus_utils.enumerate import Enumerate, StrEnum  # noqa: E402


class TestEnumerate:
    """Tests for the Enumerate class."""

    def test_basic_string_initialization(self):
        """Test creating enum from space-separated string."""
        colors = Enumerate("RED GREEN BLUE")
        # Default behavior adds underscore prefix to values
        assert colors.RED == "_RED"
        assert colors.GREEN == "_GREEN"
        assert colors.BLUE == "_BLUE"

    def test_list_initialization(self):
        """Test creating enum from list."""
        colors = Enumerate(["RED", "GREEN", "BLUE"])
        # Default behavior adds underscore prefix to values
        assert colors.RED == "_RED"
        assert colors.GREEN == "_GREEN"
        assert colors.BLUE == "_BLUE"

    def test_dict_initialization(self):
        """Test creating enum from dictionary."""
        colors = Enumerate({"RED": 1, "GREEN": 2, "BLUE": 3})
        assert colors.RED == 1
        assert colors.GREEN == 2
        assert colors.BLUE == 3

    def test_prefix(self):
        """Test enum with prefix."""
        colors = Enumerate("RED GREEN BLUE", prefix="COLOR")
        assert colors.RED == "COLOR_RED"
        assert colors.GREEN == "COLOR_GREEN"

    def test_as_int(self):
        """Test enum with integer values."""
        colors = Enumerate("RED GREEN BLUE", as_int=True)
        assert colors.RED == 0
        assert colors.GREEN == 1
        assert colors.BLUE == 2

    def test_as_int_with_offset(self):
        """Test enum with integer values and offset."""
        colors = Enumerate("RED GREEN BLUE", as_int=True, int_offset=10)
        assert colors.RED == 10
        assert colors.GREEN == 11
        assert colors.BLUE == 12

    def test_as_bit(self):
        """Test enum with bit flag values."""
        flags = Enumerate("READ WRITE EXECUTE", as_bit=True)
        # 1 << (count + offset), with default offset=0
        assert flags.READ == 1  # 1 << 0
        assert flags.WRITE == 2  # 1 << 1
        assert flags.EXECUTE == 4  # 1 << 2

    def test_key_value(self):
        """Test enum with key=value format."""
        # key_value parses "NAME=VALUE" - NAME becomes attribute, VALUE is value
        status = Enumerate("OK=200 NOT_FOUND=404 ERROR=500", key_value=True)
        assert status.OK == "200"
        assert status.NOT_FOUND == "404"
        assert status.ERROR == "500"

    def test_key_value_as_int(self):
        """Test enum with key=value format and as_int."""
        status = Enumerate(
            "OK=200 NOT_FOUND=404 ERROR=500", key_value=True, as_int=True
        )
        assert status.OK == 200
        assert status.NOT_FOUND == 404
        assert status.ERROR == 500

    def test_name_as_value(self):
        """Test enum where value equals name."""
        colors = Enumerate("RED GREEN BLUE", name_as_value=True)
        assert colors.RED == "RED"
        assert colors.GREEN == "GREEN"

    def test_name_as_value_with_prefix(self):
        """Test enum where value equals name with prefix."""
        colors = Enumerate(
            "RED GREEN BLUE", prefix="COLOR_", name_as_value=True
        )
        assert colors.RED == "COLOR_RED"
        assert colors.GREEN == "COLOR_GREEN"

    def test_is_valid_key(self):
        """Test is_valid_key method."""
        colors = Enumerate("RED GREEN BLUE")
        assert colors.is_valid_key("RED") is True
        assert colors.is_valid_key("YELLOW") is False

    def test_is_valid_value(self):
        """Test is_valid_value method."""
        colors = Enumerate("RED GREEN BLUE", as_int=True)
        assert colors.is_valid_value(0) is True
        assert colors.is_valid_value(99) is False

    def test_value_to_key(self):
        """Test value_to_key method."""
        colors = Enumerate("RED GREEN BLUE", as_int=True)
        assert colors.value_to_key(0) == "RED"
        assert colors.value_to_key(1) == "GREEN"
        assert colors.value_to_key(99) is None

    def test_keys(self):
        """Test keys method returns list of keys."""
        colors = Enumerate("RED GREEN BLUE")
        assert colors.keys() == ["RED", "GREEN", "BLUE"]

    def test_values(self):
        """Test values method returns list of values."""
        colors = Enumerate("RED GREEN BLUE", as_int=True)
        assert set(colors.values()) == {0, 1, 2}

    def test_immutability(self):
        """Test that enum values cannot be modified."""
        colors = Enumerate("RED GREEN BLUE")
        with pytest.raises(RuntimeError, match="cannot modify"):
            colors.RED = "MODIFIED"

    def test_duplicate_names_raises_error(self):
        """Test that duplicate names raise an error."""
        with pytest.raises(RuntimeError, match="cannot duplicate"):
            Enumerate("RED RED BLUE")

    def test_iteration(self):
        """Test iterating over enum keys."""
        colors = Enumerate("RED GREEN BLUE")
        assert list(colors) == ["RED", "GREEN", "BLUE"]

    def test_callable(self):
        """Test calling enum with key."""
        colors = Enumerate("RED GREEN BLUE", as_int=True)
        assert colors("RED") == 0
        assert colors("INVALID") is None

    def test_str_representation(self):
        """Test string representation."""
        colors = Enumerate("RED GREEN BLUE", as_int=True)
        result = str(colors)
        assert "RED" in result
        assert "GREEN" in result
        assert "BLUE" in result

    def test_getattr_invalid_raises(self):
        """Test accessing invalid attribute raises error."""
        colors = Enumerate("RED GREEN BLUE")
        with pytest.raises(RuntimeError, match="not found"):
            _ = colors.INVALID


class TestStrEnum:
    """Tests for StrEnum import."""

    def test_strenum_available(self):
        """Test that StrEnum is available."""
        assert StrEnum is not None

    def test_strenum_subclass(self):
        """Test creating a StrEnum subclass."""

        class Color(StrEnum):
            RED = "red"
            GREEN = "green"
            BLUE = "blue"

        assert Color.RED == "red"
        assert str(Color.RED) == "red"
        assert isinstance(Color.RED, str)
