"""Tests for git_utils modules with external calls mocked."""

from __future__ import annotations

import argparse
import types
import site
from pathlib import Path

import pytest

parent_dir = Path(__file__).absolute().parent.parent.parent
site.addsitedir(str(parent_dir))

from ionbus_utils.git_utils import base_git as bg  # noqa: E402
from ionbus_utils.git_utils.deploy import _clean_branch_name, get_repo_name  # noqa: E402


def test_get_repo_name_handles_ssh_and_https():
    """Repository name extraction works for common URL formats."""
    assert get_repo_name("git@github.com:org/repo.git") == "repo"
    assert get_repo_name("https://github.com/org/repo") == "repo"


def test_clean_branch_name_replaces_non_letters():
    """Branch names are sanitized for filesystem usage."""
    assert _clean_branch_name("feat/new-stuff") == "feat_new_stuff"


def test_run_many_git_commands_success(monkeypatch):
    """run_many_git_commands returns True when all commands succeed."""
    calls = []

    def fake_get(cmd, repo_dir=None, encoding=None):
        calls.append(cmd)
        return types.SimpleNamespace(returncode=0)

    monkeypatch.setattr(bg, "get_command_output", fake_get)
    ok, results = bg.run_many_git_commands(["git status", "git pull"])
    assert ok is True
    assert calls == ["git status", "git pull"]
    assert len(results) == 2


def test_run_many_git_commands_throws_on_error(monkeypatch):
    """run_many_git_commands raises when throw_on_error=True and a command fails."""
    def fake_get(cmd, repo_dir=None, encoding=None):
        rc = 1 if "bad" in cmd else 0
        return types.SimpleNamespace(returncode=rc)

    monkeypatch.setattr(bg, "get_command_output", fake_get)
    with pytest.raises(RuntimeError):
        bg.run_many_git_commands(["good", "bad"], throw_on_error=True)


def test_git_branch_locations_not_repo(monkeypatch):
    """git_branch_locations returns None when not a git repo."""
    monkeypatch.setattr(bg, "get_git_command_output_as_string", lambda cmd, repo_dir=None: "not a git repository")
    assert bg.git_branch_locations() is None


def test_git_branch_locations_parses(monkeypatch):
    """git_branch_locations parses worktree output."""
    output = "C:/repo main [origin/main]\n"
    monkeypatch.setattr(bg, "get_git_command_output_as_string", lambda cmd, repo_dir=None: output)
    mapping = bg.git_branch_locations()
    assert mapping == {"origin/main": "C:/repo"}


def test_git_arg_parser_flags():
    """git_arg_parser builds parser with expected options."""
    parser = bg.git_arg_parser()
    args = parser.parse_args(["--verbose"])
    assert args.verbose is True


def test_auto_generate_tag_increments_minor(monkeypatch):
    """auto_generate_tag increments version per hash tag."""
    log_output = "abc123 (HEAD -> dev) #Minor fix\n"
    describe_output = "1.2.3\n"

    def fake_git_output(cmd, repo_dir=None):
        if cmd.startswith("git log"):
            return log_output
        if cmd.startswith("git describe"):
            return describe_output
        return ""

    monkeypatch.setattr(bg, "get_git_command_output_as_string", fake_git_output)
    tag = bg.auto_generate_tag("dummy")
    assert tag == "1.3.0"
