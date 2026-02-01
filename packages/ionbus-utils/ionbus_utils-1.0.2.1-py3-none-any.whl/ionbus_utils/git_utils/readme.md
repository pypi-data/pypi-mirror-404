# git_utils

Utilities for working with Git repositories, submodules, tags, and branch
management.

<!-- TOC start (generated with https://bitdowntoc.derlin.ch/) -->

- [Functions](#functions)
   * [Command Execution](#command-execution)
      + [`get_git_command_output_as_string(git_command, repo_dir=None)`](#get_git_command_output_as_stringgit_command-repo_dirnone)
      + [`get_git_command_output(git_command, repo_dir=None)`](#get_git_command_outputgit_command-repo_dirnone)
      + [`run_many_git_commands(commands, repo_dir=None, throw_on_error=False, verbose=False)`](#run_many_git_commandscommands-repo_dirnone-throw_on_errorfalse-verbosefalse)
   * [Status & Branch Information](#status-branch-information)
      + [`git_status_summary()`](#git_status_summary)
      + [`log_git_status()`](#log_git_status)
      + [`get_current_branch(base_dir=None)`](#get_current_branchbase_dirnone)
      + [`pushing_to_main(base_dir)`](#pushing_to_mainbase_dir)
      + [`git_branch_locations(repo_dir=None)`](#git_branch_locationsrepo_dirnone)
      + [`git_repo_status(repo_dir, log_results=False)`](#git_repo_statusrepo_dir-log_resultsfalse)
   * [Tag Management](#tag-management)
      + [`get_latest_tag(repo_dir, num_prev_commits=2, use_log=False)`](#get_latest_tagrepo_dir-num_prev_commits2-use_logfalse)
      + [`auto_generate_tag(repo_dir, num_prev_commits=2)`](#auto_generate_tagrepo_dir-num_prev_commits2)
   * [Submodule Management](#submodule-management)
      + [`read_gitmodule_file(gm_file)`](#read_gitmodule_filegm_file)
      + [`get_submodule_status(base_dir, sm_dir)`](#get_submodule_statusbase_dir-sm_dir)
      + [`all_submodule_status(base_dir)`](#all_submodule_statusbase_dir)
      + [`submodule_issues_as_string(issues)`](#submodule_issues_as_stringissues)
   * [Pre-Push Verification](#pre-push-verification)
      + [`verify_ready_to_push(base_dir, verify_not_main=True)`](#verify_ready_to_pushbase_dir-verify_not_maintrue)
- [Classes](#classes)
   * [`BadStages`](#badstages)
   * [`TagVersion`](#tagversion)
   * [`GitSubmodule`](#gitsubmodule)
- [Command Line Usage](#command-line-usage)
- [auto_tag.py](#auto_tagpy)
   * [Usage](#usage)
   * [Arguments](#arguments)
   * [Workflow](#workflow)
   * [Examples](#examples)
   * [Version Hashtags](#version-hashtags)


## Functions

### Command Execution

#### `get_git_command_output_as_string(git_command, repo_dir=None)`
Execute a git command and return the output as a string.

```python
output = get_git_command_output_as_string("git status", "/path/to/repo")
```

#### `get_git_command_output(git_command, repo_dir=None)`
Execute a git command and return a `subprocess.CompletedProcess` object.

#### `run_many_git_commands(commands, repo_dir=None, throw_on_error=False, verbose=False)`
Run multiple git commands sequentially. Returns a tuple of
`(success: bool, results: list[CompletedProcess])`.

```python
success, results = run_many_git_commands([
    "git add .",
    "git commit -m 'update'",
    "git push"
], repo_dir="/path/to/repo")
```

### Status & Branch Information

#### `git_status_summary()`
Returns a filtered summary of `git status`, excluding boilerplate lines.
Returns an empty string if the working tree is clean.

#### `log_git_status()`
Logs the current git commit and status information to the logger.

#### `get_current_branch(base_dir=None)`
Returns the name of the currently checked-out branch, or `None` if not a
git repository.

#### `pushing_to_main(base_dir)`
Returns `True` if the current branch is `main` or is set to push to
`origin/main`.

#### `git_branch_locations(repo_dir=None)`
Returns a dictionary mapping branch names to their worktree locations.
Returns `None` if not a git repository.

#### `git_repo_status(repo_dir, log_results=False)`
Returns a detailed string showing the current commit hash, latest tag,
remote URL, and recursive submodule status.

### Tag Management

#### `get_latest_tag(repo_dir, num_prev_commits=2, use_log=False)`
Returns the latest git tag, or `None` if not found.

```python
tag = get_latest_tag(".")  # e.g., "1.2.3"
```

#### `auto_generate_tag(repo_dir, num_prev_commits=2)`
Automatically generates the next version tag based on commit message
hashtags:

| Hashtag | Effect |
|---------|--------|
| `#Major` | Increment major version (X.0.0.0) |
| `#Minor` | Increment minor version (0.X.0.0) |
| `#Inc` | Increment incremental version (0.0.X.0) |
| `#Bug` / `#Fix` | Increment fix version (0.0.0.X) |
| `#RC` | Mark as release candidate (e.g., 1.2.3rc1) |
| `#Prod` | Remove RC suffix for production release |

### Submodule Management

#### `read_gitmodule_file(gm_file)`
Parses a `.gitmodules` file and returns a dictionary of `GitSubmodule`
objects.

#### `get_submodule_status(base_dir, sm_dir)`
Returns a list of issues for a specific submodule, or `None` if clean.

#### `all_submodule_status(base_dir)`
Returns a dictionary of all submodules with issues. Empty dict if all
submodules are clean.

#### `submodule_issues_as_string(issues)`
Formats submodule issues dictionary into a human-readable string.

### Pre-Push Verification

#### `verify_ready_to_push(base_dir, verify_not_main=True)`
Checks if the repository is ready to push. Exits with error code 1 if:
- Pushing directly to `main` branch (when `verify_not_main=True`)
- Submodules have uncommitted changes, unstaged changes, or untracked files

## Classes

### `BadStages`
Enum representing problematic submodule states:
- `UNCOMMITTED` - Changes staged but not committed
- `UNSTAGED` - Changes not staged for commit
- `UNTRACKED` - Untracked files present
- `DETACHED_HEAD` - HEAD is detached (usually OK)

### `TagVersion`
Enum for version update types:
- `MAJOR`, `MINOR`, `INCREMENTAL`, `FIX`
- `RELEASE_CANDIDATE`, `PRODUCTION`

### `GitSubmodule`
Data class holding submodule information:
- `name` - Submodule name
- `path` - Submodule path
- `url` - Remote URL
- `branch` - Tracked branch (optional)

## Command Line Usage

The module can be run directly with these flags:

```bash
python -m ionbus_utils.git_utils --verify_push [path]
python -m ionbus_utils.git_utils --branch_locations [path]
python -m ionbus_utils.git_utils --repo_status [path]
python -m ionbus_utils.git_utils --auto-tag [path]
python -m ionbus_utils.git_utils --verbose
```

## auto_tag.py

Standalone script that automatically generates, creates, and pushes a git tag
based on commit message hashtags.

### Usage

```bash
python -m ionbus_utils.git_utils.auto_tag <repo_dir> [options]
```

### Arguments

| Argument | Description |
|----------|-------------|
| `repo_dir` | Path to the git repository (default: `.`) |
| `--debug` | Run without exception handling wrapper |
| `--name-only` | Only print the generated tag name, don't create or push |
| `--throw-on-failure` | Raise exception if pushing tags fails |

### Workflow

1. Calls `auto_generate_tag()` to compute the next version from commit message
2. Creates an annotated git tag: `git tag -a <version> -m "auto-tag <version>"`
3. Pushes the tag to remote: `git push --tags`

### Examples

```bash
# Generate and push a new tag
python -m ionbus_utils.git_utils.auto_tag .

# Preview what tag would be created (without creating it)
python -m ionbus_utils.git_utils.auto_tag . --name-only

# With full error propagation
python -m ionbus_utils.git_utils.auto_tag /path/to/repo --throw-on-failure
```

### Version Hashtags

Include these hashtags in your commit message to control versioning:

- `#Major` - Bump major version (1.0.0 -> 2.0.0)
- `#Minor` - Bump minor version (1.0.0 -> 1.1.0)
- `#Inc` - Bump incremental version (1.0.0 -> 1.0.1) **(default)**
- `#Bug` / `#Fix` - Bump fix version (1.0.0.0 -> 1.0.0.1)
- `#RC` - Create release candidate (1.0.0 -> 1.0.1rc1)
- `#Prod` - Promote RC to production (1.0.1rc1 -> 1.0.1)