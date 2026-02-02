#!/usr/bin/env python3
"""
souleyez.storage.execution_log - Track AI-driven command executions
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from souleyez import config


def get_db_path():
    """Get database path."""
    return Path(config.get("database.path", "~/.souleyez/souleyez.db")).expanduser()


class ExecutionLogManager:
    """Manage execution log entries."""

    def __init__(self):
        self.db_path = str(get_db_path())

    def log_execution(
        self,
        engagement_id: int,
        action: str,
        command: str,
        risk_level: str,
        auto_approved: bool = False,
        recommendation_id: Optional[str] = None,
    ) -> int:
        """
        Log the start of an execution.

        Args:
            engagement_id: Engagement ID
            action: Human-readable action description
            command: Actual command executed
            risk_level: LOW/MEDIUM/HIGH
            auto_approved: Whether it was auto-approved
            recommendation_id: Optional ID linking to AI recommendation

        Returns:
            execution_id for updating later
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO execution_log 
            (engagement_id, recommendation_id, action, command, risk_level, auto_approved)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (
                engagement_id,
                recommendation_id,
                action,
                command,
                risk_level,
                auto_approved,
            ),
        )

        execution_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return execution_id

    def update_result(
        self,
        execution_id: int,
        exit_code: int,
        stdout: str,
        stderr: str,
        success: bool,
        feedback_applied: Optional[Dict[str, Any]] = None,
    ):
        """
        Update execution with results.

        Args:
            execution_id: Execution log ID
            exit_code: Command exit code
            stdout: Standard output
            stderr: Standard error
            success: Whether execution succeeded
            feedback_applied: Dict describing database updates made
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Convert feedback dict to JSON
        feedback_json = json.dumps(feedback_applied) if feedback_applied else None

        cursor.execute(
            """
            UPDATE execution_log
            SET exit_code = ?,
                stdout = ?,
                stderr = ?,
                success = ?,
                feedback_applied = ?
            WHERE id = ?
        """,
            (exit_code, stdout, stderr, success, feedback_json, execution_id),
        )

        conn.commit()
        conn.close()

    def get_recent_executions(
        self, engagement_id: int, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get recent executions for an engagement.

        Args:
            engagement_id: Engagement ID
            limit: Max results

        Returns:
            List of execution records
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT *
            FROM execution_log
            WHERE engagement_id = ?
            ORDER BY executed_at DESC
            LIMIT ?
        """,
            (engagement_id, limit),
        )

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def get_execution(self, execution_id: int) -> Optional[Dict[str, Any]]:
        """Get single execution by ID."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM execution_log WHERE id = ?", (execution_id,))
        row = cursor.fetchone()
        conn.close()

        return dict(row) if row else None
