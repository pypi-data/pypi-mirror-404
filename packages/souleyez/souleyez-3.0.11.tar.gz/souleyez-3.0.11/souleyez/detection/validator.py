"""
Detection Validator.

Correlates SoulEyez attacks with SIEM alerts to determine
if attacks were detected by the security monitoring infrastructure.

Supports multiple SIEM platforms: Wazuh, Splunk, Elastic, Sentinel.
"""

import json
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from souleyez.integrations.siem import SIEMClient, SIEMFactory
from souleyez.storage.database import get_db

from .attack_signatures import DEFAULT_DETECTION_WINDOW, get_signature

# Job queue file location (same as background.py)
DATA_DIR = os.path.join(os.path.expanduser("~"), ".souleyez", "data")
JOBS_FILE = os.path.join(DATA_DIR, "jobs", "jobs.json")


def _read_jobs_file() -> List[Dict[str, Any]]:
    """Read jobs from the JSON job queue file."""
    if not os.path.exists(JOBS_FILE):
        return []
    try:
        with open(JOBS_FILE, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return []


def _get_job_by_id(job_id: int) -> Optional[Dict[str, Any]]:
    """Get a single job by ID from the job queue."""
    jobs = _read_jobs_file()
    for job in jobs:
        if job.get("id") == job_id:
            return job
    return None


def _reconstruct_command(job: Dict[str, Any]) -> str:
    """Reconstruct the command string from job data."""
    tool = job.get("tool", "")
    target = job.get("target", "")
    args = job.get("args", [])

    # Build command string
    parts = [tool]
    if args:
        parts.extend(args)
    if target and target not in args:
        parts.append(target)

    return " ".join(parts)


@dataclass
class DetectionResult:
    """Result of validating detection for a single job."""

    job_id: int
    status: str  # 'detected', 'not_detected', 'partial', 'offline', 'unknown'
    attack_type: str = ""  # Tool name (e.g., 'nmap', 'hydra')
    target_ip: str = ""  # Target IP address
    alerts_count: int = 0
    alerts: List[Dict[str, Any]] = field(default_factory=list)
    rule_ids: List[str] = field(default_factory=list)
    reason: str = ""
    checked_at: datetime = field(default_factory=datetime.now)


@dataclass
class EngagementDetectionSummary:
    """Summary of detection coverage for an engagement."""

    engagement_id: int
    total_attacks: int
    detected: int
    not_detected: int
    partial: int
    offline: int
    unknown: int
    coverage_percent: float
    results: List[DetectionResult] = field(default_factory=list)


class DetectionValidator:
    """Correlates SoulEyez attacks with SIEM alerts.

    Supports multiple SIEM platforms through the SIEMClient interface.
    """

    def __init__(self, engagement_id: int):
        """
        Initialize validator for an engagement.

        Args:
            engagement_id: The engagement to validate
        """
        self.engagement_id = engagement_id
        self._client: Optional[SIEMClient] = None

    def _get_client(self) -> Optional[SIEMClient]:
        """Get SIEM client for the engagement.

        Uses SIEMFactory to create the appropriate client based on
        the engagement's SIEM configuration (Wazuh, Splunk, Elastic, or Sentinel).
        """
        if self._client:
            return self._client

        self._client = SIEMFactory.from_engagement(self.engagement_id)
        return self._client

    def get_siem_type(self) -> Optional[str]:
        """Get the configured SIEM type for this engagement.

        Returns:
            SIEM type string ('wazuh', 'splunk', etc.) or None if not configured
        """
        client = self._get_client()
        return client.siem_type if client else None

    def validate_job(self, job_id: int) -> DetectionResult:
        """
        Check if a completed job triggered SIEM alerts.

        Args:
            job_id: The job to validate (from job queue)

        Returns:
            DetectionResult with status and matched alerts
        """
        import re

        # Get job details from job queue (jobs.json)
        job = _get_job_by_id(job_id)
        if not job:
            return DetectionResult(
                job_id=job_id, status="unknown", reason="Job not found in queue"
            )

        # Verify engagement matches
        if job.get("engagement_id") != self.engagement_id:
            return DetectionResult(
                job_id=job_id,
                status="unknown",
                reason="Job belongs to different engagement",
            )

        job_tool = job.get("tool") or "unknown"
        job_command = _reconstruct_command(job)
        # Use started_at or finished_at for execution time
        executed_at = (
            job.get("started_at") or job.get("finished_at") or job.get("created_at")
        )
        # Job ran successfully if status is done, no_results, or warning
        # (all of these sent network traffic that should be detectable by SIEM)
        job_status = job.get("status", "")
        success = job_status in ("done", "no_results", "warning")

        # Extract target IP from command (common patterns)
        target_ip = None
        ip_pattern = r"\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\b"
        ip_matches = re.findall(ip_pattern, job_command)
        if ip_matches:
            # Filter out common non-target IPs
            for ip in ip_matches:
                if not ip.startswith("127.") and not ip.startswith("0."):
                    target_ip = ip
                    break

        # Check if job was successful
        if not success:
            return DetectionResult(
                job_id=job_id,
                status="unknown",
                attack_type=job_tool,
                target_ip=target_ip or "",
                reason=f"Job did not complete successfully",
            )

        # Get attack signature
        signature = get_signature(job_tool)

        # Check if offline tool (no network detection expected)
        if signature.get("offline"):
            result = DetectionResult(
                job_id=job_id,
                status="offline",
                attack_type=job_tool,
                target_ip=target_ip or "",
                reason=f"{job_tool} is an offline tool, no network detection expected",
            )
            self._save_result(result, job_id)
            return result

        # Check if SIEM is configured
        client = self._get_client()
        if not client:
            return DetectionResult(
                job_id=job_id,
                status="unknown",
                attack_type=job_tool,
                target_ip=target_ip or "",
                reason="SIEM not configured for this engagement",
            )

        # Parse timestamp
        try:
            if isinstance(executed_at, str):
                exec_time = datetime.fromisoformat(
                    executed_at.replace("Z", "+00:00").replace(" ", "T")
                )
            else:
                exec_time = executed_at or datetime.now()
        except Exception:
            exec_time = datetime.now() - timedelta(hours=1)

        # Query window: 5 minutes before execution to detection_window after
        detection_window = signature.get(
            "detection_window_seconds", DEFAULT_DETECTION_WINDOW
        )
        query_start = exec_time - timedelta(minutes=5)
        query_end = exec_time + timedelta(seconds=detection_window)

        # Get expected rule IDs (convert to strings for compatibility)
        expected_rules = signature.get("wazuh_rules", [])
        rule_id_strings = [str(r) for r in expected_rules] if expected_rules else None

        # Query SIEM for alerts
        try:
            alerts = client.get_alerts(
                start_time=query_start,
                end_time=query_end,
                dest_ip=target_ip,  # Target IP is the destination
                rule_ids=rule_id_strings,
                limit=100,
            )
        except Exception as e:
            siem_type = client.siem_type if client else "SIEM"
            return DetectionResult(
                job_id=job_id,
                status="unknown",
                reason=f"Error querying {siem_type}: {str(e)}",
            )

        # Also search by patterns if no rule matches
        if not alerts and signature.get("search_patterns"):
            for pattern in signature["search_patterns"][:3]:  # Limit searches
                try:
                    pattern_alerts = client.get_alerts(
                        start_time=query_start,
                        end_time=query_end,
                        search_text=pattern,
                        limit=50,
                    )
                    alerts.extend(pattern_alerts)
                except Exception:
                    continue

        # Deduplicate alerts (SIEMAlert objects have .id attribute)
        seen_ids = set()
        unique_alerts = []
        for alert in alerts:
            alert_id = getattr(alert, "id", None) or str(
                getattr(alert, "timestamp", "")
            )
            if alert_id not in seen_ids:
                seen_ids.add(alert_id)
                unique_alerts.append(alert)

        # Determine detection status
        if unique_alerts:
            rule_ids = list(
                set(getattr(a, "rule_id", "unknown") for a in unique_alerts)
            )
            # Convert SIEMAlert dataclass objects to dicts for storage
            # Include all normalized fields (rule_id, rule_name, severity, etc.)
            alert_dicts = []
            for a in unique_alerts[:20]:
                if hasattr(a, "__dataclass_fields__"):
                    # Convert dataclass to dict
                    alert_dict = asdict(a)
                    # Convert datetime to ISO string for JSON serialization
                    if isinstance(alert_dict.get("timestamp"), datetime):
                        alert_dict["timestamp"] = alert_dict["timestamp"].isoformat()
                    alert_dicts.append(alert_dict)
                elif isinstance(a, dict):
                    alert_dicts.append(a)
                else:
                    # Fallback: try to extract raw_data or convert to dict
                    alert_dicts.append(getattr(a, "raw_data", {}) or {})
            result = DetectionResult(
                job_id=job_id,
                status="detected",
                attack_type=job_tool,
                target_ip=target_ip or "",
                alerts_count=len(unique_alerts),
                alerts=alert_dicts,
                rule_ids=rule_ids,
                reason=f"Found {len(unique_alerts)} related alert(s)",
            )
        else:
            result = DetectionResult(
                job_id=job_id,
                status="not_detected",
                attack_type=job_tool,
                target_ip=target_ip or "",
                alerts_count=0,
                reason=f"No alerts found for {job_tool} attack on {target_ip}",
            )

        # Save result to database
        self._save_result(result, job_id)
        return result

    def _save_result(self, result: DetectionResult, job_id: int):
        """Save detection result to database."""
        import re

        # Get job info from job queue
        job = _get_job_by_id(job_id)
        if not job:
            return

        # Extract target IP from command or use job target
        target_ip = job.get("target")
        command = _reconstruct_command(job)

        # Try to extract more specific IP from command
        ip_pattern = r"\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\b"
        ip_matches = re.findall(ip_pattern, command)
        if ip_matches:
            for ip in ip_matches:
                if not ip.startswith("127.") and not ip.startswith("0."):
                    target_ip = ip
                    break

        # Get timestamps
        attack_start = job.get("started_at") or job.get("created_at")
        attack_end = job.get("finished_at") or attack_start

        db = get_db()
        conn = db.get_connection()
        cursor = conn.cursor()

        # Delete existing result for this job (if any)
        cursor.execute("DELETE FROM detection_results WHERE job_id = ?", (job_id,))

        # Insert new result
        cursor.execute(
            """
            INSERT INTO detection_results
            (job_id, engagement_id, attack_type, target_ip, attack_start, attack_end,
             detection_status, alerts_count, wazuh_alerts_json, rule_ids, checked_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                job_id,
                self.engagement_id,
                job.get("tool"),  # attack_type (tool)
                target_ip,
                attack_start,
                attack_end,
                result.status,
                result.alerts_count,
                json.dumps(result.alerts[:20]) if result.alerts else None,
                ",".join(result.rule_ids) if result.rule_ids else None,
                datetime.now().isoformat(),
            ),
        )
        conn.commit()

    def validate_engagement(self) -> EngagementDetectionSummary:
        """
        Get detection coverage for the entire engagement.

        Returns:
            Summary with counts and individual results
        """
        from souleyez.detection.attack_signatures import ATTACK_SIGNATURES

        # Get all completed jobs for this engagement from job queue
        all_jobs = _read_jobs_file()
        completed_jobs = [
            job
            for job in all_jobs
            if job.get("engagement_id") == self.engagement_id
            and job.get("status") == "done"
            # Only include known attack tools (filter out echo, cat, etc.)
            and job.get("tool", "").lower() in ATTACK_SIGNATURES
        ]

        # Sort by finished_at descending
        completed_jobs.sort(
            key=lambda j: j.get("finished_at") or j.get("started_at") or "",
            reverse=True,
        )

        job_ids = [job.get("id") for job in completed_jobs if job.get("id") is not None]

        if not job_ids:
            return EngagementDetectionSummary(
                engagement_id=self.engagement_id,
                total_attacks=0,
                detected=0,
                not_detected=0,
                partial=0,
                offline=0,
                unknown=0,
                coverage_percent=0.0,
            )

        # Validate each job
        results = []
        for job_id in job_ids:
            result = self.validate_job(job_id)
            results.append(result)

        # Calculate summary
        detected = sum(1 for r in results if r.status == "detected")
        not_detected = sum(1 for r in results if r.status == "not_detected")
        partial = sum(1 for r in results if r.status == "partial")
        offline = sum(1 for r in results if r.status == "offline")
        unknown = sum(1 for r in results if r.status == "unknown")

        # Calculate coverage (excluding offline and unknown)
        countable = detected + not_detected + partial
        coverage = (detected / countable * 100) if countable > 0 else 0.0

        return EngagementDetectionSummary(
            engagement_id=self.engagement_id,
            total_attacks=len(results),
            detected=detected,
            not_detected=not_detected,
            partial=partial,
            offline=offline,
            unknown=unknown,
            coverage_percent=round(coverage, 1),
            results=results,
        )

    def get_detection_gaps(self) -> List[DetectionResult]:
        """Get list of attacks that were NOT detected."""
        summary = self.validate_engagement()
        return [r for r in summary.results if r.status == "not_detected"]
