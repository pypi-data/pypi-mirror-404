#!/usr/bin/env python3
"""
souleyez.storage.crypto - Credential encryption/decryption

Provides transparent encryption for sensitive credential data using Fernet (symmetric encryption).
The encryption key is derived from a master password using PBKDF2-HMAC-SHA256.
"""

import base64
import json
import os
import traceback
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from souleyez import config
from souleyez.log_config import get_logger

logger = get_logger(__name__)


class CryptoManager:
    """Manages encryption/decryption of credential data."""

    # Singleton instance
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.config_dir = Path.home() / ".souleyez"
        self.crypto_config_path = self.config_dir / "crypto.json"
        self._fernet: Optional[Fernet] = None
        self._encryption_enabled = False
        self._salt: Optional[bytes] = None
        self._last_access: Optional[datetime] = None
        self._last_unlock_time: Optional[datetime] = None
        self._timeout_minutes = config.get("security.session_timeout_minutes", 30)

        # Vault lockout tracking
        self._failed_attempts = 0
        self._lockout_until: Optional[datetime] = None
        self._lockout_minutes = 15
        self._max_attempts = 3

        # Load or initialize crypto configuration
        self._load_or_create_config()
        self._initialized = True

    def _load_or_create_config(self):
        """Load existing crypto config or create new one."""
        if self.crypto_config_path.exists():
            try:
                with open(self.crypto_config_path, "r") as f:
                    cfg = json.load(f)
                    self._salt = base64.b64decode(cfg.get("salt", ""))
                    self._encryption_enabled = cfg.get("encryption_enabled", False)

                    # Load persisted lockout state
                    lockout_str = cfg.get("lockout_until")
                    if lockout_str:
                        self._lockout_until = datetime.fromisoformat(lockout_str)
                        # Check if lockout has expired
                        if datetime.now() >= self._lockout_until:
                            # Lockout expired - reset everything
                            self._lockout_until = None
                            self._failed_attempts = 0
                        else:
                            # Active lockout - load the failed attempts count
                            self._failed_attempts = cfg.get("failed_attempts", 0)
                    else:
                        # No lockout - reset failed attempts (fresh start)
                        self._failed_attempts = 0

                logger.info(
                    "Crypto config loaded",
                    extra={"encryption_enabled": self._encryption_enabled},
                )
            except (json.JSONDecodeError, KeyError) as e:
                # Corrupted config, regenerate
                logger.warning(
                    "Crypto config corrupted, regenerating",
                    extra={"error": str(e), "traceback": traceback.format_exc()},
                )
                self._initialize_config()
        else:
            logger.info("Initializing new crypto config")
            self._initialize_config()

    def _initialize_config(self):
        """Initialize new crypto configuration with random salt."""
        self._salt = os.urandom(32)  # 256-bit salt
        self._encryption_enabled = False
        self._save_config()
        logger.info(
            "Crypto config initialized",
            extra={"salt_generated": True, "encryption_enabled": False},
        )

    def _save_config(self):
        """Save crypto configuration to disk."""
        self.config_dir.mkdir(parents=True, exist_ok=True)

        # Preserve existing password_verification if we don't have fernet to create new one
        existing_verification = None
        if self.crypto_config_path.exists():
            try:
                with open(self.crypto_config_path, "r") as f:
                    existing_config = json.load(f)
                    existing_verification = existing_config.get("password_verification")
            except (json.JSONDecodeError, IOError):
                pass

        config = {
            "salt": base64.b64encode(self._salt).decode("utf-8"),
            "encryption_enabled": self._encryption_enabled,
            "failed_attempts": self._failed_attempts,
            "lockout_until": (
                self._lockout_until.isoformat() if self._lockout_until else None
            ),
        }

        # Add password verification token
        if self._fernet:
            # Create new verification token with current fernet
            verification_data = b"SOULEYEZ_PASSWORD_VERIFICATION_TOKEN"
            config["password_verification"] = self._fernet.encrypt(
                verification_data
            ).decode("utf-8")
        elif existing_verification:
            # Preserve existing verification token
            config["password_verification"] = existing_verification

        with open(self.crypto_config_path, "w") as f:
            json.dump(config, f, indent=2)
        # Secure permissions (readable only by owner)
        os.chmod(self.crypto_config_path, 0o600)

    def is_encryption_enabled(self) -> bool:
        """Check if encryption is currently enabled."""
        return self._encryption_enabled

    def is_unlocked(self) -> bool:
        """Check if crypto manager is unlocked (key loaded)."""
        return self._fernet is not None

    def _check_timeout(self):
        """Check if session has timed out and lock if necessary."""
        if self._last_access and self._fernet:
            elapsed = (datetime.now() - self._last_access).total_seconds() / 60
            if elapsed > self._timeout_minutes:
                logger.warning(
                    "Session expired due to inactivity",
                    extra={
                        "elapsed_minutes": round(elapsed, 2),
                        "timeout_minutes": self._timeout_minutes,
                    },
                )
                self.lock()
                raise RuntimeError(
                    f"Session expired after {self._timeout_minutes} minutes of inactivity. Please unlock again."
                )
        self._last_access = datetime.now()

    def derive_key_from_password(self, password: str) -> bytes:
        """
        Derive encryption key from password using PBKDF2.

        Args:
            password: Master password

        Returns:
            32-byte encryption key suitable for Fernet
        """
        if not self._salt:
            raise ValueError("Salt not initialized")

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self._salt,
            iterations=config.get("crypto.iterations", 600000),
            backend=default_backend(),
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode("utf-8")))
        return key

    def is_locked_out(self) -> bool:
        """Check if vault is in lockout period."""
        if self._lockout_until is None:
            return False
        return datetime.now() < self._lockout_until

    def get_lockout_remaining(self) -> int:
        """Return seconds remaining in lockout, or 0."""
        if not self.is_locked_out():
            return 0
        remaining = (self._lockout_until - datetime.now()).total_seconds()
        return max(0, int(remaining))

    def record_failed_attempt(self) -> tuple:
        """
        Record failed unlock attempt.

        Returns:
            (remaining_attempts, is_locked_out)
        """
        self._failed_attempts += 1
        remaining = self._max_attempts - self._failed_attempts

        if self._failed_attempts >= self._max_attempts:
            self._lockout_until = datetime.now() + timedelta(
                minutes=self._lockout_minutes
            )
            logger.warning(
                "Vault locked out",
                extra={
                    "failed_attempts": self._failed_attempts,
                    "lockout_minutes": self._lockout_minutes,
                },
            )
            # Persist lockout state to survive app restarts
            self._save_config()
            return (0, True)

        logger.info(
            "Failed vault unlock attempt",
            extra={
                "failed_attempts": self._failed_attempts,
                "remaining_attempts": remaining,
            },
        )
        # Persist failed attempt count
        self._save_config()
        return (remaining, False)

    def reset_failed_attempts(self):
        """Reset failed attempts counter on successful unlock."""
        self._failed_attempts = 0
        self._lockout_until = None
        # Persist cleared state
        self._save_config()

    def get_recent_failure_count(self) -> int:
        """Get number of recent failed attempts (for cross-layer delay)."""
        return self._failed_attempts

    @property
    def last_unlock_time(self) -> Optional[datetime]:
        """Get timestamp of last successful unlock."""
        return self._last_unlock_time

    def unlock(self, password: str) -> bool:
        """
        Unlock crypto manager with master password.

        Args:
            password: Master password

        Returns:
            True if unlock successful, False if password incorrect
        """
        # Check if locked out
        if self.is_locked_out():
            remaining = self.get_lockout_remaining()
            logger.warning(
                "Unlock attempt during lockout", extra={"remaining_seconds": remaining}
            )
            return False

        # Reject empty passwords immediately
        if not password or not password.strip():
            logger.warning("Unlock failed - empty password not allowed")
            return False

        try:
            key = self.derive_key_from_password(password)
            self._fernet = Fernet(key)

            # Validate password by trying to decrypt the verification token
            # Load current config to get verification token
            if self.crypto_config_path.exists():
                with open(self.crypto_config_path, "r") as f:
                    cfg = json.load(f)

                verification_token = cfg.get("password_verification")
                if verification_token:
                    # Try to decrypt the verification token
                    try:
                        decrypted = self._fernet.decrypt(
                            verification_token.encode("utf-8")
                        )
                        if decrypted != b"SOULEYEZ_PASSWORD_VERIFICATION_TOKEN":
                            self._fernet = None
                            logger.warning(
                                "Unlock failed - password verification failed"
                            )
                            return False
                    except Exception as decrypt_error:
                        self._fernet = None
                        logger.warning(
                            f"Unlock failed - incorrect password: {decrypt_error}"
                        )
                        return False
                else:
                    # No verification token yet (old version or first unlock after upgrade)
                    # Save one now for future use
                    logger.info("No verification token found - creating one")
                    self._save_config()

            # Success - reset lockout tracking
            self.reset_failed_attempts()
            self._last_access = datetime.now()
            self._last_unlock_time = datetime.now()
            logger.info(
                "Crypto manager unlocked",
                extra={"encryption_enabled": self._encryption_enabled},
            )

            # Write msfrpc session file if configured (enables background worker RPC access)
            self._write_msfrpc_session_if_configured()

            return True
        except Exception as e:
            self._fernet = None
            logger.error(
                "Unlock failed",
                extra={"error_type": type(e).__name__, "error_message": "<redacted>"},
            )
            return False

    def lock(self):
        """Lock crypto manager (clear encryption key from memory)."""
        self._fernet = None
        self._last_access = None
        logger.info("Crypto manager locked")

        # Clear msfrpc session file (background worker should no longer have access)
        self._clear_msfrpc_session()

    def _write_msfrpc_session_if_configured(self):
        """
        Write msfrpc password to session file if msfrpc is configured.

        This enables the background worker (separate process) to authenticate
        to msfrpcd for RPC mode exploit execution.
        """
        try:
            from souleyez import config as app_config

            # Only write if msfrpc is enabled
            if not app_config.get("msfrpc.enabled", False):
                return

            # Get encrypted password
            encrypted = app_config.get("msfrpc.password")
            if not encrypted:
                return

            # Decrypt it (vault is unlocked at this point)
            decrypted = self.decrypt(encrypted)
            if not decrypted:
                return

            # Write to session file
            from souleyez.core.msf_rpc_manager import write_msfrpc_session

            write_msfrpc_session(decrypted)
            logger.debug("MSF RPC session file written for background worker")

        except Exception as e:
            logger.debug(f"Failed to write msfrpc session: {e}")

    def _clear_msfrpc_session(self):
        """Clear the msfrpc session file on lock."""
        try:
            from souleyez.core.msf_rpc_manager import clear_msfrpc_session

            clear_msfrpc_session()
        except Exception:
            pass  # Best effort cleanup

    def enable_encryption(self, password: str) -> bool:
        """
        Enable encryption for credentials and migrate existing plaintext credentials.

        Args:
            password: Master password to use

        Returns:
            True if encryption enabled successfully
        """
        if self._encryption_enabled:
            logger.info("Encryption already enabled")
            return True

        try:
            # When enabling encryption (fresh or after disable), we need to:
            # 1. Generate new salt (or use existing if valid)
            # 2. Derive key from password
            # 3. Create new fernet
            # 4. Save config with new verification token

            # Generate fresh salt if needed
            if not self._salt:
                self._salt = os.urandom(32)

            # Derive key and create fernet
            key = self.derive_key_from_password(password)
            self._fernet = Fernet(key)

            # Enable encryption and save (this creates new verification token)
            self._encryption_enabled = True
            self._save_config()

            # Reset lockout state on successful enable
            self.reset_failed_attempts()
            self._last_access = datetime.now()
            self._last_unlock_time = datetime.now()

            # Migrate existing plaintext credentials
            migrated = self._migrate_plaintext_credentials()
            logger.info(
                "Encryption enabled successfully",
                extra={"credentials_migrated": migrated},
            )

            return True
        except Exception as e:
            logger.error(
                "Failed to enable encryption",
                extra={"error_type": type(e).__name__, "error": str(e)},
            )
            self._fernet = None
            return False

    def _migrate_plaintext_credentials(self) -> int:
        """
        Migrate existing plaintext credentials to encrypted format.

        Returns:
            Number of credentials migrated
        """
        from souleyez.storage.database import Database

        if not self._fernet:
            logger.error("Cannot migrate credentials - crypto manager not unlocked")
            return 0

        db = Database()
        credentials = db.execute("SELECT id, username, password FROM credentials")

        migrated = 0
        for cred in credentials:
            cred_id = cred["id"]
            username = cred.get("username")
            password = cred.get("password")

            updated = False
            update_data = {}

            # Check if username is plaintext (not encrypted)
            if username and not self._is_encrypted(username):
                encrypted_username = self.encrypt(username)
                if encrypted_username:
                    update_data["username"] = encrypted_username
                    updated = True

            # Check if password is plaintext (not encrypted)
            if password and not self._is_encrypted(password):
                encrypted_password = self.encrypt(password)
                if encrypted_password:
                    update_data["password"] = encrypted_password
                    updated = True

            if updated:
                db.execute(
                    f"UPDATE credentials SET {', '.join([f'{k}=?' for k in update_data.keys()])} WHERE id = ?",
                    tuple(list(update_data.values()) + [cred_id]),
                )
                migrated += 1

        if migrated > 0:
            logger.info(
                f"Migrated {migrated} plaintext credentials to encrypted format"
            )

        return migrated

    def _is_encrypted(self, value: str) -> bool:
        """
        Check if a value appears to be encrypted (simple heuristic).
        Encrypted values are base64-encoded and start with 'gAAAAA' (Fernet signature).
        """
        if not value:
            return False
        try:
            # Fernet tokens always start with version byte (0x80 = gA in base64)
            return value.startswith("gA") and len(value) > 50
        except:
            return False

    def disable_encryption(self) -> bool:
        """
        Disable encryption (WARNING: credentials will be stored in plaintext).

        Returns:
            True if disabled successfully
        """
        if not self._encryption_enabled:
            logger.info("Encryption already disabled")
            return True

        self._encryption_enabled = False
        self.lock()  # Lock first so _save_config doesn't write old verification token
        self._save_config()
        logger.warning("Encryption disabled - credentials will be stored in plaintext")
        return True

    def encrypt(self, plaintext: str) -> Optional[str]:
        """
        Encrypt plaintext string.

        Args:
            plaintext: String to encrypt

        Returns:
            Base64-encoded encrypted string, or None if encryption disabled/locked
        """
        if not self._encryption_enabled:
            # Encryption disabled, return plaintext
            return plaintext

        if not self._fernet:
            raise RuntimeError("Crypto manager is locked. Call unlock() first.")

        # Check for session timeout
        self._check_timeout()

        if plaintext is None:
            return None

        try:
            encrypted_bytes = self._fernet.encrypt(plaintext.encode("utf-8"))
            logger.debug(
                "Data encrypted",
                extra={"data_type": "credential_field", "size_bytes": len(plaintext)},
            )
            return encrypted_bytes.decode("utf-8")
        except Exception as e:
            logger.error(
                "Encryption failed",
                extra={"error_type": type(e).__name__, "error_message": "<redacted>"},
            )
            raise RuntimeError("Encryption failed")

    def decrypt(self, ciphertext: str) -> Optional[str]:
        """
        Decrypt ciphertext string.

        Args:
            ciphertext: Encrypted string to decrypt

        Returns:
            Decrypted plaintext string, or None if decryption fails
        """
        if not self._encryption_enabled:
            # Encryption disabled, return as-is
            return ciphertext

        if not self._fernet:
            raise RuntimeError("Crypto manager is locked. Call unlock() first.")

        # Check for session timeout
        self._check_timeout()

        if ciphertext is None:
            return None

        try:
            decrypted_bytes = self._fernet.decrypt(ciphertext.encode("utf-8"))
            logger.debug(
                "Data decrypted",
                extra={"data_type": "credential_field", "success": True},
            )
            return decrypted_bytes.decode("utf-8")
        except InvalidToken:
            # Data might be plaintext (migration scenario)
            logger.warning("Decryption failed - data may be plaintext")
            return ciphertext
        except Exception as e:
            logger.error(
                "Decryption failed",
                extra={"error_type": type(e).__name__, "error_message": "<redacted>"},
            )
            raise RuntimeError("Decryption failed")

    def change_password(self, old_password: str, new_password: str) -> tuple:
        """
        Change master password with atomic credential re-encryption.

        Safely re-encrypts all credentials with the new password. If any step
        fails, the old password remains valid and no data is lost.

        Args:
            old_password: Current password
            new_password: New password

        Returns:
            Tuple of (success: bool, error_message: str or None, credentials_migrated: int)
        """
        from souleyez.storage.database import Database

        # Step 1: Verify old password
        if not self.unlock(old_password):
            logger.warning("Password change failed - old password incorrect")
            return (False, "Incorrect current password", 0)

        old_fernet = self._fernet
        old_salt = self._salt

        # Step 2: Read all encrypted credentials BEFORE changing anything
        db = Database()
        credentials = db.execute("SELECT id, username, password FROM credentials")

        # Step 3: Decrypt all credentials with old key
        decrypted_creds = []
        for cred in credentials:
            cred_id = cred["id"]
            username = cred.get("username")
            password = cred.get("password")

            try:
                decrypted_username = None
                decrypted_password = None

                if username and self._is_encrypted(username):
                    decrypted_username = old_fernet.decrypt(
                        username.encode("utf-8")
                    ).decode("utf-8")
                else:
                    decrypted_username = username

                if password and self._is_encrypted(password):
                    decrypted_password = old_fernet.decrypt(
                        password.encode("utf-8")
                    ).decode("utf-8")
                else:
                    decrypted_password = password

                decrypted_creds.append(
                    {
                        "id": cred_id,
                        "username": decrypted_username,
                        "password": decrypted_password,
                    }
                )
            except Exception as e:
                # Rollback - don't change anything
                logger.error(
                    "Password change failed - could not decrypt credential",
                    extra={"cred_id": cred_id, "error": str(e)},
                )
                return (False, f"Failed to decrypt credential ID {cred_id}", 0)

        # Step 4: Generate new salt and key
        new_salt = os.urandom(32)
        self._salt = new_salt
        new_key = self.derive_key_from_password(new_password)
        new_fernet = Fernet(new_key)

        # Step 5: Re-encrypt all credentials with new key
        re_encrypted = []
        for cred in decrypted_creds:
            try:
                encrypted_username = None
                encrypted_password = None

                if cred["username"]:
                    encrypted_username = new_fernet.encrypt(
                        cred["username"].encode("utf-8")
                    ).decode("utf-8")

                if cred["password"]:
                    encrypted_password = new_fernet.encrypt(
                        cred["password"].encode("utf-8")
                    ).decode("utf-8")

                re_encrypted.append(
                    {
                        "id": cred["id"],
                        "username": encrypted_username,
                        "password": encrypted_password,
                    }
                )
            except Exception as e:
                # Rollback - restore old salt and don't update anything
                self._salt = old_salt
                self._fernet = old_fernet
                logger.error(
                    "Password change failed - could not re-encrypt credential",
                    extra={"cred_id": cred["id"], "error": str(e)},
                )
                return (False, f"Failed to re-encrypt credential ID {cred['id']}", 0)

        # Step 6: Update database with re-encrypted credentials
        migrated = 0
        try:
            for cred in re_encrypted:
                db.execute(
                    "UPDATE credentials SET username = ?, password = ? WHERE id = ?",
                    (cred["username"], cred["password"], cred["id"]),
                )
                migrated += 1
        except Exception as e:
            # Database update failed - this is problematic but old salt is still in config
            # The safest thing is to not update the config file
            self._salt = old_salt
            self._fernet = old_fernet
            logger.error(
                "Password change failed - database update error",
                extra={"error": str(e), "credentials_updated": migrated},
            )
            return (
                False,
                f"Database error after updating {migrated} credentials",
                migrated,
            )

        # Step 7: Only NOW update the fernet and save config
        self._fernet = new_fernet
        self._save_config()

        logger.info(
            "Master password changed successfully",
            extra={"credentials_migrated": migrated},
        )
        return (True, None, migrated)


# Singleton accessor
_crypto_manager = None


def get_crypto_manager() -> CryptoManager:
    """Get the global CryptoManager singleton."""
    global _crypto_manager
    if _crypto_manager is None:
        _crypto_manager = CryptoManager()
    return _crypto_manager
