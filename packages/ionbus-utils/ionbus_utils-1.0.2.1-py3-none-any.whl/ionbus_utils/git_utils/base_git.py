"""Git utilities"""

from __future__ import annotations

# pylint: disable=W0611,C0411
# pylint: disable=logging-fstring-interpolation
# flake8: noqa F401
# cSpell: ignore unstaged, fstring
import argparse
import enum
import os
import re
import subprocess  # nosec
import sys
from pathlib import Path
from typing import ClassVar

from packaging.version import Version

from ionbus_utils.logging_utils import logger
from ionbus_utils.regex_utils import NEWLINE_RE
from ionbus_utils.subprocess_utils import get_command_output

VERBOSE = False
submodule_re = re.compile(r'^\[submodule "(\w+)"\]')
key_value_re = re.compile(r"^\s+(\w+)\s*=\s*(\S+)")
branch_re = re.compile(r"On branch (\w+)")
use_re = re.compile(r'\(use "git')
origin_main_re = re.compile(r"'origin/main'")
git_re = re.compile(r"^(git)\b", re.IGNORECASE)
git_locations_re = re.compile(r"^(\S+)\s*(\S+)\s\[(\S+?)\]\s*$")
not_repo_re = re.compile(r"not a git repository")
short_log_tag_re = re.compile(r"[\da-f]{6} \(.*?tag: ([^\),]+)")
short_log_comment_with_parens_re = re.compile(r"[\da-f]{6}.+?\) (.+)$")
hash_re = re.compile(r"#\w+")
space_re = re.compile(r"\s+")
tag_re = re.compile(r"^([^\-]+)")
backwhack_re = re.compile(r"\\")
status_lines_to_ignore_regex = [
    re.compile(x)
    for x in [
        r"^On branch",
        r'use "git',
        r"no changes added to commit",
        r"Your branch is up to date with ",
        r"working tree clean",
    ]
]


def set_git_verbose(val: bool) -> None:
    """Sets verbose mode for git utilities"""
    global VERBOSE  # pylint: disable=global-statement
    VERBOSE = val


def git_veerbose() -> bool:
    """Returns current verbose setting"""
    return VERBOSE


class TagVersion(enum.Enum):
    """Different Tag Version Updates"""

    MAJOR = 0
    MINOR = 1
    INCREMENTAL = 2
    FIX = 3
    RELEASE_CANDIDATE = enum.auto()
    PRODUCTION = enum.auto()


tv_parts = {
    TagVersion.MAJOR,
    TagVersion.MINOR,
    TagVersion.INCREMENTAL,
    TagVersion.FIX,
}


tag_regex_map = {
    TagVersion.MAJOR: re.compile(r"#Major", re.IGNORECASE),
    TagVersion.MINOR: re.compile(r"#Minor", re.IGNORECASE),
    TagVersion.INCREMENTAL: re.compile(r"#Inc", re.IGNORECASE),
    TagVersion.FIX: re.compile(r"#Bug|#fix", re.IGNORECASE),
    TagVersion.RELEASE_CANDIDATE: re.compile(r"#RC", re.IGNORECASE),
    TagVersion.PRODUCTION: re.compile(r"#Prod", re.IGNORECASE),
}


class BadStages(enum.Enum):
    """Different bad states a submodule could be in"""

    UNCOMMITTED = "changes to be committed"
    UNSTAGED = "changes not staged"
    UNTRACKED = "untracked files"
    DETACHED_HEAD = "Head detached - almost always OK"


git_regexes = {
    BadStages.UNCOMMITTED: re.compile(r"Changes to be committed"),
    BadStages.UNSTAGED: re.compile(r"Changes not staged"),
    BadStages.UNTRACKED: re.compile(r"Untracked files:"),
    BadStages.DETACHED_HEAD: re.compile(r"HEAD detached"),
}


class GitSubmodule:
    """Class that holds submodule info"""

    allowed: ClassVar[list[str]] = ["path", "url", "branch"]
    name: str
    path: str
    url: str
    branch: str | None = None

    def __init__(self, name: str):
        self.name = name

    def set(self, key: str, value: str) -> None:
        """sets key to value"""
        self.__dict__[key] = value

    def __str__(self):
        return str(self.__dict__)

    @staticmethod
    def output_dict(sm_dict: dict) -> str:
        """Converts dictionary of submodules into a string"""
        ret_str = ""
        for key, value in sm_dict.items():
            ret_str += f"{key} : {value}\n"
        return ret_str


