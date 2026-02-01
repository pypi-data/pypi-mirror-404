"""
souleyez.auth - Authentication and authorization system

Usage:
    from souleyez.auth import get_current_user, requires_pro, Role, Tier

    user = get_current_user()
    if user and user.is_pro:
        # Pro feature access
        pass
"""

from .audit import AuditAction, AuditLogger, audit_log, get_audit_logger
from .permissions import (
    PRO_TIER_PERMISSIONS,
    ROLE_PERMISSIONS,
    Permission,
    PermissionChecker,
    Role,
    Tier,
    requires_permission,
    requires_pro,
    requires_role,
)
from .session_manager import Session, SessionManager
from .user_manager import User, UserManager

# Module-level session manager instance (initialized on first use)
_session_manager: SessionManager = None


def init_auth(db_path: str, config_dir: str = None):
    """Initialize the auth system with database path."""
    global _session_manager
    _session_manager = SessionManager(db_path, config_dir)


def get_session_manager() -> SessionManager:
    """Get the session manager instance."""
    if _session_manager is None:
        raise RuntimeError("Auth system not initialized. Call init_auth() first.")
    return _session_manager


def get_current_user() -> User:
    """Get the currently logged-in user."""
    if _session_manager is None:
        return None
    return _session_manager.get_current_user()


def is_logged_in() -> bool:
    """Check if a user is logged in."""
    if _session_manager is None:
        return False
    return _session_manager.is_logged_in()


def is_pro() -> bool:
    """Check if current user has Pro tier."""
    user = get_current_user()
    return user is not None and user.tier == Tier.PRO


__all__ = [
    # Classes
    "Role",
    "Tier",
    "Permission",
    "PermissionChecker",
    "User",
    "UserManager",
    "Session",
    "SessionManager",
    "AuditLogger",
    "AuditAction",
    # Decorators
    "requires_permission",
    "requires_pro",
    "requires_role",
    # Functions
    "init_auth",
    "get_session_manager",
    "get_current_user",
    "is_logged_in",
    "is_pro",
    "audit_log",
    "get_audit_logger",
    # Constants
    "PRO_TIER_PERMISSIONS",
    "ROLE_PERMISSIONS",
]
