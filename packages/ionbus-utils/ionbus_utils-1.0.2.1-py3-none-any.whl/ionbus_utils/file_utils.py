"""File utilities"""

from __future__ import annotations

import datetime as dt
import gzip
import hashlib
import inspect
import os
import shutil
from glob import glob
from pathlib import Path

from ionbus_utils.base_utils import int_to_base, is_windows, is_wsl, uuid_baseN
from ionbus_utils.logging_utils import logger


this_timezone = dt.datetime.now().astimezone().tzinfo

# pylint: disable=W1203
# cSpell: ignore gzip gzips


def touch_file(
    path: str | os.PathLike | None, file_perms: int | None = None
) -> None:
    """Updates modify time of file 'path'.  will create
    if necessary, but otherwise leaves the contents untouched."""
    if path is None:
        # This is a no-op
        return
    try:
        with open(path, "a", encoding="UTF-8"):
            os.utime(path, None)
        if file_perms:
            os.chmod(str(path), file_perms)
    # pylint: disable=W0702
    except:  # noqa: E722
        logger.error(f"Unable to touch file {path}")


def file_modify_time(
    path: str | os.PathLike, with_tz: bool = False
) -> dt.datetime | None:
    """Returns last modify datetime if file exists,
    otherwise returns None.  Returns with (NYC) timezone if requested."""
    filepath = Path(path)
    if not filepath.exists():
        return None
    return dt.datetime.fromtimestamp(
        filepath.stat().st_mtime,
        tz=this_timezone if with_tz else None,
    )


def get_module_filepath(
    filename: str | os.PathLike | None = None, level: int = 2
) -> Path:
    """Returns absolute pathname of file passed in"""
    if filename is None:
        frame = inspect.stack()[level][0]
        func = frame.f_code
        filename = func.co_filename
    return Path(filename).absolute()


def get_module_name(filename: str | os.PathLike | None = None) -> str:
    """Returns module name of the filename passed in.  If nothing passed in,
    the module name of the file from the calling function is used."""
    filepath = get_module_filepath(filename)
    return os.path.basename(str(filepath.parent))


def move_single_file(
    orig_name: str | os.PathLike, new_name: str | os.PathLike
) -> None:
    """Moves a single file.  If new_name exists, it will be deleted before
    moving."""
    if os.path.exists(new_name):
        os.unlink(new_name)
    shutil.move(str(orig_name), str(new_name))


def gzip_file(
    filename: str | os.PathLike,
    unlink_orig: bool = True,
    verbose: bool = False,
) -> None:
    """Gzips given file.
    By default, the original file is removed.
    unlink_orig: when true, removes original file (DEFAULT).
    verbose: prints filename, sizes, and reduction percentage"""
    before = os.path.getsize(filename)
    if not before:
        if verbose:
            logger.info(f"Skipping {filename} because it is empty")
        return
    zip_name = f"{filename}.gz"
    with gzip.open(zip_name, "wb") as target, open(filename, "rb") as source:
        target.write(source.read())
    mod_time = Path(filename).stat().st_mtime
    os.utime(zip_name, (mod_time, mod_time))
    if verbose:
        after = os.path.getsize(zip_name)
        percent = 100 * after / before
        logger.info(f"{filename}: {before:,} -> {after:,} ({percent:.1f}%)")
    if unlink_orig:
        os.unlink(filename)


def get_file_hash(
    filename: str | os.PathLike,
    use_md5: bool = False,
    chunk_size: int = 65536,
    as_base62: bool = False,
) -> str:
    """Returns file hexadecimal hash (blake2b if use_md5 is false,
    else md5)"""
    hash_obj = hashlib.md5() if use_md5 else hashlib.blake2b()
    with open(filename, "rb") as source:
        while chunk := source.read(chunk_size):
            hash_obj.update(chunk)
    hex_digest = hash_obj.hexdigest()
    if as_base62:
        return int_to_base(int(hex_digest, 16))
    return hex_digest


def get_logfile_name(
    prefix: str = "process",
    log_dir: str = ".",
    gzip_old_logfiles: bool = True,
    old_age_days: float = 1,
    add_uuid: bool = False,
    ignore_env: bool = False,
) -> str:
    """Gives name of log file to write to. Will gzip old log files if
    requested"""
    now = dt.datetime.now()
    if (log_env := os.getenv("IBU_LOG_DIR")) is not None and not ignore_env:
        log_dir = log_env
    dir_name = now.strftime(f"{log_dir}/%Y/%m")
    if gzip_old_logfiles:
        unzipped = glob(f"{log_dir}/*/*/*.log")
        max_age = dt.datetime.now() - dt.timedelta(days=old_age_days)
        for old in unzipped:
            mod_time = file_modify_time(old)
            if mod_time and mod_time < max_age:
                gzip_file(old, verbose=False)
    os.makedirs(dir_name, exist_ok=True)
    suffix = f"_{uuid_baseN()}" if add_uuid else ""
    return now.strftime(f"{dir_name}/{prefix}_%Y%m%d_%H%M%S{suffix}.log")
