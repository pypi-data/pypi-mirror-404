"""Utilities for creating and updating authentication files."""

from __future__ import annotations

import argparse
from typing import TypeVar
import json
import getpass
import os
import site
from pathlib import Path

site.addsitedir(str(Path(__file__).absolute().parent.parent.parent))

from ionbus_utils.crypto_utils.crypto_utils import (
    decrypt_password,
    encrypt_password,
    generate_key,
)
from ionbus_utils.exceptions import log_exception
from ionbus_utils.logging_utils import logger
from ionbus_utils.yaml_utils import PDYaml, yaml

T = TypeVar("T", bound=PDYaml)


def add_auth_yaml_file(
    nickname: str,
    filename: str,
    env_name: str,
) -> None:
    """Adds the given YAML file to the environment variable IBU_AUTH.
    If the environment variable is not set, it is created. If it is set,
    the new file is added to the end of the list."""
    env_dict = get_auth_dictionary(env_name, empty_dict_on_failure=True)
    existing = env_dict.get(nickname)
    if existing and existing != filename:
        logger.warning(f"Updating {nickname} in {env_name} to {filename}.")
    env_dict[nickname] = filename
    os.environ[env_name] = ";".join(
        f"{key}::{value}" for key, value in env_dict.items()
    )
    logger.info(
        f"Added {nickname}::{filename} to {env_name} environment variable."
    )


def get_auth_dictionary(
    env_name: str = "IBU_AUTH",
    empty_dict_on_failure: bool = False,
) -> dict[str, str]:
    """Returns the credentials dictionary from the environment variable.
    Raises RuntimeError if the environment variable is not set or empty.
    Default environment variable name is IBU_AUTH.

    The environment variable is expected to be a semicolon-separated
    and use double colons to split key and value."""
    if not (env_var := os.environ.get(env_name)):
        if empty_dict_on_failure:
            return {}
        raise RuntimeError(f"{env_name} environment variable is not set.")
    env_dict = {}
    for raw_item in env_var.split(";"):
        item = raw_item.strip()
        if not item:
            continue
        parts = item.split("::")
        if len(parts) != 2 or not parts[0] or not parts[1]:
            if empty_dict_on_failure:
                return {}
            raise RuntimeError(
                f"Invalid entry '{item}' in {env_name}; "
                "expected nickname::filename."
            )
        key, value = parts
        env_dict[key] = value
    if not env_dict:
        if empty_dict_on_failure:
            return {}
        raise RuntimeError(f"{env_name} environment variable is empty.")
    return env_dict


def get_auth_credentials(
    name: str | None = None,
    env_name: str = "IBU_AUTH",
    empty_dict_on_failure: bool = False,
    required_fields: list[str] | None = None,
) -> dict[str, str]:
    """Returns the credentials for the given name. If name is not
    specified, then the first key in the  environment variable is used.
    Raises RuntimeError if the environment variable is not set, empty,
    or if the key is not found in the environment variable.  Default
    environment variable name is IBU_AUTH.

    The environment variable ie expected to be a semicolon-separated
    and use double colons to split key and value.

    Example:
    prod::/some_dir/prod_auth.yaml;dev::/some_dir/dev_auth.yaml"""
    if required_fields is None:
        required_fields = []
    env_dict = get_auth_dictionary(env_name, empty_dict_on_failure)
    if not env_dict:
        return {}
    if not name:
        name = next(iter(env_dict))
    if not (filename := env_dict.get(name)):
        if empty_dict_on_failure:
            return {}
        raise RuntimeError(
            f"Key '{name}' not found in {env_name} environment variable."
        )
    info = PDYaml.read_yaml_file(filename)
    missing = []
    for key in ["key_name", "encrypted_salt"] + required_fields:
        if key not in info:
            missing.append(key)
    if missing:
        raise RuntimeError(
            f"Needed keys {missing} not found in file {filename}."
        )
    info["password"] = decrypt_password(
        info["encrypted_salt"], info["key_name"]
    )
    info["name"] = name
    return info


def get_auth_credentials_pdyaml(
    pdyaml_type: type[T],
    name: str | None = None,
    env_name: str = "IBU_AUTH",
    empty_dict_on_failure: bool = False,
    required_fields: list[str] | None = None,
) -> T:
    """Returns the credentials for the given name as a PDYaml object.

    This is a wrapper around get_auth_credentials that returns a PDYaml
    instance instead of a dictionary.

    Args:
        pdyaml_type: The PDYaml subclass to instantiate with the credentials.
        name: The key name in the environment variable. If not specified,
            the first key is used.
        env_name: The environment variable name. Defaults to IBU_AUTH.
        empty_dict_on_failure: If True, returns an empty instance on failure.
        required_fields: List of additional required fields to check for.

    Returns:
        An instance of pdyaml_type populated with the credentials.
    """
    info = get_auth_credentials(
        name=name,
        env_name=env_name,
        empty_dict_on_failure=empty_dict_on_failure,
        required_fields=required_fields,
    )
    return pdyaml_type(**info)