def read_gitmodule_file(gm_file: str) -> dict:
    """reads submodule information"""
    submodules = {}
    sm = None
    with open(gm_file, encoding="ascii") as source:
        for line in source.readlines():
            match = submodule_re.search(line)
            if match:
                sm = GitSubmodule(match.group(1))
                submodules[sm.name] = sm
                continue
            match = key_value_re.search(line)
            if match and not sm:
                logger.warning("Equality line before submodule line")
                continue
            if match and sm:  # silly pylint
                sm.set(match.group(1), match.group(2))
    return submodules


def get_git_command_output_as_string(
    git_command: str,
    repo_dir: str | Path | None = None,
) -> str:
    """Switches to optional directory, grabs output of git command,
    switches back (if needed) to original directory, and returns output as
    string.

    NOTE: This assumes that a single git command is being used.  When `repo_dir`
    is used, "-C repo_dir" is passed to the command.
    """
    return get_git_command_output(git_command, repo_dir).stdout


def get_git_command_output(
    git_command: str,
    repo_dir: str | Path | None = None,
) -> subprocess.CompletedProcess:
    """Grabs output of git command and returns output as
    subprocess CompletedProcess. "UTF-8" encoding is set (so stdout and stderr
    are strings and not bytes).

    NOTE: This assumes that a single git command is being used.  When `repo_dir`
    is used, "-C repo_dir" is passed to the command.
    """
    if repo_dir:
        # The regex substitution can fail if there are random backwhacks
        # in repo_dir.  So make sure you have only forward slashes.
        git_command = git_re.sub(
            rf"\1 -C {backwhack_re.sub('/', str(repo_dir))}", git_command
        )
    return get_command_output(git_command, encoding="utf-8")


def run_many_git_commands(
    commands: list[str],
    repo_dir: str | Path | None = None,
    throw_on_error: bool = False,
    verbose: bool = False,
) -> tuple[bool, list[subprocess.CompletedProcess]]:
    results = []
    for cmd in commands:
        result = get_git_command_output(cmd, repo_dir)
        results.append(result)
        if result.returncode != 0:
            if throw_on_error:
                raise RuntimeError(f"Command failed: {cmd}")
            return False, results
        if verbose or VERBOSE:
            logger.info(f"Ran successfully: {cmd}")
    return True, results


def git_status_summary() -> str:
    """Returns summary of git status; will return empty string
    if there is nothing not committed."""
    full_status = get_git_command_output_as_string("git status")
    status = ""
    for line in NEWLINE_RE.split(full_status):
        # is this a blank line?
        if not line.strip():
            continue
        # Are we told to skip this line?
        skip = False
        for regex in status_lines_to_ignore_regex:
            if regex.search(line):
                skip = True
                break
        if skip:
            continue
        status += f"{line.rstrip()}\n"
    return status


def log_git_status():
    """Logs git information."""
    commit = get_git_command_output_as_string(
        "git log --pretty=oneline -1 --decorate"
    )
    # logger.info(f"{commit=}")
    lines = NEWLINE_RE.split(commit)
    git_status = lines[0]
    if status := git_status_summary():
        git_status += f"\n{status}"
    logger.info(f"Git status: {git_status}")


def git_branch_locations(repo_dir: str | None = None) -> dict | None:
    """Returns locations of git branches.  None if not a git repo"""
    output = get_git_command_output_as_string("git worktree list", repo_dir)
    if not_repo_re.search(output):
        return None
    git_map = {}
    for line in output.split("\n"):
        if not line.strip():
            continue
        match = git_locations_re.search(line)
        if match:
            git_map[match.group(3)] = match.group(1)
        else:
            logger.warning(f"Nope: {line}")
    return git_map


def get_submodule_status(base_dir: str, sm_dir: str) -> list | None:
    """Returns list of submodule readiness issues"""
    output = get_git_command_output_as_string(
        "git status", f"{base_dir}/{sm_dir}"
    )
    branch = None
    issues = set()
    for line in output.split("\n"):
        match = branch_re.search(line)
        if match:
            branch = match.group(1)
        for key, regex in git_regexes.items():
            if regex.search(line):
                issues.add(key.value)
    if branch != "main":
        if branch is None and BadStages.DETACHED_HEAD.value in issues:
            # this is not likely a problem
            issues.remove(BadStages.DETACHED_HEAD.value)
        else:
            issues.add(f"Not on main branch (on {branch})")
    if issues:
        return sorted(issues)
    return None


