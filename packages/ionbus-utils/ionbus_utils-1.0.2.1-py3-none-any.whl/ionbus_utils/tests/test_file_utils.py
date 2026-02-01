"""Tests for file_utils.py module."""

from __future__ import annotations

import datetime as dt
import gzip
import os
import site
import tempfile
from pathlib import Path

import pytest

parent_dir = Path(__file__).absolute().parent.parent.parent
site.addsitedir(str(parent_dir))

from ionbus_utils.file_utils import (
    file_modify_time,
    get_file_hash,
    get_logfile_name,
    get_module_filepath,
    get_module_name,
    gzip_file,
    move_single_file,
    touch_file,
)


class TestTouchFile:
    """Tests for touch_file function."""

    def test_touch_creates_new_file(self, temp_dir):
        """Test touch creates a new file."""
        filepath = temp_dir / "new_file.txt"
        assert not filepath.exists()
        touch_file(filepath)
        assert filepath.exists()

    def test_touch_updates_mtime(self, temp_file):
        """Test touch updates modification time."""
        old_mtime = temp_file.stat().st_mtime
        import time

        time.sleep(0.1)
        touch_file(temp_file)
        new_mtime = temp_file.stat().st_mtime
        assert new_mtime >= old_mtime

    def test_touch_none_is_noop(self):
        """Test touch with None does nothing."""
        touch_file(None)  # Should not raise

    def test_touch_with_permissions(self, temp_dir):
        """Test touch with file permissions."""
        filepath = temp_dir / "perm_file.txt"
        touch_file(filepath, file_perms=0o644)
        assert filepath.exists()


class TestFileModifyTime:
    """Tests for file_modify_time function."""

    def test_returns_datetime_for_existing_file(self, temp_file):
        """Test returns datetime for existing file."""
        result = file_modify_time(temp_file)
        assert isinstance(result, dt.datetime)

    def test_returns_none_for_nonexistent_file(self, temp_dir):
        """Test returns None for nonexistent file."""
        result = file_modify_time(temp_dir / "nonexistent.txt")
        assert result is None

    def test_with_timezone(self, temp_file):
        """Test returns datetime with timezone when requested."""
        result = file_modify_time(temp_file, with_tz=True)
        assert result is not None
        assert result.tzinfo is not None


class TestGetModuleFilepath:
    """Tests for get_module_filepath function."""

    def test_returns_path_object(self):
        """Test returns Path object."""
        result = get_module_filepath(__file__)
        assert isinstance(result, Path)

    def test_returns_absolute_path(self):
        """Test returns absolute path."""
        result = get_module_filepath(__file__)
        assert result.is_absolute()

    def test_returns_correct_file(self):
        """Test returns correct file path."""
        result = get_module_filepath(__file__)
        assert result.name == "test_file_utils.py"


class TestGetModuleName:
    """Tests for get_module_name function."""

    def test_returns_string(self):
        """Test returns string."""
        result = get_module_name(__file__)
        assert isinstance(result, str)

    def test_returns_parent_dir_name(self):
        """Test returns parent directory name."""
        result = get_module_name(__file__)
        assert result == "tests"


class TestMoveSingleFile:
    """Tests for move_single_file function."""

    def test_moves_file(self, temp_dir):
        """Test moves file to new location."""
        src = temp_dir / "source.txt"
        dst = temp_dir / "dest.txt"
        src.write_text("content")
        move_single_file(src, dst)
        assert not src.exists()
        assert dst.exists()
        assert dst.read_text() == "content"

    def test_overwrites_existing_destination(self, temp_dir):
        """Test overwrites existing destination file."""
        src = temp_dir / "source.txt"
        dst = temp_dir / "dest.txt"
        src.write_text("new content")
        dst.write_text("old content")
        move_single_file(src, dst)
        assert dst.read_text() == "new content"


class TestGzipFile:
    """Tests for gzip_file function."""

    def test_creates_gzip_file(self, temp_dir):
        """Test creates .gz file."""
        filepath = temp_dir / "test.txt"
        filepath.write_text("test content " * 100)
        gzip_file(filepath)
        assert (temp_dir / "test.txt.gz").exists()

    def test_removes_original_by_default(self, temp_dir):
        """Test removes original file by default."""
        filepath = temp_dir / "test.txt"
        filepath.write_text("test content " * 100)
        gzip_file(filepath)
        assert not filepath.exists()

    def test_keeps_original_when_requested(self, temp_dir):
        """Test keeps original file when unlink_orig=False."""
        filepath = temp_dir / "test.txt"
        filepath.write_text("test content " * 100)
        gzip_file(filepath, unlink_orig=False)
        assert filepath.exists()
        assert (temp_dir / "test.txt.gz").exists()

    def test_skips_empty_files(self, temp_dir):
        """Test skips empty files."""
        filepath = temp_dir / "empty.txt"
        filepath.write_text("")
        gzip_file(filepath)
        assert not (temp_dir / "empty.txt.gz").exists()

    def test_gzipped_content_decompresses_correctly(self, temp_dir):
        """Test gzipped content can be decompressed."""
        filepath = temp_dir / "test.txt"
        original_content = "test content for compression"
        filepath.write_text(original_content)
        gzip_file(filepath)
        with gzip.open(temp_dir / "test.txt.gz", "rt") as f:
            assert f.read() == original_content


