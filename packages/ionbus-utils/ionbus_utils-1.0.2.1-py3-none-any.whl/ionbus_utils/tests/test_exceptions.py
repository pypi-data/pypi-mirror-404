"""Tests for exceptions.py module."""

from __future__ import annotations

import logging
import site
from pathlib import Path

import pytest

parent_dir = Path(__file__).absolute().parent.parent.parent
site.addsitedir(str(parent_dir))

from ionbus_utils.exceptions import exception_to_string, log_exception


class TestExceptionToString:
    """Tests for exception_to_string function."""

    def test_returns_string(self):
        """Test returns a string."""
        try:
            raise ValueError("test error")
        except ValueError as e:
            result = exception_to_string(e)
        assert isinstance(result, str)

    def test_contains_exception_type(self):
        """Test result contains exception type."""
        try:
            raise ValueError("test error")
        except ValueError as e:
            result = exception_to_string(e)
        assert "ValueError" in result

    def test_contains_exception_message(self):
        """Test result contains exception message."""
        try:
            raise ValueError("specific error message")
        except ValueError as e:
            result = exception_to_string(e)
        assert "specific error message" in result

    def test_contains_traceback(self):
        """Test result contains traceback information."""
        try:
            raise ValueError("test error")
        except ValueError as e:
            result = exception_to_string(e)
        assert "Traceback" in result

    def test_nested_exception(self):
        """Test with nested exception."""

        def inner():
            raise RuntimeError("inner error")

        def outer():
            inner()

        try:
            outer()
        except RuntimeError as e:
            result = exception_to_string(e)
        assert "RuntimeError" in result
        assert "inner error" in result


class TestLogException:
    """Tests for log_exception function."""

    def test_logs_exception(self, caplog):
        """Test logs the exception."""
        with caplog.at_level(logging.ERROR):
            try:
                raise ValueError("test logging error")
            except ValueError as e:
                log_exception(e)
        assert "ValueError" in caplog.text
        assert "test logging error" in caplog.text

    def test_includes_location_info(self, caplog):
        """Test includes file and function information."""
        with caplog.at_level(logging.ERROR):
            try:
                raise ValueError("test error")
            except ValueError as e:
                log_exception(e)
        # Should include filename
        assert "test_exceptions.py" in caplog.text

    def test_includes_hostname(self, caplog):
        """Test includes hostname information."""
        with caplog.at_level(logging.ERROR):
            try:
                raise ValueError("test error")
            except ValueError as e:
                log_exception(e)
        # Should include "running" and "on" indicating hostname info
        assert "running" in caplog.text
        assert "on" in caplog.text

    def test_with_different_stack_level(self, caplog):
        """Test with different stack level."""

        def helper():
            try:
                raise ValueError("helper error")
            except ValueError as e:
                log_exception(e, level=1)

        with caplog.at_level(logging.ERROR):
            helper()
        assert "helper error" in caplog.text
