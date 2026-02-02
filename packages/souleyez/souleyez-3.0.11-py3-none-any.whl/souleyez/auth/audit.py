"""
souleyez.auth.audit - Centralized audit logging

All sensitive actions should be logged through this module.
Logs are immutable and include user context automatically.
"""

import json
import sqlite3
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

from souleyez.storage.database import get_db


class AuditAction(Enum):
    """All auditable actions in the system."""

    # User actions
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"
    USER_CREATED = "user.created"
    USER_UPDATED = "user.updated"
    USER_DELETED = "user.deleted"
    USER_PASSWORD_CHANGED = "user.password_changed"
    USER_LOCKED = "user.locked"
    USER_UNLOCKED = "user.unlocked"

    # Engagement actions
    ENGAGEMENT_CREATED = "engagement.created"
    ENGAGEMENT_DELETED = "engagement.deleted"
    ENGAGEMENT_SWITCHED = "engagement.switched"
    ENGAGEMENT_TEAM_ADDED = "engagement.team.added"
    ENGAGEMENT_TEAM_REMOVED = "engagement.team.removed"
    ENGAGEMENT_TRANSFERRED = "engagement.transferred"

    # Scan actions
    SCAN_STARTED = "scan.started"
    SCAN_COMPLETED = "scan.completed"
    SCAN_FAILED = "scan.failed"
    SCAN_KILLED = "scan.killed"

    # Finding actions
    FINDING_CREATED = "finding.created"
    FINDING_UPDATED = "finding.updated"
    FINDING_DELETED = "finding.deleted"

    # Credential actions
    CREDENTIAL_CREATED = "credential.created"
    CREDENTIAL_UPDATED = "credential.updated"
    CREDENTIAL_DELETED = "credential.deleted"
    CREDENTIAL_VIEWED = "credential.viewed"

    # Report actions
    REPORT_GENERATED = "report.generated"
    REPORT_EXPORTED = "report.exported"

    # AI actions
    AI_EXECUTED = "ai.executed"
    AI_RECOMMENDATION = "ai.recommendation"

    # License actions
    LICENSE_ACTIVATED = "license.activated"
    LICENSE_EXPIRED = "license.expired"
    LICENSE_VALIDATION_FAILED = "license.validation_failed"

    # Tier management
    USER_TIER_UPGRADED = "user.tier_upgraded"
    USER_TIER_DOWNGRADED = "user.tier_downgraded"

    # System actions
    SYSTEM_ENCRYPTION_ENABLED = "system.encryption_enabled"
    SYSTEM_MIGRATION_RUN = "system.migration_run"

    # Security events
    AUTH_FAILED = "auth.failed"
    PERMISSION_DENIED = "permission.denied"

    # Vault events
    VAULT_UNLOCK = "vault.unlock"
    VAULT_UNLOCK_FAILED = "vault.unlock_failed"
    VAULT_LOCKED_OUT = "vault.locked_out"
    VAULT_TIMEOUT = "vault.timeout"
    VAULT_PASSWORD_CHANGED = "vault.password_changed"


