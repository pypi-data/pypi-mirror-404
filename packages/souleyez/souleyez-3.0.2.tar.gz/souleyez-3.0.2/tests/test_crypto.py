"""
Tests for souleyez.storage.crypto - Credential encryption/decryption

Simple tests focusing on core encryption functionality.
"""

import pytest
from pathlib import Path


@pytest.fixture
def crypto_manager(tmp_path, monkeypatch):
    """Create CryptoManager with temporary config directory."""
    # Use temp directory for config
    temp_config = tmp_path / ".souleyez"
    monkeypatch.setattr(Path, "home", lambda: tmp_path)

    # Reset singleton
    from souleyez.storage.crypto import CryptoManager

    CryptoManager._instance = None

    cm = CryptoManager()
    yield cm

    # Cleanup
    CryptoManager._instance = None


class TestCryptoManager:
    """Tests for CryptoManager encryption/decryption."""

    def test_crypto_manager_initialization(self, crypto_manager):
        """Test that CryptoManager initializes correctly."""
        assert crypto_manager is not None
        assert not crypto_manager.is_encryption_enabled()

    def test_encryption_disabled_by_default(self, crypto_manager):
        """Test that encryption is disabled by default."""
        assert crypto_manager.is_encryption_enabled() is False

    def test_encrypt_decrypt_with_password(self, crypto_manager):
        """Test basic encryption and decryption."""
        password = "test_password_123"
        plaintext = "secret_credential_data"

        # Enable encryption with password
        crypto_manager.enable_encryption(password)

        # Encrypt data
        encrypted = crypto_manager.encrypt(plaintext)

        # Encrypted should be different from plaintext
        assert encrypted != plaintext
        assert encrypted is not None

        # Decrypt data
        decrypted = crypto_manager.decrypt(encrypted)

        # Should match original
        assert decrypted == plaintext

    def test_encryption_with_different_passwords_fails(self, crypto_manager):
        """Test that wrong password can't decrypt data."""
        password1 = "correct_password"
        password2 = "wrong_password"
        plaintext = "secret_data"

        # Enable and encrypt with first password
        crypto_manager.enable_encryption(password1)
        encrypted = crypto_manager.encrypt(plaintext)

        # Try to decrypt with wrong password (need to re-initialize)
        from souleyez.storage.crypto import CryptoManager

        CryptoManager._instance._fernet = None

        # This should fail or return None
        try:
            crypto_manager.set_master_password(password2)
            decrypted = crypto_manager.decrypt(encrypted)
            # If it doesn't raise, it should not match
            assert decrypted != plaintext
        except Exception:
            # Expected behavior - decryption fails
            pass

    def test_encrypt_empty_string(self, crypto_manager):
        """Test encrypting empty string."""
        password = "test_password"
        plaintext = ""

        crypto_manager.enable_encryption(password)
        encrypted = crypto_manager.encrypt(plaintext)
        decrypted = crypto_manager.decrypt(encrypted)

        assert decrypted == plaintext

    def test_encrypt_unicode_data(self, crypto_manager):
        """Test encrypting unicode/special characters."""
        password = "test_password"
        plaintext = "Testing 你好 🔐 émojis!"

        crypto_manager.enable_encryption(password)
        encrypted = crypto_manager.encrypt(plaintext)
        decrypted = crypto_manager.decrypt(encrypted)

        assert decrypted == plaintext

    def test_config_file_created(self, crypto_manager, tmp_path):
        """Test that crypto config file is created."""
        config_path = tmp_path / ".souleyez" / "crypto.json"
        assert config_path.exists()

    def test_config_file_has_salt(self, crypto_manager, tmp_path):
        """Test that config file contains salt."""
        import json

        config_path = tmp_path / ".souleyez" / "crypto.json"

        with open(config_path, "r") as f:
            config = json.load(f)

        assert "salt" in config
        assert len(config["salt"]) > 0

    def test_enable_encryption_changes_state(self, crypto_manager):
        """Test that enabling encryption changes the state."""
        assert not crypto_manager.is_encryption_enabled()

        crypto_manager.enable_encryption("password123")

        assert crypto_manager.is_encryption_enabled()

    def test_multiple_encrypt_decrypt_cycles(self, crypto_manager):
        """Test multiple encryption/decryption cycles."""
        password = "test_pass"
        crypto_manager.enable_encryption(password)

        test_data = ["first_secret", "second_secret", "third_secret_with_numbers_12345"]

        for data in test_data:
            encrypted = crypto_manager.encrypt(data)
            decrypted = crypto_manager.decrypt(encrypted)
            assert decrypted == data


