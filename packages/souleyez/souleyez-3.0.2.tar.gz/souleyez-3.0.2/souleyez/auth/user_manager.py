"""
souleyez.auth.user_manager - User account management

Handles:
- User CRUD operations
- Password hashing (PBKDF2-HMAC-SHA256, 480k iterations)
- Default admin user creation
- Tier management for licensing
"""

import hashlib
import re
import secrets
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from .permissions import Role, Tier

# OWASP 2023 recommendation for PBKDF2-HMAC-SHA256
HASH_ITERATIONS = 480_000
SALT_LENGTH = 32
MIN_PASSWORD_LENGTH = 8


@dataclass
class User:
    """User account model."""

    id: str
    username: str
    email: Optional[str]
    role: Role
    tier: Tier
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime]
    license_key: Optional[str]
    license_expires_at: Optional[datetime]
    failed_login_attempts: int
    locked_until: Optional[datetime]

    # Password fields (not exposed)
    _password_hash: str = ""
    _salt: str = ""

    @property
    def is_locked(self) -> bool:
        """Check if account is currently locked."""
        if self.locked_until is None:
            return False
        return datetime.now() < self.locked_until

    @property
    def is_pro(self) -> bool:
        """Check if user has Pro tier."""
        return self.tier == Tier.PRO

    @property
    def is_admin(self) -> bool:
        """Check if user is admin."""
        return self.role == Role.ADMIN