class AuditLogger:
    """
    Centralized audit logging.

    Usage:
        from souleyez.auth.audit import audit_log

        audit_log(
            AuditAction.SCAN_STARTED,
            resource_type="job",
            resource_id="123",
            details={"tool": "nmap", "target": "10.0.0.1"}
        )
    """

    def __init__(self, db_path: str = None):
        self.db_path = db_path or get_db().db_path

    def log(
        self,
        action: AuditAction,
        user_id: Optional[str] = None,
        username: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        success: bool = True,
    ):
        """
        Log an audit event.

        Args:
            action: The action being logged
            user_id: User ID (auto-detected if not provided)
            username: Username (auto-detected if not provided)
            resource_type: Type of resource (engagement, job, finding, etc.)
            resource_id: ID of the resource
            details: Additional details as dict (stored as JSON)
            ip_address: Client IP address
            success: Whether the action succeeded
        """
        # Auto-detect user if not provided
        if user_id is None or username is None:
            try:
                from souleyez.auth import get_current_user

                user = get_current_user()
                if user:
                    user_id = user_id or user.id
                    username = username or user.username
            except Exception:
                pass

        # Serialize details to JSON
        details_json = json.dumps(details) if details else None

        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute(
                """
                INSERT INTO audit_log
                (timestamp, user_id, username, action, resource_type, resource_id, details, ip_address, success)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    datetime.now().isoformat(),
                    user_id,
                    username,
                    action.value,
                    resource_type,
                    str(resource_id) if resource_id else None,
                    details_json,
                    ip_address,
                    success,
                ),
            )
            conn.commit()
            conn.close()
        except Exception:
            # Never let audit logging break the application
            pass

    def log_vault_event(
        self,
        action: AuditAction,
        ip_address: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        success: bool = True,
    ):
        """
        Log vault events (no user_id since pre-login).

        Args:
            action: Vault action being logged
            ip_address: Client IP address
            details: Additional details
            success: Whether the action succeeded
        """
        self.log(
            action=action,
            user_id="vault",
            username="vault",
            resource_type="vault",
            details=details,
            ip_address=ip_address,
            success=success,
        )

    def query(
        self,
        user_id: Optional[str] = None,
        username: Optional[str] = None,
        action: Optional[str] = None,
        resource_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        success_only: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Query audit logs with filters.

        Returns:
            List of audit log entries as dicts
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row

        query = "SELECT * FROM audit_log WHERE 1=1"
        params = []

        if user_id:
            query += " AND user_id = ?"
            params.append(user_id)

        if username:
            query += " AND username = ?"
            params.append(username)

        if action:
            query += " AND action LIKE ?"
            params.append(f"%{action}%")

        if resource_type:
            query += " AND resource_type = ?"
            params.append(resource_type)

        if start_date:
            query += " AND timestamp >= ?"
            params.append(start_date.isoformat())

        if end_date:
            query += " AND timestamp <= ?"
            params.append(end_date.isoformat())

        if success_only:
            query += " AND success = 1"

        query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        rows = conn.execute(query, params).fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def get_stats(self, days: int = 30) -> Dict[str, Any]:
        """Get audit log statistics for the last N days."""
        conn = sqlite3.connect(self.db_path)

        cutoff = (
            datetime.now().replace(hour=0, minute=0, second=0) - timedelta(days=days)
        ).isoformat()

        # Total events
        total = conn.execute(
            "SELECT COUNT(*) FROM audit_log WHERE timestamp >= ?", (cutoff,)
        ).fetchone()[0]

        # Events by action category
        by_category = conn.execute(
            """
            SELECT
                SUBSTR(action, 1, INSTR(action, '.') - 1) as category,
                COUNT(*) as count
            FROM audit_log
            WHERE timestamp >= ?
            GROUP BY category
            ORDER BY count DESC
        """,
            (cutoff,),
        ).fetchall()

        # Failed events
        failed = conn.execute(
            "SELECT COUNT(*) FROM audit_log WHERE timestamp >= ? AND success = 0",
            (cutoff,),
        ).fetchone()[0]

        # Unique users
        users = conn.execute(
            "SELECT COUNT(DISTINCT user_id) FROM audit_log WHERE timestamp >= ?",
            (cutoff,),
        ).fetchone()[0]

        conn.close()

        return {
            "total_events": total,
            "failed_events": failed,
            "unique_users": users,
            "by_category": {row[0]: row[1] for row in by_category},
            "period_days": days,
        }


# Global instance for convenience
_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """Get the global audit logger instance."""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger


def audit_log(
    action: AuditAction,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    success: bool = True,
):
    """
    Convenience function for audit logging.

    Usage:
        audit_log(AuditAction.SCAN_STARTED, "job", job_id, {"tool": "nmap"})
    """
    get_audit_logger().log(
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
        success=success,
    )
