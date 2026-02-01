"""Handles windows/linux subprocess differences"""

from __future__ import annotations

import os
import re
import signal
import subprocess  # nosec
from typing import Any

from ionbus_utils.base_utils import is_windows
from ionbus_utils.logging_utils import logger

# cSpell: words pids
# cSpell: ignore ppid killpg

spaces_re = re.compile(r"\s+", re.MULTILINE)
TimeoutExpired = subprocess.TimeoutExpired


def get_child_pids_linux(
    parent_pid: Any, include_parent: bool = True, recursive: bool = True
) -> list:
    """Returns a list lf all child process IDs in linux"""
    pid_output = subprocess.getoutput(
        f"ps -o pid --ppid {parent_pid} --noheaders"
    )
    pids = [x for x in spaces_re.split(pid_output) if x]
    if recursive:
        children = []
        for pid in pids:
            children.extend(
                get_child_pids_linux(pid, include_parent=False, recursive=True)
            )
        pids.extend(children)
    if include_parent:
        pids.insert(0, parent_pid)
    return [int(x) for x in pids]


def popen(
    command: str | list[str], pipe_output: bool = True
) -> subprocess.Popen:
    """Calls subprocess Popen appropriately for the given operating system.
    This is used when the process is not expected to return immediately.

    IMPORTANT: This command will run whatever commands are passed to this.
    Make sure these commands are properly vetted before being run."""
    pipe = subprocess.PIPE if pipe_output else None
    if is_windows():
        return subprocess.Popen(
            command,
            shell=True,  # nosec
            text=True,
            stdout=pipe,
            stderr=pipe,
        )
    # linux
    # pylint: disable=no-member
    # pylint: disable-next=no-member, E1101
    return subprocess.Popen(  # nosec
        command,
        shell=True,
        text=True,
        stdout=pipe,
        stderr=pipe,
        preexec_fn=os.setsid,  # type: ignore  # noqa: PLW1509
    )


def get_command_output(
    command: str,
    encoding: str | None = "utf-8",
) -> subprocess.CompletedProcess:
    """Runs command (waiting for it to finish) and returns output as
    subprocess CompletedProcess. "UTF-8" encoding is set by default
    (so stdout and stderr are strings and not bytes).
    Works on both Windows and Linux.

    IMPORTANT: This command will run whatever commands are passed to this.
    Make sure these commands are properly vetted before being run."""
    return subprocess.run(
        command,
        capture_output=True,
        check=False,
        shell=True,
        encoding=encoding,
    )


def get_command_output_as_string(
    command: str,
    encoding: str | None = "utf-8",
) -> str:
    """runs command (waiting for it to finihs) and returns output as string.

    IMPORTANT: This command will run whatever commands are passed to this.
    Make sure these commands are properly vetted before being run."""
    return get_command_output(command, encoding).stdout


def kill_proc(proc: subprocess.Popen, forcefully: bool = False) -> bool:
    """Tries to kill process.  Returns True if successful"""
    # TODO: Implement checking of successful
    if forcefully:
        raise NotImplementedError("Sorry, not yet.")
    success = True
    if is_windows():
        os.kill(proc.pid, signal.SIGTERM)
    else:
        # pylint: disable=no-member
        # pylint: disable-next=no-member, E1101
        os.killpg(proc.pid, signal.SIGTERM)  # type: ignore
    return success


def proc_still_running(proc: subprocess.Popen) -> bool:
    """Returns true if process is still running"""
    return proc.poll() is None


# pylint: disable=W1203
class SubProcessPopenObject:
    """A class to hole a subprocess Popen object that
    works both on linux and windows.

    This class is designed to help with long-running processes
    (more than a couple of seconds) that are started and then monitored.

    Sample Usage:
    proc = SubProcessPopenObject('some long running command')
    while proc.running:
        proc.check_process()
        time.sleep(5)
    # it's now done
    print(proc.stdout, '\n', proc.stderr)

    NOTE: Grabbing output on Windows is tricky.  It is recommended to
    run a .bat file that logs output."""

    def __init__(
        self,
        command: str | list[str],
        pipe_output: bool = True,
        verbose: bool = True,
    ):
        self.pipe_output = pipe_output
        self.running = True
        self.verbose = verbose
        self.exit_code = None
        self.stdout = ""
        self.stderr = ""
        self.command = command
        if self.verbose:
            logger.info(f"starting {command=}")
        self.spp_obj = popen(command, pipe_output)

    def terminate(self, forcefully: bool = False) -> bool:
        """Tries to kill subprocess"""
        return kill_proc(self.spp_obj, forcefully)

    def check_process(self) -> bool:
        """checks whether or not process is running.  Copies
        stdout/stderr if appropriate.

        Returns True if process is still running, otherwise False"""
        if not self.running:
            # We're already done.
            if self.verbose:
                logger.info("not running")
            return self.running
        # grab output if necessary
        if self.pipe_output:
            try:
                out, err = self.spp_obj.communicate(timeout=1)  # type: ignore
                self.stdout += out
                self.stderr += err
                if self.verbose:
                    logger.info(f"{len(self.stdout)=} {len(self.stderr)=}")
            except subprocess.TimeoutExpired:
                if self.verbose:
                    logger.info("no output")
        self.exit_code = self.spp_obj.poll()
        self.running = self.exit_code is None
        if self.verbose:
            logger.info(f"{self.exit_code=} {self.running=}")
        return self.running
