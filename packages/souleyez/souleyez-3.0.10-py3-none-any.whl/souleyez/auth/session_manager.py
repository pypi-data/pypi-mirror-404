"""
souleyez.auth.session_manager - Session management

Handles:
- Session token generation and validation
- Session storage and cleanup
- Current user context
"""

import hashlib
import json
import secrets
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from .permissions import Role, Tier
from .user_manager import User, UserManager

# Session configuration
SESSION_TOKEN_BYTES = 32
DEFAULT_SESSION_HOURS = 8
SESSION_FILE_NAME = "session.json"


@dataclass
class Session:
    """Active user session."""

    id: str
    user_id: str
    token: str  # Only available at creation time
    expires_at: datetime
    created_at: datetime
    ip_address: Optional[str]
    user_agent: Optional[str]
    vault_unlocked_at: Optional[datetime] = None  # Vault session binding


class SessionManager:
    """Manages user sessions."""

    def __init__(self, db_path: str, config_dir: Optional[str] = None):
        self.db_path = db_path
        self.config_dir = Path(config_dir) if config_dir else Path.home() / ".souleyez"
        self.session_file = self.config_dir / SESSION_FILE_NAME
        self._current_user: Optional[User] = None
        self._current_session: Optional[Session] = None
        self._vault_timeout_minutes = 30  # Vault session timeout
        self._cross_layer_delay_applied_at: Optional[datetime] = None

    def _get_conn(self) -> sqlite3.Connection:
        """Get database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _generate_session_id(self) -> str:
        """Generate unique session ID."""
        return f"ses_{secrets.token_hex(8)}"

    def _generate_token(self) -> str:
        """Generate secure session token."""
        return secrets.token_urlsafe(SESSION_TOKEN_BYTES)

    def _hash_token(self, token: str) -> str:
        """Hash token for storage (we don't store plain tokens)."""
        return hashlib.sha256(token.encode()).hexdigest()

    # =========================================================================
    # Session CRUD
    # =========================================================================

    def create_session(
        self,
        user: User,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        duration_hours: int = DEFAULT_SESSION_HOURS,
        vault_unlocked_at: Optional[datetime] = None,
    ) -> Session:
        """
        Create a new session for a user.

        Args:
            user: Authenticated user
            ip_address: Client IP
            user_agent: Client user agent
            duration_hours: Session duration
            vault_unlocked_at: When vault was unlocked (for binding)

        Returns:
            Session with token (token only available now!)
        """
        session_id = self._generate_session_id()
        token = self._generate_token()
        token_hash = self._hash_token(token)

        now = datetime.now()
        expires_at = now + timedelta(hours=duration_hours)

        conn = self._get_conn()
        conn.execute(
            """
            INSERT INTO sessions (id, user_id, token_hash, expires_at, created_at, ip_address, user_agent)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (
                session_id,
                user.id,
                token_hash,
                expires_at.isoformat(),
                now.isoformat(),
                ip_address,
                user_agent,
            ),
        )
        conn.commit()
        conn.close()

        session = Session(
            id=session_id,
            user_id=user.id,
            token=token,  # Plain token returned only at creation
            expires_at=expires_at,
            created_at=now,
            ip_address=ip_address,
            user_agent=user_agent,
            vault_unlocked_at=vault_unlocked_at or now,
        )

        # Save session to local file
        self._save_session_to_file(session)

        return session

    def validate_token(self, token: str) -> Optional[User]:
        """
        Validate a session token and return the user.

        Returns:
            User if token is valid, None otherwise
        """
        token_hash = self._hash_token(token)

        conn = self._get_conn()
        row = conn.execute(
            """
            SELECT s.*, u.*
            FROM sessions s
            JOIN users u ON s.user_id = u.id
            WHERE s.token_hash = ? AND s.expires_at > ?
        """,
            (token_hash, datetime.now().isoformat()),
        ).fetchone()
        conn.close()

        if row is None:
            return None

        # Build user from row
        user_manager = UserManager(self.db_path)
        return user_manager.get_user_by_id(row["user_id"])

    def invalidate_session(self, session_id: str) -> bool:
        """Invalidate (logout) a specific session."""
        conn = self._get_conn()
        result = conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
        conn.commit()
        conn.close()

        # Clear local session file
        self._clear_session_file()

        return result.rowcount > 0

    def invalidate_user_sessions(self, user_id: str) -> int:
        """Invalidate all sessions for a user."""
        conn = self._get_conn()
        result = conn.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
        conn.commit()
        count = result.rowcount
        conn.close()

        # Clear local session file if it belongs to this user
        if self._current_user and self._current_user.id == user_id:
            self._clear_session_file()

        return count

    def cleanup_expired_sessions(self) -> int:
        """Remove all expired sessions from the database."""
        conn = self._get_conn()
        result = conn.execute(
            "DELETE FROM sessions WHERE expires_at < ?", (datetime.now().isoformat(),)
        )
        conn.commit()
        count = result.rowcount
        conn.close()
        return count

    # =========================================================================
    # Local Session Persistence
    # =========================================================================

    def is_vault_session_valid(self) -> bool:
        """
        Check if vault unlock is still valid (30 min inactivity).

        Returns:
            True if vault session is still valid
        """
        if (
            self._current_session is None
            or self._current_session.vault_unlocked_at is None
        ):
            return False

        elapsed = datetime.now() - self._current_session.vault_unlocked_at
        return elapsed < timedelta(minutes=self._vault_timeout_minutes)

    def require_full_reauth(self) -> bool:
        """
        Check if both layers need re-authentication.

        Returns:
            True if full re-auth (vault + user) is required
        """
        if self._current_session is None:
            return True

        # Check if vault session has timed out
        if not self.is_vault_session_valid():
            return True

        # Check if user session has expired
        if datetime.now() >= self._current_session.expires_at:
            return True

        return False

    def apply_cross_layer_delay(self, vault_failures: int):
        """
        Apply delay based on vault failures before allowing user login.

        Args:
            vault_failures: Number of recent vault unlock failures
        """
        import time

        import click

        if vault_failures >= 2:
            delay = 30 * (vault_failures - 1)  # 30s for 2, 60s for 3+

            # Avoid re-applying same delay multiple times
            if self._cross_layer_delay_applied_at:
                since_last = (
                    datetime.now() - self._cross_layer_delay_applied_at
                ).total_seconds()
                if since_last < delay:
                    return

            click.echo(
                f"\n⚠️  Security delay: {delay} seconds (vault failures detected)"
            )

            # Show countdown
            for remaining in range(delay, 0, -1):
                click.echo(f"\r   Continuing in {remaining}s...  ", nl=False)
                time.sleep(1)
            click.echo("\r   Continuing...              ")

            self._cross_layer_delay_applied_at = datetime.now()

    def _save_session_to_file(self, session: Session):
        """Save session token to local file for persistence."""
        self.config_dir.mkdir(parents=True, exist_ok=True)

        data = {
            "session_id": session.id,
            "token": session.token,
            "expires_at": session.expires_at.isoformat(),
            "user_id": session.user_id,
            "vault_unlocked_at": (
                session.vault_unlocked_at.isoformat()
                if session.vault_unlocked_at
                else None
            ),
        }

        self.session_file.write_text(json.dumps(data, indent=2))
        # Secure the file
        self.session_file.chmod(0o600)

    def _load_session_from_file(self) -> Optional[dict]:
        """Load session data from local file."""
        if not self.session_file.exists():
            return None

        try:
            data = json.loads(self.session_file.read_text())
            # Check expiration
            expires_at = datetime.fromisoformat(data["expires_at"])
            if expires_at < datetime.now():
                self._clear_session_file()
                return None
            return data
        except Exception:
            return None

    def _clear_session_file(self):
        """Remove local session file."""
        if self.session_file.exists():
            self.session_file.unlink()
        self._current_user = None
        self._current_session = None

    # =========================================================================
    # Current User Context
    # =========================================================================

    def get_current_user(self) -> Optional[User]:
        """
        Get the currently logged-in user.

        Checks local session file and validates against database.
        """
        if self._current_user is not None:
            return self._current_user

        session_data = self._load_session_from_file()
        if session_data is None:
            return None

        user = self.validate_token(session_data["token"])
        if user is None:
            self._clear_session_file()
            return None

        self._current_user = user
        return user

    def set_current_user(self, user: Optional[User]):
        """Set the current user in memory."""
        self._current_user = user

    def is_logged_in(self) -> bool:
        """Check if a user is currently logged in."""
        return self.get_current_user() is not None

    def logout(self) -> bool:
        """Log out the current user."""
        session_data = self._load_session_from_file()
        if session_data:
            self.invalidate_session(session_data["session_id"])

        self._clear_session_file()
        self._current_user = None
        return True