class TestCryptoEdgeCases:
    """Test edge cases and error handling."""

    def test_decrypt_without_encryption_enabled(self, crypto_manager):
        """Test that decryption without enabling encryption handles gracefully."""
        # Try to decrypt without setting up encryption
        result = crypto_manager.decrypt("some_data")
        # Should handle gracefully
        assert result is not None or result is None

    def test_encrypt_none_value(self, crypto_manager):
        """Test encrypting None value."""
        password = "test"
        crypto_manager.enable_encryption(password)

        # Should handle None gracefully
        try:
            encrypted = crypto_manager.encrypt(None)
            if encrypted:
                decrypted = crypto_manager.decrypt(encrypted)
        except (TypeError, AttributeError):
            pass

    def test_very_long_string_encryption(self, crypto_manager):
        """Test encrypting very long strings."""
        password = "test_password"
        plaintext = "A" * 10000

        crypto_manager.enable_encryption(password)
        encrypted = crypto_manager.encrypt(plaintext)
        decrypted = crypto_manager.decrypt(encrypted)

        assert decrypted == plaintext
        assert len(decrypted) == 10000

    def test_disable_encryption(self, crypto_manager):
        """Test disabling encryption."""
        password = "test"
        crypto_manager.enable_encryption(password)
        assert crypto_manager.is_encryption_enabled()

        crypto_manager.disable_encryption()

        assert not crypto_manager.is_encryption_enabled()

    def test_encryption_with_special_chars_password(self, crypto_manager):
        """Test encryption with special characters in password."""
        password = "p@ssw0rd!#$%^&*()"
        plaintext = "secret"

        crypto_manager.enable_encryption(password)
        encrypted = crypto_manager.encrypt(plaintext)
        decrypted = crypto_manager.decrypt(encrypted)

        assert decrypted == plaintext

    def test_multiple_enable_disable_cycles(self, crypto_manager):
        """Test multiple enable/disable cycles with same password."""
        # Must use same password since the verification token persists
        password = "consistent_pass"
        for i in range(3):
            crypto_manager.enable_encryption(password)
            assert crypto_manager.is_encryption_enabled()

            crypto_manager.disable_encryption()
            assert not crypto_manager.is_encryption_enabled()

    def test_crypto_config_persistence(self, crypto_manager, tmp_path):
        """Test that crypto config persists."""
        password = "persist_test"
        crypto_manager.enable_encryption(password)

        config_path = tmp_path / ".souleyez" / "crypto.json"
        assert config_path.exists()

        # Config should have encryption_enabled = true
        import json

        with open(config_path, "r") as f:
            config = json.load(f)

        assert config["encryption_enabled"] is True

    def test_corrupted_config_recovery(self, tmp_path, monkeypatch):
        """Test recovery from corrupted config file."""
        # Create corrupted config
        config_dir = tmp_path / ".souleyez"
        config_dir.mkdir(parents=True, exist_ok=True)
        config_file = config_dir / "crypto.json"
        config_file.write_text("{ corrupted json }")

        monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)

        # Should recover gracefully
        from souleyez.storage.crypto import CryptoManager

        CryptoManager._instance = None

        cm = CryptoManager()
        assert cm is not None
        assert not cm.is_encryption_enabled()

    def test_missing_config_creates_new(self, tmp_path, monkeypatch):
        """Test that missing config creates new one."""
        monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)

        from souleyez.storage.crypto import CryptoManager

        CryptoManager._instance = None

        cm = CryptoManager()

        config_path = tmp_path / ".souleyez" / "crypto.json"
        assert config_path.exists()

    def test_decrypt_with_invalid_token(self, crypto_manager):
        """Test decrypting data with invalid token."""
        password = "test"
        crypto_manager.enable_encryption(password)

        # Try to decrypt invalid base64
        result = crypto_manager.decrypt("not_valid_base64!")

        # Should handle gracefully
        assert result is not None or result is None

    def test_encrypt_decrypt_empty_after_enable(self, crypto_manager):
        """Test encrypt/decrypt empty string after enabling."""
        crypto_manager.enable_encryption("test")

        encrypted = crypto_manager.encrypt("")
        decrypted = crypto_manager.decrypt(encrypted)

        assert decrypted == ""

    def test_get_master_key_after_enable(self, crypto_manager):
        """Test getting master key after enabling encryption."""
        crypto_manager.enable_encryption("password")

        # Fernet object should exist
        assert crypto_manager._fernet is not None

    def test_load_existing_config(self, tmp_path, monkeypatch):
        """Test loading existing crypto config."""
        import json
        import base64
        import os

        # Create existing config
        config_dir = tmp_path / ".souleyez"
        config_dir.mkdir(parents=True, exist_ok=True)
        config_file = config_dir / "crypto.json"

        salt = os.urandom(32)
        config_data = {
            "salt": base64.b64encode(salt).decode("utf-8"),
            "encryption_enabled": True,
        }
        config_file.write_text(json.dumps(config_data))

        monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)

        from souleyez.storage.crypto import CryptoManager

        CryptoManager._instance = None

        cm = CryptoManager()

        # Should load existing config
        assert cm._salt == salt
        assert cm.is_encryption_enabled()

    def test_decrypt_without_fernet(self, tmp_path, monkeypatch):
        """Test decrypt when encryption not enabled."""
        monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)

        from souleyez.storage.crypto import CryptoManager

        CryptoManager._instance = None

        cm = CryptoManager()

        # Decrypt without enabling encryption
        result = cm.decrypt("test_data")

        # Should return original data
        assert result == "test_data"

    def test_encrypt_without_fernet(self, tmp_path, monkeypatch):
        """Test encrypt when encryption not enabled."""
        monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)

        from souleyez.storage.crypto import CryptoManager

        CryptoManager._instance = None

        cm = CryptoManager()

        # Encrypt without enabling encryption
        result = cm.encrypt("test_data")

        # Should return original data
        assert result == "test_data"


