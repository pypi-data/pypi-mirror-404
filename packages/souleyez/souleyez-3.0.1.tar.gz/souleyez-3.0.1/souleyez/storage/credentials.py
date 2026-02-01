#!/usr/bin/env python3
"""
souleyez.storage.credentials - Credential storage and management

Similar to MSF's creds command - tracks enumerated usernames and discovered passwords.
"""

import re
from typing import Any, Dict, List, Optional

from souleyez.log_config import get_logger

from .crypto import get_crypto_manager
from .database import get_db

logger = get_logger(__name__)


class CredentialsManager:
    def __init__(self, engagement: str = None):
        self.db = get_db()
        self.crypto = get_crypto_manager()
        self.engagement = engagement
        self._ensure_table()

    def validate_master_password(self, password: str):
        """
        Validate master password meets security requirements.

        Requirements:
        - At least 12 characters
        - Contains uppercase letter
        - Contains lowercase letter
        - Contains number
        - Contains special character
        """
        if len(password) < 12:
            raise ValueError("Password must be at least 12 characters")
        if not re.search(r"[A-Z]", password):
            raise ValueError("Password must contain uppercase letter")
        if not re.search(r"[a-z]", password):
            raise ValueError("Password must contain lowercase letter")
        if not re.search(r"[0-9]", password):
            raise ValueError("Password must contain number")
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValueError("Password must contain special character")

    def _encrypt_field(self, value: str) -> Optional[str]:
        """Encrypt a credential field if encryption is enabled."""
        if value is None:
            return None
        if self.crypto.is_encryption_enabled():
            if not self.crypto.is_unlocked():
                # Store with a marker prefix to indicate it needs encryption
                # This allows background workers to store discovered credentials
                # They will be encrypted when the user next unlocks the database
                logger.warning(
                    f"Storing credential field with UNENCRYPTED: marker - crypto locked"
                )
                return f"UNENCRYPTED:{value}"
            return self.crypto.encrypt(value)
        return value

    def _decrypt_field(self, value: str) -> Optional[str]:
        """Decrypt a credential field if encryption is enabled."""
        if value is None:
            return None
        if self.crypto.is_encryption_enabled():
            # Check for unencrypted marker
            if isinstance(value, str) and value.startswith("UNENCRYPTED:"):
                # Strip marker and return plaintext
                return value[12:]  # len("UNENCRYPTED:") = 12
            if not self.crypto.is_unlocked():
                raise RuntimeError(
                    "Credentials are encrypted but crypto manager is locked. Call unlock() first."
                )
            return self.crypto.decrypt(value)
        return value

    def _ensure_table(self):
        """Ensure credentials table exists."""
        conn = self.db.get_connection()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS credentials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                engagement_id INTEGER NOT NULL,
                host_id INTEGER,
                service TEXT,
                port INTEGER,
                protocol TEXT DEFAULT 'tcp',
                username TEXT,
                password TEXT,
                credential_type TEXT DEFAULT 'user',
                status TEXT DEFAULT 'untested',
                tool TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (engagement_id) REFERENCES engagements(id),
                FOREIGN KEY (host_id) REFERENCES hosts(id)
            )
        """)

        # Create index for faster lookups
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_credentials_engagement
            ON credentials(engagement_id)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_credentials_host
            ON credentials(host_id)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_credentials_status
            ON credentials(status)
        """)

        conn.commit()
        conn.close()

    def add_credential(
        self,
        engagement_id: int,
        host_id: int,
        username: str = None,
        password: str = None,
        service: str = None,
        port: int = None,
        protocol: str = "tcp",
        credential_type: str = "user",
        status: str = "untested",
        tool: str = None,
        notes: str = None,
        source: str = None,  # Legacy alias for tool
    ) -> int:
        """
        Add a credential to the database.

        Args:
            engagement_id: Engagement ID
            host_id: Host ID
            username: Username (optional for password-only creds)
            password: Password (optional for username enumeration)
            service: Service name (ssh, smb, mysql, etc.)
            port: Service port
            protocol: Protocol (tcp/udp)
            credential_type: Type of credential (user, password, hash, key)
            status: Status (untested, valid, invalid)
            tool: Tool that discovered this credential
            notes: Additional notes about the credential
            source: Legacy alias for tool parameter

        Returns:
            Credential ID
        """
        # Handle legacy 'source' parameter
        if source and not tool:
            tool = source
        # Check for duplicates (must encrypt before comparing)
        encrypted_username = self._encrypt_field(username) if username else None
        encrypted_password = self._encrypt_field(password) if password else None

        existing = self.get_credential(
            engagement_id,
            host_id,
            encrypted_username,
            encrypted_password,
            service,
            port,
        )
        if existing:
            # Update status if this one is more definitive
            if status == "valid" and existing["status"] != "valid":
                self._update_status(existing["id"], status, tool)
            return existing["id"]

        # Special case: If adding a valid username:password pair, check if we have
        # a username-only entry that should be upgraded instead of creating duplicate
        if username and password and status == "valid":
            username_only = self.get_credential(
                engagement_id, host_id, encrypted_username, None, service, port
            )
            if username_only:
                # Upgrade the existing entry with the password
                self._update_credential(
                    username_only["id"],
                    password=encrypted_password,
                    status=status,
                    tool=tool,
                )
                return username_only["id"]

        data = {
            "engagement_id": engagement_id,
            "host_id": host_id,
            "service": service,
            "port": port,
            "protocol": protocol,
            "username": encrypted_username,
            "password": encrypted_password,
            "credential_type": credential_type,
            "status": status,
            "tool": tool,
            "notes": notes,
        }

        cred_id = self.db.insert("credentials", data)

        # Audit log (never log actual password)
        logger.info(
            "Credential added",
            extra={
                "engagement": self.engagement or engagement_id,
                "cred_id": cred_id,
                "username": username if username else "<none>",
                "host_id": host_id,
                "service": service,
                "port": port,
                "tool": tool,
            },
        )

        return cred_id

    def get_credential(
        self,
        engagement_id: int,
        host_id: int,
        username: str = None,
        password: str = None,
        service: str = None,
        port: int = None,
    ) -> Optional[Dict[str, Any]]:
        """Check if credential already exists."""
        query = """
            SELECT * FROM credentials
            WHERE engagement_id = ? AND host_id = ?
        """
        params = [engagement_id, host_id]

        if username is not None:
            query += " AND username = ?"
            params.append(username)
        else:
            query += " AND username IS NULL"

        if password is not None:
            query += " AND password = ?"
            params.append(password)
        else:
            query += " AND password IS NULL"

        if service is not None:
            query += " AND service = ?"
            params.append(service)

        if port is not None:
            query += " AND port = ?"
            params.append(port)

        query += " LIMIT 1"

        result = self.db.execute_one(query, tuple(params))

        # Audit log credential access (never log password)
        if result:
            logger.info(
                "Credential accessed",
                extra={
                    "engagement": self.engagement or engagement_id,
                    "cred_id": result.get("id"),
                    "username": username if username else "<none>",
                    "host_id": host_id,
                },
            )

        return result

    def _update_status(self, credential_id: int, status: str, tool: str = None):
        """Update credential status."""
        conn = self.db.get_connection()
        if tool:
            conn.execute(
                "UPDATE credentials SET status = ?, tool = ? WHERE id = ?",
                (status, tool, credential_id),
            )
        else:
            conn.execute(
                "UPDATE credentials SET status = ? WHERE id = ?",
                (status, credential_id),
            )
        conn.commit()
        conn.close()

        logger.info(
            "Credential status updated",
            extra={
                "engagement": self.engagement,
                "cred_id": credential_id,
                "new_status": status,
                "tool": tool,
            },
        )

    def _update_credential(
        self,
        credential_id: int,
        password: str = None,
        status: str = None,
        tool: str = None,
        notes: str = None,
        last_tested: str = None,
    ):
        """Update credential with password and/or status."""
        conn = self.db.get_connection()

        updates = []
        params = []

        if password is not None:
            updates.append("password = ?")
            params.append(password)

        if status is not None:
            updates.append("status = ?")
            params.append(status)

        if tool is not None:
            updates.append("tool = ?")
            params.append(tool)

        if notes is not None:
            updates.append("notes = ?")
            params.append(notes)

        if last_tested is not None:
            updates.append("last_tested = ?")
            params.append(last_tested)

        if updates:
            query = f"UPDATE credentials SET {', '.join(updates)} WHERE id = ?"
            params.append(credential_id)
            conn.execute(query, tuple(params))

        conn.commit()
        conn.close()

    def update_credential_status(
        self, credential_id: int, status: str = None, notes: str = None
    ):
        """
        Update the status and/or notes of a credential.

        Args:
            credential_id: Credential ID
            status: New status (valid, invalid, untested, discovered, etc.)
            notes: Optional notes about the credential

        Returns:
            bool: True if successful
        """
        from datetime import datetime

        # Update last_tested if status is changing
        last_tested = datetime.now().isoformat() if status else None

        self._update_credential(
            credential_id, status=status, notes=notes, last_tested=last_tested
        )

        logger.info(
            "Credential status updated",
            extra={
                "engagement": self.engagement,
                "cred_id": credential_id,
                "new_status": status,
            },
        )

        return True

    def delete_credential(self, credential_id: int):
        """
        Delete a credential.

        Args:
            credential_id: Credential ID to delete

        Raises:
            PermissionError: If user lacks CREDENTIAL_DELETE permission
        """
        # Check permission
        from souleyez.auth import get_current_user
        from souleyez.auth.permissions import Permission, PermissionChecker

        user = get_current_user()
        if user:
            checker = PermissionChecker(user.role, user.tier)
            if not checker.has_permission(Permission.CREDENTIAL_DELETE):
                raise PermissionError("Permission denied: CREDENTIAL_DELETE required")

        # Get username for audit log before deleting
        cred = self.db.execute_one(
            "SELECT username FROM credentials WHERE id = ?", (credential_id,)
        )
        username = cred.get("username") if cred else "<unknown>"

        conn = self.db.get_connection()
        conn.execute("DELETE FROM credentials WHERE id = ?", (credential_id,))
        conn.commit()
        conn.close()

        logger.info(
            "Credential deleted",
            extra={
                "engagement": self.engagement,
                "cred_id": credential_id,
                "username": username,
            },
        )

    def enable_encryption(self, password: str) -> bool:
        """
        Enable encryption for credentials.

        Args:
            password: Master password

        Returns:
            True if encryption enabled successfully
        """
        # Validate password complexity
        self.validate_master_password(password)

        result = self.crypto.enable_encryption(password)

        if result:
            logger.info("Encryption enabled", extra={"engagement": self.engagement})
        else:
            logger.warning(
                "Encryption enable failed", extra={"engagement": self.engagement}
            )

        return result

    def unlock(self, password: str) -> bool:
        """
        Unlock encrypted credentials.

        Args:
            password: Master password

        Returns:
            True if unlock successful
        """
        result = self.crypto.unlock(password)

        if result:
            logger.info(
                "Credentials unlocked",
                extra={"engagement": self.engagement, "success": True},
            )
        else:
            logger.warning(
                "Credentials unlock failed",
                extra={"engagement": self.engagement, "success": False},
            )

        return result

    def list_credentials(
        self,
        engagement_id: int,
        host_id: int = None,
        service: str = None,
        status: str = None,
        decrypt: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        List credentials for an engagement.

        Args:
            engagement_id: Engagement ID
            host_id: Filter by host (optional)
            service: Filter by service (optional)
            status: Filter by status (optional)
            decrypt: Whether to decrypt credentials (default: True)

        Returns:
            List of credentials with host information
        """
        query = """
            SELECT
                c.*,
                h.ip_address,
                h.hostname
            FROM credentials c
            LEFT JOIN hosts h ON c.host_id = h.id
            WHERE c.engagement_id = ?
        """
        params = [engagement_id]

        if host_id:
            query += " AND c.host_id = ?"
            params.append(host_id)

        if service:
            query += " AND c.service = ?"
            params.append(service)

        if status:
            query += " AND c.status = ?"
            params.append(status)

        query += " ORDER BY c.created_at DESC"

        results = self.db.execute(query, tuple(params))

        # Decrypt username and password fields if requested
        if decrypt:
            for row in results:
                if row.get("username"):
                    row["username"] = self._decrypt_field(row["username"])
                if row.get("password"):
                    row["password"] = self._decrypt_field(row["password"])
        else:
            # Mask credentials when not decrypting (for display purposes)
            for row in results:
                if row.get("username"):
                    row["username"] = "••••••••"
                if row.get("password"):
                    row["password"] = "••••••••"

        return results

    def list_credentials_for_engagement(
        self, engagement_id: int, decrypt: bool = True
    ) -> List[Dict[str, Any]]:
        """
        List all credentials for an engagement (alias method for compatibility).

        Args:
            engagement_id: Engagement ID
            decrypt: Whether to decrypt credentials (default: True)

        Returns:
            List of credentials with host information
        """
        return self.list_credentials(engagement_id, decrypt=decrypt)

    def get_stats(self, engagement_id: int) -> Dict[str, int]:
        """Get credential statistics for an engagement."""
        conn = self.db.get_connection()

        # Total credentials
        total = conn.execute(
            "SELECT COUNT(*) as count FROM credentials WHERE engagement_id = ?",
            (engagement_id,),
        ).fetchone()["count"]

        # Valid credentials (confirmed working)
        valid = conn.execute(
            "SELECT COUNT(*) as count FROM credentials WHERE engagement_id = ? AND status = 'valid'",
            (engagement_id,),
        ).fetchone()["count"]

        # Username-only (enumerated users)
        users_only = conn.execute(
            "SELECT COUNT(*) as count FROM credentials WHERE engagement_id = ? AND username IS NOT NULL AND password IS NULL",
            (engagement_id,),
        ).fetchone()["count"]

        # Password-only
        passwords_only = conn.execute(
            "SELECT COUNT(*) as count FROM credentials WHERE engagement_id = ? AND username IS NULL AND password IS NOT NULL",
            (engagement_id,),
        ).fetchone()["count"]

        # Username:password pairs
        pairs = conn.execute(
            "SELECT COUNT(*) as count FROM credentials WHERE engagement_id = ? AND username IS NOT NULL AND password IS NOT NULL",
            (engagement_id,),
        ).fetchone()["count"]

        conn.close()

        return {
            "total": total,
            "valid": valid,
            "users_only": users_only,
            "passwords_only": passwords_only,
            "pairs": pairs,
        }

    def encrypt_all_unencrypted(self) -> Dict[str, int]:
        """
        Encrypt all plaintext credentials in the database.

        This should be called after unlocking crypto to encrypt credentials
        that were stored while the worker was running without the master password.

        Returns:
            Dict with counts of encrypted credentials
        """
        if not self.crypto.is_encryption_enabled():
            return {"error": "Encryption not enabled"}

        if not self.crypto.is_unlocked():
            return {"error": "Crypto manager is locked - cannot encrypt"}

        conn = self.db.get_connection()

        # Get all credentials
        rows = conn.execute("SELECT id, username, password FROM credentials").fetchall()

        encrypted_count = 0
        skipped_count = 0

        for row in rows:
            cred_id = row["id"]
            username = row["username"]
            password = row["password"]

            needs_update = False
            new_username = username
            new_password = password

            # Check if username needs encryption
            if username and isinstance(username, str):
                if username.startswith("UNENCRYPTED:"):
                    # Strip marker and encrypt
                    plaintext = username[12:]
                    new_username = self.crypto.encrypt(plaintext)
                    needs_update = True
                else:
                    # Try to decrypt - if it works, already encrypted
                    try:
                        self.crypto.decrypt(username)
                        # Already encrypted, skip
                    except Exception:
                        # Not encrypted and no marker - encrypt as-is (legacy data)
                        new_username = self.crypto.encrypt(username)
                        needs_update = True

            # Check if password needs encryption
            if password and isinstance(password, str):
                if password.startswith("UNENCRYPTED:"):
                    # Strip marker and encrypt
                    plaintext = password[12:]
                    new_password = self.crypto.encrypt(plaintext)
                    needs_update = True
                else:
                    # Try to decrypt - if it works, already encrypted
                    try:
                        self.crypto.decrypt(password)
                        # Already encrypted, skip
                    except Exception:
                        # Not encrypted and no marker - encrypt as-is (legacy data)
                        new_password = self.crypto.encrypt(password)
                        needs_update = True

            if needs_update:
                conn.execute(
                    "UPDATE credentials SET username = ?, password = ? WHERE id = ?",
                    (new_username, new_password, cred_id),
                )
                encrypted_count += 1
            else:
                skipped_count += 1

        conn.commit()
        conn.close()

        logger.info(
            f"Encrypted {encrypted_count} credentials, skipped {skipped_count} already encrypted"
        )

        return {
            "encrypted": encrypted_count,
            "skipped": skipped_count,
            "total": encrypted_count + skipped_count,
        }

    def remove_duplicates(self, engagement_id: int) -> Dict[str, int]:
        """
        Remove duplicate credentials from the database.
        Keeps the one with the most definitive status (valid > untested).

        Returns:
            dict: {'removed': count, 'kept': count}
        """
        # Get all credentials for this engagement
        query = """
            SELECT id, host_id, username, password, service, port, status, created_at
            FROM credentials
            WHERE engagement_id = ?
            ORDER BY 
                CASE status 
                    WHEN 'valid' THEN 1 
                    WHEN 'invalid' THEN 2 
                    ELSE 3 
                END,
                created_at DESC
        """

        all_creds = self.db.execute(query, (engagement_id,))

        seen = set()
        to_remove = []
        kept_count = 0

        for cred in all_creds:
            # Create a unique key for this credential
            key = (
                cred["host_id"],
                cred["username"],
                cred["password"],
                cred["service"],
                cred["port"],
            )

            if key in seen:
                # Duplicate found
                to_remove.append(cred["id"])
            else:
                # First occurrence, keep it
                seen.add(key)
                kept_count += 1

        # Remove duplicates
        if to_remove:
            placeholders = ",".join(["?"] * len(to_remove))
            self.db.execute(
                f"DELETE FROM credentials WHERE id IN ({placeholders})",
                tuple(to_remove),
            )

        logger.info(
            f"Removed {len(to_remove)} duplicate credentials, kept {kept_count}"
        )

        return {"removed": len(to_remove), "kept": kept_count}