class TestGetFileHash:
    """Tests for get_file_hash function."""

    def test_returns_hex_string(self, temp_file):
        """Test returns hexadecimal string."""
        result = get_file_hash(temp_file)
        assert isinstance(result, str)
        # Should be valid hex
        int(result, 16)

    def test_blake2b_by_default(self, temp_file):
        """Test uses blake2b by default."""
        result = get_file_hash(temp_file)
        # blake2b produces 128 character hex string
        assert len(result) == 128

    def test_md5_when_requested(self, temp_file):
        """Test uses MD5 when requested."""
        result = get_file_hash(temp_file, use_md5=True)
        # MD5 produces 32 character hex string
        assert len(result) == 32

    def test_same_file_same_hash(self, temp_dir):
        """Test same content produces same hash."""
        file1 = temp_dir / "file1.txt"
        file2 = temp_dir / "file2.txt"
        file1.write_text("identical content")
        file2.write_text("identical content")
        assert get_file_hash(file1) == get_file_hash(file2)

    def test_different_files_different_hash(self, temp_dir):
        """Test different content produces different hash."""
        file1 = temp_dir / "file1.txt"
        file2 = temp_dir / "file2.txt"
        file1.write_text("content A")
        file2.write_text("content B")
        assert get_file_hash(file1) != get_file_hash(file2)

    def test_as_base62(self, temp_file):
        """Test returns base62 string when requested."""
        result = get_file_hash(temp_file, as_base62=True)
        assert isinstance(result, str)
        # Base62 should be alphanumeric
        assert result.isalnum()


class TestGetLogfileName:
    """Tests for get_logfile_name function."""

    def test_returns_string(self, temp_dir):
        """Test returns string path."""
        result = get_logfile_name(
            prefix="test", log_dir=str(temp_dir), gzip_old_logfiles=False
        )
        assert isinstance(result, str)

    def test_creates_directory_structure(self, temp_dir):
        """Test creates year/month directory structure."""
        result = get_logfile_name(
            prefix="test", log_dir=str(temp_dir), gzip_old_logfiles=False
        )
        result_path = Path(result)
        assert result_path.parent.exists()

    def test_includes_prefix(self, temp_dir):
        """Test filename includes prefix."""
        result = get_logfile_name(
            prefix="myprefix", log_dir=str(temp_dir), gzip_old_logfiles=False
        )
        assert "myprefix" in Path(result).name

    def test_includes_timestamp(self, temp_dir):
        """Test filename includes timestamp."""
        now = dt.datetime.now()
        result = get_logfile_name(
            prefix="test", log_dir=str(temp_dir), gzip_old_logfiles=False
        )
        assert now.strftime("%Y%m%d") in Path(result).name

    def test_ends_with_log_extension(self, temp_dir):
        """Test filename ends with .log."""
        result = get_logfile_name(
            prefix="test", log_dir=str(temp_dir), gzip_old_logfiles=False
        )
        assert result.endswith(".log")

    def test_add_uuid_option(self, temp_dir):
        """Test add_uuid adds unique suffix."""
        result1 = get_logfile_name(
            prefix="test",
            log_dir=str(temp_dir),
            gzip_old_logfiles=False,
            add_uuid=True,
        )
        result2 = get_logfile_name(
            prefix="test",
            log_dir=str(temp_dir),
            gzip_old_logfiles=False,
            add_uuid=True,
        )
        # UUIDs should make filenames different
        assert result1 != result2

    def test_respects_env_variable(self, temp_dir, monkeypatch):
        """Test respects IBU_LOG_DIR environment variable."""
        env_dir = temp_dir / "env_logs"
        env_dir.mkdir()
        monkeypatch.setenv("IBU_LOG_DIR", str(env_dir))
        result = get_logfile_name(
            prefix="test", log_dir="should_be_ignored", gzip_old_logfiles=False
        )
        assert str(env_dir) in result

    def test_ignores_env_when_requested(self, temp_dir, monkeypatch):
        """Test ignores env variable when ignore_env=True."""
        env_dir = temp_dir / "env_logs"
        env_dir.mkdir()
        explicit_dir = temp_dir / "explicit_logs"
        explicit_dir.mkdir()
        monkeypatch.setenv("IBU_LOG_DIR", str(env_dir))
        result = get_logfile_name(
            prefix="test",
            log_dir=str(explicit_dir),
            gzip_old_logfiles=False,
            ignore_env=True,
        )
        assert str(explicit_dir) in result
        assert str(env_dir) not in result
