"""Tests for subprocess_utils module."""

from __future__ import annotations

import types
import site
from pathlib import Path

import pytest

parent_dir = Path(__file__).absolute().parent.parent.parent
site.addsitedir(str(parent_dir))

from ionbus_utils import subprocess_utils as su  # noqa: E402


def test_get_child_pids_linux(monkeypatch):
    """Parses ps output and recurses for descendants."""
    outputs = {"100": "101\n102", "102": "103"}

    def fake_getoutput(cmd):
        parts = cmd.split()
        parent = parts[parts.index("--ppid") + 1]
        return outputs.get(parent, "")

    monkeypatch.setattr(su, "is_windows", lambda: False)
    monkeypatch.setattr(su.subprocess, "getoutput", fake_getoutput)
    pids = su.get_child_pids_linux("100")
    assert set(pids) == {100, 101, 102, 103}


def test_get_command_output(monkeypatch):
    """get_command_output delegates to subprocess.run with expected arguments."""
    called = {}

    def fake_run(command, capture_output, check, shell, encoding):
        called["command"] = command
        assert capture_output and not check and shell and encoding == "utf-8"
        return types.SimpleNamespace(stdout="out", stderr="err", returncode=0)

    monkeypatch.setattr(su.subprocess, "run", fake_run)
    result = su.get_command_output("echo hi")
    assert result.stdout == "out"
    assert called["command"] == "echo hi"


def test_get_command_output_as_string(monkeypatch):
    """Returns stdout string from completed process."""
    monkeypatch.setattr(
        su, "get_command_output", lambda command, encoding=None: types.SimpleNamespace(stdout="hello")
    )
    assert su.get_command_output_as_string("echo") == "hello"


def test_kill_proc_windows(monkeypatch):
    """kill_proc uses os.kill on Windows."""
    calls = []
    monkeypatch.setattr(su, "is_windows", lambda: True)
    monkeypatch.setattr(su.os, "kill", lambda pid, sig: calls.append((pid, sig)))
    proc = types.SimpleNamespace(pid=123)
    su.kill_proc(proc)
    assert calls and calls[0][0] == 123


def test_kill_proc_linux(monkeypatch):
    """kill_proc uses os.killpg on Linux."""
    calls = []
    monkeypatch.setattr(su, "is_windows", lambda: False)
    monkeypatch.setattr(
        su.os, "killpg", lambda pid, sig: calls.append((pid, sig)), raising=False
    )
    proc = types.SimpleNamespace(pid=321)
    su.kill_proc(proc)
    assert calls and calls[0][0] == 321


def test_proc_still_running():
    """proc_still_running returns True when poll is None."""
    proc = types.SimpleNamespace(poll=lambda: None)
    assert su.proc_still_running(proc) is True


def test_subprocess_popen_object(monkeypatch):
    """SubProcessPopenObject monitors process and captures output."""

    class FakePopen:
        def __init__(self, *args, **kwargs):
            self.pid = 1
            self._called = 0

        def communicate(self, timeout):
            self._called += 1
            if self._called == 1:
                raise su.subprocess.TimeoutExpired(cmd="cmd", timeout=timeout)
            return "out", "err"

        def poll(self):
            return None if self._called < 2 else 0

    monkeypatch.setattr(su, "popen", lambda *args, **kwargs: FakePopen())
    obj = su.SubProcessPopenObject("cmd", pipe_output=True, verbose=False)
    assert obj.running is True
    obj.check_process()
    obj.check_process()
    assert obj.running is False
    assert obj.stdout == "out"
    assert obj.stderr == "err"
