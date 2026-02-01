"""Tests for logging_utils.py module."""

from __future__ import annotations

import logging
import site
import tempfile
from pathlib import Path

import pytest

parent_dir = Path(__file__).absolute().parent.parent.parent
site.addsitedir(str(parent_dir))

from ionbus_utils.logging_utils import (
    NOTICE_LEVEL,
    BadLogConfigError,
    get_logger,
    log_critical_if,
    log_debug_if,
    log_error_if,
    log_if,
    log_info_if,
    log_notice_if,
    log_warning_if,
    logger,
    set_log_level,
    setup_logger_format,
    warn_once,
    _log_once_locations,
)


class TestLoggerSetup:
    """Tests for logger setup functions."""

    def test_get_logger_returns_logger(self):
        """Test that get_logger returns a Logger instance."""
        log = get_logger()
        assert isinstance(log, logging.Logger)

    def test_default_logger_exists(self):
        """Test that the default logger is available."""
        assert logger is not None
        assert isinstance(logger, logging.Logger)

    def test_setup_logger_format_returns_logger(self):
        """Test setup_logger_format returns a Logger."""
        log = setup_logger_format(logger_name="test_logger")
        assert isinstance(log, logging.Logger)

    def test_setup_logger_format_with_thread_info(self):
        """Test setup with thread info."""
        log = setup_logger_format(
            logger_name="test_thread_logger",
            thread_info=True,
            update_format=True,
        )
        assert log is not None

    def test_setup_logger_format_with_multiprocessing_info(self):
        """Test setup with multiprocessing info."""
        log = setup_logger_format(
            logger_name="test_mp_logger",
            multiprocessing_info=True,
            update_format=True,
        )
        assert log is not None

    def test_setup_logger_format_with_extra_info(self):
        """Test setup with extra info."""
        log = setup_logger_format(
            logger_name="test_extra_logger",
            extra_info=" %(name)s",
            update_format=True,
        )
        assert log is not None


class TestNoticeLevelRegistered:
    """Tests for NOTICE level registration."""

    def test_notice_level_value(self):
        """Test NOTICE level has correct value."""
        assert NOTICE_LEVEL == 25
        assert logging.INFO < NOTICE_LEVEL < logging.WARNING

    def test_notice_level_registered(self):
        """Test NOTICE level is registered."""
        level_name = logging.getLevelName(NOTICE_LEVEL)
        assert level_name == "NOTICE"

    def test_logger_has_notice_method(self):
        """Test logger has notice method."""
        assert hasattr(logger, "notice")
        assert callable(logger.notice)


class TestSetLogLevel:
    """Tests for set_log_level function."""

    def test_set_log_level_with_int(self):
        """Test setting log level with integer."""
        original_level = logger.level
        try:
            set_log_level(logging.DEBUG)
            assert logger.level == logging.DEBUG
        finally:
            logger.setLevel(original_level)

    def test_set_log_level_with_string(self):
        """Test setting log level with string."""
        original_level = logger.level
        try:
            set_log_level("DEBUG")
            assert logger.level == logging.DEBUG
        finally:
            logger.setLevel(original_level)


class TestLogIf:
    """Tests for log_if functions."""

    def test_log_if_with_true_bool(self, caplog):
        """Test log_if logs when condition is True."""
        with caplog.at_level(logging.INFO):
            log_if("test message", True)
        assert "test message" in caplog.text

    def test_log_if_with_false_bool(self, caplog):
        """Test log_if does not log when condition is False."""
        with caplog.at_level(logging.INFO):
            log_if("should not appear", False)
        assert "should not appear" not in caplog.text

    def test_log_if_with_flags(self, caplog):
        """Test log_if with bit flags."""
        verbose = 0x5  # bits 0 and 2 set
        with caplog.at_level(logging.INFO):
            log_if("should appear", verbose, 0x1)  # bit 0 matches
            log_if("should not appear", verbose, 0x2)  # bit 1 doesn't match
        assert "should appear" in caplog.text
        assert "should not appear" not in caplog.text

    def test_log_info_if(self, caplog):
        """Test log_info_if function."""
        with caplog.at_level(logging.INFO):
            log_info_if("info message", True)
        assert "info message" in caplog.text

    def test_log_warning_if(self, caplog):
        """Test log_warning_if function."""
        with caplog.at_level(logging.WARNING):
            log_warning_if("warning message", True)
        assert "warning message" in caplog.text

    def test_log_error_if(self, caplog):
        """Test log_error_if function."""
        with caplog.at_level(logging.ERROR):
            log_error_if("error message", True)
        assert "error message" in caplog.text

    def test_log_debug_if(self, caplog):
        """Test log_debug_if function."""
        # Need to set logger level too, not just caplog level
        original_level = logger.level
        try:
            logger.setLevel(logging.DEBUG)
            with caplog.at_level(logging.DEBUG):
                log_debug_if("debug message", True)
            assert "debug message" in caplog.text
        finally:
            logger.setLevel(original_level)

    def test_log_critical_if(self, caplog):
        """Test log_critical_if function."""
        with caplog.at_level(logging.CRITICAL):
            log_critical_if("critical message", True)
        assert "critical message" in caplog.text

    def test_log_notice_if(self, caplog):
        """Test log_notice_if function."""
        with caplog.at_level(NOTICE_LEVEL):
            log_notice_if("notice message", True)
        assert "notice message" in caplog.text


class TestWarnOnce:
    """Tests for warn_once function."""

    def test_warn_once_logs_first_time(self, caplog):
        """Test warn_once logs the first time."""
        # Clear previous locations
        _log_once_locations.clear()
        with caplog.at_level(logging.WARNING):
            warn_once("unique warning message 1")
        assert "unique warning message 1" in caplog.text

    def test_warn_once_does_not_repeat(self, caplog):
        """Test warn_once doesn't log same location+message twice."""
        _log_once_locations.clear()
        # warn_once tracks by (file, line, function, message).
        # Same message from same line won't repeat.
        with caplog.at_level(logging.WARNING):
            for _ in range(2):
                warn_once("same warning message")
        # Should only appear once despite being called twice
        assert caplog.text.count("same warning message") == 1

    def test_warn_once_different_messages(self, caplog):
        """Test warn_once logs different messages."""
        _log_once_locations.clear()
        with caplog.at_level(logging.WARNING):
            warn_once("message A")
            warn_once("message B")
        assert "message A" in caplog.text
        assert "message B" in caplog.text


class TestBadLogConfigError:
    """Tests for BadLogConfigError."""

    def test_error_is_runtime_error(self):
        """Test BadLogConfigError is a RuntimeError."""
        assert issubclass(BadLogConfigError, RuntimeError)

    def test_error_message(self):
        """Test error message is preserved."""
        error = BadLogConfigError("test error")
        assert str(error) == "test error"