def create_auth_file(
    filename: str,
    username: str | None = None,
    key_name: str | None = None,
    encrypted_salt: str | None = None,
    data: dict[str, str] | None = None,
) -> None:
    """Creates a auth file with the given data."""
    if data is None:
        data = {}
    val_list = [
        ("username", username),
        ("key_name", key_name),
        ("encrypted_salt", encrypted_salt),
    ]
    for name, value in val_list:
        if value is not None:
            data[name] = value
    missing = []
    for name, _ in val_list:
        if data.get(name) is None:
            missing.append(name)
    if missing:
        raise RuntimeError(f"Missing the following required keys: {missing}")
    with open(filename, "w", encoding="utf-8") as target:
        yaml.dump(data, target, allow_unicode=True)
    logger.info(f"Created {filename}")


def update_auth_file(
    filename: str,
    encrypted_salt: str,
) -> None:
    """Updates a auth file with the given data."""
    data = PDYaml.read_yaml_file(filename)
    data["encrypted_salt"] = encrypted_salt
    with open(filename, "w", encoding="utf-8") as target:
        yaml.dump(data, target, allow_unicode=True)
    logger.info(f"Updated {filename}")


def setup_args() -> argparse.ArgumentParser:
    """Create an argument parser.  Should always have at
    least --debug option"""
    parser_obj = argparse.ArgumentParser()
    # add any additional args as desired
    parser_obj.add_argument("--debug", action="store_true")
    parser_obj.add_argument(
        "--create",
        action="store_true",
        help="Create new authentication YAML file.",
    )
    parser_obj.add_argument(
        "--update",
        action="store_true",
        help="Update password in existing authentication YAML file.",
    )
    parser_obj.add_argument(
        "--generate_hash",
        action="store_true",
        help="Generate hash for encrypting passwords.",
    )

    parser_obj.add_argument(
        "filename",
        type=str,
        default=None,
        nargs="?",
        help="Name of the auth file to create or update. Linux home directory "
        "is assumed if no path is given.",
    )
    parser_obj.add_argument(
        "--username",
        type=str,
        default=None,
        help="username for server. Current user is assumed if not given.",
    )
    parser_obj.add_argument(
        "--key-name",
        type=str,
        default="personal",
        help="Key name used for encryption. Defaults to 'personal'.",
    )
    parser_obj.add_argument(
        "--json",
        type=str,
        default=None,
        help="JSON blob for extra fields to add to YAML file..",
    )

    return parser_obj


def update_auth_from_command_line(args: argparse.Namespace) -> None:
    """Creates an auth config file from command line options
    and keyboard input."""
    if (sum([args.create, args.update, args.generate_hash])) != 1:
        raise RuntimeError(
            "Must specify exactly one of --create, --update, or "
            "--generate_hash."
        )
    if not args.filename:
        raise RuntimeError("Must specify a filename to create or update.")
    if args.generate_hash:
        generate_key(args.key_name)
        return
    # use home directory if we can find it
    guess_dir = str(home) if (home := Path.home()) else "."
    file_path = Path(args.filename)
    logger.info(f"{file_path=} {file_path.is_absolute()=}")
    if not file_path.is_absolute():
        if guess_dir == ".":
            logger.warning(
                "Cannot determine home directory. Using current path."
            )
        file_path = Path(guess_dir) / file_path
        logger.info(f"Using {file_path=} {guess_dir=}")
    args.filename = str(file_path)
    pass1 = getpass.getpass("Enter password:")
    pass2 = getpass.getpass("Re-enter password:")
    if pass1 != pass2:
        raise RuntimeError("Passwords do not match.")
    encrypted_salt = encrypt_password(pass1, args.key_name)
    if args.json and args.debug:
        logger.info(f"{args.json}")
    if args.create:
        create_auth_file(
            filename=args.filename,
            username=args.username,
            key_name=args.key_name,
            encrypted_salt=encrypted_salt,
            data=json.loads(args.json) if args.json else {},
        )
    elif args.update:
        update_auth_file(
            filename=args.filename,
            encrypted_salt=encrypted_salt,
        )


if __name__ == "__main__":
    parser = setup_args()
    args_obj = parser.parse_args()
    if args_obj.debug:
        # only send to person running when debugging
        update_auth_from_command_line(args_obj)
    else:
        try:
            update_auth_from_command_line(args_obj)
        # pylint: disable-next=broad-exception-caught
        except Exception as excp:
            log_exception(excp)
            raise excp
