#!/usr/bin/env python3
"""
souleyez.storage.database - Core database operations
"""

import os
import sqlite3
import time
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional

from souleyez import config
from souleyez.log_config import get_logger

logger = get_logger(__name__)
DB_PATH = Path(config.get("database.path", "~/.souleyez/souleyez.db")).expanduser()


class Database:
    def __init__(self, db_path: str = None):
        self.db_path = db_path or str(DB_PATH)
        logger.info("Initializing database", extra={"db_path": self.db_path})
        self._ensure_db()

    def _ensure_db(self):
        """Ensure database and schema exist."""
        try:
            db_dir = os.path.dirname(self.db_path)
            if db_dir:  # Only create if there's a directory component
                os.makedirs(db_dir, exist_ok=True)

            conn = sqlite3.connect(self.db_path, timeout=30.0)

            # Set secure permissions (owner read/write only)
            os.chmod(self.db_path, 0o600)
            conn.row_factory = sqlite3.Row
            # Enable foreign key constraints
            conn.execute("PRAGMA foreign_keys = ON")
            # Enable WAL mode for better concurrent access
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA busy_timeout=30000")

            logger.info(
                "Database connection established",
                extra={"wal_mode": True, "foreign_keys": True},
            )

            # Check if this is an existing database (has tables)
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='engagements'"
            )
            is_existing_db = cursor.fetchone() is not None
            conn.close()

            # For EXISTING databases: Run migrations FIRST
            # This ensures new columns exist before schema.sql tries to create indexes on them
            if is_existing_db:
                try:
                    from .migrations.migration_manager import MigrationManager

                    manager = MigrationManager(self.db_path)
                    pending = manager.get_pending_migrations()
                    if pending:
                        logger.info(
                            "Running pending migrations for existing database",
                            extra={"pending_count": len(pending)},
                        )
                        manager.migrate()
                        logger.info(
                            "Migrations completed successfully",
                            extra={"count": len(pending)},
                        )
                except Exception as migration_error:
                    logger.error(
                        "Failed to run migrations on existing database",
                        extra={
                            "error": str(migration_error),
                            "error_type": type(migration_error).__name__,
                            "traceback": traceback.format_exc(),
                        },
                    )
                    raise  # Don't continue if migrations fail for existing DB

            # Reconnect for schema loading
            conn = sqlite3.connect(self.db_path, timeout=30.0)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")

            # Load and execute schema from the same directory as this file
            # For fresh DBs: Creates all tables with current schema
            # For existing DBs: CREATE TABLE IF NOT EXISTS is no-op, but ensures new tables/indexes
            schema_path = Path(__file__).parent / "schema.sql"

            if schema_path.exists():
                with open(schema_path, "r") as f:
                    schema_sql = f.read()
                    conn.executescript(schema_sql)
                logger.info(
                    "Schema loaded from file", extra={"schema_file": str(schema_path)}
                )
            else:
                # If schema file doesn't exist, create essential tables inline
                # This must match schema.sql structure for migrations to work
                logger.warning(
                    "Schema file not found, using inline schema",
                    extra={"expected_path": str(schema_path)},
                )
                conn.executescript("""
                CREATE TABLE IF NOT EXISTS engagements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    description TEXT,
                    engagement_type TEXT DEFAULT 'custom',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS hosts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    engagement_id INTEGER NOT NULL,
                    ip_address TEXT NOT NULL,
                    hostname TEXT,
                    domain TEXT,
                    os_name TEXT,
                    os_accuracy INTEGER,
                    mac_address TEXT,
                    status TEXT DEFAULT 'up',
                    access_level TEXT DEFAULT 'none',
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (engagement_id) REFERENCES engagements(id) ON DELETE CASCADE,
                    UNIQUE(engagement_id, ip_address)
                );

                CREATE TABLE IF NOT EXISTS services (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    host_id INTEGER NOT NULL,
                    port INTEGER NOT NULL,
                    protocol TEXT DEFAULT 'tcp',
                    state TEXT DEFAULT 'open',
                    service_name TEXT,
                    service_version TEXT,
                    service_product TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (host_id) REFERENCES hosts(id) ON DELETE CASCADE,
                    UNIQUE(host_id, port, protocol)
                );

                CREATE TABLE IF NOT EXISTS findings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    engagement_id INTEGER NOT NULL,
                    host_id INTEGER,
                    service_id INTEGER,
                    finding_type TEXT NOT NULL,
                    severity TEXT DEFAULT 'info',
                    title TEXT NOT NULL,
                    description TEXT,
                    evidence TEXT,
                    refs TEXT,
                    port INTEGER,
                    path TEXT,
                    tool TEXT,
                    scan_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (engagement_id) REFERENCES engagements(id) ON DELETE CASCADE,
                    FOREIGN KEY (host_id) REFERENCES hosts(id) ON DELETE SET NULL,
                    FOREIGN KEY (service_id) REFERENCES services(id) ON DELETE SET NULL
                );

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
                    updated_at TIMESTAMP,
                    notes TEXT,
                    last_tested TIMESTAMP,
                    FOREIGN KEY (engagement_id) REFERENCES engagements(id) ON DELETE CASCADE,
                    FOREIGN KEY (host_id) REFERENCES hosts(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS web_paths (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    host_id INTEGER NOT NULL,
                    url TEXT NOT NULL,
                    status_code INTEGER,
                    content_length INTEGER,
                    redirect TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (host_id) REFERENCES hosts(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS osint_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    engagement_id INTEGER NOT NULL,
                    data_type TEXT NOT NULL,
                    value TEXT NOT NULL,
                    source TEXT,
                    target TEXT,
                    summary TEXT,
                    content TEXT,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (engagement_id) REFERENCES engagements(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS screenshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    engagement_id INTEGER NOT NULL,
                    host_id INTEGER,
                    finding_id INTEGER,
                    filename TEXT NOT NULL,
                    filepath TEXT NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (engagement_id) REFERENCES engagements(id) ON DELETE CASCADE,
                    FOREIGN KEY (host_id) REFERENCES hosts(id) ON DELETE SET NULL,
                    FOREIGN KEY (finding_id) REFERENCES findings(id) ON DELETE SET NULL
                );

                CREATE TABLE IF NOT EXISTS exploits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    engagement_id INTEGER NOT NULL,
                    service_id INTEGER,
                    edb_id TEXT,
                    title TEXT,
                    platform TEXT,
                    type TEXT,
                    url TEXT,
                    date_published TEXT,
                    search_term TEXT,
                    found_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (engagement_id) REFERENCES engagements(id) ON DELETE CASCADE,
                    FOREIGN KEY (service_id) REFERENCES services(id) ON DELETE SET NULL
                );

                CREATE TABLE IF NOT EXISTS execution_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    engagement_id INTEGER NOT NULL,
                    recommendation_id TEXT,
                    action TEXT NOT NULL,
                    command TEXT NOT NULL,
                    risk_level TEXT NOT NULL,
                    auto_approved BOOLEAN DEFAULT 0,
                    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    exit_code INTEGER,
                    stdout TEXT,
                    stderr TEXT,
                    success BOOLEAN,
                    feedback_applied TEXT,
                    FOREIGN KEY (engagement_id) REFERENCES engagements(id) ON DELETE CASCADE
                );

                -- Essential indexes
                CREATE INDEX IF NOT EXISTS idx_hosts_engagement ON hosts(engagement_id);
                CREATE INDEX IF NOT EXISTS idx_services_host ON services(host_id);
                CREATE INDEX IF NOT EXISTS idx_findings_engagement ON findings(engagement_id);
                CREATE INDEX IF NOT EXISTS idx_credentials_engagement ON credentials(engagement_id);
                CREATE INDEX IF NOT EXISTS idx_credentials_host ON credentials(host_id);
                CREATE INDEX IF NOT EXISTS idx_credentials_status ON credentials(status);
            """)

            conn.commit()
            conn.close()

            # For FRESH databases: Run migrations after schema.sql loads
            # (Existing DBs already had migrations run before schema.sql)
            if not is_existing_db:
                try:
                    from .migrations.migration_manager import MigrationManager

                    manager = MigrationManager(self.db_path)
                    pending = manager.get_pending_migrations()
                    if pending:
                        logger.info(
                            "Running pending migrations for fresh database",
                            extra={"pending_count": len(pending)},
                        )
                        manager.migrate()
                        logger.info(
                            "Migrations completed successfully",
                            extra={"count": len(pending)},
                        )
                except Exception as migration_error:
                    logger.error(
                        "Failed to run migrations",
                        extra={
                            "error": str(migration_error),
                            "error_type": type(migration_error).__name__,
                            "traceback": traceback.format_exc(),
                        },
                    )

        except Exception as e:
            logger.error(
                "Database initialization failed",
                extra={"error": str(e), "traceback": traceback.format_exc()},
            )
            if "conn" in locals():
                try:
                    conn.close()
                except:
                    pass
            raise

    def get_connection(self, fast_mode: bool = False):
        """
        Get database connection with timeout and WAL mode for concurrency.

        Args:
            fast_mode: If True, use shorter timeout (2s) for UI queries to prevent hanging
        """
        timeout = 2.0 if fast_mode else 30.0
        conn = sqlite3.connect(self.db_path, timeout=timeout, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        # Enable foreign key constraints
        conn.execute("PRAGMA foreign_keys = ON")
        # Enable WAL mode for better concurrent access
        conn.execute("PRAGMA journal_mode=WAL")
        # Reduce lock contention (shorter for fast mode)
        busy_timeout = 2000 if fast_mode else 30000
        conn.execute(f"PRAGMA busy_timeout={busy_timeout}")
        return conn

    def execute(
        self,
        query: str,
        params: tuple = None,
        retries: int = 3,
        fast_mode: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Execute query and return results with retry logic.

        Args:
            query: SQL query to execute
            params: Query parameters
            retries: Number of retry attempts (reduced to 1 for fast_mode)
            fast_mode: If True, use short timeout and don't retry (for UI queries)
        """
        max_retries = 1 if fast_mode else retries
        for attempt in range(max_retries):
            try:
                conn = self.get_connection(fast_mode=fast_mode)
                cursor = conn.cursor()

                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)

                results = [dict(row) for row in cursor.fetchall()]
                conn.commit()
                conn.close()

                return results
            except sqlite3.OperationalError as e:
                if (
                    "locked" in str(e).lower()
                    and attempt < max_retries - 1
                    and not fast_mode
                ):
                    time.sleep(0.1 * (attempt + 1))  # Exponential backoff
                    continue
                # For fast_mode, don't retry - just raise immediately
                raise
            except Exception:
                if "conn" in locals():
                    conn.close()
                raise

    def execute_one(self, query: str, params: tuple = None) -> Optional[Dict[str, Any]]:
        """Execute query and return single result."""
        results = self.execute(query, params)
        return results[0] if results else None

    def insert(self, table: str, data: Dict[str, Any], retries: int = 3) -> int:
        """Insert row and return ID with retry logic."""
        columns = ", ".join(data.keys())
        placeholders = ", ".join(["?" for _ in data])
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"

        for attempt in range(retries):
            try:
                conn = self.get_connection()
                cursor = conn.cursor()
                cursor.execute(query, tuple(data.values()))
                row_id = cursor.lastrowid
                conn.commit()
                conn.close()

                return row_id
            except sqlite3.OperationalError as e:
                if "locked" in str(e).lower() and attempt < retries - 1:
                    time.sleep(0.1 * (attempt + 1))  # Exponential backoff
                    continue
                raise
            except Exception:
                if "conn" in locals():
                    conn.close()
                raise


# Singleton instance
_db = None


def get_db() -> Database:
    """Get database singleton."""
    global _db
    if _db is None:
        _db = Database()
    return _db
