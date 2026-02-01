"""Group membership utilities."""

from __future__ import annotations

import getpass
import os
import subprocess as sp
from ionbus_utils.base_utils import is_windows

if not (IS_WINDOWS := is_windows()):
    # pylint: disable-msg=E0401
    import grp
    import pwd
else:
    pwd = None


def get_user_name(upper_case: bool = True) -> str | None:
    """Returns current users username.  On a container, this may
    return None"""
    try:
        username = getpass.getuser()
        if upper_case:
            return username.upper()
        return username.lower()
    except:  # noqa: E722
        return None


def get_group_members(group_name: str) -> list[str]:
    """Get the members of a group. Returns empty list if group does
    not exist."""
    if IS_WINDOWS:
        # Windows
        cp = sp.run(
            f'powershell.exe "Get-ADGroupMember -Identity '
            f'{group_name} | select SamAccountName"',
            capture_output=True,
            check=False,
            shell=True,
            encoding="utf-8",
        )
        return [x.strip() for x in cp.stdout.split("\n")[3:] if x.strip()]
    try:
        group_info = grp.getgrnam(group_name)  # type: ignore
        return group_info.gr_mem
    except KeyError:
        return []


def get_groups_for_user(username: str) -> list[str]:
    """Returns the groups a user is a member of. Returns empty list if
    user does not exist."""
    if IS_WINDOWS:
        # Windows
        cp = sp.run(
            f'powershell.exe "Get-ADPrincipalGroupMembership {username}'
            f' | select Name"',
            capture_output=True,
            check=False,
            shell=True,
            encoding="utf-8",
        )
        return [x.strip() for x in cp.stdout.split("\n")[3:] if x.strip()]
    # linux
    if (uid := _get_uid_for_username_linux_only(username)) is None:
        return []
    user = pwd.getpwuid(uid)  # type: ignore
    # pylint: disable-next=E1101
    group_ids = os.getgrouplist(user.pw_name, user.pw_gid)  # type: ignore
    return [grp.getgrgid(g).gr_name for g in group_ids]  # type: ignore


def _get_uid_for_username_linux_only(username: str) -> int | None:
    """Gets uid for username. Only works on linux."""
    try:
        user_info = pwd.getpwnam(username)  # type: ignore
        return user_info.pw_uid
    except KeyError:
        return None
