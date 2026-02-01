"""Tests for regex_utils.py module."""

from __future__ import annotations

import site
from pathlib import Path

import pytest

parent_dir = Path(__file__).absolute().parent.parent.parent
site.addsitedir(str(parent_dir))

from ionbus_utils.regex_utils import (
    COMMA_SEMI_RE,
    LEADING_UNDER_RE,
    NEWLINE_RE,
    NON_DIGIT_RE,
    NON_LETTER_LIKE_RE,
    SPACE_RE,
)


class TestNewlineRe:
    """Tests for NEWLINE_RE pattern."""

    def test_splits_unix_newlines(self):
        """Test splitting on Unix newlines."""
        text = "line1\nline2\nline3"
        result = NEWLINE_RE.split(text)
        assert result == ["line1", "line2", "line3"]

    def test_splits_windows_newlines(self):
        """Test splitting on Windows newlines."""
        text = "line1\r\nline2\r\nline3"
        result = NEWLINE_RE.split(text)
        assert result == ["line1", "line2", "line3"]

    def test_splits_mixed_newlines(self):
        """Test splitting on mixed newlines."""
        text = "line1\nline2\r\nline3"
        result = NEWLINE_RE.split(text)
        assert result == ["line1", "line2", "line3"]

    def test_no_newlines(self):
        """Test text without newlines."""
        text = "single line"
        result = NEWLINE_RE.split(text)
        assert result == ["single line"]


class TestSpaceRe:
    """Tests for SPACE_RE pattern."""

    def test_replaces_single_space(self):
        """Test replacing single spaces."""
        text = "hello world"
        result = SPACE_RE.sub("_", text)
        assert result == "hello_world"

    def test_replaces_multiple_spaces(self):
        """Test replacing multiple consecutive spaces."""
        text = "hello   world"
        result = SPACE_RE.sub("_", text)
        assert result == "hello_world"

    def test_replaces_tabs(self):
        """Test replacing tabs."""
        text = "hello\tworld"
        result = SPACE_RE.sub("_", text)
        assert result == "hello_world"

    def test_replaces_mixed_whitespace(self):
        """Test replacing mixed whitespace."""
        text = "hello \t  world"
        result = SPACE_RE.sub("_", text)
        assert result == "hello_world"


class TestCommaSemiRe:
    """Tests for COMMA_SEMI_RE pattern."""

    def test_splits_on_comma(self):
        """Test splitting on commas."""
        text = "a, b, c"
        result = COMMA_SEMI_RE.split(text)
        assert result == ["a", "b", "c"]

    def test_splits_on_semicolon(self):
        """Test splitting on semicolons."""
        text = "a; b; c"
        result = COMMA_SEMI_RE.split(text)
        assert result == ["a", "b", "c"]

    def test_splits_on_mixed(self):
        """Test splitting on mixed separators."""
        text = "a, b; c"
        result = COMMA_SEMI_RE.split(text)
        assert result == ["a", "b", "c"]

    def test_handles_no_spaces(self):
        """Test splitting without surrounding spaces."""
        text = "a,b,c"
        result = COMMA_SEMI_RE.split(text)
        assert result == ["a", "b", "c"]


class TestNonLetterLikeRe:
    """Tests for NON_LETTER_LIKE_RE pattern."""

    def test_removes_spaces_and_punctuation(self):
        """Test removing non-word characters."""
        text = "hello, world!"
        result = NON_LETTER_LIKE_RE.sub("", text)
        assert result == "helloworld"

    def test_keeps_letters_and_numbers(self):
        """Test keeping letters and numbers."""
        text = "abc123"
        result = NON_LETTER_LIKE_RE.sub("", text)
        assert result == "abc123"

    def test_keeps_underscores(self):
        """Test keeping underscores (part of \\w)."""
        text = "hello_world"
        result = NON_LETTER_LIKE_RE.sub("", text)
        assert result == "hello_world"


class TestNonDigitRe:
    """Tests for NON_DIGIT_RE pattern."""

    def test_removes_letters(self):
        """Test removing letters."""
        text = "abc123def"
        result = NON_DIGIT_RE.sub("", text)
        assert result == "123"

    def test_removes_punctuation(self):
        """Test removing punctuation."""
        text = "2024-07-23"
        result = NON_DIGIT_RE.sub("", text)
        assert result == "20240723"

    def test_keeps_only_digits(self):
        """Test keeping only digits."""
        text = "Phone: (555) 123-4567"
        result = NON_DIGIT_RE.sub("", text)
        assert result == "5551234567"


class TestLeadingUnderRe:
    """Tests for LEADING_UNDER_RE pattern."""

    def test_removes_single_leading_underscore(self):
        """Test removing single leading underscore."""
        text = "_private"
        result = LEADING_UNDER_RE.sub("", text)
        assert result == "private"

    def test_removes_only_first_underscore(self):
        """Test removes only the first underscore."""
        text = "__dunder"
        result = LEADING_UNDER_RE.sub("", text)
        assert result == "_dunder"

    def test_no_leading_underscore(self):
        """Test text without leading underscore."""
        text = "public"
        result = LEADING_UNDER_RE.sub("", text)
        assert result == "public"

    def test_underscore_in_middle(self):
        """Test underscore in middle is not removed."""
        text = "hello_world"
        result = LEADING_UNDER_RE.sub("", text)
        assert result == "hello_world"
