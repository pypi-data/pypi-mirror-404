"""Command line git deploy functionality"""

from __future__ import annotations

import argparse
import json
import os
import site

from pathlib import Path
from urllib.parse import urlparse
import numpy as np

site.addsitedir(str(Path(__file__).absolute().parent.parent.parent))

import ionbus_utils.git_utils.base_git as bg
from ionbus_utils.general import load_json, temporarily_change_dir
from ionbus_utils.general_classes import ArgParseRangeAction
from ionbus_utils.logging_utils import logger
from ionbus_utils.regex_utils import NON_LETTER_LIKE_RE


DEFAULT_BRANCH = "dev"
DEFAULT_PATH: Path | None = None


class OneOrTwoAction(argparse.Action):
    def __call__(
        self,
        parser: argparse.ArgumentParser,
        namespace: argparse.Namespace,
        values: list[str],
        option_string: str | None = None,
    ):
        if len(values) < 1 or len(values) > 2:
            error = f"{self.dest} requires 1 or 2 arguments"
            parser.error(error)
            raise RuntimeError(error)
        setattr(namespace, self.dest, values)


def deploy_arg_parser() -> argparse.ArgumentParser:
    """Argument parser for git utilities"""
    _setup_defaults()
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "repo_path",
        type=str,
        nargs="?",
        default=None,
    )
    parser.add_argument(
        "--base-path",
        type=str,
        help="Base path for new repo - only used with --create",
    )
    parser.add_argument(
        "--create",
        type=str,
        action=ArgParseRangeAction,
        max_args=2,
        help="Clone new repo for the first time. git url must be provided",
    )
    parser.add_argument(
        "--pull-latest",
        type=str,
        action=ArgParseRangeAction,
        min_args=0,
        max_args=1,
        help="Pull latest changes from the remote repository. Branch name "
        "should be provided if not the default branch.",
        default=None,
    )
    parser.add_argument(
        "--new-branch",
        type=str,
        action=ArgParseRangeAction,
        max_args=2,
        help="Create a new branch in the repository. If a single name is "
        "provided, this branch much already exist.  If two names are provided, "
        "the second name is from where the branch will be copied. If the "
        "second name is `.`, the branch will be copied from the default "
        "branch.",
        default=None,
    )
    parser.add_argument(
        "--simple",
        action="store_true",
        help="When creating a new repo area, use simplified directory "
        "structure. Note that --pull-latest will not work with this option.",
    )
    parser.add_argument(
        "--push-new-branch",
        action="store_true",
        help="Push the new branch to the remote repository.  Only used "
        "with --new-branch when copying from an existing branch.",
    )
    parser.add_argument(
        "--default-branch",
        type=str,
        default=DEFAULT_BRANCH,
    )
    parser.add_argument(
        "--umask",
        type=str,
        default="007",
        help="Set the file permissions mask for the new branch.",
    )
    return parser


def get_base_and_info(args: argparse.Namespace) -> tuple[Path, dict]:
    """Get the base directory of the git repository."""
    # set umask.  This is a no-op on Windows.
    umask_str = args.umask
    while len(umask_str) < 3:
        umask_str = "0" + umask_str
    os.umask(int(umask_str, 8))
    if (create := args.create) and args.simple:
        # do simple thing
        if DEFAULT_PATH is None:
            raise ValueError(
                "ionbus_CODE_DIR environment variable must be set when "
                "using --simple"
            )
        return DEFAULT_PATH, {
            "git_url": create[0],
            "default_branch": args.default_branch,
            "local_dir": (
                get_repo_name(create[0]) if len(create) == 1 else create[1]
            ),
        }
    if args.repo_path and args.create:
        raise ValueError("Cannot provide both `--repo-path` and `--create`")
    #
    if args.repo_path:
        repo_path = Path(args.repo_path)
        if not repo_path.is_absolute():
            if DEFAULT_PATH is None:
                raise ValueError(
                    "Relative path provided but ionbus_CODE_DIR environment "
                    "variable not set"
                )
            repo_path = Path(DEFAULT_PATH) / repo_path
        info_path = repo_path / "repo_info.json"
        if info_path.exists():
            info = load_json(info_path)
            info["simple"] = False
        elif (repo_path / ".git").is_dir():
            info = {"simple": True}
        else:
            raise RuntimeError(
                f"repo_info.json not found in {repo_path} and not a git "
                f"directory."
            )
        return repo_path, info
    if not create:
        raise RuntimeError(
            "Must provide `--repo-path` when not using `--create`"
        )

    base_dir = args.base_path or DEFAULT_PATH
    if not base_dir:
        raise ValueError(
            "Must provide `--base-path` when not using ionbus_CODE_DIR "
            "environment variable with --create"
        )
    local_dir = get_repo_name(create[0]) if len(create) == 1 else create[1]
    ret_path = Path(base_dir) / local_dir
    if ret_path.exists():
        raise RuntimeError(
            f"Directory {ret_path} already exists.  Cannot --create."
        )
    ret_path.mkdir(parents=True, exist_ok=True)
    info = {
        "git_url": create[0],
        "default_branch": args.default_branch,
    }
    with open(ret_path / "repo_info.json", "w", encoding="UTF-8") as outfile:
        json.dump(info, outfile, indent=4)
    return ret_path, info


