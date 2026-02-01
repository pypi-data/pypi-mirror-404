"""
License validation using Ed25519 cryptographic signatures.

License keys are base64-encoded signed payloads containing:
- email: Licensee email
- tier: License tier (PRO)
- issued_at: Issue timestamp
- expires_at: Expiration timestamp (null for perpetual)
- machine_id: Optional hardware binding

The signature is created with Ed25519 private key (kept by issuer).
Validation uses the embedded public key - no internet required.
"""

import base64
import hashlib
import json
import os
import platform
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple


def _add_base64_padding(data: str) -> str:
    """Add padding to base64 string if missing."""
    padding = 4 - len(data) % 4
    if padding != 4:
        data += "=" * padding
    return data


# Ed25519 public key for license verification (Base64 encoded)
# Private key is kept secure by the license issuer
# This public key can only VERIFY signatures, not create them
LICENSE_PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
MCowBQYDK2VwAyEABS0eqd9OPCtqOvQI1Aw8vGnXiX1qecBjZ0UY7esPk1I=
-----END PUBLIC KEY-----"""


@dataclass
class LicenseInfo:
    """Validated license information."""

    email: str
    tier: str
    issued_at: datetime
    expires_at: Optional[datetime]
    machine_id: Optional[str]
    is_valid: bool
    error: Optional[str] = None

    @property
    def is_expired(self) -> bool:
        """Check if license has expired."""
        if self.expires_at is None:
            return False  # Perpetual license
        return datetime.now() > self.expires_at

    @property
    def days_remaining(self) -> Optional[int]:
        """Days until expiration, None if perpetual."""
        if self.expires_at is None:
            return None
        delta = self.expires_at - datetime.now()
        return max(0, delta.days)


class LicenseValidator:
    """Validates license keys using Ed25519 signatures."""

    def __init__(self):
        self.license_file = Path.home() / ".souleyez" / "license.key"
        self._cached_license: Optional[LicenseInfo] = None

    def get_machine_id(self) -> str:
        """
        Generate a stable machine identifier.
        Used for hardware-bound licenses.
        """
        # Combine multiple hardware identifiers for stability
        components = []

        # Platform info
        components.append(platform.node())
        components.append(platform.machine())

        # Try to get more stable identifiers
        try:
            # On Linux, try machine-id
            machine_id_path = Path("/etc/machine-id")
            if machine_id_path.exists():
                components.append(machine_id_path.read_text().strip())
        except Exception:
            pass

        try:
            # Fallback to UUID based on hardware
            components.append(str(uuid.getnode()))
        except Exception:
            pass

        # Hash all components for a stable ID
        combined = "|".join(components)
        return hashlib.sha256(combined.encode()).hexdigest()[:32]

    def validate(self, license_key: str) -> LicenseInfo:
        """
        Validate a license key.

        Args:
            license_key: Base64-encoded signed license

        Returns:
            LicenseInfo with validation result
        """
        try:
            # Decode the license key
            try:
                padded_key = _add_base64_padding(license_key.strip())
                decoded = base64.urlsafe_b64decode(padded_key)
                payload = json.loads(decoded)
            except Exception as e:
                return LicenseInfo(
                    email="",
                    tier="FREE",
                    issued_at=datetime.now(),
                    expires_at=None,
                    machine_id=None,
                    is_valid=False,
                    error=f"Invalid license format: {e}",
                )

            # Extract components
            data = payload.get("data", {})
            signature = payload.get("signature", "")

            if not data or not signature:
                return LicenseInfo(
                    email="",
                    tier="FREE",
                    issued_at=datetime.now(),
                    expires_at=None,
                    machine_id=None,
                    is_valid=False,
                    error="Missing license data or signature",
                )

            # Verify signature
            if not self._verify_signature(data, signature):
                return LicenseInfo(
                    email=data.get("email", ""),
                    tier="FREE",
                    issued_at=datetime.now(),
                    expires_at=None,
                    machine_id=None,
                    is_valid=False,
                    error="Invalid license signature",
                )

            # Parse dates
            issued_at = datetime.fromisoformat(data["issued_at"])
            expires_at = None
            if data.get("expires_at"):
                expires_at = datetime.fromisoformat(data["expires_at"])

            # Check expiration
            if expires_at and datetime.now() > expires_at:
                return LicenseInfo(
                    email=data.get("email", ""),
                    tier=data.get("tier", "FREE"),
                    issued_at=issued_at,
                    expires_at=expires_at,
                    machine_id=data.get("machine_id"),
                    is_valid=False,
                    error="License has expired",
                )

            # Check machine binding if present
            if data.get("machine_id"):
                current_machine = self.get_machine_id()
                if data["machine_id"] != current_machine:
                    return LicenseInfo(
                        email=data.get("email", ""),
                        tier=data.get("tier", "FREE"),
                        issued_at=issued_at,
                        expires_at=expires_at,
                        machine_id=data.get("machine_id"),
                        is_valid=False,
                        error="License is bound to a different machine",
                    )

            # License is valid
            return LicenseInfo(
                email=data.get("email", ""),
                tier=data.get("tier", "PRO"),
                issued_at=issued_at,
                expires_at=expires_at,
                machine_id=data.get("machine_id"),
                is_valid=True,
                error=None,
            )

        except Exception as e:
            return LicenseInfo(
                email="",
                tier="FREE",
                issued_at=datetime.now(),
                expires_at=None,
                machine_id=None,
                is_valid=False,
                error=f"License validation error: {e}",
            )

    def _verify_signature(self, data: dict, signature_b64: str) -> bool:
        """
        Verify Ed25519 signature of license data.

        Args:
            data: License data dictionary
            signature_b64: Base64-encoded signature

        Returns:
            True if signature is valid
        """
        try:
            from cryptography.hazmat.primitives.asymmetric.ed25519 import (
                Ed25519PublicKey,
            )
            from cryptography.hazmat.primitives.serialization import load_pem_public_key

            # Check if public key is configured
            if LICENSE_PUBLIC_KEY == "REPLACE_WITH_REAL_PUBLIC_KEY_AFTER_GENERATION":
                # Development mode - accept test licenses
                return self._verify_dev_signature(data, signature_b64)

            # Load public key
            public_key = load_pem_public_key(LICENSE_PUBLIC_KEY.encode())

            # Recreate the signed message
            message = json.dumps(data, sort_keys=True, separators=(",", ":")).encode()

            # Decode signature
            signature = base64.urlsafe_b64decode(_add_base64_padding(signature_b64))

            # Verify
            public_key.verify(signature, message)
            return True

        except Exception:
            return False

    def _verify_dev_signature(self, data: dict, signature_b64: str) -> bool:
        """
        Development mode signature verification.
        Uses HMAC with a known dev key for testing.
        """
        import hmac

        DEV_SECRET = "souleyez-dev-license-key-for-testing-only"

        message = json.dumps(data, sort_keys=True, separators=(",", ":")).encode()
        expected = hmac.new(DEV_SECRET.encode(), message, hashlib.sha256).digest()

        try:
            actual = base64.urlsafe_b64decode(_add_base64_padding(signature_b64))
            return hmac.compare_digest(expected, actual)
        except Exception:
            return False

    def save_license(self, license_key: str) -> Tuple[bool, str]:
        """
        Save license key to file after validation.

        Args:
            license_key: License key to save

        Returns:
            (success, message)
        """
        # Validate first
        info = self.validate(license_key)
        if not info.is_valid:
            return False, info.error or "Invalid license"

        # Save to file
        try:
            self.license_file.parent.mkdir(parents=True, exist_ok=True)
            self.license_file.write_text(license_key.strip())

            # Secure the file (owner read/write only)
            os.chmod(self.license_file, 0o600)

            self._cached_license = info
            return True, f"License activated for {info.email}"

        except Exception as e:
            return False, f"Failed to save license: {e}"

    def load_license(self) -> Optional[LicenseInfo]:
        """
        Load and validate saved license.

        Returns:
            LicenseInfo if valid license exists, None otherwise
        """
        if self._cached_license is not None:
            return self._cached_license

        if not self.license_file.exists():
            return None

        try:
            license_key = self.license_file.read_text().strip()
            info = self.validate(license_key)

            if info.is_valid:
                self._cached_license = info
                return info

            return None

        except Exception:
            return None

    def remove_license(self) -> bool:
        """Remove saved license."""
        try:
            if self.license_file.exists():
                self.license_file.unlink()
            self._cached_license = None
            return True
        except Exception:
            return False


# Module-level convenience functions
_validator = None


def _get_validator() -> LicenseValidator:
    global _validator
    if _validator is None:
        _validator = LicenseValidator()
    return _validator


def validate_license(license_key: str) -> LicenseInfo:
    """Validate a license key."""
    return _get_validator().validate(license_key)


def activate_license(license_key: str) -> Tuple[bool, str]:
    """Activate and save a license key."""
    return _get_validator().save_license(license_key)


def get_active_license() -> Optional[LicenseInfo]:
    """Get currently active license."""
    return _get_validator().load_license()


def deactivate_license() -> bool:
    """Remove active license."""
    return _get_validator().remove_license()


def get_machine_id() -> str:
    """Get this machine's ID for hardware-bound licenses."""
    return _get_validator().get_machine_id()
