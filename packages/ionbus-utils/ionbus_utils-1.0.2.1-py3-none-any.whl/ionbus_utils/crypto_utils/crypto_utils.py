"""Cryptography utilities"""

from __future__ import annotations

import base64
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM  # type: ignore

import site
from pathlib import Path

site.addsitedir(str(Path(__file__).absolute().parent.parent.parent))

from ionbus_utils.base_utils import is_windows
from ionbus_utils.logging_utils import logger


def generate_key(name: str = "personal") -> str:
    """Generates a key."""
    keys = _get_crypto_keys_dict()
    if name in keys:
        raise RuntimeError(f"Key '{name}' already exists.")
    keys[name] = base64.urlsafe_b64encode(os.urandom(16)).decode("utf-8")
    updated_string = ";".join(f"{k}:{v}" for k, v in keys.items())
    if is_windows():
        logger.info(
            f"Set IBU_AESGCM environment variable to {updated_string}\n"
            f"You can run in command prompt\nsetx IBU_AESGCM {updated_string}"
        )
    else:
        logger.info(
            f"Set IBU_AESGCM environment variable to {updated_string}\n"
            f"Add this line to your ~/.bash_profile\n"
            f"export IBU_AESGCM={updated_string}\n"
            f"Make sure you remove any old versions of this export command."
        )

        os.environ["IBU_AESGCM"] = updated_string
    return updated_string


def encrypt_password(password: str, name: str, encoding: str = "utf-8") -> str:
    """
    Encrypt `password` with AES-128-GCM.
    Returns a Base-64 string containing:
        [12-byte nonce | ciphertext | 16-byte tag]
    """
    aesgcm = _get_crypto_aesgcm(name)

    nonce = os.urandom(12)  # 96-bit nonce recommended for GCM
    ct = aesgcm.encrypt(nonce, password.encode(encoding), None)

    blob = nonce + ct  # tag is already appended to ct by AESGCM
    return base64.urlsafe_b64encode(blob).decode()


def decrypt_password(token_b64: str, name: str, encoding: str = "utf-8") -> str:
    """
    Reverse of `encrypt_password`.
    Accepts the Base-64 token produced earlier and returns the clear-text
    password.
    """
    aesgcm = _get_crypto_aesgcm(name)
    blob = base64.urlsafe_b64decode(token_b64.encode("utf-8"))
    nonce, ct = blob[:12], blob[12:]
    plaintext = aesgcm.decrypt(nonce, ct, None)
    return plaintext.decode(encoding)


def _get_crypto_aesgcm(name: str) -> AESGCM:
    """Returns an AESGCM object for the given name"""
    key = _get_crypto_key(name)
    return AESGCM(key)


def _get_crypto_key(name: str) -> bytes:
    """Returns the key for the given name from the IBU_AESGCM environment
    variable"""
    keys = _get_crypto_keys_dict()
    if not (encoded_key := keys.get(name)):
        raise RuntimeError(
            f"Key '{name}' not found in IBU_AESGCM environment variable."
        )
    return base64.urlsafe_b64decode(encoded_key.encode("utf-8"))


def _get_crypto_keys_dict() -> dict[str, str]:
    """Returns a dictionary of keys from the IBU_AESGCM environment variable"""
    keys_string = os.environ.get("IBU_AESGCM")
    if keys_string is None:
        return {}
    return {
        k.strip(): v.strip()
        for k, v in (
            pair.split(":", 1) for pair in keys_string.split(";") if pair
        )
    }