def all_submodule_status(base_dir: str) -> dict:
    """Returns status of submodules of the main repo.
    NOTE: This does (not yet?) investigate recursive submodules."""
    gm_file = f"{base_dir}/.gitmodules"
    results = {}
    # If there aren't submodules, then there's nothing further\
    # to check
    if not os.path.exists(gm_file):
        return results
    submodules = read_gitmodule_file(gm_file)
    for name, sm in submodules.items():
        status = get_submodule_status(base_dir, sm.path)
        if status:
            results[name] = status
        os.chdir(base_dir)
    return results


def get_current_branch(base_dir: str | None = None) -> str | None:
    """Return current branch checked out.  None if not git repo."""
    return _get_branch(get_git_command_output_as_string("git status", base_dir))


def _get_branch(git_status_output: str) -> str | None:
    branch = None
    for line in git_status_output.split("\n"):
        match = branch_re.search(line)
        if match:
            branch = match.group(1)
    return branch


def pushing_to_main(base_dir: str) -> bool:
    """returns true if branch is main or is pushing to origin/main"""
    git_status_output = get_git_command_output_as_string("git status", base_dir)
    branch = _get_branch(git_status_output)
    return (
        branch == "main" or origin_main_re.search(git_status_output) is not None
    )


def submodule_issues_as_string(issues: dict | None) -> str | None:
    """Nicely formatted submodules issues"""
    if issues is None:
        return None
    ret_str = ""
    for key, values in issues.items():
        ret_str += f"In submodule {key}:\n   * " + "\n   * ".join(values) + "\n"
    return ret_str


def get_latest_tag(
    repo_dir: str, num_prev_commits: int = 2, use_log: bool = False
) -> str | None:
    """Gets latest tag; returns None if not found in num_prev_commits"""
    if use_log:
        output = get_git_command_output_as_string(
            f"git log -{num_prev_commits} --oneline --decorate", repo_dir
        )
        for line in output.split("\n"):
            if not (match := short_log_tag_re.search(line)):
                continue
            return match.group(1)
    else:
        output = get_git_command_output_as_string(
            "git describe --tags", repo_dir
        )
        match = tag_re.search(output)
        if match:
            return match.group(1).strip()
    return None


# pylint: disable-next=too-many-branches
def auto_generate_tag(  # noqa: C901, PLR0912
    repo_dir: str, num_prev_commits: int = 2
) -> str:
    """Given tag of previous"""
    # In [52]: ver = Version('0.1.2.3rc1')
    #
    # In [53]: ver.release
    # Out[53]: (0, 1, 2, 3)
    #
    # In [54]: ver.pre
    # Out[54]: ('rc', 1)
    _ = num_prev_commits  # pylint
    output = get_git_command_output_as_string(
        "git log -1 --oneline --decorate", repo_dir
    )
    comment = ""
    prev_tag = None
    idx = 0
    for idx, line in enumerate(output.split("\n")):
        if not idx:
            comment = (
                comment_match.group(1)
                if (
                    comment_match := short_log_comment_with_parens_re.search(
                        line
                    )
                )
                else ""
            )
        if not (match := short_log_tag_re.search(line)):
            continue
        prev_tag = match.group(1)
        break

    if prev_tag:
        raise RuntimeError("head already tagged")
    prev_tag = get_latest_tag(repo_dir)
    if not prev_tag:
        raise RuntimeError("No previous tag found")
    version_obj = Version(prev_tag)
    version_list = list(version_obj.release)
    rc_tuple = version_obj.pre
    # Get tag version mode
    tg_mode = set()
    for word in space_re.split(comment):
        if not hash_re.search(word):
            continue
        found = [
            tv for tv, regex in tag_regex_map.items() if regex.search(word)
        ]
        if not found:
            raise RuntimeError(f"Unknown tag {word} found")
        tg_mode.update(found)
    mode_set = tg_mode.intersection(tv_parts)
    if not mode_set:
        # no explicit part mode, set Incremental
        mode_set = {TagVersion.INCREMENTAL}
    elif len(mode_set) > 1:
        raise RuntimeError(f"Too many modes set {[x.Name for x in mode_set]}")
    mode = next(iter(mode_set))
    if (
        TagVersion.RELEASE_CANDIDATE in tg_mode
        and TagVersion.PRODUCTION in tg_mode
    ):
        # seriously, make up your mind
        raise RuntimeError(
            "Must not use both RELEASE_CANDIDATE and PRODUCTION modes at "
            "the same time."
        )
    this_version = version_list[:]
    is_release_candidate = TagVersion.RELEASE_CANDIDATE in tg_mode or (
        TagVersion.PRODUCTION not in tg_mode and rc_tuple
    )
    # Update version unless this was an RC version.
    if not rc_tuple:
        if mode.value >= len(version_list):
            raise RuntimeError(f"Version {version_list} is too short")
        this_version[mode.value] += 1
        for index in range(mode.value + 1, len(this_version)):
            this_version[index] = 0
    version_str = ".".join([str(x) for x in this_version])
    if is_release_candidate:
        version_str += f"rc{rc_tuple[1] + 1 if rc_tuple else 1}"
    return version_str


