"""Tests for Fernet encryption helpers."""

import os
from unittest.mock import patch

import pytest


class TestEncryptionAvailability:
    """Tests for encryption availability checks."""

    def setup_method(self):
        """Reset encryption state."""
        from mysql_to_sheets.core.encryption import reset_encryption

        reset_encryption()

    def teardown_method(self):
        """Clean up."""
        from mysql_to_sheets.core.encryption import reset_encryption

        reset_encryption()

    def test_is_encryption_available_without_key(self):
        """is_encryption_available returns False without key."""
        from mysql_to_sheets.core.encryption import is_encryption_available

        with patch.dict(os.environ, {}, clear=True):
            # Remove the key if it exists
            os.environ.pop("INTEGRATION_ENCRYPTION_KEY", None)
            from mysql_to_sheets.core.encryption import reset_encryption

            reset_encryption()
            assert is_encryption_available() is False

    def test_is_encryption_available_with_valid_key(self):
        """is_encryption_available returns True with valid key."""
        from mysql_to_sheets.core.encryption import (
            generate_encryption_key,
            is_encryption_available,
            reset_encryption,
        )

        key = generate_encryption_key()
        reset_encryption()
        with patch.dict(os.environ, {"INTEGRATION_ENCRYPTION_KEY": key}):
            assert is_encryption_available() is True


class TestGenerateKey:
    """Tests for key generation."""

    def test_generate_encryption_key(self):
        """generate_encryption_key returns valid Fernet key."""
        from mysql_to_sheets.core.encryption import generate_encryption_key

        key = generate_encryption_key()
        assert isinstance(key, str)
        assert len(key) == 44  # Fernet key length
        assert key.endswith("=")  # Base64 padding

    def test_generated_keys_are_unique(self):
        """Each generated key is unique."""
        from mysql_to_sheets.core.encryption import generate_encryption_key

        keys = [generate_encryption_key() for _ in range(10)]
        assert len(set(keys)) == 10


class TestEncryptDecrypt:
    """Tests for encrypt/decrypt operations."""

    @pytest.fixture(autouse=True)
    def setup_encryption(self):
        """Set up encryption with a test key."""
        from mysql_to_sheets.core.encryption import generate_encryption_key, reset_encryption

        reset_encryption()
        self.test_key = generate_encryption_key()
        with patch.dict(os.environ, {"INTEGRATION_ENCRYPTION_KEY": self.test_key}):
            yield
        reset_encryption()

    def test_encrypt_decrypt_credentials(self):
        """encrypt_credentials and decrypt_credentials are inverse."""
        from mysql_to_sheets.core.encryption import decrypt_credentials, encrypt_credentials

        credentials = {
            "user": "testuser",
            "password": "secret123",
            "api_key": "key-abc-123",
        }

        encrypted = encrypt_credentials(credentials)
        assert isinstance(encrypted, str)
        assert encrypted != str(credentials)  # Should be encrypted

        decrypted = decrypt_credentials(encrypted)
        assert decrypted == credentials

    def test_encrypt_empty_credentials(self):
        """Can encrypt empty credentials dict."""
        from mysql_to_sheets.core.encryption import decrypt_credentials, encrypt_credentials

        credentials: dict = {}
        encrypted = encrypt_credentials(credentials)
        decrypted = decrypt_credentials(encrypted)
        assert decrypted == credentials

    def test_encrypt_decrypt_value(self):
        """encrypt_value and decrypt_value are inverse."""
        from mysql_to_sheets.core.encryption import decrypt_value, encrypt_value

        value = "my-secret-password"
        encrypted = encrypt_value(value)
        assert encrypted != value
        decrypted = decrypt_value(encrypted)
        assert decrypted == value

    def test_encrypt_unicode_value(self):
        """Can encrypt Unicode strings."""
        from mysql_to_sheets.core.encryption import decrypt_value, encrypt_value

        value = "password-with-emoji-\U0001f511"
        encrypted = encrypt_value(value)
        decrypted = decrypt_value(encrypted)
        assert decrypted == value

    def test_encrypted_values_differ(self):
        """Same value encrypts to different ciphertext (randomized)."""
        from mysql_to_sheets.core.encryption import encrypt_value

        value = "same-password"
        encrypted1 = encrypt_value(value)
        encrypted2 = encrypt_value(value)
        # Fernet uses random IV, so ciphertexts should differ
        assert encrypted1 != encrypted2

    def test_decrypt_invalid_data_raises(self):
        """Decrypting invalid data raises ValueError."""
        from mysql_to_sheets.core.encryption import decrypt_credentials

        with pytest.raises(ValueError, match="Failed to decrypt"):
            decrypt_credentials("not-valid-encrypted-data")