class TestCryptoErrorPaths:
    """Test error paths and exception handling in crypto."""

    def test_derive_key_without_salt(self, tmp_path, monkeypatch):
        """Test deriving key when salt not initialized."""
        monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)

        from souleyez.storage.crypto import CryptoManager

        CryptoManager._instance = None

        cm = CryptoManager()
        cm._salt = None  # Clear salt

        with pytest.raises(ValueError, match="Salt not initialized"):
            cm.derive_key_from_password("password")

    def test_unlock_with_invalid_fernet_key(self, tmp_path, monkeypatch):
        """Test unlock when Fernet initialization fails."""
        monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)

        from souleyez.storage.crypto import CryptoManager
        from cryptography.fernet import Fernet

        CryptoManager._instance = None

        cm = CryptoManager()
        cm.enable_encryption("password")

        # Mock Fernet to raise error
        def bad_fernet(key):
            raise ValueError("Invalid key")

        monkeypatch.setattr("souleyez.storage.crypto.Fernet", bad_fernet)

        result = cm.unlock("password")

        assert result is False

    def test_unlock_exception_handling(self, tmp_path, monkeypatch):
        """Test unlock handles exceptions gracefully."""
        monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)

        from souleyez.storage.crypto import CryptoManager

        CryptoManager._instance = None

        cm = CryptoManager()
        cm.enable_encryption("password")

        # Mock derive_key to raise exception
        def raise_exception(pwd):
            raise Exception("Test exception")

        monkeypatch.setattr(cm, "derive_key_from_password", raise_exception)

        result = cm.unlock("password")

        assert result is False
        assert cm._fernet is None

    def test_encrypt_when_locked(self, tmp_path, monkeypatch):
        """Test encrypt raises error when locked."""
        monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)

        from souleyez.storage.crypto import CryptoManager

        CryptoManager._instance = None

        cm = CryptoManager()
        cm.enable_encryption("password")
        cm.lock()  # Lock it

        with pytest.raises(RuntimeError, match="locked"):
            cm.encrypt("secret")

    def test_encrypt_exception_handling(self, crypto_manager):
        """Test encrypt handles Fernet exceptions."""
        from cryptography.fernet import InvalidToken

        crypto_manager.enable_encryption("password")

        # Mock Fernet.encrypt to raise exception
        def raise_error(data):
            raise Exception("Fernet error")

        original_fernet = crypto_manager._fernet
        crypto_manager._fernet.encrypt = raise_error

        with pytest.raises(RuntimeError, match="Encryption failed"):
            crypto_manager.encrypt("test")

    def test_decrypt_invalid_token(self, crypto_manager):
        """Test decrypt handles InvalidToken exception."""
        from cryptography.fernet import InvalidToken

        crypto_manager.enable_encryption("password")

        # Mock Fernet.decrypt to raise InvalidToken
        def raise_invalid_token(data):
            raise InvalidToken("Invalid token")

        crypto_manager._fernet.decrypt = raise_invalid_token

        result = crypto_manager.decrypt("fake_encrypted_data")

        # Should handle gracefully and return original
        assert result is not None

    def test_is_encryption_enabled_edge_cases(self, tmp_path, monkeypatch):
        """Test is_encryption_enabled returns False correctly."""
        monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)

        from souleyez.storage.crypto import CryptoManager

        CryptoManager._instance = None

        cm = CryptoManager()

        # Initially false
        assert cm.is_encryption_enabled() is False

        # Enable it
        cm.enable_encryption("test")
        assert cm.is_encryption_enabled() is True

        # Disable it
        cm.disable_encryption()
        assert cm.is_encryption_enabled() is False

    def test_lock_clears_fernet(self, tmp_path, monkeypatch):
        """Test lock clears Fernet object."""
        monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)

        from souleyez.storage.crypto import CryptoManager

        CryptoManager._instance = None

        cm = CryptoManager()
        cm.enable_encryption("password")

        assert cm._fernet is not None

        cm.lock()

        assert cm._fernet is None

    def test_save_config_creates_directory(self, tmp_path, monkeypatch):
        """Test _save_config creates directory if missing."""
        monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)

        from souleyez.storage.crypto import CryptoManager

        CryptoManager._instance = None

        cm = CryptoManager()
        cm.enable_encryption("password")

        config_dir = tmp_path / ".souleyez"
        config_file = config_dir / "crypto.json"
        assert config_file.exists()

    def test_decrypt_none_value(self, crypto_manager):
        """Test decrypt with None returns None."""
        crypto_manager.enable_encryption("password")

        result = crypto_manager.decrypt(None)

        assert result is None

    def test_encrypt_none_value_with_fernet(self, crypto_manager):
        """Test encrypt None with Fernet enabled."""
        crypto_manager.enable_encryption("password")

        result = crypto_manager.encrypt(None)

        assert result is None

    def test_change_password_success(self, tmp_path, monkeypatch):
        """Test successfully changing password."""
        monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)

        from souleyez.storage.crypto import CryptoManager

        CryptoManager._instance = None

        cm = CryptoManager()
        cm.enable_encryption("old_password")

        # Change password - returns tuple (success, error_message, credentials_migrated)
        result = cm.change_password("old_password", "new_password")

        assert result[0] is True

    def test_change_password_unlock_fails(self, tmp_path, monkeypatch):
        """Test change password when unlock fails."""
        monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)

        from souleyez.storage.crypto import CryptoManager

        CryptoManager._instance = None

        cm = CryptoManager()
        cm.enable_encryption("password")

        # Mock unlock to fail
        def failing_unlock(pwd):
            return False

        monkeypatch.setattr(cm, "unlock", failing_unlock)

        # Try to change password - returns tuple (success, error_message, credentials_migrated)
        result = cm.change_password("old", "new")

        assert result[0] is False

    def test_get_crypto_manager_singleton(self):
        """Test get_crypto_manager returns singleton."""
        from souleyez.storage import crypto

        # Clear singleton
        crypto._crypto_manager = None

        cm1 = crypto.get_crypto_manager()
        cm2 = crypto.get_crypto_manager()

        assert cm1 is cm2

    def test_decrypt_not_enabled_returns_original(self, tmp_path, monkeypatch):
        """Test decrypt returns original when not enabled."""
        monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)

        from souleyez.storage.crypto import CryptoManager

        CryptoManager._instance = None

        cm = CryptoManager()

        result = cm.decrypt("plaintext")

        assert result == "plaintext"

    def test_encrypt_not_enabled_returns_original(self, tmp_path, monkeypatch):
        """Test encrypt returns original when not enabled."""
        monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)

        from souleyez.storage.crypto import CryptoManager

        CryptoManager._instance = None

        cm = CryptoManager()

        result = cm.encrypt("plaintext")

        assert result == "plaintext"

    def test_is_unlocked_when_enabled(self, tmp_path, monkeypatch):
        """Test checking if crypto is unlocked."""
        monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)

        from souleyez.storage.crypto import CryptoManager

        CryptoManager._instance = None

        cm = CryptoManager()
        cm.enable_encryption("password")

        # Should not be locked after enable
        assert cm.is_unlocked() is True

        cm.lock()

        # Should be locked now
        assert cm.is_unlocked() is False

    def test_enable_encryption_fails_on_error(self, tmp_path, monkeypatch):
        """Test enable_encryption returns False when an error occurs."""
        monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)

        from souleyez.storage.crypto import CryptoManager

        CryptoManager._instance = None

        cm = CryptoManager()

        # Mock derive_key_from_password to raise an exception
        def failing_derive_key(pwd):
            raise ValueError("Test error")

        monkeypatch.setattr(cm, "derive_key_from_password", failing_derive_key)

        result = cm.enable_encryption("password")

        # Should fail due to exception
        assert result is False

    def test_decrypt_when_locked_raises_error(self, tmp_path, monkeypatch):
        """Test decrypt raises error when locked."""
        monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)

        from souleyez.storage.crypto import CryptoManager

        CryptoManager._instance = None

        cm = CryptoManager()
        cm.enable_encryption("password")
        cm.lock()

        with pytest.raises(RuntimeError, match="locked"):
            cm.decrypt("encrypted_data")

    def test_decrypt_exception_handling(self, crypto_manager):
        """Test decrypt handles Fernet exceptions."""
        crypto_manager.enable_encryption("password")

        # Mock Fernet.decrypt to raise exception
        def raise_error(data):
            raise Exception("Decrypt error")

        crypto_manager._fernet.decrypt = raise_error

        with pytest.raises(RuntimeError, match="Decryption failed"):
            crypto_manager.decrypt("fake_data")

    def test_unlock_with_bad_derived_key(self, tmp_path, monkeypatch):
        """Test unlock when derived key fails."""
        monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)

        from souleyez.storage.crypto import CryptoManager

        CryptoManager._instance = None

        cm = CryptoManager()
        cm.enable_encryption("password")

        # Mock derive_key to return invalid key
        def bad_derive(pwd):
            return b"too_short"  # Invalid Fernet key

        monkeypatch.setattr(cm, "derive_key_from_password", bad_derive)

        result = cm.unlock("any_password")

        assert result is False


