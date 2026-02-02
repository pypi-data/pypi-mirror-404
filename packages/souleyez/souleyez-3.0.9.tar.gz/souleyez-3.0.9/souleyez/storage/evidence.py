#!/usr/bin/env python3
"""
Evidence collection and organization for pentest workflow.
Aggregates all artifacts from jobs, findings, credentials, etc.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional


class EvidenceManager:
    """Manages evidence collection across all data sources."""

    def __init__(self):
        # Import existing managers
        from souleyez.storage.credentials import CredentialsManager
        from souleyez.storage.findings import FindingsManager
        from souleyez.storage.hosts import HostManager
        from souleyez.storage.osint import OsintManager
        from souleyez.storage.screenshots import ScreenshotManager

        self.osint = OsintManager()
        self.hosts = HostManager()
        self.findings = FindingsManager()
        self.creds = CredentialsManager()
        self.screenshots = ScreenshotManager()

    def get_all_evidence(
        self, engagement_id: int, filters: Optional[Dict] = None
    ) -> Dict[str, List[Dict]]:
        """
        Get all evidence organized by pentesting phase.

        Returns:
            {
                'reconnaissance': [...],
                'enumeration': [...],
                'exploitation': [...],
                'post_exploitation': [...]
            }
        """
        evidence = {
            "reconnaissance": [],
            "enumeration": [],
            "exploitation": [],
            "post_exploitation": [],
        }

        # Get all jobs and categorize
        from souleyez.engine.background import list_jobs

        jobs = list_jobs()

        # Filter jobs by engagement
        engagement_jobs = [j for j in jobs if j.get("engagement_id") == engagement_id]

        for job in engagement_jobs:
            if job.get("status") not in ["done", "error"]:
                continue  # Only show completed jobs

            phase = self._classify_phase(job["tool"])
            item = self._job_to_evidence(job)
            if self._matches_filters(item, filters):
                evidence[phase].append(item)

        # Get findings (exploitation phase)
        findings = self.findings.list_findings(engagement_id)
        for finding in findings:
            item = self._finding_to_evidence(finding)
            if self._matches_filters(item, filters):
                evidence["exploitation"].append(item)

        # Get credentials (exploitation phase)
        creds = self.creds.list_credentials(engagement_id)
        for cred in creds:
            item = self._credential_to_evidence(cred)
            if self._matches_filters(item, filters):
                evidence["exploitation"].append(item)

        # Get screenshots (all phases based on links)
        screenshots = self.screenshots.list_screenshots(engagement_id)
        for screenshot in screenshots:
            item = self._screenshot_to_evidence(screenshot)
            if self._matches_filters(item, filters):
                # Determine phase based on linked entities
                phase = self._classify_screenshot_phase(screenshot)
                evidence[phase].append(item)

        # Sort each phase by date (newest first)
        for phase in evidence:
            evidence[phase].sort(key=lambda x: x["created_at"], reverse=True)

        return evidence

    def _classify_phase(self, tool: str) -> str:
        """Classify tool into pentesting methodology phase."""
        tool_lower = tool.lower()

        # Reconnaissance tools
        if tool_lower in [
            "nmap",
            "theharvester",
            "dnsrecon",
            "whois",
            "fierce",
            "masscan",
        ]:
            return "reconnaissance"

        # Enumeration tools
        if tool_lower in [
            "gobuster",
            "dirb",
            "wpscan",
            "enum4linux",
            "smbclient",
            "smbmap",
            "rpcclient",
            "snmpwalk",
            "nuclei",
        ]:
            return "enumeration"

        # Exploitation tools
        if tool_lower in [
            "metasploit",
            "sqlmap",
            "hydra",
            "medusa",
            "john",
            "hashcat",
            "exploit",
            "msfconsole",
        ]:
            return "exploitation"

        # Default to enumeration for unknown tools
        return "enumeration"

    def _job_to_evidence(self, job: Dict) -> Dict:
        """Convert job to evidence item."""
        # Generate a meaningful title
        label = job.get("label", "").strip()
        if label:
            title = label
        else:
            # Generate smart title from tool + target
            title = self._generate_job_title(job)

        return {
            "type": "job",
            "id": job["id"],
            "tool": job["tool"],
            "target": job.get("target", "N/A"),
            "title": title,
            "label": label,  # Keep label separate for display
            "description": self._generate_job_summary(job),
            "created_at": job.get("created_at", ""),
            "status": job.get("status", "unknown"),
            "log_path": job.get("log"),
            "metadata": {
                "job_id": job["id"],
                "label": label,
                "args": job.get("args", []),
            },
        }

    def _generate_job_title(self, job: Dict) -> str:
        """Generate a meaningful title for jobs without labels."""
        tool = job["tool"].title()
        target = job.get("target", "N/A")

        # Handle multiple targets (space-separated IPs)
        if " " in target:
            targets = target.split()
            if len(targets) > 3:
                return f"{tool} scan ({len(targets)} hosts)"
            else:
                return f"{tool} - {targets[0]} +{len(targets)-1} more"

        # Handle CIDR notation
        if "/" in target:
            return f"{tool} - {target}"

        # Single target - just show it
        return f"{tool} - {target}"

    def _finding_to_evidence(self, finding: Dict) -> Dict:
        """Convert finding to evidence item."""
        target = finding.get("host") or finding.get("url", "Unknown")
        return {
            "type": "finding",
            "id": finding["id"],
            "tool": finding.get("tool", "Unknown"),
            "target": target,
            "title": finding["title"],
            "description": finding.get("description", "")[:200],
            "created_at": finding.get("created_at", ""),
            "severity": finding.get("severity", "info"),
            "metadata": {
                "finding_id": finding["id"],
                "cvss": finding.get("cvss"),
                "cve": finding.get("cve"),
            },
        }

    def _credential_to_evidence(self, cred: Dict) -> Dict:
        """Convert credential to evidence item."""
        return {
            "type": "credential",
            "id": cred["id"],
            "tool": cred.get("source", "Unknown"),
            "target": f"{cred.get('host', 'N/A')}:{cred.get('port', '?')}",
            "title": f"Credential: {cred.get('username', 'unknown')}",
            "description": f"Service: {cred.get('service', 'unknown')}",
            "created_at": cred.get("created_at", ""),
            "metadata": {
                "credential_id": cred["id"],
                "username": cred.get("username"),
                "service": cred.get("service"),
                "status": cred.get("status"),
            },
        }

    def _screenshot_to_evidence(self, screenshot: Dict) -> Dict:
        """Convert screenshot to evidence item."""
        file_size = screenshot.get("file_size", 0)
        if file_size < 1024:
            size_str = f"{file_size} B"
        elif file_size < 1024 * 1024:
            size_str = f"{file_size / 1024:.1f} KB"
        else:
            size_str = f"{file_size / (1024 * 1024):.1f} MB"

        return {
            "type": "screenshot",
            "id": screenshot["id"],
            "tool": "Screenshot",
            "target": screenshot.get("title", screenshot.get("filename", "Unknown")),
            "title": screenshot.get("title", screenshot.get("filename", "Untitled")),
            "description": screenshot.get(
                "description", f"Visual evidence ({size_str})"
            ),
            "created_at": screenshot.get("created_at", ""),
            "metadata": {
                "screenshot_id": screenshot["id"],
                "filename": screenshot.get("filename"),
                "filepath": screenshot.get("filepath"),
                "file_size": file_size,
                "mime_type": screenshot.get("mime_type"),
                "host_id": screenshot.get("host_id"),
                "finding_id": screenshot.get("finding_id"),
                "job_id": screenshot.get("job_id"),
            },
        }

    def _classify_screenshot_phase(self, screenshot: Dict) -> str:
        """Classify screenshot into pentesting phase based on linked entities."""
        # If linked to a finding, it's exploitation phase
        if screenshot.get("finding_id"):
            return "exploitation"

        # If linked to a job, classify by tool
        if screenshot.get("job_id"):
            from souleyez.engine.background import get_job

            job = get_job(screenshot["job_id"])
            if job:
                return self._classify_phase(job.get("tool", ""))

        # Default to post-exploitation
        return "post_exploitation"

    def _generate_job_summary(self, job: Dict) -> str:
        """Generate human-readable summary from job."""
        tool = job["tool"].lower()
        status = job.get("status", "unknown")

        if status == "error":
            return "Completed with errors"
        elif status == "killed":
            return "Job was killed"

        # Tool-specific summaries
        if tool == "nmap":
            return "Network port scan completed"

        if tool == "theharvester":
            return "OSINT data collection completed"

        if tool == "nuclei":
            return "Web vulnerability scan completed"

        if tool == "gobuster":
            return "Directory/file enumeration completed"

        if tool == "sqlmap":
            return "SQL injection testing completed"

        if tool == "hydra":
            return "Password brute force completed"

        # Generic summary
        return f"Scan completed: {status}"

    def _matches_filters(self, item: Dict, filters: Optional[Dict]) -> bool:
        """Check if item matches filter criteria."""
        if not filters:
            return True

        # Filter by tool
        if "tool" in filters and filters["tool"] != "all":
            if item["tool"].lower() != filters["tool"].lower():
                return False

        # Filter by host/target
        if "host" in filters and filters["host"] != "all":
            if filters["host"] not in item["target"]:
                return False

        # Filter by date range
        if "days" in filters:
            try:
                cutoff = datetime.now() - timedelta(days=filters["days"])
                item_date = datetime.fromisoformat(
                    item["created_at"].replace("Z", "+00:00")
                )
                if item_date < cutoff:
                    return False
            except:
                pass  # Skip date filtering if parsing fails

        return True

    def get_evidence_count(self, engagement_id: int) -> Dict[str, int]:
        """Get count of evidence items per phase."""
        evidence = self.get_all_evidence(engagement_id)
        return {phase: len(items) for phase, items in evidence.items()}