def main_deploy_func(args: argparse.Namespace) -> None:
    """main deploy function"""
    repo_path, info = get_base_and_info(args)

    if (
        count := np.sum(
            [
                args.create is not None,
                args.pull_latest is not None,
                args.new_branch is not None,
            ]
        )
        != 1
    ):
        raise ValueError(
            f"Must provide exactly one of --create or --pull-latest.  You "
            f"provided {count}."
        )
    with temporarily_change_dir(repo_path):
        if args.create:
            return create_new_repo(args, repo_path, info)
        if args.pull_latest is not None:
            return pull_latest(args, repo_path, info)
        if (new_branch := args.new_branch) is not None:
            return setup_new_branch(args, repo_path, info, new_branch)
    raise RuntimeError("No argument provided")


def get_repo_name(git_url: str) -> str:
    """
    Extract repository name from a git remote URL.
    """
    # Handle SSH format (git@...)
    if git_url.startswith("git@"):
        # Split on colon and take the part after it
        path = git_url.split(":", 1)[1]
    else:
        # Handle HTTPS format
        parsed = urlparse(git_url)
        path = parsed.path

    # Extract the basename and remove .git extension if present
    repo_name = Path(path).name
    if repo_name.endswith(".git"):
        repo_name = repo_name[:-4]

    return repo_name


def create_new_repo(
    args: argparse.Namespace,
    repo_path: Path,
    info: dict,
) -> None:
    """Creates new directory structure and clones repo"""
    if (
        not (branch := info.get("default_branch", DEFAULT_BRANCH))
        and not args.simple
    ) or not (git_url := info.get("git_url")):
        raise ValueError(
            "Must provide git_url and default_branch in repo_info.json"
        )
    branch_dir = (
        info["local_dir"] if args.simple else _clean_branch_name(branch)
    )
    cmd = f"git clone --branch {branch} {git_url} {branch_dir}"
    response = bg.get_git_command_output(cmd)
    if response.returncode != 0:
        logger.error(response.stderr)
        raise RuntimeError(
            f"Unable to clone {git_url} branch {branch} in {repo_path}"
        )
    success, responses = bg.run_many_git_commands(
        ["git submodule update --init --recursive"],
        repo_dir=branch_dir,
        throw_on_error=True,
        verbose=True,
    )
    logger.info(f"cloned {git_url} branch {branch} in {repo_path / branch_dir}")


def pull_latest(
    args: argparse.Namespace,
    repo_path: Path,
    info: dict,
) -> None:
    """Pulls latest changes from remote repository"""
    if info.get("simple"):
        raise RuntimeError("--pull-latest not supported with --simple option")
    branch = (
        args.pull_latest[0]
        if args.pull_latest
        else info.get("default_branch", "dev")
    )
    branch_dir = _clean_branch_name(branch)
    branch_path = repo_path / branch_dir
    if not branch_path.exists():
        raise RuntimeError(
            f"Branch path {branch_path} does not exist.  Cannot pull."
        )
    success, responses = bg.run_many_git_commands(
        [
            "git stash",
            f"git checkout {branch}",
            f"git pull origin {branch}",
            "git submodule update --init --recursive",
        ],
        repo_dir=branch_path,
        throw_on_error=True,
        verbose=True,
    )
    logger.info(
        f"Successfully pulled latest changes in {repo_path} "
        f"for {branch} branch."
    )