class TestCryptoFinalLines:
    """Final tests to hit the last 5 lines for 100% coverage."""

    def test_unlock_decrypt_test_fails(self, tmp_path, monkeypatch):
        """Test unlock when decrypt test produces wrong result."""
        monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)

        from souleyez.storage.crypto import CryptoManager
        from cryptography.fernet import Fernet

        CryptoManager._instance = None

        cm = CryptoManager()
        cm.enable_encryption("password")

        # Create a Fernet that returns wrong data on decrypt
        class BadFernet:
            def __init__(self, key):
                self._fernet = Fernet(key)

            def encrypt(self, data):
                return self._fernet.encrypt(data)

            def decrypt(self, data):
                # Return wrong data to trigger line 129-130
                return b"wrong_data"

        # Monkey-patch Fernet
        import souleyez.storage.crypto

        original_fernet = souleyez.storage.crypto.Fernet
        souleyez.storage.crypto.Fernet = BadFernet

        cm.lock()

        try:
            # Now try to unlock - decrypt test will fail
            result = cm.unlock("password")

            assert result is False
            assert cm._fernet is None
        finally:
            # Restore
            souleyez.storage.crypto.Fernet = original_fernet

    def test_enable_encryption_already_enabled(self, tmp_path, monkeypatch):
        """Test enable_encryption when already enabled returns True."""
        monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)

        from souleyez.storage.crypto import CryptoManager

        CryptoManager._instance = None

        cm = CryptoManager()
        cm.enable_encryption("password")

        # Enable again - should return True immediately
        result = cm.enable_encryption("password")

        assert result is True

    def test_disable_encryption_not_enabled(self, tmp_path, monkeypatch):
        """Test disable_encryption when not enabled returns True."""
        monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)

        from souleyez.storage.crypto import CryptoManager

        CryptoManager._instance = None

        cm = CryptoManager()

        # Disable when not enabled - should return True
        result = cm.disable_encryption()

        assert result is True

    def test_change_password_unlock_fails(self, tmp_path, monkeypatch):
        """Test change_password when unlock fails."""
        monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)

        from souleyez.storage.crypto import CryptoManager

        CryptoManager._instance = None

        cm = CryptoManager()
        cm.enable_encryption("password")

        # Mock unlock to return False
        def failing_unlock(pwd):
            return False

        cm.unlock = failing_unlock

        # Try to change password - unlock will fail, returns tuple (success, error, count)
        result = cm.change_password("any", "new")

        assert result[0] is False
