#!/usr/bin/env python3
"""
souleyez.storage.sqlmap_data

Storage manager for SQLMap SQL injection discoveries (databases, tables, columns, dumped data)
"""

import json
import sqlite3
from typing import Any, Dict, List, Optional

from souleyez.log_config import get_logger
from souleyez.storage.crypto import get_crypto_manager
from souleyez.storage.database import Database

logger = get_logger(__name__)


class SQLMapDataManager:
    """Manager for storing and retrieving SQLMap discoveries."""

    def __init__(self, db_path: str = None):
        self.db = Database(db_path)

    def add_database(
        self,
        engagement_id: int,
        host_id: int,
        database_name: str,
        dbms_type: str = None,
    ) -> Optional[int]:
        """
        Add a discovered database.

        Args:
            engagement_id: Engagement ID
            host_id: Host ID
            database_name: Name of the database
            dbms_type: Type of DBMS (MySQL, PostgreSQL, etc.)

        Returns:
            Database ID if successful, None otherwise
        """
        try:
            conn = sqlite3.connect(self.db.db_path, timeout=30.0)
            cursor = conn.cursor()

            # Try to insert, or get existing ID
            cursor.execute(
                """
                INSERT OR IGNORE INTO sqli_databases 
                (engagement_id, host_id, database_name, dbms_type)
                VALUES (?, ?, ?, ?)
            """,
                (engagement_id, host_id, database_name, dbms_type),
            )

            if cursor.rowcount > 0:
                db_id = cursor.lastrowid
            else:
                # Get existing ID
                cursor.execute(
                    """
                    SELECT id FROM sqli_databases 
                    WHERE engagement_id = ? AND host_id = ? AND database_name = ?
                """,
                    (engagement_id, host_id, database_name),
                )
                row = cursor.fetchone()
                db_id = row[0] if row else None

            conn.commit()
            conn.close()

            logger.info(
                f"Added database: {database_name}",
                extra={"db_id": db_id, "dbms_type": dbms_type},
            )
            return db_id

        except Exception as e:
            logger.error(f"Failed to add database: {e}")
            return None

    def add_table(
        self, database_id: int, table_name: str, row_count: int = None
    ) -> Optional[int]:
        """
        Add a discovered table.

        Args:
            database_id: Database ID
            table_name: Name of the table
            row_count: Number of rows in the table

        Returns:
            Table ID if successful, None otherwise
        """
        try:
            conn = sqlite3.connect(self.db.db_path, timeout=30.0)
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT OR IGNORE INTO sqli_tables 
                (database_id, table_name, row_count)
                VALUES (?, ?, ?)
            """,
                (database_id, table_name, row_count),
            )

            if cursor.rowcount > 0:
                table_id = cursor.lastrowid
            else:
                cursor.execute(
                    """
                    SELECT id FROM sqli_tables 
                    WHERE database_id = ? AND table_name = ?
                """,
                    (database_id, table_name),
                )
                row = cursor.fetchone()
                table_id = row[0] if row else None

            conn.commit()
            conn.close()

            logger.info(
                f"Added table: {table_name}",
                extra={"table_id": table_id, "row_count": row_count},
            )
            return table_id

        except Exception as e:
            logger.error(f"Failed to add table: {e}")
            return None

    def add_columns(self, table_id: int, columns: List[Dict[str, str]]) -> bool:
        """
        Add discovered columns for a table.

        Args:
            table_id: Table ID
            columns: List of column dicts with 'name' and optionally 'type'

        Returns:
            True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(self.db.db_path, timeout=30.0)
            cursor = conn.cursor()

            for col in columns:
                col_name = col.get("name") or col.get("column_name")
                col_type = col.get("type") or col.get("column_type")

                cursor.execute(
                    """
                    INSERT OR IGNORE INTO sqli_columns 
                    (table_id, column_name, column_type)
                    VALUES (?, ?, ?)
                """,
                    (table_id, col_name, col_type),
                )

            conn.commit()
            conn.close()

            logger.info(f"Added {len(columns)} columns", extra={"table_id": table_id})
            return True

        except Exception as e:
            logger.error(f"Failed to add columns: {e}")
            return False

    def add_dumped_data(
        self, table_id: int, data: List[Dict[str, Any]], csv_file_path: str = None
    ) -> Optional[int]:
        """
        Add dumped table data.

        Args:
            table_id: Table ID
            data: List of row dicts
            csv_file_path: Path to SQLMap's CSV dump file

        Returns:
            Dump ID if successful, None otherwise
        """
        try:
            conn = sqlite3.connect(self.db.db_path, timeout=30.0)
            cursor = conn.cursor()

            data_json = json.dumps(data)
            row_count = len(data)

            # Try to encrypt if crypto is available
            is_encrypted = 0
            try:
                crypto = get_crypto_manager()
                if crypto.is_encryption_enabled():
                    data_json = crypto.encrypt(data_json)
                    is_encrypted = 1
                    logger.info("Encrypted dumped data", extra={"table_id": table_id})
            except Exception as e:
                logger.warning(f"Could not encrypt dumped data: {e}")
                # Continue with unencrypted data

            cursor.execute(
                """
                INSERT INTO sqli_dumped_data 
                (table_id, data_json, csv_file_path, row_count, is_encrypted)
                VALUES (?, ?, ?, ?, ?)
            """,
                (table_id, data_json, csv_file_path, row_count, is_encrypted),
            )

            dump_id = cursor.lastrowid
            conn.commit()
            conn.close()

            logger.info(
                f"Added dumped data",
                extra={
                    "table_id": table_id,
                    "row_count": row_count,
                    "dump_id": dump_id,
                    "encrypted": is_encrypted,
                },
            )
            return dump_id

        except Exception as e:
            logger.error(f"Failed to add dumped data: {e}")
            return None

    def get_databases(
        self, engagement_id: int, host_id: int = None
    ) -> List[Dict[str, Any]]:
        """Get all discovered databases for an engagement."""
        try:
            conn = sqlite3.connect(self.db.db_path, timeout=30.0)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            if host_id:
                cursor.execute(
                    """
                    SELECT d.*, h.ip_address, h.hostname,
                           COUNT(DISTINCT t.id) as table_count
                    FROM sqli_databases d
                    JOIN hosts h ON d.host_id = h.id
                    LEFT JOIN sqli_tables t ON d.id = t.database_id
                    WHERE d.engagement_id = ? AND d.host_id = ?
                    GROUP BY d.id
                    ORDER BY d.discovered_at DESC
                """,
                    (engagement_id, host_id),
                )
            else:
                cursor.execute(
                    """
                    SELECT d.*, h.ip_address, h.hostname,
                           COUNT(DISTINCT t.id) as table_count
                    FROM sqli_databases d
                    JOIN hosts h ON d.host_id = h.id
                    LEFT JOIN sqli_tables t ON d.id = t.database_id
                    WHERE d.engagement_id = ?
                    GROUP BY d.id
                    ORDER BY d.discovered_at DESC
                """,
                    (engagement_id,),
                )

            rows = cursor.fetchall()
            conn.close()

            return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"Failed to get databases: {e}")
            return []

    def get_tables(self, database_id: int) -> List[Dict[str, Any]]:
        """Get all tables for a database."""
        try:
            conn = sqlite3.connect(self.db.db_path, timeout=30.0)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT t.*,
                       COUNT(DISTINCT c.id) as column_count,
                       CASE WHEN d.id IS NOT NULL THEN 1 ELSE 0 END as has_dumped_data
                FROM sqli_tables t
                LEFT JOIN sqli_columns c ON t.id = c.table_id
                LEFT JOIN sqli_dumped_data d ON t.id = d.table_id
                WHERE t.database_id = ?
                GROUP BY t.id
                ORDER BY t.table_name
            """,
                (database_id,),
            )

            rows = cursor.fetchall()
            conn.close()

            return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"Failed to get tables: {e}")
            return []

    def get_columns(self, table_id: int) -> List[Dict[str, Any]]:
        """Get all columns for a table."""
        try:
            conn = sqlite3.connect(self.db.db_path, timeout=30.0)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT * FROM sqli_columns
                WHERE table_id = ?
                ORDER BY column_name
            """,
                (table_id,),
            )

            rows = cursor.fetchall()
            conn.close()

            return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"Failed to get columns: {e}")
            return []

    def get_dumped_data(self, table_id: int) -> Optional[Dict[str, Any]]:
        """Get dumped data for a table."""
        try:
            conn = sqlite3.connect(self.db.db_path, timeout=30.0)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT * FROM sqli_dumped_data
                WHERE table_id = ?
                ORDER BY dumped_at DESC
                LIMIT 1
            """,
                (table_id,),
            )

            row = cursor.fetchone()
            conn.close()

            if row:
                result = dict(row)
                data_json = result["data_json"]

                # Decrypt if encrypted
                if result.get("is_encrypted"):
                    try:
                        crypto = get_crypto_manager()
                        if crypto.is_encryption_enabled():
                            data_json = crypto.decrypt(data_json)
                        else:
                            logger.error("Data is encrypted but crypto is not enabled")
                            return None
                    except Exception as e:
                        logger.error(f"Failed to decrypt dumped data: {e}")
                        return None

                result["data"] = json.loads(data_json)
                return result
            return None

        except Exception as e:
            logger.error(f"Failed to get dumped data: {e}")
            return None

    def get_summary(self, engagement_id: int) -> Dict[str, int]:
        """Get summary statistics for SQLMap discoveries."""
        try:
            conn = sqlite3.connect(self.db.db_path, timeout=30.0)
            cursor = conn.cursor()

            # Count databases
            cursor.execute(
                """
                SELECT COUNT(*) FROM sqli_databases
                WHERE engagement_id = ?
            """,
                (engagement_id,),
            )
            db_count = cursor.fetchone()[0]

            # Count tables
            cursor.execute(
                """
                SELECT COUNT(*) FROM sqli_tables t
                JOIN sqli_databases d ON t.database_id = d.id
                WHERE d.engagement_id = ?
            """,
                (engagement_id,),
            )
            table_count = cursor.fetchone()[0]

            # Count columns
            cursor.execute(
                """
                SELECT COUNT(*) FROM sqli_columns c
                JOIN sqli_tables t ON c.table_id = t.id
                JOIN sqli_databases d ON t.database_id = d.id
                WHERE d.engagement_id = ?
            """,
                (engagement_id,),
            )
            column_count = cursor.fetchone()[0]

            # Count dumped tables
            cursor.execute(
                """
                SELECT COUNT(DISTINCT table_id) FROM sqli_dumped_data dd
                JOIN sqli_tables t ON dd.table_id = t.id
                JOIN sqli_databases d ON t.database_id = d.id
                WHERE d.engagement_id = ?
            """,
                (engagement_id,),
            )
            dumped_count = cursor.fetchone()[0]

            conn.close()

            return {
                "databases": db_count,
                "tables": table_count,
                "columns": column_count,
                "dumped_tables": dumped_count,
            }

        except Exception as e:
            logger.error(f"Failed to get summary: {e}")
            return {"databases": 0, "tables": 0, "columns": 0, "dumped_tables": 0}