def verify_ready_to_push(base_dir: str, verify_not_main: bool = True) -> None:
    """function to run to see if we're ready to push.
    Prints output and exits with error code if an issue is found."""
    branch = get_current_branch(base_dir)
    repo_dir = None
    if branch:
        branch_map = git_branch_locations(base_dir) or {}
        repo_dir = branch_map.get(branch)
    if not repo_dir:
        logger.warning(
            "Could not find branch.  Falling back to using hook location"
        )
        repo_dir = str(Path(base_dir).absolute())
    if VERBOSE:
        logger.info(f"{repo_dir=}")
    problem = False
    status = all_submodule_status(repo_dir)
    if verify_not_main and pushing_to_main(repo_dir):
        problem = True
        logger.warning("You are trying to push to main.")
    if status:
        problem = True
        logger.warning("There are submodules in non-production states.")
        logger.warning(submodule_issues_as_string(status))
    if problem:
        sys.exit(1)


def git_repo_status(repo_dir: str, log_results: bool = False) -> str:
    """Returns a string that shows  tag/commit hash of current repo as well
    as submodule status"""
    current_status = get_git_command_output_as_string(
        'git log -1 --format="%H"', repo_dir
    )
    submodule_status = get_git_command_output_as_string(
        "git submodule status --recursive", repo_dir
    )
    latest_tag = get_git_command_output_as_string(
        "git tag --sort=committerdate", repo_dir
    )
    remote_url = get_git_command_output_as_string(
        "git ls-remote --get-url", repo_dir
    )
    tag = latest_tag.rstrip().split("\n")[-1]  # Grab most recent tag
    if tag:
        tag = f"- tag {tag}"
    repo_path = Path(repo_dir).absolute()
    current = (
        f"current directory: {repo_path}\n   remote url: {remote_url}\n"
        f"   checksum: {current_status.rstrip()} {tag}\n"
        f"   submodules:\n"
    )
    pieces = submodule_status.split("\n")
    for piece in pieces:
        bits = piece.split(" ")
        if len(bits) < 3:  # noqa: PLR2004
            continue
        while (
            "/" in bits[-2]
        ):  # for every level of submodule we go down: add indent and remove
            # parent repo
            bits[-2] = bits[-2].split("/", 1)[-1]
            current += "    "
            # submodule - commit
        current += f"       {bits[-2]} : {bits[-3]}\n"
    if log_results:
        logger.info(f"Git status:\n{current}")
    return current


def git_arg_parser() -> argparse.ArgumentParser:
    """Argument parser for git utilities"""
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify_push", action="store_true")
    parser.add_argument("--branch_locations", action="store_true")
    parser.add_argument("--repo_status", action="store_true")
    parser.add_argument("--auto-tag", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("args", type=str, nargs="*")
    return parser


def main_git_func(args: argparse.Namespace) -> None:
    """main function"""
    if args.verify_push:
        path = args.args[0] if args.args else "."
        verify_ready_to_push(path)
    elif args.branch_locations:
        path = args.args[0] if args.args else "."
        local_results = git_branch_locations(path)
        logger.info(f"Branch locations: {local_results}")
    elif args.repo_status:
        path = args.args[0] if args.args else "."
        git_repo_status(path, log_results=True)
    elif args.auto_tag:
        path = args.args[0] if args.args else "."
