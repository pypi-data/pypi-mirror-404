"""Automatically generates and tags release."""

import argparse
import os
import site
from pathlib import Path

site.addsitedir(str(Path(__file__).absolute().parent.parent.parent))

# pylint: disable=W0611,C0411,E0402
# pylint: disable=W1203,C0413
# flake8: noqa F401
# ruff: noqa: F401,E402

from ionbus_utils.exceptions import log_exception
from ionbus_utils.git_utils import (
    auto_generate_tag,
    get_git_command_output,
    get_git_command_output_as_string,
)
from ionbus_utils.logging_utils import logger


def main(args: argparse.Namespace) -> None:
    """Main function."""
    tag = auto_generate_tag(args.repo_dir)
    logger.info(f"{tag=}")
    if args.name_only:
        return
    tag_output = get_git_command_output(
        f'git tag -a {tag} -m "auto-tag {tag}"', args.repo_dir
    )
    logger.info(f"Tagging output {tag_output.returncode=} {tag_output.stderr=}")
    if tag_output.returncode:
        raise RuntimeError("Tagging failed")
    output = get_git_command_output("git push --tags", args.repo_dir)
    if output.stderr:
        logger.warning(f"STDERR: {output.stderr}")
    if output.returncode:
        logger.warning(f"Pushing tags failed {output.returncode}")
        if args.throw_on_failure:
            raise RuntimeError("Pushing tags failed")


def setup_args() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("repo_dir", type=str, default=".")
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--name-only", action="store_true")
    parser.add_argument("--throw-on-failure", action="store_true")
    return parser


if __name__ == "__main__":
    args_obj = setup_args().parse_args()
    if args_obj.debug:
        # only send to person running when debugging
        main(args_obj)
    else:
        try:
            main(args_obj)
        # pylint: disable-next=broad-exception-caught
        except Exception as excp:
            log_exception(excp)
            if alias := os.environ.get("OPS_GENIE_ALIAS"):
                excp_message = repr(excp)
            raise excp
