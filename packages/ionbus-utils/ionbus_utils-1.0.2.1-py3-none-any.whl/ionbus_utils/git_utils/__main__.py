"""main function for git utils"""

from __future__ import annotations

from ionbus_utils.git_utils.base_git import (
    git_arg_parser,
    main_git_func,
    set_git_verbose,
)

if __name__ == "__main__":
    parser = git_arg_parser()
    local_args = parser.parse_args()
    if local_args.verbose:
        set_git_verbose(True)
    main_git_func(local_args)
