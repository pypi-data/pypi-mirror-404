"""
souleyez.auth.permissions - Role-based access control definitions

Roles: Admin, Lead, Analyst, Viewer
Tiers: FREE, PRO (for licensing)
"""

from enum import Enum, auto
from functools import wraps
from typing import Optional, Set


class Role(Enum):
    """User roles with hierarchical permissions."""

    ADMIN = "admin"
    LEAD = "lead"
    ANALYST = "analyst"
    VIEWER = "viewer"


class Tier(Enum):
    """Licensing tiers."""

    FREE = "FREE"
    PRO = "PRO"


class Permission(Enum):
    """Individual permissions that can be checked."""

    # User management
    USER_CREATE = auto()
    USER_UPDATE = auto()
    USER_DELETE = auto()
    USER_LIST = auto()

    # Engagement management
    ENGAGEMENT_CREATE = auto()
    ENGAGEMENT_UPDATE = auto()
    ENGAGEMENT_DELETE = auto()
    ENGAGEMENT_VIEW = auto()

    # Scanning & tools
    SCAN_RUN = auto()
    SCAN_KILL = auto()

    # Findings
    FINDING_CREATE = auto()
    FINDING_UPDATE = auto()
    FINDING_DELETE = auto()
    FINDING_VIEW = auto()

    # Credentials
    CREDENTIAL_CREATE = auto()
    CREDENTIAL_VIEW = auto()
    CREDENTIAL_DELETE = auto()

    # Hosts
    HOST_CREATE = auto()
    HOST_UPDATE = auto()
    HOST_DELETE = auto()
    HOST_VIEW = auto()

    # Services
    SERVICE_DELETE = auto()
    SERVICE_VIEW = auto()

    # Reports
    REPORT_GENERATE = auto()
    REPORT_EXPORT = auto()

    # AI features (Pro tier)
    AI_EXECUTE = auto()
    AI_REPORT_ENHANCE = auto()

    # Automation (Pro tier)
    AUTOMATION_MANAGE = auto()

    # MSF Integration (Pro tier)
    MSF_INTEGRATION = auto()

    # Audit
    AUDIT_VIEW = auto()

    # System
    SYSTEM_CONFIG = auto()


# Role -> Permissions mapping
ROLE_PERMISSIONS: dict[Role, Set[Permission]] = {
    Role.ADMIN: set(Permission),  # All permissions
    Role.LEAD: {
        Permission.ENGAGEMENT_CREATE,
        Permission.ENGAGEMENT_UPDATE,
        Permission.ENGAGEMENT_DELETE,
        Permission.ENGAGEMENT_VIEW,
        Permission.SCAN_RUN,
        Permission.SCAN_KILL,
        Permission.FINDING_CREATE,
        Permission.FINDING_UPDATE,
        Permission.FINDING_DELETE,
        Permission.FINDING_VIEW,
        Permission.CREDENTIAL_CREATE,
        Permission.CREDENTIAL_VIEW,
        Permission.CREDENTIAL_DELETE,
        Permission.HOST_CREATE,
        Permission.HOST_UPDATE,
        Permission.HOST_DELETE,
        Permission.HOST_VIEW,
        Permission.SERVICE_DELETE,
        Permission.SERVICE_VIEW,
        Permission.REPORT_GENERATE,
        Permission.REPORT_EXPORT,
        Permission.AI_EXECUTE,
        Permission.AI_REPORT_ENHANCE,
        Permission.AUTOMATION_MANAGE,
        Permission.MSF_INTEGRATION,
        Permission.AUDIT_VIEW,
        Permission.USER_LIST,
    },
    Role.ANALYST: {
        Permission.ENGAGEMENT_VIEW,
        Permission.SCAN_RUN,
        Permission.FINDING_CREATE,
        Permission.FINDING_UPDATE,
        Permission.FINDING_VIEW,
        Permission.CREDENTIAL_CREATE,
        Permission.CREDENTIAL_VIEW,
        Permission.HOST_CREATE,
        Permission.HOST_UPDATE,
        Permission.HOST_VIEW,
        Permission.SERVICE_VIEW,
        Permission.REPORT_GENERATE,
        Permission.REPORT_EXPORT,
        Permission.AI_EXECUTE,
        Permission.AI_REPORT_ENHANCE,
        Permission.AUTOMATION_MANAGE,
        Permission.MSF_INTEGRATION,
    },
    Role.VIEWER: {
        Permission.ENGAGEMENT_VIEW,
        Permission.FINDING_VIEW,
        Permission.CREDENTIAL_VIEW,
        Permission.HOST_VIEW,
        Permission.SERVICE_VIEW,
    },
}