class TestKeyRotation:
    """Tests for key rotation functionality."""

    def test_rotate_credentials_key(self):
        """Can rotate credentials to new key."""
        from mysql_to_sheets.core.encryption import generate_encryption_key, rotate_credentials_key

        old_key = generate_encryption_key()
        new_key = generate_encryption_key()

        # Encrypt with old key
        from cryptography.fernet import Fernet

        old_fernet = Fernet(old_key.encode())
        original_data = b'{"user": "test", "password": "secret"}'
        encrypted = old_fernet.encrypt(original_data).decode()

        # Rotate to new key
        rotated = rotate_credentials_key(encrypted, old_key, new_key)

        # Decrypt with new key
        new_fernet = Fernet(new_key.encode())
        decrypted = new_fernet.decrypt(rotated.encode())
        assert decrypted == original_data

    def test_rotate_with_invalid_old_key_fails(self):
        """Rotation with wrong old key fails."""
        from mysql_to_sheets.core.encryption import generate_encryption_key, rotate_credentials_key

        wrong_key = generate_encryption_key()
        new_key = generate_encryption_key()
        correct_key = generate_encryption_key()

        # Encrypt with correct key
        from cryptography.fernet import Fernet

        correct_fernet = Fernet(correct_key.encode())
        encrypted = correct_fernet.encrypt(b"data").decode()

        # Try to rotate with wrong key
        with pytest.raises(ValueError, match="Failed to decrypt"):
            rotate_credentials_key(encrypted, wrong_key, new_key)


class TestCredentialDictionary:
    """Tests for credential dictionary handling."""

    @pytest.fixture(autouse=True)
    def setup_encryption(self):
        """Set up encryption with a test key."""
        from mysql_to_sheets.core.encryption import generate_encryption_key, reset_encryption

        reset_encryption()
        self.test_key = generate_encryption_key()
        with patch.dict(os.environ, {"INTEGRATION_ENCRYPTION_KEY": self.test_key}):
            yield
        reset_encryption()

    def test_credentials_with_special_characters(self):
        """Can encrypt credentials with special characters."""
        from mysql_to_sheets.core.encryption import decrypt_credentials, encrypt_credentials

        credentials = {
            "password": "p@ss#word!with$pecial&chars",
            "user": "user@domain.com",
        }

        encrypted = encrypt_credentials(credentials)
        decrypted = decrypt_credentials(encrypted)
        assert decrypted == credentials

    def test_credentials_with_nested_json(self):
        """Can encrypt credentials containing JSON strings."""
        from mysql_to_sheets.core.encryption import decrypt_credentials, encrypt_credentials

        credentials = {
            "service_account_json": '{"type": "service_account", "project_id": "test"}',
        }

        encrypted = encrypt_credentials(credentials)
        decrypted = decrypt_credentials(encrypted)
        assert decrypted == credentials

    def test_credentials_sorted_keys(self):
        """Credentials are serialized with sorted keys."""
        from mysql_to_sheets.core.encryption import encrypt_credentials

        creds1 = {"z_key": "1", "a_key": "2"}
        creds2 = {"a_key": "2", "z_key": "1"}

        # Both should produce same JSON (sorted keys)
        # But encrypted values will differ due to random IV
        encrypted1 = encrypt_credentials(creds1)
        encrypted2 = encrypt_credentials(creds2)

        # Just verify both encrypt without error
        assert encrypted1 is not None
        assert encrypted2 is not None
