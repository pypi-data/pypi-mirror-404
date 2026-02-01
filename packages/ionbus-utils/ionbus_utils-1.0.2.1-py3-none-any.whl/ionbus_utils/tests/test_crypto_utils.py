"""Tests for crypto_utils module."""

from __future__ import annotations

import argparse
import base64
import os
import site
from pathlib import Path

import pytest

parent_dir = Path(__file__).absolute().parent.parent.parent
site.addsitedir(str(parent_dir))

from ionbus_utils.crypto_utils.crypto_utils import (
    decrypt_password,
    encrypt_password,
    generate_key,
    _get_crypto_keys_dict,
)
from ionbus_utils.crypto_utils.auth_utils import (
    add_auth_yaml_file,
    create_auth_file,
    get_auth_credentials,
    get_auth_dictionary,
    update_auth_file,
    update_auth_from_command_line,
)
from ionbus_utils.yaml_utils import PDYaml


class TestGetCryptoKeysDict:
    """Tests for _get_crypto_keys_dict function."""

    def test_returns_empty_dict_when_env_not_set(self, monkeypatch):
        """Test returns empty dict when IBU_AESGCM not set."""
        monkeypatch.delenv("IBU_AESGCM", raising=False)
        result = _get_crypto_keys_dict()
        assert result == {}

    def test_parses_single_key(self, monkeypatch):
        """Test parses single key from environment."""
        monkeypatch.setenv("IBU_AESGCM", "personal:abc123")
        result = _get_crypto_keys_dict()
        assert result == {"personal": "abc123"}

    def test_parses_multiple_keys(self, monkeypatch):
        """Test parses multiple keys from environment."""
        monkeypatch.setenv("IBU_AESGCM", "personal:abc123;work:xyz789")
        result = _get_crypto_keys_dict()
        assert result == {"personal": "abc123", "work": "xyz789"}

    def test_handles_whitespace(self, monkeypatch):
        """Test handles whitespace in keys."""
        monkeypatch.setenv("IBU_AESGCM", " personal : abc123 ; work : xyz789 ")
        result = _get_crypto_keys_dict()
        assert result == {"personal": "abc123", "work": "xyz789"}


class TestEncryptDecrypt:
    """Tests for encrypt_password and decrypt_password functions."""

    @pytest.fixture
    def valid_key_env(self, monkeypatch):
        """Set up a valid encryption key."""
        # Generate a valid 16-byte key encoded in base64
        key = base64.urlsafe_b64encode(os.urandom(16)).decode("utf-8")
        monkeypatch.setenv("IBU_AESGCM", f"test:{key}")
        return key

    def test_encrypt_returns_string(self, valid_key_env):
        """Test encrypt returns a string."""
        result = encrypt_password("secret", "test")
        assert isinstance(result, str)

    def test_decrypt_returns_original(self, valid_key_env):
        """Test decrypt returns original password."""
        original = "my_secret_password"
        encrypted = encrypt_password(original, "test")
        decrypted = decrypt_password(encrypted, "test")
        assert decrypted == original

    def test_different_passwords_different_ciphertext(self, valid_key_env):
        """Test different passwords produce different ciphertext."""
        enc1 = encrypt_password("password1", "test")
        enc2 = encrypt_password("password2", "test")
        assert enc1 != enc2

    def test_same_password_different_ciphertext(self, valid_key_env):
        """Test same password produces different ciphertext (due to nonce)."""
        enc1 = encrypt_password("same_password", "test")
        enc2 = encrypt_password("same_password", "test")
        # Due to random nonce, encryptions should differ
        assert enc1 != enc2

    def test_unicode_password(self, valid_key_env):
        """Test encrypting unicode password."""
        original = "p@ssw0rd_\u4e2d\u6587_\U0001f600"
        encrypted = encrypt_password(original, "test")
        decrypted = decrypt_password(encrypted, "test")
        assert decrypted == original

    def test_missing_key_raises_error(self, monkeypatch):
        """Test missing key raises error."""
        monkeypatch.setenv("IBU_AESGCM", "other:abc123")
        with pytest.raises(RuntimeError, match="not found"):
            encrypt_password("secret", "nonexistent")


