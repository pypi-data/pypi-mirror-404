"""
MSF Sessions Storage

Functions for managing Metasploit Framework session records in the database.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def add_msf_session(
    db,
    engagement_id: int,
    host_id: int,
    msf_session_id: int,
    session_type: Optional[str] = None,
    via_exploit: Optional[str] = None,
    via_payload: Optional[str] = None,
    platform: Optional[str] = None,
    arch: Optional[str] = None,
    username: Optional[str] = None,
    port: Optional[int] = None,
    tunnel_peer: Optional[str] = None,
    opened_at: Optional[datetime] = None,
    notes: Optional[str] = None,
) -> int:
    """
    Add or update MSF session record

    Args:
        db: Database connection
        engagement_id: Engagement ID
        host_id: Host ID
        msf_session_id: MSF session ID
        session_type: Session type (shell, meterpreter, etc.)
        via_exploit: Exploit used to create session
        via_payload: Payload used
        platform: Target platform
        arch: Target architecture
        username: Session username
        port: Target port
        tunnel_peer: Tunnel connection info
        opened_at: Session opened timestamp
        notes: Additional notes

    Returns:
        Session record ID
    """
    cursor = db.cursor()

    # Check if session already exists
    cursor.execute(
        """
        SELECT id FROM msf_sessions
        WHERE engagement_id = ? AND msf_session_id = ?
    """,
        (engagement_id, msf_session_id),
    )

    existing = cursor.fetchone()

    if existing:
        # Update existing session
        cursor.execute(
            """
            UPDATE msf_sessions
            SET session_type = ?,
                via_exploit = ?,
                via_payload = ?,
                platform = ?,
                arch = ?,
                username = ?,
                port = ?,
                tunnel_peer = ?,
                opened_at = ?,
                notes = ?,
                is_active = 1,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """,
            (
                session_type,
                via_exploit,
                via_payload,
                platform,
                arch,
                username,
                port,
                tunnel_peer,
                opened_at,
                notes,
                existing[0],
            ),
        )
        return existing[0]
    else:
        # Insert new session
        cursor.execute(
            """
            INSERT INTO msf_sessions (
                engagement_id, host_id, msf_session_id,
                session_type, via_exploit, via_payload,
                platform, arch, username, port,
                tunnel_peer, opened_at, notes, is_active
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
        """,
            (
                engagement_id,
                host_id,
                msf_session_id,
                session_type,
                via_exploit,
                via_payload,
                platform,
                arch,
                username,
                port,
                tunnel_peer,
                opened_at,
                notes,
            ),
        )
        return cursor.lastrowid


def close_msf_session(
    db, engagement_id: int, msf_session_id: int, close_reason: Optional[str] = None
) -> bool:
    """
    Mark MSF session as closed

    Args:
        db: Database connection
        engagement_id: Engagement ID
        msf_session_id: MSF session ID
        close_reason: Reason for closure

    Returns:
        True if session was closed, False if not found
    """
    cursor = db.cursor()

    cursor.execute(
        """
        UPDATE msf_sessions
        SET is_active = 0,
            closed_at = CURRENT_TIMESTAMP,
            close_reason = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE engagement_id = ? AND msf_session_id = ?
    """,
        (close_reason, engagement_id, msf_session_id),
    )

    return cursor.rowcount > 0


def get_msf_sessions(
    db, engagement_id: int, active_only: bool = True, host_id: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Get MSF sessions

    Args:
        db: Database connection
        engagement_id: Engagement ID
        active_only: Only return active sessions (default: True)
        host_id: Filter by host ID (optional)

    Returns:
        List of session dictionaries
    """
    cursor = db.cursor()

    query = """
        SELECT
            s.*,
            h.ip_address as host_ip,
            h.hostname
        FROM msf_sessions s
        JOIN hosts h ON s.host_id = h.id
        WHERE s.engagement_id = ?
    """
    params = [engagement_id]

    if active_only:
        query += " AND s.is_active = 1"

    if host_id:
        query += " AND s.host_id = ?"
        params.append(host_id)

    query += " ORDER BY s.opened_at DESC"

    cursor.execute(query, params)

    columns = [desc[0] for desc in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def get_msf_session_by_id(
    db, engagement_id: int, msf_session_id: int
) -> Optional[Dict[str, Any]]:
    """
    Get MSF session by MSF session ID

    Args:
        db: Database connection
        engagement_id: Engagement ID
        msf_session_id: MSF session ID

    Returns:
        Session dictionary or None if not found
    """
    cursor = db.cursor()

    cursor.execute(
        """
        SELECT
            s.*,
            h.ip_address as host_ip,
            h.hostname
        FROM msf_sessions s
        JOIN hosts h ON s.host_id = h.id
        WHERE s.engagement_id = ? AND s.msf_session_id = ?
    """,
        (engagement_id, msf_session_id),
    )

    row = cursor.fetchone()
    if row:
        columns = [desc[0] for desc in cursor.description]
        return dict(zip(columns, row))
    return None


def update_session_last_seen(db, engagement_id: int, msf_session_id: int) -> bool:
    """
    Update session last_seen timestamp

    Args:
        db: Database connection
        engagement_id: Engagement ID
        msf_session_id: MSF session ID

    Returns:
        True if updated, False if not found
    """
    cursor = db.cursor()

    cursor.execute(
        """
        UPDATE msf_sessions
        SET last_seen = CURRENT_TIMESTAMP,
            updated_at = CURRENT_TIMESTAMP
        WHERE engagement_id = ? AND msf_session_id = ?
    """,
        (engagement_id, msf_session_id),
    )

    return cursor.rowcount > 0


def get_session_stats(db, engagement_id: int) -> Dict[str, Any]:
    """
    Get MSF session statistics

    Args:
        db: Database connection
        engagement_id: Engagement ID

    Returns:
        Dictionary with session statistics
    """
    cursor = db.cursor()

    stats = {
        "total": 0,
        "active": 0,
        "closed": 0,
        "by_type": {},
        "by_exploit": {},
        "compromised_hosts": 0,
    }

    # Total and active sessions
    cursor.execute(
        """
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END) as active
        FROM msf_sessions
        WHERE engagement_id = ?
    """,
        (engagement_id,),
    )

    row = cursor.fetchone()
    if row:
        stats["total"] = row[0] or 0
        stats["active"] = row[1] or 0
        stats["closed"] = stats["total"] - stats["active"]

    # Sessions by type
    cursor.execute(
        """
        SELECT session_type, COUNT(*) as count
        FROM msf_sessions
        WHERE engagement_id = ?
        GROUP BY session_type
    """,
        (engagement_id,),
    )

    for row in cursor.fetchall():
        session_type = row[0] or "unknown"
        stats["by_type"][session_type] = row[1]

    # Sessions by exploit
    cursor.execute(
        """
        SELECT via_exploit, COUNT(*) as count
        FROM msf_sessions
        WHERE engagement_id = ? AND via_exploit IS NOT NULL
        GROUP BY via_exploit
    """,
        (engagement_id,),
    )

    for row in cursor.fetchall():
        stats["by_exploit"][row[0]] = row[1]

    # Compromised hosts (hosts with active sessions)
    cursor.execute(
        """
        SELECT COUNT(DISTINCT host_id)
        FROM msf_sessions
        WHERE engagement_id = ? AND is_active = 1
    """,
        (engagement_id,),
    )

    row = cursor.fetchone()
    if row:
        stats["compromised_hosts"] = row[0] or 0

    return stats


def delete_msf_session(db, engagement_id: int, msf_session_id: int) -> bool:
    """
    Delete MSF session record

    Args:
        db: Database connection
        engagement_id: Engagement ID
        msf_session_id: MSF session ID

    Returns:
        True if deleted, False if not found
    """
    cursor = db.cursor()

    cursor.execute(
        """
        DELETE FROM msf_sessions
        WHERE engagement_id = ? AND msf_session_id = ?
    """,
        (engagement_id, msf_session_id),
    )

    return cursor.rowcount > 0
