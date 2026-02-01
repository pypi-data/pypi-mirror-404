"""Tests for base_utils.py module."""

from __future__ import annotations

import site
import sys
import uuid
from pathlib import Path

import pytest

parent_dir = Path(__file__).absolute().parent.parent.parent
site.addsitedir(str(parent_dir))

from ionbus_utils.base_utils import (
    base_to_int,
    int_to_base,
    is_mac,
    is_windows,
    is_wsl,
    uuid_baseN,
)


class TestPlatformDetection:
    """Tests for platform detection functions."""

    def test_is_windows(self):
        """Test is_windows returns boolean."""
        result = is_windows()
        assert isinstance(result, bool)
        if sys.platform.lower().startswith("win"):
            assert result is True
        else:
            assert result is False

    def test_is_mac(self):
        """Test is_mac returns boolean."""
        result = is_mac()
        assert isinstance(result, bool)
        if sys.platform == "darwin":
            assert result is True
        else:
            assert result is False

    def test_is_wsl(self):
        """Test is_wsl returns boolean."""
        result = is_wsl()
        assert isinstance(result, bool)
        # WSL detection depends on environment, just check it returns bool


class TestIntToBase:
    """Tests for int_to_base function."""

    def test_base10(self):
        """Test conversion to base 10."""
        assert int_to_base(123, base=10) == "123"
        assert int_to_base(0, base=10) == "0"
        assert int_to_base(9, base=10) == "9"

    def test_base2(self):
        """Test conversion to base 2 (binary)."""
        assert int_to_base(5, base=2) == "101"
        assert int_to_base(8, base=2) == "1000"
        assert int_to_base(0, base=2) == "0"

    def test_base16(self):
        """Test conversion to base 16 (hex)."""
        assert int_to_base(255, base=16).upper() == "FF"
        assert int_to_base(16, base=16).upper() == "10"

    def test_base62(self):
        """Test conversion to base 62."""
        result = int_to_base(1000, base=62)
        assert isinstance(result, str)
        # All characters should be alphanumeric
        assert result.isalnum()

    def test_base64(self):
        """Test conversion to base 64."""
        result = int_to_base(1000, base=64)
        assert isinstance(result, str)

    def test_negative_number_raises(self):
        """Test that negative numbers raise error."""
        with pytest.raises(RuntimeError, match="negative"):
            int_to_base(-1, base=10)

    def test_invalid_base_raises(self):
        """Test that invalid base raises error."""
        with pytest.raises(RuntimeError, match="base must be"):
            int_to_base(10, base=1)
        with pytest.raises(RuntimeError, match="base must be"):
            int_to_base(10, base=65)

    def test_zero(self):
        """Test conversion of zero."""
        assert int_to_base(0, base=10) == "0"
        assert int_to_base(0, base=62) == "0"


class TestBaseToInt:
    """Tests for base_to_int function."""

    def test_base10(self):
        """Test conversion from base 10."""
        assert base_to_int("123", base=10) == 123
        assert base_to_int("0", base=10) == 0

    def test_base2(self):
        """Test conversion from base 2."""
        assert base_to_int("101", base=2) == 5
        assert base_to_int("1000", base=2) == 8

    def test_base16(self):
        """Test conversion from base 16."""
        assert base_to_int("FF", base=16) == 255
        assert base_to_int("10", base=16) == 16

    def test_invalid_base_raises(self):
        """Test that invalid base raises error."""
        with pytest.raises(RuntimeError, match="base must be"):
            base_to_int("10", base=1)
        with pytest.raises(RuntimeError, match="base must be"):
            base_to_int("10", base=65)


class TestRoundTrip:
    """Tests for round-trip conversion."""

    @pytest.mark.parametrize("base", [2, 10, 16, 36, 62])
    def test_round_trip(self, base):
        """Test that int_to_base and base_to_int are inverses."""
        for num in [0, 1, 100, 1000, 999999]:
            encoded = int_to_base(num, base=base)
            decoded = base_to_int(encoded, base=base)
            assert decoded == num

    def test_round_trip_large_number(self):
        """Test round trip with large number."""
        large_num = 2**64
        for base in [62, 64]:
            encoded = int_to_base(large_num, base=base)
            decoded = base_to_int(encoded, base=base)
            assert decoded == large_num


class TestUuidBaseN:
    """Tests for uuid_baseN function."""

    def test_uuid_base62(self):
        """Test UUID generation in base 62."""
        result = uuid_baseN(base=62)
        assert isinstance(result, str)
        assert len(result) > 0
        # Should be alphanumeric for base 62
        assert result.isalnum()

    def test_uuid_uniqueness(self):
        """Test that generated UUIDs are unique."""
        uuids = [uuid_baseN() for _ in range(100)]
        assert len(set(uuids)) == 100

    def test_uuid_base64(self):
        """Test UUID generation in base 64."""
        result = uuid_baseN(base=64)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_uuid_different_bases_different_length(self):
        """Test that different bases produce different length strings."""
        uuid62 = uuid_baseN(base=62)
        uuid10 = uuid_baseN(base=10)
        # Base 10 should be longer than base 62
        assert len(uuid10) > len(uuid62)