def setup_new_branch(
    args: argparse.Namespace,
    repo_path: Path,
    info: dict,
    new_branch: list[str],
) -> None:
    """Creates a new branch checkout"""
    if info.get("simple"):
        return setup_simple_branch(args, repo_path, info, new_branch)
    if (copy_branch := len(new_branch) == 2) and new_branch[1] == ".":
        new_branch[1] = info.get("default_branch", "dev")
    new_branch_name = new_branch[0]
    new_branch_dir = _clean_branch_name(new_branch_name)
    if (repo_path / new_branch_dir).exists():
        raise RuntimeError(
            f"New branch directory {new_branch_dir} already exists."
        )
    git_url = info.get("git_url")
    if not git_url:
        raise RuntimeError("git_url not found in repo_info.json")
    from_branch_name = new_branch[1 if len(new_branch) == 2 else 0]
    commands = [
        f"git clone --branch {from_branch_name} {git_url} {new_branch_dir}"
    ]
    success, responses = bg.run_many_git_commands(
        commands,
        throw_on_error=True,
        verbose=True,
    )
    if not copy_branch:
        # Done!
        logger.info(
            f"Cloned new branch {new_branch_name} in {repo_path} to "
            f"{new_branch_dir}"
        )
        return
    _finish_new_branch_setup(
        args,
        repo_path,
        new_branch,
        new_branch_name,
        from_branch_name,
        new_branch_dir,
    )


def _finish_new_branch_setup(
    args: argparse.Namespace,
    repo_path: Path,
    new_branch: list[str],
    new_branch_name: str,
    from_branch_name: str,
    new_branch_dir: str,
) -> None:
    commands = [
        "git submodule update --init --recursive",
    ]
    if len(new_branch) > 1:
        commands.append(f"git checkout -b {new_branch_name}")
    if args.push_new_branch:
        commands.append(f"git push -u origin {new_branch_name}")
    commands.append("git submodule update --init --recursive")
    success, responses = bg.run_many_git_commands(
        commands,
        repo_dir=repo_path / new_branch_dir,
        throw_on_error=True,
        verbose=True,
    )
    logger.info(
        f"Created new branch {new_branch_name} in {repo_path} from "
        f"{from_branch_name}."
    )


def setup_simple_branch(
    args: argparse.Namespace,
    repo_path: Path,
    info: dict,
    new_branch: list[str],
) -> None:
    """Sets up new branch `repo_path`_branch"""
    result = bg.get_git_command_output("git config --get remote.origin.url")
    if result.returncode != 0:
        raise RuntimeError(
            f"Unable to get remote.origin.url in {repo_path}.  Cannot create "
            f"new branch."
        )
    git_url = result.stdout.strip()
    new_branch_name = new_branch[0]
    clean_branch_name = _clean_branch_name(new_branch_name)
    branch = new_branch[-1]
    path = f"{repo_path}_{clean_branch_name}"
    success, responses = bg.run_many_git_commands(
        [
            f"git clone --branch {branch} {git_url} {path}",
        ],
        throw_on_error=True,
        verbose=True,
    )
    from_branch_name = new_branch[1 if len(new_branch) == 2 else 0]
    _finish_new_branch_setup(
        args,
        repo_path,
        new_branch,
        new_branch_name,
        from_branch_name,
        path,
    )


def _setup_defaults() -> None:
    """Sets the default branch from environment variable if it exists"""
    global DEFAULT_BRANCH, DEFAULT_PATH  # pylint: disable=global-statement
    if "IBU_GIT_DEFAULT_BRANCH" in os.environ:
        DEFAULT_BRANCH = os.environ["IBU_GIT_DEFAULT_BRANCH"]
    elif os.environ.get("ENVIRONMENT", "").lower() == "production":
        DEFAULT_BRANCH = "release"
    else:
        DEFAULT_BRANCH = "dev"
    DEFAULT_PATH = (
        Path(value)
        if (value := os.environ.get("IONBUS_CODE_DIR", None))
        else None
    )


def _clean_branch_name(branch: str) -> str:
    """Cleans branch name to be used in git commands"""
    return NON_LETTER_LIKE_RE.sub("_", branch)


if __name__ == "__main__":
    parser = deploy_arg_parser()
    local_args = parser.parse_args()
    main_deploy_func(local_args)
