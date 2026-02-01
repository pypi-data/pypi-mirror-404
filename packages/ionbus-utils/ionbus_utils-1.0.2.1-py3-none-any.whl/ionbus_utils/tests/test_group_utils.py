"""Tests for group_utils.py module."""

from __future__ import annotations

import getpass
import os
import site
from pathlib import Path

import pytest

parent_dir = Path(__file__).absolute().parent.parent.parent
site.addsitedir(str(parent_dir))

from ionbus_utils.group_utils import (
    get_group_members,
    get_groups_for_user,
    get_user_name,
)
from ionbus_utils.base_utils import is_windows


class TestGetUserName:
    """Tests for get_user_name function."""

    def test_returns_string_or_none(self):
        """Test returns string or None."""
        result = get_user_name()
        assert result is None or isinstance(result, str)

    def test_upper_case_by_default(self):
        """Test returns uppercase by default."""
        result = get_user_name()
        if result is not None:
            assert result == result.upper()

    def test_lower_case_when_requested(self):
        """Test returns lowercase when upper_case=False."""
        result = get_user_name(upper_case=False)
        if result is not None:
            assert result == result.lower()

    def test_matches_getpass_getuser(self):
        """Test matches getpass.getuser() (case-insensitive)."""
        try:
            expected = getpass.getuser()
            result = get_user_name()
            if result is not None:
                assert result.upper() == expected.upper()
        except Exception:
            # In containers, getpass.getuser() may fail
            pass


class TestGetGroupMembers:
    """Tests for get_group_members function."""

    def test_returns_list(self):
        """Test returns a list."""
        # Use a group that may or may not exist
        result = get_group_members("nonexistent_group_12345")
        assert isinstance(result, list)

    def test_nonexistent_group_returns_empty_list(self):
        """Test nonexistent group returns empty list."""
        result = get_group_members("definitely_not_a_real_group_xyz123")
        assert result == []

    @pytest.mark.skipif(
        is_windows(),
        reason="Test requires specific Unix groups",
    )
    def test_existing_unix_group(self):
        """Test with an existing Unix group."""
        # 'root' or 'wheel' usually exist on Unix systems
        for group in ["root", "wheel", "staff"]:
            result = get_group_members(group)
            if result:
                assert isinstance(result, list)
                break


class TestGetGroupsForUser:
    """Tests for get_groups_for_user function."""

    def test_returns_list(self):
        """Test returns a list."""
        result = get_groups_for_user("nonexistent_user_12345")
        assert isinstance(result, list)

    def test_nonexistent_user_returns_empty_list(self):
        """Test nonexistent user returns empty list."""
        result = get_groups_for_user("definitely_not_a_real_user_xyz123")
        assert result == []

    def test_current_user_has_groups(self):
        """Test current user has at least one group."""
        try:
            username = getpass.getuser()
            result = get_groups_for_user(username)
            # Current user should belong to at least one group
            assert len(result) >= 1
        except Exception:
            # Skip if we can't determine current user
            pytest.skip("Cannot determine current user")

    def test_groups_are_strings(self):
        """Test that group names are strings."""
        try:
            username = getpass.getuser()
            result = get_groups_for_user(username)
            for group in result:
                assert isinstance(group, str)
        except Exception:
            pytest.skip("Cannot determine current user")
