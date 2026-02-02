"""
Screenshot management for visual evidence collection.
"""

import os
import shutil
import time
from pathlib import Path
from typing import Dict, List, Optional

from .database import get_db

SCREENSHOTS_DIR = Path("~/.souleyez/screenshots").expanduser()


class ScreenshotManager:
    """Manage screenshots for engagements."""

    def __init__(self):
        self.db = get_db()
        self._ensure_screenshots_dir()

    def _ensure_screenshots_dir(self):
        """Ensure screenshots directory exists."""
        SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
        os.chmod(SCREENSHOTS_DIR, 0o700)

    def add_screenshot(
        self,
        engagement_id: int,
        source_path: str,
        title: str = None,
        description: str = None,
        host_id: int = None,
        finding_id: int = None,
        job_id: int = None,
    ) -> int:
        """
        Add a screenshot to the engagement.

        Args:
            engagement_id: Engagement ID
            source_path: Path to source screenshot file
            title: Screenshot title
            description: Screenshot description
            host_id: Optional host ID
            finding_id: Optional finding ID
            job_id: Optional job ID

        Returns:
            Screenshot ID
        """
        source = Path(source_path).expanduser()

        if not source.exists():
            raise FileNotFoundError(f"Screenshot not found: {source_path}")

        file_size = source.stat().st_size
        mime_type = self._get_mime_type(source)

        timestamp = int(time.time())
        filename = f"{engagement_id}_{timestamp}_{source.name}"
        dest_path = SCREENSHOTS_DIR / filename

        shutil.copy2(source, dest_path)
        os.chmod(dest_path, 0o600)

        screenshot_id = self.db.insert(
            "screenshots",
            {
                "engagement_id": engagement_id,
                "host_id": host_id,
                "finding_id": finding_id,
                "job_id": job_id,
                "filename": filename,
                "filepath": str(dest_path),
                "title": title or source.name,
                "description": description,
                "file_size": file_size,
                "mime_type": mime_type,
            },
        )

        return screenshot_id

    def list_screenshots(
        self,
        engagement_id: int,
        host_id: int = None,
        finding_id: int = None,
        job_id: int = None,
    ) -> List[Dict]:
        """
        List screenshots for engagement.

        Args:
            engagement_id: Engagement ID
            host_id: Optional filter by host
            finding_id: Optional filter by finding
            job_id: Optional filter by job

        Returns:
            List of screenshot records
        """
        query = "SELECT * FROM screenshots WHERE engagement_id = ?"
        params = [engagement_id]

        if host_id:
            query += " AND host_id = ?"
            params.append(host_id)

        if finding_id:
            query += " AND finding_id = ?"
            params.append(finding_id)

        if job_id:
            query += " AND job_id = ?"
            params.append(job_id)

        query += " ORDER BY created_at DESC"

        return self.db.execute(query, tuple(params))

    def get_screenshot(self, screenshot_id: int) -> Optional[Dict]:
        """Get screenshot by ID."""
        return self.db.execute_one(
            "SELECT * FROM screenshots WHERE id = ?", (screenshot_id,)
        )

    def delete_screenshot(self, screenshot_id: int) -> bool:
        """Delete screenshot and file."""
        screenshot = self.get_screenshot(screenshot_id)
        if not screenshot:
            return False

        filepath = Path(screenshot["filepath"])
        if filepath.exists():
            filepath.unlink()

        self.db.execute("DELETE FROM screenshots WHERE id = ?", (screenshot_id,))
        return True

    def link_to_finding(self, screenshot_id: int, finding_id: int) -> bool:
        """Link screenshot to a finding."""
        self.db.execute(
            "UPDATE screenshots SET finding_id = ? WHERE id = ?",
            (finding_id, screenshot_id),
        )
        return True

    def link_to_job(self, screenshot_id: int, job_id: int) -> bool:
        """Link screenshot to a job."""
        self.db.execute(
            "UPDATE screenshots SET job_id = ? WHERE id = ?", (job_id, screenshot_id)
        )
        return True

    def link_to_host(self, screenshot_id: int, host_id: int) -> bool:
        """Link screenshot to a host."""
        self.db.execute(
            "UPDATE screenshots SET host_id = ? WHERE id = ?", (host_id, screenshot_id)
        )
        return True

    def _get_mime_type(self, filepath: Path) -> str:
        """Detect MIME type from file extension."""
        ext = filepath.suffix.lower()
        mime_types = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".bmp": "image/bmp",
            ".webp": "image/webp",
            ".svg": "image/svg+xml",
        }
        return mime_types.get(ext, "application/octet-stream")

    def get_screenshot_count(self, engagement_id: int) -> int:
        """Get total screenshot count for engagement."""
        result = self.db.execute_one(
            "SELECT COUNT(*) as count FROM screenshots WHERE engagement_id = ?",
            (engagement_id,),
        )
        return result["count"] if result else 0
