"""Tests for general_classes.py module."""

from __future__ import annotations

import argparse
import site
from pathlib import Path

import pytest

parent_dir = Path(__file__).absolute().parent.parent.parent
site.addsitedir(str(parent_dir))

from ionbus_utils.general_classes import (
    ArgParseRangeAction,
    DictClass,
    GenObject,
)


class TestGenObject:
    """Tests for GenObject class."""

    def test_can_create_empty(self):
        """Test creating empty GenObject."""
        obj = GenObject()
        assert obj is not None

    def test_can_set_attributes(self):
        """Test setting attributes dynamically."""
        obj = GenObject()
        obj.value = 42
        obj.name = "test"
        assert obj.value == 42
        assert obj.name == "test"

    def test_attributes_persist(self):
        """Test attributes persist after setting."""
        obj = GenObject()
        obj.a = 1
        obj.b = 2
        assert obj.a == 1
        assert obj.b == 2


class TestDictClass:
    """Tests for DictClass class."""

    def test_init_from_dict(self):
        """Test initializing from dictionary."""
        d = DictClass({"name": "Alice", "age": 30})
        assert d["name"] == "Alice"
        assert d["age"] == 30

    def test_init_from_kwargs(self):
        """Test initializing from keyword arguments."""
        d = DictClass(name="Alice", age=30)
        assert d["name"] == "Alice"
        assert d["age"] == 30

    def test_attribute_access(self):
        """Test accessing values as attributes."""
        d = DictClass({"name": "Alice", "age": 30})
        assert d.name == "Alice"
        assert d.age == 30

    def test_attribute_setting(self):
        """Test setting values as attributes."""
        d = DictClass()
        d.name = "Alice"
        d.age = 30
        assert d["name"] == "Alice"
        assert d["age"] == 30

    def test_dict_access(self):
        """Test accessing values as dictionary."""
        d = DictClass()
        d["name"] = "Alice"
        assert d["name"] == "Alice"
        assert d.name == "Alice"

    def test_copy(self):
        """Test copy returns DictClass."""
        d = DictClass({"name": "Alice"})
        d_copy = d.copy()
        assert isinstance(d_copy, DictClass)
        assert d_copy["name"] == "Alice"
        # Ensure it's a new object
        d_copy.name = "Bob"
        assert d.name == "Alice"

    def test_as_dict(self):
        """Test as_dict returns regular dict."""
        d = DictClass({"name": "Alice", "age": 30})
        regular = d.as_dict()
        assert isinstance(regular, dict)
        assert not isinstance(regular, DictClass)
        assert regular["name"] == "Alice"

    def test_inherits_dict_methods(self):
        """Test DictClass inherits dict methods."""
        d = DictClass({"a": 1, "b": 2})
        assert list(d.keys()) == ["a", "b"]
        assert list(d.values()) == [1, 2]
        assert len(d) == 2


class TestArgParseRangeAction:
    """Tests for ArgParseRangeAction class."""

    def test_accepts_within_range(self):
        """Test accepts arguments within range."""
        parser = argparse.ArgumentParser()
        parser.add_argument(
            "--files",
            action=ArgParseRangeAction,
            min_args=1,
            max_args=3,
        )
        args = parser.parse_args(["--files", "a.txt", "b.txt"])
        assert args.files == ["a.txt", "b.txt"]

    def test_accepts_min_args(self):
        """Test accepts minimum number of arguments."""
        parser = argparse.ArgumentParser()
        parser.add_argument(
            "--files",
            action=ArgParseRangeAction,
            min_args=1,
            max_args=3,
        )
        args = parser.parse_args(["--files", "a.txt"])
        assert args.files == ["a.txt"]

    def test_accepts_max_args(self):
        """Test accepts maximum number of arguments."""
        parser = argparse.ArgumentParser()
        parser.add_argument(
            "--files",
            action=ArgParseRangeAction,
            min_args=1,
            max_args=3,
        )
        args = parser.parse_args(["--files", "a.txt", "b.txt", "c.txt"])
        assert args.files == ["a.txt", "b.txt", "c.txt"]

    def test_rejects_too_few_args(self):
        """Test rejects too few arguments."""
        parser = argparse.ArgumentParser()
        parser.add_argument(
            "--files",
            action=ArgParseRangeAction,
            min_args=2,
            max_args=3,
        )
        with pytest.raises(SystemExit):
            parser.parse_args(["--files", "a.txt"])

    def test_rejects_too_many_args(self):
        """Test rejects too many arguments."""
        parser = argparse.ArgumentParser()
        parser.add_argument(
            "--files",
            action=ArgParseRangeAction,
            min_args=1,
            max_args=2,
        )
        with pytest.raises(SystemExit):
            parser.parse_args(["--files", "a.txt", "b.txt", "c.txt"])

    def test_min_zero_allows_empty(self):
        """Test min_args=0 allows empty list."""
        parser = argparse.ArgumentParser()
        parser.add_argument(
            "--files",
            action=ArgParseRangeAction,
            min_args=0,
            max_args=2,
            default=None,
        )
        args = parser.parse_args(["--files"])
        assert args.files == []

    def test_no_max_allows_unlimited(self):
        """Test no max_args allows unlimited."""
        parser = argparse.ArgumentParser()
        parser.add_argument(
            "--files",
            action=ArgParseRangeAction,
            min_args=1,
            max_args=None,
        )
        args = parser.parse_args(
            ["--files", "a.txt", "b.txt", "c.txt", "d.txt", "e.txt"]
        )
        assert len(args.files) == 5
