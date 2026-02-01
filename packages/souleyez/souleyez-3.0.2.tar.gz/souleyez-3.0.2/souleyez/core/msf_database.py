"""
Metasploit Database Integration

This module provides direct PostgreSQL database access to Metasploit Framework's
workspace data, allowing SoulEyez to import hosts, services, vulnerabilities,
credentials, and sessions directly from MSF.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor

    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False

logger = logging.getLogger(__name__)

# Tested MSF versions (major.minor)
TESTED_MSF_VERSIONS = ["6.2", "6.3", "6.4"]
KNOWN_SCHEMA_VERSION = 20230313  # MSF schema version we're compatible with


class MSFDatabaseSchemaError(Exception):
    """Raised when MSF database schema is incompatible"""

    pass


class MSFDatabase:
    """Interface to Metasploit's PostgreSQL database"""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 5432,
        database: str = "msf",
        username: str = "msf",
        password: str = "",
        workspace: str = "default",
    ):
        """
        Initialize MSF database connection

        Args:
            host: PostgreSQL host
            port: PostgreSQL port
            database: Database name (default: msf)
            username: Database username
            password: Database password
            workspace: MSF workspace to query (default: default)
        """
        if not PSYCOPG2_AVAILABLE:
            raise ImportError(
                "psycopg2 is required for MSF database integration. "
                "Install with: pip install psycopg2-binary"
            )

        self.host = host
        self.port = port
        self.database = database
        self.username = username
        self.password = password
        self.workspace_name = workspace
        self.conn = None
        self.workspace_id = None

    def connect(self) -> bool:
        """
        Connect to MSF database

        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.username,
                password=self.password,
                connect_timeout=10,  # Prevent hanging on unreachable database
            )

            # Get workspace ID
            self.workspace_id = self._get_workspace_id(self.workspace_name)
            if not self.workspace_id:
                logger.warning(f"Workspace '{self.workspace_name}' not found")

            # Check MSF version and schema compatibility
            self._check_compatibility()

            return True

        except Exception as e:
            logger.error(f"Failed to connect to MSF database: {e}")
            return False

    def disconnect(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            self.conn = None

    def _get_workspace_id(self, workspace_name: str) -> Optional[int]:
        """Get workspace ID by name"""
        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    "SELECT id FROM workspaces WHERE name = %s", (workspace_name,)
                )
                result = cur.fetchone()
                return result[0] if result else None
        except Exception as e:
            logger.error(f"Failed to get workspace ID: {e}")
            return None

    def _check_compatibility(self):
        """Check MSF version and schema compatibility"""
        try:
            # Try to determine MSF version from database metadata
            version_info = self._get_msf_version_info()

            if version_info:
                version_str = version_info.get("version", "unknown")
                # Check if version is tested
                major_minor = (
                    ".".join(version_str.split(".")[:2])
                    if "." in version_str
                    else version_str
                )
                if major_minor not in TESTED_MSF_VERSIONS and version_str != "unknown":
                    logger.warning(
                        f"MSF version {version_str} has not been tested with this integration. "
                        f"Tested versions: {', '.join(TESTED_MSF_VERSIONS)}. "
                        "Schema changes may cause errors."
                    )

            # Validate critical tables exist
            if not self._validate_schema():
                logger.warning(
                    "MSF database schema validation failed. Some tables may be missing or modified. "
                    "Consider using MSF XML export instead for more stability."
                )

        except Exception as e:
            logger.debug(f"Compatibility check failed (non-critical): {e}")

    def _get_msf_version_info(self) -> Optional[Dict[str, str]]:
        """Try to get MSF version information from database"""
        try:
            # MSF doesn't store version in DB reliably, but we can try mod_refs table
            # or check for schema_migrations to infer version
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Check latest schema migration
                cur.execute("""
                    SELECT version
                    FROM schema_migrations
                    ORDER BY version DESC
                    LIMIT 1
                """)
                result = cur.fetchone()

                if result:
                    return {
                        "schema_version": str(result["version"]),
                        "version": "unknown",  # Can't reliably determine from DB
                    }
        except Exception as e:
            logger.debug(f"Could not determine MSF version: {e}")

        return None

    def _validate_schema(self) -> bool:
        """Validate that critical tables exist with expected columns"""
        try:
            with self.conn.cursor() as cur:
                # Check critical tables exist
                critical_tables = [
                    "hosts",
                    "services",
                    "vulns",
                    "sessions",
                    "workspaces",
                ]

                for table in critical_tables:
                    cur.execute(
                        """
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables
                            WHERE table_name = %s
                        )
                    """,
                        (table,),
                    )

                    exists = cur.fetchone()[0]
                    if not exists:
                        logger.error(
                            f"Critical table '{table}' not found in MSF database"
                        )
                        return False

                # Validate key columns exist in hosts table
                cur.execute("""
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_name = 'hosts'
                """)
                columns = {row[0] for row in cur.fetchall()}

                required_columns = {"id", "address", "workspace_id"}
                if not required_columns.issubset(columns):
                    missing = required_columns - columns
                    logger.error(
                        f"Required columns missing from 'hosts' table: {missing}"
                    )
                    return False

                return True

        except Exception as e:
            logger.error(f"Schema validation failed: {e}")
            return False

    def list_workspaces(self) -> List[Dict[str, Any]]:
        """
        List all MSF workspaces

        Returns:
            List of workspace dictionaries with id, name, created_at, updated_at
        """
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT id, name, created_at, updated_at,
                           boundary,
                           description,
                           owner_id,
                           limit_to_network
                    FROM workspaces
                    ORDER BY name
                """)
                return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Failed to list workspaces: {e}")
            return []

    def get_hosts(self, workspace_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get all hosts from MSF database

        Args:
            workspace_id: Workspace ID (uses current workspace if None)

        Returns:
            List of host dictionaries
        """
        ws_id = workspace_id or self.workspace_id
        if not ws_id:
            logger.error("No workspace specified")
            return []

        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT
                        id,
                        address,
                        mac,
                        name,
                        os_name,
                        os_flavor,
                        os_sp,
                        os_lang,
                        arch,
                        purpose,
                        info,
                        comments,
                        created_at,
                        updated_at,
                        state
                    FROM hosts
                    WHERE workspace_id = %s
                    ORDER BY address
                """,
                    (ws_id,),
                )
                return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Failed to get hosts: {e}")
            return []

    def get_services(
        self, workspace_id: Optional[int] = None, host_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all services from MSF database

        Args:
            workspace_id: Workspace ID (uses current workspace if None)
            host_id: Filter by host ID (optional)

        Returns:
            List of service dictionaries
        """
        ws_id = workspace_id or self.workspace_id
        if not ws_id:
            logger.error("No workspace specified")
            return []

        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                query = """
                    SELECT
                        s.id,
                        s.host_id,
                        s.port,
                        s.proto,
                        s.state,
                        s.name,
                        s.info,
                        s.created_at,
                        s.updated_at,
                        h.address as host_address
                    FROM services s
                    JOIN hosts h ON s.host_id = h.id
                    WHERE h.workspace_id = %s
                """
                params = [ws_id]

                if host_id:
                    query += " AND s.host_id = %s"
                    params.append(host_id)

                query += " ORDER BY h.address, s.port"

                cur.execute(query, params)
                return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Failed to get services: {e}")
            return []

    def get_vulns(self, workspace_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get all vulnerabilities from MSF database

        Args:
            workspace_id: Workspace ID (uses current workspace if None)

        Returns:
            List of vulnerability dictionaries
        """
        ws_id = workspace_id or self.workspace_id
        if not ws_id:
            logger.error("No workspace specified")
            return []

        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Try full query first (without v.refs which doesn't exist in some MSF versions)
                try:
                    cur.execute(
                        """
                        SELECT
                            v.id,
                            v.host_id,
                            v.service_id,
                            v.name,
                            v.info,
                            v.created_at,
                            v.updated_at,
                            v.exploited_at,
                            h.address as host_address,
                            s.port as service_port,
                            s.proto as service_proto
                        FROM vulns v
                        JOIN hosts h ON v.host_id = h.id
                        LEFT JOIN services s ON v.service_id = s.id
                        WHERE h.workspace_id = %s
                        ORDER BY v.created_at DESC
                    """,
                        (ws_id,),
                    )
                    results = cur.fetchall()
                    return [dict(row) for row in results]
                except Exception as schema_error:
                    # Rollback the failed transaction
                    self.conn.rollback()
                    logger.warning(
                        f"Full vulns query failed, trying minimal query: {schema_error}"
                    )

                    # Try minimal query with only essential columns
                    cur.execute(
                        """
                        SELECT
                            v.id,
                            v.host_id,
                            v.service_id,
                            v.name,
                            v.info,
                            h.address as host_address
                        FROM vulns v
                        JOIN hosts h ON v.host_id = h.id
                        WHERE h.workspace_id = %s
                        ORDER BY v.id DESC
                    """,
                        (ws_id,),
                    )
                    results = cur.fetchall()
                    return [dict(row) for row in results]
        except Exception as e:
            logger.error(f"Failed to get vulnerabilities: {e}")
            import traceback

            logger.error(f"Traceback: {traceback.format_exc()}")
            # Rollback transaction on error
            try:
                self.conn.rollback()
            except:
                pass
            return []

    def get_creds(self, workspace_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get all credentials from MSF database

        Args:
            workspace_id: Workspace ID (uses current workspace if None)

        Returns:
            List of credential dictionaries
        """
        ws_id = workspace_id or self.workspace_id
        if not ws_id:
            logger.error("No workspace specified")
            return []

        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                # MSF uses a complex credential schema with cores, logins, and privates
                # We'll join them to get usable credential data
                cur.execute(
                    """
                    SELECT
                        l.id,
                        l.core_id,
                        l.service_id,
                        c.origin_type,
                        c.origin_id,
                        pub.username,
                        priv.data as private_data,
                        priv.type as private_type,
                        l.status,
                        l.created_at,
                        l.updated_at,
                        s.port as service_port,
                        s.proto as service_proto,
                        h.address as host_address
                    FROM logins l
                    JOIN cores c ON l.core_id = c.id
                    LEFT JOIN publics pub ON c.public_id = pub.id
                    LEFT JOIN privates priv ON c.private_id = priv.id
                    LEFT JOIN services s ON l.service_id = s.id
                    LEFT JOIN hosts h ON s.host_id = h.id
                    WHERE c.workspace_id = %s
                    ORDER BY l.created_at DESC
                """,
                    (ws_id,),
                )
                return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            logger.debug(f"Failed to get credentials: {e}")
            # Rollback transaction on error
            try:
                self.conn.rollback()
            except:
                pass
            return []

    def get_sessions(
        self, workspace_id: Optional[int] = None, active_only: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get all sessions from MSF database

        Args:
            workspace_id: Workspace ID (uses current workspace if None)
            active_only: Only return active sessions (default: True)

        Returns:
            List of session dictionaries
        """
        ws_id = workspace_id or self.workspace_id
        if not ws_id:
            logger.error("No workspace specified")
            return []

        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Try full query first
                try:
                    query = """
                        SELECT
                            s.id,
                            s.host_id,
                            s.stype,
                            s.via_exploit,
                            s.via_payload,
                            s.desc,
                            s.port,
                            s.platform,
                            s.datastore,
                            s.opened_at,
                            s.closed_at,
                            s.close_reason,
                            s.local_id,
                            s.last_seen,
                            h.address as host_address
                        FROM sessions s
                        JOIN hosts h ON s.host_id = h.id
                        WHERE h.workspace_id = %s
                    """

                    if active_only:
                        query += " AND s.closed_at IS NULL"

                    query += " ORDER BY s.opened_at DESC"

                    cur.execute(query, (ws_id,))
                    results = cur.fetchall()
                    return [dict(row) for row in results]
                except Exception as schema_error:
                    # Rollback the failed transaction
                    self.conn.rollback()
                    logger.warning(
                        f"Full sessions query failed, trying minimal query: {schema_error}"
                    )

                    # Try minimal query with only essential columns
                    query = """
                        SELECT
                            s.id,
                            s.host_id,
                            s.stype,
                            s.via_exploit,
                            s.via_payload,
                            s.opened_at,
                            s.closed_at,
                            h.address as host_address
                        FROM sessions s
                        JOIN hosts h ON s.host_id = h.id
                        WHERE h.workspace_id = %s
                    """

                    if active_only:
                        query += " AND s.closed_at IS NULL"

                    query += " ORDER BY s.id DESC"

                    cur.execute(query, (ws_id,))
                    results = cur.fetchall()
                    return [dict(row) for row in results]
        except Exception as e:
            logger.error(f"Failed to get sessions: {e}")
            import traceback

            logger.error(f"Traceback: {traceback.format_exc()}")
            # Rollback transaction on error
            try:
                self.conn.rollback()
            except:
                pass
            return []

    def get_session_events(self, session_id: int) -> List[Dict[str, Any]]:
        """
        Get events for a specific session

        Args:
            session_id: MSF session ID

        Returns:
            List of session event dictionaries
        """
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT
                        id,
                        session_id,
                        etype,
                        command,
                        output,
                        remote_path,
                        local_path,
                        created_at
                    FROM session_events
                    WHERE session_id = %s
                    ORDER BY created_at
                """,
                    (session_id,),
                )
                return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Failed to get session events: {e}")
            return []

    def get_exploit_attempts(
        self, workspace_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get exploit attempt data from MSF database

        This queries the vulns table for exploited_at timestamps to track
        successful exploits.

        Args:
            workspace_id: Workspace ID (uses current workspace if None)

        Returns:
            List of exploit attempt dictionaries
        """
        ws_id = workspace_id or self.workspace_id
        if not ws_id:
            logger.error("No workspace specified")
            return []

        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT
                        v.id,
                        v.host_id,
                        v.service_id,
                        v.name as vuln_name,
                        v.exploited_at,
                        v.info,
                        h.address as host_address,
                        s.port as service_port,
                        s.proto as service_proto,
                        s.name as service_name
                    FROM vulns v
                    JOIN hosts h ON v.host_id = h.id
                    LEFT JOIN services s ON v.service_id = s.id
                    WHERE h.workspace_id = %s
                      AND v.exploited_at IS NOT NULL
                    ORDER BY v.exploited_at DESC
                """,
                    (ws_id,),
                )
                return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Failed to get exploit attempts: {e}")
            return []

    def get_database_stats(
        self, workspace_id: Optional[int] = None, max_retries: int = 3
    ) -> Dict[str, int]:
        """
        Get statistics about MSF database contents

        Args:
            workspace_id: Workspace ID (uses current workspace if None)
            max_retries: Maximum number of retries for database lock errors (default: 3)

        Returns:
            Dictionary with counts of hosts, services, vulns, creds, sessions
        """
        ws_id = workspace_id or self.workspace_id
        if not ws_id:
            logger.error("No workspace specified")
            return {}

        stats = {
            "hosts": 0,
            "services": 0,
            "vulns": 0,
            "creds": 0,
            "active_sessions": 0,
            "total_sessions": 0,
        }

        # Retry logic for database locks
        import time

        for attempt in range(max_retries):
            try:
                with self.conn.cursor() as cur:
                    # Count hosts
                    try:
                        cur.execute(
                            "SELECT COUNT(*) FROM hosts WHERE workspace_id = %s",
                            (ws_id,),
                        )
                        stats["hosts"] = cur.fetchone()[0]
                    except Exception as e:
                        logger.warning(f"Failed to count hosts: {e}")
                        self.conn.rollback()  # Clear aborted transaction state

                    # Count services
                    try:
                        cur.execute(
                            """
                            SELECT COUNT(*)
                            FROM services s
                            JOIN hosts h ON s.host_id = h.id
                            WHERE h.workspace_id = %s
                        """,
                            (ws_id,),
                        )
                        stats["services"] = cur.fetchone()[0]
                    except Exception as e:
                        logger.warning(f"Failed to count services: {e}")
                        self.conn.rollback()  # Clear aborted transaction state

                    # Count vulns
                    try:
                        cur.execute(
                            """
                            SELECT COUNT(*)
                            FROM vulns v
                            JOIN hosts h ON v.host_id = h.id
                            WHERE h.workspace_id = %s
                        """,
                            (ws_id,),
                        )
                        stats["vulns"] = cur.fetchone()[0]
                    except Exception as e:
                        logger.warning(f"Failed to count vulns: {e}")
                        self.conn.rollback()  # Clear aborted transaction state

                    # Count creds - credential schema varies by MSF version
                    # Some versions don't have credential tables at all
                    try:
                        cur.execute(
                            """
                            SELECT COUNT(*)
                            FROM cores
                            WHERE workspace_id = %s
                        """,
                            (ws_id,),
                        )
                        stats["creds"] = cur.fetchone()[0]
                    except Exception as e:
                        logger.debug(
                            f"Failed to count credentials (table may not exist in this MSF version): {e}"
                        )
                        self.conn.rollback()  # Clear aborted transaction state

                    # Count active sessions
                    try:
                        cur.execute(
                            """
                            SELECT COUNT(*)
                            FROM sessions s
                            JOIN hosts h ON s.host_id = h.id
                            WHERE h.workspace_id = %s
                              AND s.closed_at IS NULL
                        """,
                            (ws_id,),
                        )
                        stats["active_sessions"] = cur.fetchone()[0]
                    except Exception as e:
                        logger.warning(f"Failed to count active sessions: {e}")
                        self.conn.rollback()  # Clear aborted transaction state

                    # Count total sessions
                    try:
                        cur.execute(
                            """
                            SELECT COUNT(*)
                            FROM sessions s
                            JOIN hosts h ON s.host_id = h.id
                            WHERE h.workspace_id = %s
                        """,
                            (ws_id,),
                        )
                        stats["total_sessions"] = cur.fetchone()[0]
                    except Exception as e:
                        logger.warning(f"Failed to count total sessions: {e}")
                        self.conn.rollback()  # Clear aborted transaction state

                # Success - break out of retry loop
                break

            except Exception as e:
                # Check if it's a database lock error
                error_msg = str(e).lower()
                if "lock" in error_msg or "locked" in error_msg:
                    if attempt < max_retries - 1:
                        wait_time = 0.5 * (
                            attempt + 1
                        )  # Incremental backoff: 0.5s, 1s, 1.5s
                        logger.warning(
                            f"MSF database is locked (attempt {attempt + 1}/{max_retries}), retrying in {wait_time}s..."
                        )
                        time.sleep(wait_time)
                        # Rollback the transaction before retrying
                        try:
                            self.conn.rollback()
                        except:
                            pass
                    else:
                        logger.error(
                            f"MSF database is locked after {max_retries} attempts: {e}"
                        )
                        logger.error(
                            "Recommendation: Wait for MSF operations to complete, then try again"
                        )
                else:
                    logger.error(f"Failed to get database stats: {e}")
                    import traceback

                    logger.debug(f"Traceback: {traceback.format_exc()}")
                    break  # Don't retry for non-lock errors

        return stats

    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()


def test_msf_database_connection(
    host: str = "localhost",
    port: int = 5432,
    database: str = "msf",
    username: str = "msf",
    password: str = "",
) -> bool:
    """
    Test MSF database connection

    Returns:
        True if connection successful, False otherwise
    """
    if not PSYCOPG2_AVAILABLE:
        logger.error("psycopg2 not available")
        return False

    try:
        with MSFDatabase(host, port, database, username, password) as db:
            workspaces = db.list_workspaces()
            logger.info(f"Found {len(workspaces)} workspaces")
            return True
    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        return False