class TestGenerateKey:
    """Tests for generate_key function."""

    def test_raises_if_key_exists(self, monkeypatch):
        """Test raises error if key already exists."""
        monkeypatch.setenv("IBU_AESGCM", "personal:existing_key")
        with pytest.raises(RuntimeError, match="already exists"):
            generate_key("personal")

    def test_creates_new_key(self, monkeypatch):
        """Test creates new key when it doesn't exist."""
        monkeypatch.delenv("IBU_AESGCM", raising=False)
        result = generate_key("newkey")
        assert "newkey:" in result


class TestGetAuthDictionary:
    """Tests for get_auth_dictionary function."""

    def test_raises_when_env_not_set(self, monkeypatch):
        """Test raises when environment variable not set."""
        monkeypatch.delenv("IBU_AUTH", raising=False)
        with pytest.raises(RuntimeError, match="not set"):
            get_auth_dictionary("IBU_AUTH")

    def test_returns_empty_dict_on_failure(self, monkeypatch):
        """Test returns empty dict when empty_dict_on_failure=True."""
        monkeypatch.delenv("IBU_AUTH", raising=False)
        result = get_auth_dictionary("IBU_AUTH", empty_dict_on_failure=True)
        assert result == {}

    def test_parses_env_correctly(self, monkeypatch):
        """Test parses environment variable correctly."""
        monkeypatch.setenv("IBU_AUTH", "prod::/path/to/prod.yaml;dev::/path/to/dev.yaml")
        result = get_auth_dictionary("IBU_AUTH")
        assert result == {
            "prod": "/path/to/prod.yaml",
            "dev": "/path/to/dev.yaml",
        }

    def test_invalid_entry_raises_or_returns_empty(self, monkeypatch):
        """Test invalid env entry handling."""
        env_name = "TEST_AUTH_INVALID"
        monkeypatch.setenv(env_name, "badentry")
        with pytest.raises(RuntimeError, match="Invalid entry"):
            get_auth_dictionary(env_name)
        result = get_auth_dictionary(env_name, empty_dict_on_failure=True)
        assert result == {}


class TestCreateAuthFile:
    """Tests for create_auth_file function."""

    def test_creates_file(self, temp_dir):
        """Test creates auth file."""
        filepath = temp_dir / "auth.yaml"
        create_auth_file(
            str(filepath),
            username="testuser",
            key_name="personal",
            encrypted_salt="encrypted_value",
        )
        assert filepath.exists()

    def test_file_contains_required_fields(self, temp_dir):
        """Test file contains required fields."""
        filepath = temp_dir / "auth.yaml"
        create_auth_file(
            str(filepath),
            username="testuser",
            key_name="personal",
            encrypted_salt="encrypted_value",
        )
        content = filepath.read_text()
        assert "username: testuser" in content
        assert "key_name: personal" in content
        assert "encrypted_salt: encrypted_value" in content

    def test_includes_extra_data(self, temp_dir):
        """Test includes extra data fields."""
        filepath = temp_dir / "auth.yaml"
        create_auth_file(
            str(filepath),
            username="testuser",
            key_name="personal",
            encrypted_salt="encrypted_value",
            data={"extra_field": "extra_value"},
        )
        content = filepath.read_text()
        assert "extra_field: extra_value" in content

    def test_raises_on_missing_fields(self, temp_dir):
        """Test raises error when required fields missing."""
        filepath = temp_dir / "auth.yaml"
        with pytest.raises(RuntimeError, match="Missing"):
            create_auth_file(str(filepath), username="testuser")


class TestUpdateAuthFile:
    """Tests for update_auth_file function."""

    def test_updates_encrypted_salt(self, temp_dir):
        """Test updates encrypted_salt in existing file."""
        filepath = temp_dir / "auth.yaml"
        # Create initial file
        create_auth_file(
            str(filepath),
            username="testuser",
            key_name="personal",
            encrypted_salt="old_value",
        )
        # Update it
        update_auth_file(str(filepath), encrypted_salt="new_value")
        content = filepath.read_text()
        assert "encrypted_salt: new_value" in content
        assert "old_value" not in content

    def test_preserves_other_fields(self, temp_dir):
        """Test preserves other fields when updating."""
        filepath = temp_dir / "auth.yaml"
        create_auth_file(
            str(filepath),
            username="testuser",
            key_name="personal",
            encrypted_salt="old_value",
            data={"extra": "preserved"},
        )
        update_auth_file(str(filepath), encrypted_salt="new_value")
        content = filepath.read_text()
        assert "username: testuser" in content
        assert "extra: preserved" in content


