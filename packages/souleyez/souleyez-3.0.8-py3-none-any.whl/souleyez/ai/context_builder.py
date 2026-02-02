#!/usr/bin/env python3
"""
souleyez.ai.context_builder - Build context from engagement data for LLM
"""

from typing import Optional

from ..storage.credentials import CredentialsManager
from ..storage.engagements import EngagementManager
from ..storage.findings import FindingsManager
from ..storage.hosts import HostManager


class ContextBuilder:
    """Builds formatted context from engagement data for LLM consumption."""

    def __init__(self):
        self.engagement_mgr = EngagementManager()
        self.host_mgr = HostManager()
        self.creds_mgr = CredentialsManager()
        self.findings_mgr = FindingsManager()

    def build_context(
        self, engagement_id: int, target_host_ids: Optional[list] = None
    ) -> str:
        """
        Build formatted context string from engagement data.

        Args:
            engagement_id: Engagement ID to build context for
            target_host_ids: Optional list of specific host IDs to include

        Returns:
            Formatted context string for LLM
        """
        # Get engagement details
        engagement = self.engagement_mgr.get_by_id(engagement_id)
        if not engagement:
            return f"ERROR: Engagement ID {engagement_id} not found"

        # Build context sections
        sections = []

        # Engagement info
        sections.append("=" * 60)
        sections.append(f"ENGAGEMENT: {engagement['name']}")
        if engagement.get("description"):
            sections.append(f"Description: {engagement['description']}")
        sections.append("=" * 60)
        sections.append("")

        # Get hosts (filtered if target_host_ids provided)
        all_hosts = self.host_mgr.list_hosts(engagement_id)
        if target_host_ids:
            hosts = [h for h in all_hosts if h["id"] in target_host_ids]
            sections.append(
                f"SELECTED TARGET HOSTS ({len(hosts)} of {len(all_hosts)}):"
            )
        else:
            hosts = all_hosts
            sections.append(f"DISCOVERED HOSTS ({len(hosts)}):")

        if hosts:
            for host in hosts:
                ip = host.get("ip_address", "unknown")
                hostname = host.get("hostname", "")
                os_name = host.get("os_name", "")
                status = host.get("status", "unknown")
                access_level = host.get("access_level", "none")
                notes = host.get("notes", "")

                # Status icon
                if status == "compromised" or access_level != "none":
                    icon = "🔓"
                elif status in ["up", "active"]:
                    icon = "🔒"
                else:
                    icon = "❓"

                host_line = f"  {icon} {ip}"
                if hostname:
                    host_line += f" ({hostname})"

                # Show access level if compromised
                if access_level != "none":
                    host_line += f" - COMPROMISED [access={access_level.upper()}]"
                elif status:
                    host_line += f" [{status.upper()}]"

                if os_name:
                    host_line += f" - {os_name}"

                if notes:
                    host_line += f"\n    Note: {notes}"

                sections.append(host_line)
        else:
            sections.append("  - None discovered yet")
        sections.append("")

        # Get services for each host
        total_services = 0
        service_lines = []
        for host in hosts:
            host_id = host["id"]
            ip = host.get("ip_address", "unknown")
            services = self.host_mgr.get_host_services(host_id)

            for service in services:
                port = service.get("port", "?")
                protocol = service.get("protocol", "tcp")
                service_name = service.get("service_name", "unknown")
                version = service.get("service_version", "")

                service_line = f"  - {ip}:{port}/{protocol} - {service_name}"
                if version:
                    service_line += f" ({version})"

                service_lines.append(service_line)
                total_services += 1

        sections.append(f"OPEN SERVICES ({total_services}):")
        if service_lines:
            sections.extend(service_lines)
        else:
            sections.append("  - None discovered yet")
        sections.append("")

        # Get credentials
        try:
            creds = self.creds_mgr.list_credentials(engagement_id)
            sections.append(f"AVAILABLE CREDENTIALS ({len(creds)}):")
            if creds:
                for cred in creds:
                    username = cred.get("username", "unknown")
                    password = cred.get("password", "unknown")
                    service = cred.get("service", "")
                    status = cred.get("status", "untested")
                    last_tested = cred.get("last_tested", "")
                    notes = cred.get("notes", "")

                    # Status icon
                    if status == "valid":
                        icon = "✓"
                    elif status == "invalid":
                        icon = "✗"
                    else:
                        icon = "?"

                    cred_line = f"  {icon} {username}:{password}"
                    if service:
                        cred_line += f" ({service})"

                    cred_line += f" - {status.upper()}"

                    if last_tested:
                        # Extract date from timestamp
                        test_date = (
                            last_tested.split("T")[0]
                            if "T" in last_tested
                            else last_tested
                        )
                        cred_line += f", tested {test_date}"

                    if notes:
                        cred_line += f"\n    Note: {notes}"

                    sections.append(cred_line)
            else:
                sections.append("  - None discovered yet")
        except Exception as e:
            sections.append(f"  - Error accessing credentials: {str(e)}")
        sections.append("")

        # Get findings
        findings = self.findings_mgr.list_findings(engagement_id)
        sections.append(f"FINDINGS ({len(findings)}):")
        if findings:
            # Group by severity
            critical = [f for f in findings if f.get("severity") == "critical"]
            high = [f for f in findings if f.get("severity") == "high"]
            medium = [f for f in findings if f.get("severity") == "medium"]
            low = [f for f in findings if f.get("severity") == "low"]
            info = [f for f in findings if f.get("severity") == "info"]

            if critical:
                sections.append(f"  CRITICAL ({len(critical)}):")
                for f in critical:
                    sections.append(f"    - {f.get('title', 'Untitled')}")
                    if f.get("cve_id"):
                        sections.append(f"      CVE: {f['cve_id']}")
                    if f.get("cvss_score"):
                        sections.append(f"      CVSS: {f['cvss_score']}")

            if high:
                sections.append(f"  HIGH ({len(high)}):")
                for f in high:
                    sections.append(f"    - {f.get('title', 'Untitled')}")
                    if f.get("cve_id"):
                        sections.append(f"      CVE: {f['cve_id']}")

            if medium:
                sections.append(f"  MEDIUM ({len(medium)}):")
                for f in medium:
                    sections.append(f"    - {f.get('title', 'Untitled')}")

            if low:
                sections.append(f"  LOW ({len(low)}):")
                for f in low:
                    sections.append(f"    - {f.get('title', 'Untitled')}")

            if info:
                sections.append(f"  INFO ({len(info)}):")
                for f in info[:5]:  # Limit to first 5 info findings
                    sections.append(f"    - {f.get('title', 'Untitled')}")
                if len(info) > 5:
                    sections.append(f"    ... and {len(info) - 5} more")
        else:
            sections.append("  - None discovered yet")
        sections.append("")

        sections.append("=" * 60)

        return "\n".join(sections)

    def get_state_summary(
        self, engagement_id: int, target_host_ids: Optional[list] = None
    ) -> str:
        """
        Build a summary of current engagement state (what's already done).

        Args:
            engagement_id: Engagement ID
            target_host_ids: Optional list of specific host IDs to include

        Returns:
            String summary of completed actions and current access level
        """
        sections = []

        # Get data (filtered if target_host_ids provided)
        all_hosts = self.host_mgr.list_hosts(engagement_id)
        if target_host_ids:
            hosts = [h for h in all_hosts if h["id"] in target_host_ids]
        else:
            hosts = all_hosts

        creds = self.creds_mgr.list_credentials(engagement_id)

        # Track state
        compromised_hosts = []
        highest_access = "none"
        validated_creds = []
        invalid_creds = []

        # Analyze hosts
        for host in hosts:
            access = host.get("access_level", "none")
            if access != "none":
                ip = host.get("ip_address", "unknown")
                compromised_hosts.append(f"{ip} ({access})")

                # Track highest access
                access_levels = ["none", "user", "admin", "root"]
                if access_levels.index(access) > access_levels.index(highest_access):
                    highest_access = access

        # Analyze credentials
        for cred in creds:
            status = cred.get("status", "untested")
            if status == "valid":
                username = cred.get("username", "unknown")
                service = cred.get("service", "")
                validated_creds.append(
                    f"{username} ({service})" if service else username
                )
            elif status == "invalid":
                invalid_creds.append(f"{cred.get('username', 'unknown')}")

        # Build summary
        if not compromised_hosts and not validated_creds:
            sections.append("CURRENT STATE: Initial reconnaissance phase")
            sections.append("- No systems compromised yet")
            sections.append("- No credentials validated yet")
        else:
            sections.append("CURRENT STATE:")

            if compromised_hosts:
                sections.append(f"- Compromised hosts: {', '.join(compromised_hosts)}")
                sections.append(
                    f"- Highest access level achieved: {highest_access.upper()}"
                )
            else:
                sections.append("- No systems compromised yet")

            if validated_creds:
                sections.append(
                    f"- Validated credentials: {', '.join(validated_creds)}"
                )

            if invalid_creds:
                sections.append(
                    f"- Failed credentials tested: {', '.join(invalid_creds[:3])}"
                )

        return "\n".join(sections)