# Pro tier features - require PRO tier regardless of role
PRO_TIER_PERMISSIONS: Set[Permission] = {
    Permission.AI_EXECUTE,
    Permission.AI_REPORT_ENHANCE,
    Permission.AUTOMATION_MANAGE,
    Permission.MSF_INTEGRATION,
    Permission.REPORT_EXPORT,
}


class PermissionChecker:
    """Check user permissions based on role and tier."""

    def __init__(self, role: Role, tier: Tier = Tier.FREE):
        self.role = role
        self.tier = tier

    def has_permission(self, permission: Permission) -> bool:
        """Check if user has a specific permission."""
        # First check role
        role_perms = ROLE_PERMISSIONS.get(self.role, set())
        if permission not in role_perms:
            return False

        # Then check tier for Pro features
        if permission in PRO_TIER_PERMISSIONS:
            return self.tier == Tier.PRO

        return True

    def has_any_permission(self, permissions: Set[Permission]) -> bool:
        """Check if user has any of the specified permissions."""
        return any(self.has_permission(p) for p in permissions)

    def has_all_permissions(self, permissions: Set[Permission]) -> bool:
        """Check if user has all specified permissions."""
        return all(self.has_permission(p) for p in permissions)

    def get_missing_permissions(self, permissions: Set[Permission]) -> Set[Permission]:
        """Get permissions the user is missing."""
        return {p for p in permissions if not self.has_permission(p)}

    def requires_pro(self, permission: Permission) -> bool:
        """Check if a permission requires Pro tier."""
        return permission in PRO_TIER_PERMISSIONS


def requires_permission(permission: Permission):
    """Decorator to require a permission for a function."""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get current user from context (implementation depends on how session is managed)
            from souleyez.auth import get_current_user

            user = get_current_user()

            if user is None:
                raise PermissionError("Authentication required")

            checker = PermissionChecker(user.role, user.tier)
            if not checker.has_permission(permission):
                if permission in PRO_TIER_PERMISSIONS and user.tier != Tier.PRO:
                    raise PermissionError(f"Pro license required for {permission.name}")
                raise PermissionError(f"Permission denied: {permission.name}")

            return func(*args, **kwargs)

        return wrapper

    return decorator


def requires_pro(func):
    """Decorator to require Pro tier for a function."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        from souleyez.auth import get_current_user

        user = get_current_user()

        if user is None:
            raise PermissionError("Authentication required")

        if user.tier != Tier.PRO:
            raise PermissionError("Pro license required")

        return func(*args, **kwargs)

    return wrapper


def requires_role(min_role: Role):
    """Decorator to require a minimum role level."""
    role_hierarchy = [Role.VIEWER, Role.ANALYST, Role.LEAD, Role.ADMIN]

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            from souleyez.auth import get_current_user

            user = get_current_user()

            if user is None:
                raise PermissionError("Authentication required")

            user_level = role_hierarchy.index(user.role)
            required_level = role_hierarchy.index(min_role)

            if user_level < required_level:
                raise PermissionError(f"Requires {min_role.value} role or higher")

            return func(*args, **kwargs)

        return wrapper

    return decorator