class UserManager:
    """Manages user accounts in the database."""

    def __init__(self, db_path: str):
        self.db_path = db_path

    def _get_conn(self) -> sqlite3.Connection:
        """Get database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    # =========================================================================
    # Password Hashing
    # =========================================================================

    def _generate_salt(self) -> str:
        """Generate a cryptographically secure salt."""
        return secrets.token_hex(SALT_LENGTH)

    def _hash_password(self, password: str, salt: str) -> str:
        """
        Hash password using PBKDF2-HMAC-SHA256.

        Args:
            password: Plain text password
            salt: Hex-encoded salt

        Returns:
            Hex-encoded password hash
        """
        key = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), bytes.fromhex(salt), HASH_ITERATIONS
        )
        return key.hex()

    def _verify_password(self, password: str, password_hash: str, salt: str) -> bool:
        """Verify a password against stored hash."""
        computed_hash = self._hash_password(password, salt)
        # Constant-time comparison to prevent timing attacks
        return secrets.compare_digest(computed_hash, password_hash)

    def _validate_password_strength(self, password: str) -> tuple[bool, str]:
        """
        Validate password meets security requirements.

        Requirements:
        - Minimum 8 characters
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one digit
        - At least one special character

        Returns:
            (is_valid, error_message)
        """
        if len(password) < MIN_PASSWORD_LENGTH:
            return False, f"Password must be at least {MIN_PASSWORD_LENGTH} characters"

        if not re.search(r"[A-Z]", password):
            return False, "Password must contain at least one uppercase letter"

        if not re.search(r"[a-z]", password):
            return False, "Password must contain at least one lowercase letter"

        if not re.search(r"\d", password):
            return False, "Password must contain at least one digit"

        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False, "Password must contain at least one special character"

        return True, ""

    # =========================================================================
    # User CRUD
    # =========================================================================

    def _generate_user_id(self) -> str:
        """Generate unique user ID."""
        return f"usr_{secrets.token_hex(8)}"

    def create_user(
        self,
        username: str,
        password: str,
        email: Optional[str] = None,
        role: Role = Role.ANALYST,
        tier: Tier = Tier.FREE,
        skip_password_validation: bool = False,
    ) -> tuple[Optional[User], str]:
        """
        Create a new user account.

        Args:
            username: Unique username
            password: Plain text password (will be hashed)
            email: Optional email address
            role: User role (default: analyst)
            tier: License tier (default: FREE)
            skip_password_validation: Skip password strength check (for admin creation)

        Returns:
            (User object, error_message) - User is None if creation failed
        """
        # Validate username
        if not username or len(username) < 3:
            return None, "Username must be at least 3 characters"

        if not re.match(r"^[a-zA-Z0-9_-]+$", username):
            return (
                None,
                "Username can only contain letters, numbers, underscores, and hyphens",
            )

        # Validate password
        if not skip_password_validation:
            is_valid, error = self._validate_password_strength(password)
            if not is_valid:
                return None, error

        # Generate salt and hash password
        salt = self._generate_salt()
        password_hash = self._hash_password(password, salt)

        user_id = self._generate_user_id()
        now = datetime.now().isoformat()

        try:
            conn = self._get_conn()
            conn.execute(
                """
                INSERT INTO users (
                    id, username, password_hash, salt, email, role, tier,
                    is_active, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    user_id,
                    username.lower(),
                    password_hash,
                    salt,
                    email,
                    role.value,
                    tier.value,
                    True,
                    now,
                    now,
                ),
            )
            conn.commit()
            conn.close()

            return self.get_user_by_id(user_id), ""

        except sqlite3.IntegrityError:
            return None, f"Username '{username}' already exists"
        except Exception as e:
            return None, f"Failed to create user: {e}"

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        conn = self._get_conn()
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        conn.close()

        if row is None:
            return None

        return self._row_to_user(row)

    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username (case-insensitive)."""
        conn = self._get_conn()
        row = conn.execute(
            "SELECT * FROM users WHERE username = ?", (username.lower(),)
        ).fetchone()
        conn.close()

        if row is None:
            return None

        return self._row_to_user(row)

    def list_users(self, include_inactive: bool = False) -> List[User]:
        """List all users."""
        conn = self._get_conn()

        if include_inactive:
            rows = conn.execute("SELECT * FROM users ORDER BY username").fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM users WHERE is_active = 1 ORDER BY username"
            ).fetchall()

        conn.close()
        return [self._row_to_user(row) for row in rows]

    def update_user(
        self,
        user_id: str,
        email: Optional[str] = None,
        role: Optional[Role] = None,
        tier: Optional[Tier] = None,
        is_active: Optional[bool] = None,
    ) -> tuple[bool, str]:
        """
        Update user fields.

        Returns:
            (success, error_message)
        """
        updates = []
        params = []

        if email is not None:
            updates.append("email = ?")
            params.append(email)

        if role is not None:
            updates.append("role = ?")
            params.append(role.value)

        if tier is not None:
            updates.append("tier = ?")
            params.append(tier.value)

        if is_active is not None:
            updates.append("is_active = ?")
            params.append(is_active)

        if not updates:
            return False, "No fields to update"

        updates.append("updated_at = ?")
        params.append(datetime.now().isoformat())
        params.append(user_id)

        try:
            conn = self._get_conn()
            result = conn.execute(
                f"UPDATE users SET {', '.join(updates)} WHERE id = ?",  # nosec B608 - column names are whitelisted, not user input
                params,
            )
            conn.commit()
            conn.close()

            if result.rowcount == 0:
                return False, "User not found"

            return True, ""

        except Exception as e:
            return False, f"Failed to update user: {e}"

    def change_password(
        self, user_id: str, new_password: str, skip_validation: bool = False
    ) -> tuple[bool, str]:
        """Change user password."""
        if not skip_validation:
            is_valid, error = self._validate_password_strength(new_password)
            if not is_valid:
                return False, error

        salt = self._generate_salt()
        password_hash = self._hash_password(new_password, salt)

        try:
            conn = self._get_conn()
            result = conn.execute(
                """
                UPDATE users
                SET password_hash = ?, salt = ?, updated_at = ?
                WHERE id = ?
            """,
                (password_hash, salt, datetime.now().isoformat(), user_id),
            )
            conn.commit()
            conn.close()

            if result.rowcount == 0:
                return False, "User not found"

            return True, ""

        except Exception as e:
            return False, f"Failed to change password: {e}"

    def delete_user(self, user_id: str) -> tuple[bool, str]:
        """Delete a user account."""
        try:
            conn = self._get_conn()
            result = conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
            conn.commit()
            conn.close()

            if result.rowcount == 0:
                return False, "User not found"

            return True, ""

        except Exception as e:
            return False, f"Failed to delete user: {e}"

    # =========================================================================
    # Authentication
    # =========================================================================

    def authenticate(self, username: str, password: str) -> tuple[Optional[User], str]:
        """
        Authenticate user with username and password.

        Returns:
            (User, error_message) - User is None if auth failed
        """
        conn = self._get_conn()
        row = conn.execute(
            "SELECT * FROM users WHERE username = ?", (username.lower(),)
        ).fetchone()

        if row is None:
            conn.close()
            return None, "Invalid username or password"

        user = self._row_to_user(row)

        # Check if account is locked
        if user.is_locked:
            conn.close()
            return None, "Account is temporarily locked. Try again later."

        # Check if account is active
        if not user.is_active:
            conn.close()
            return None, "Account is disabled"

        # Verify password
        if not self._verify_password(password, user._password_hash, user._salt):
            # Increment failed login attempts
            self._record_failed_login(conn, user.id)
            conn.close()
            return None, "Invalid username or password"

        # Successful login - reset failed attempts and update last_login
        conn.execute(
            """
            UPDATE users
            SET failed_login_attempts = 0, locked_until = NULL, last_login = ?
            WHERE id = ?
        """,
            (datetime.now().isoformat(), user.id),
        )
        conn.commit()
        conn.close()

        return user, ""

    def _record_failed_login(self, conn: sqlite3.Connection, user_id: str):
        """Record a failed login attempt, potentially locking the account."""
        MAX_ATTEMPTS = 5
        LOCKOUT_MINUTES = 15

        conn.execute(
            """
            UPDATE users
            SET failed_login_attempts = failed_login_attempts + 1
            WHERE id = ?
        """,
            (user_id,),
        )

        # Check if we need to lock the account
        row = conn.execute(
            "SELECT failed_login_attempts FROM users WHERE id = ?", (user_id,)
        ).fetchone()

        if row and row[0] >= MAX_ATTEMPTS:
            from datetime import timedelta

            locked_until = datetime.now() + timedelta(minutes=LOCKOUT_MINUTES)
            conn.execute(
                """
                UPDATE users SET locked_until = ? WHERE id = ?
            """,
                (locked_until.isoformat(), user_id),
            )

        conn.commit()

    # =========================================================================
    # Default Admin
    # =========================================================================

    def ensure_default_admin(self) -> tuple[bool, str]:
        """
        Ensure a default admin user exists.
        Called on first startup.

        Returns:
            (created, message)
        """
        # Check if any admin exists
        conn = self._get_conn()
        row = conn.execute(
            "SELECT COUNT(*) FROM users WHERE role = ?", (Role.ADMIN.value,)
        ).fetchone()
        conn.close()

        if row[0] > 0:
            return False, "Admin user already exists"

        # Generate a secure random password
        default_password = secrets.token_urlsafe(16)

        user, error = self.create_user(
            username="admin",
            password=default_password,
            role=Role.ADMIN,
            tier=Tier.FREE,  # Start FREE, upgrade when license is activated
            skip_password_validation=True,
        )

        if user is None:
            return False, f"Failed to create admin: {error}"

        # Return the generated password so it can be displayed once
        return True, default_password

    def get_user_count(self) -> int:
        """Get total number of users."""
        conn = self._get_conn()
        row = conn.execute("SELECT COUNT(*) FROM users").fetchone()
        conn.close()
        return row[0] if row else 0

    # =========================================================================
    # Tier Management (for licensing)
    # =========================================================================

    def set_user_tier(
        self,
        user_id: str,
        tier: Tier,
        license_key: Optional[str] = None,
        expires_at: Optional[datetime] = None,
        _bypass_validation: bool = False,
    ) -> tuple[bool, str]:
        """
        Set user's license tier.

        Upgrading to PRO requires a valid license. Use the licensing module
        to activate a license first, which will call this with validation bypassed.

        Args:
            user_id: User ID
            tier: New tier
            license_key: Optional license key reference (truncated)
            expires_at: Optional expiration date
            _bypass_validation: Internal flag, set by licensing module

        Returns:
            (success, error_message)
        """
        # Validate license when upgrading to PRO
        if tier == Tier.PRO and not _bypass_validation:
            try:
                from souleyez.licensing import get_active_license

                license_info = get_active_license()

                if not license_info or not license_info.is_valid:
                    return (
                        False,
                        "Valid license required for Pro tier. Use 'souleyez license activate <key>'",
                    )

                # Use license info for expiration
                expires_at = license_info.expires_at

            except ImportError:
                return False, "Licensing module not available"
            except Exception as e:
                return False, f"License validation failed: {e}"

        try:
            conn = self._get_conn()
            conn.execute(
                """
                UPDATE users
                SET tier = ?, license_key = ?, license_expires_at = ?, updated_at = ?
                WHERE id = ?
            """,
                (
                    tier.value,
                    license_key,
                    expires_at.isoformat() if expires_at else None,
                    datetime.now().isoformat(),
                    user_id,
                ),
            )
            conn.commit()
            conn.close()
            return True, ""

        except Exception as e:
            return False, f"Failed to set tier: {e}"

    def reset_all_pro_tiers(self) -> tuple[int, str]:
        """
        Reset all users with PRO tier to FREE tier.

        Called when license is deactivated to ensure no users retain Pro access.

        Returns:
            (count_reset, error_message)
        """
        try:
            conn = self._get_conn()
            cursor = conn.execute(
                """
                UPDATE users
                SET tier = ?, license_key = NULL, license_expires_at = NULL, updated_at = ?
                WHERE tier = ?
            """,
                (Tier.FREE.value, datetime.now().isoformat(), Tier.PRO.value),
            )
            count = cursor.rowcount
            conn.commit()
            conn.close()
            return count, ""
        except Exception as e:
            return 0, f"Failed to reset tiers: {e}"

    # =========================================================================
    # Helpers
    # =========================================================================

    def _row_to_user(self, row: sqlite3.Row) -> User:
        """Convert database row to User object."""
        user = User(
            id=row["id"],
            username=row["username"],
            email=row["email"],
            role=Role(row["role"]),
            tier=Tier(row["tier"]),
            is_active=bool(row["is_active"]),
            created_at=(
                datetime.fromisoformat(row["created_at"])
                if row["created_at"]
                else datetime.now()
            ),
            updated_at=(
                datetime.fromisoformat(row["updated_at"])
                if row["updated_at"]
                else datetime.now()
            ),
            last_login=(
                datetime.fromisoformat(row["last_login"]) if row["last_login"] else None
            ),
            license_key=row["license_key"],
            license_expires_at=(
                datetime.fromisoformat(row["license_expires_at"])
                if row["license_expires_at"]
                else None
            ),
            failed_login_attempts=row["failed_login_attempts"] or 0,
            locked_until=(
                datetime.fromisoformat(row["locked_until"])
                if row["locked_until"]
                else None
            ),
        )
        # Set password fields (private)
        user._password_hash = row["password_hash"]
        user._salt = row["salt"]
        return user