class TestGetAuthCredentials:
    """Tests for get_auth_credentials function."""

    @pytest.fixture
    def auth_setup(self, temp_dir, monkeypatch):
        """Set up auth file and environment."""
        # Create a valid encryption key
        key = base64.urlsafe_b64encode(os.urandom(16)).decode("utf-8")
        monkeypatch.setenv("IBU_AESGCM", f"testkey:{key}")

        # Encrypt a test password
        from ionbus_utils.crypto_utils.crypto_utils import encrypt_password

        encrypted = encrypt_password("test_password", "testkey")

        # Create auth file
        auth_file = temp_dir / "auth.yaml"
        auth_file.write_text(
            f"username: testuser\nkey_name: testkey\nencrypted_salt: {encrypted}\n"
        )

        # Set up environment
        monkeypatch.setenv("TEST_AUTH", f"myauth::{auth_file}")

        return {"file": auth_file, "encrypted": encrypted}

    def test_returns_dict(self, auth_setup):
        """Test returns a dictionary."""
        result = get_auth_credentials("myauth", env_name="TEST_AUTH")
        assert isinstance(result, dict)

    def test_contains_decrypted_password(self, auth_setup):
        """Test result contains decrypted password."""
        result = get_auth_credentials("myauth", env_name="TEST_AUTH")
        assert result["password"] == "test_password"

    def test_contains_username(self, auth_setup):
        """Test result contains username."""
        result = get_auth_credentials("myauth", env_name="TEST_AUTH")
        assert result["username"] == "testuser"

    def test_uses_first_key_when_name_not_specified(self, auth_setup):
        """Test uses first key when name not specified."""
        result = get_auth_credentials(env_name="TEST_AUTH")
        assert result["password"] == "test_password"

    def test_raises_on_missing_required_fields(self, temp_dir, monkeypatch):
        """Test raises when required fields missing."""
        auth_file = temp_dir / "incomplete.yaml"
        auth_file.write_text("username: testuser\n")
        monkeypatch.setenv("TEST_AUTH", f"test::{auth_file}")
        with pytest.raises(RuntimeError, match="Needed keys"):
            get_auth_credentials("test", env_name="TEST_AUTH")

    def test_empty_env_returns_empty_dict(self, monkeypatch):
        """Test empty env returns empty dict when allowed."""
        env_name = "TEST_EMPTY_AUTH"
        monkeypatch.delenv(env_name, raising=False)
        result = get_auth_credentials(env_name=env_name, empty_dict_on_failure=True)
        assert result == {}


class TestAddAuthYamlFile:
    """Tests for add_auth_yaml_file function."""

    def test_adds_entry_to_env(self, temp_dir, monkeypatch):
        """Test that an entry is added with correct format."""
        env_name = "TEST_AUTH_VAR"
        monkeypatch.delenv(env_name, raising=False)
        path = temp_dir / "auth.yaml"
        add_auth_yaml_file("nick", str(path), env_name)
        assert os.environ[env_name] == f"nick::{path}"

    def test_updates_existing_entry_preserves_others(self, temp_dir, monkeypatch):
        """Test updating existing nickname rewrites value and keeps others."""
        env_name = "TEST_AUTH_VAR"
        other_entry = "keep::/keep/path"
        monkeypatch.setenv(env_name, f"old::/old/path;{other_entry}")
        new_path = temp_dir / "new.yaml"
        add_auth_yaml_file("old", str(new_path), env_name)
        env_dict = get_auth_dictionary(env_name)
        assert env_dict["old"] == str(new_path)
        assert env_dict["keep"] == "/keep/path"


class TestUpdateAuthFromCommandLine:
    """Tests for update_auth_from_command_line helper."""

    def test_requires_filename(self):
        """Test that filename is required."""
        args = argparse.Namespace(
            create=True,
            update=False,
            generate_hash=False,
            filename=None,
            username=None,
            key_name="personal",
            json=None,
            debug=False,
        )
        with pytest.raises(RuntimeError, match="Must specify a filename"):
            update_auth_from_command_line(args)
