#!/usr/bin/env python3
"""
souleyez.ai.feedback_handler - Auto-update database after command execution
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from ..storage.credentials import CredentialsManager
from ..storage.hosts import HostManager

logger = logging.getLogger(__name__)


class FeedbackHandler:
    """
    Automatically update database based on command execution results.

    Implements the feedback loop:
    - Update credential status (valid/invalid)
    - Update host status (compromised/active)
    - Set access levels (user/root)
    - Add notes with execution details
    """

    def __init__(self):
        """Initialize feedback handler."""
        self.host_mgr = HostManager()
        self.creds_mgr = CredentialsManager()

    def apply_feedback(
        self,
        engagement_id: int,
        parsed_result: Dict[str, Any],
        recommendation: Dict[str, Any],
        command: str,
    ) -> Dict[str, Any]:
        """
        Apply feedback updates to database.

        Args:
            engagement_id: Current engagement ID
            parsed_result: Parsed command result
            recommendation: Original AI recommendation
            command: Command that was executed

        Returns:
            Dict describing what was updated
        """
        feedback = {
            "hosts_updated": 0,
            "credentials_updated": 0,
            "services_added": 0,
            "notes_added": [],
        }

        # Extract target IP
        target = recommendation.get("target", "")
        action = recommendation.get("action", "").lower()

        import re

        ip_match = re.search(r"\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\b", target)
        if not ip_match:
            logger.warning(f"Could not extract IP from target: {target}")
            return feedback

        ip = ip_match.group(1)

        # Get host from database
        host = self.host_mgr.get_host_by_ip(engagement_id, ip)
        if not host:
            logger.warning(f"Host {ip} not found in engagement {engagement_id}")
            return feedback

        # Handle SSH results
        if (
            "ssh" in command.lower()
            and parsed_result.get("credential_valid") is not None
        ):
            feedback.update(
                self._handle_ssh_feedback(
                    engagement_id, host, parsed_result, recommendation
                )
            )

        # Handle MySQL results
        elif (
            "mysql" in command.lower()
            and parsed_result.get("credential_valid") is not None
        ):
            feedback.update(
                self._handle_mysql_feedback(
                    engagement_id, host, parsed_result, recommendation
                )
            )

        # Handle nmap results
        elif "nmap" in command.lower() and parsed_result.get("open_ports"):
            feedback.update(
                self._handle_nmap_feedback(engagement_id, host, parsed_result)
            )

        return feedback

    def _handle_ssh_feedback(
        self,
        engagement_id: int,
        host: Dict[str, Any],
        result: Dict[str, Any],
        recommendation: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Handle feedback for SSH credential testing."""
        feedback = {"hosts_updated": 0, "credentials_updated": 0, "notes_added": []}

        # Extract credentials from recommendation
        import re

        text = (
            f"{recommendation.get('action', '')} {recommendation.get('rationale', '')}"
        )
        cred_match = re.search(r"(\w+):(\w+)", text)

        if not cred_match:
            logger.warning("Could not extract credentials from recommendation")
            return feedback

        username = cred_match.group(1)
        password = cred_match.group(2)

        # Find credential in database
        creds = self.creds_mgr.list_credentials(engagement_id)
        cred_id = None
        for cred in creds:
            if cred.get("username") == username and cred.get("password") == password:
                cred_id = cred.get("id")
                break

        # Update credential status
        if cred_id:
            status = "valid" if result.get("credential_valid") else "invalid"
            notes = result.get("details", "")

            self.creds_mgr.update_credential_status(cred_id, status=status, notes=notes)
            feedback["credentials_updated"] = 1
            feedback["notes_added"].append(
                f"Updated credential {username} status: {status}"
            )
            logger.info(f"Updated credential {cred_id} status to {status}")

        # Update host status if credentials were valid
        if result.get("credential_valid"):
            access_level = result.get("access_level", "user")
            status = "compromised"
            notes = f"Gained {access_level} access via SSH with {username}:{password}"

            self.host_mgr.update_host_status(
                host["id"], status=status, access_level=access_level, notes=notes
            )
            feedback["hosts_updated"] = 1
            feedback["notes_added"].append(
                f"Updated host {host['ip_address']}: {status}, access={access_level}"
            )
            logger.info(
                f"Updated host {host['id']} to {status} with {access_level} access"
            )

        return feedback

    def _handle_mysql_feedback(
        self,
        engagement_id: int,
        host: Dict[str, Any],
        result: Dict[str, Any],
        recommendation: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Handle feedback for MySQL credential testing."""
        feedback = {"hosts_updated": 0, "credentials_updated": 0, "notes_added": []}

        # Extract credentials
        import re

        text = (
            f"{recommendation.get('action', '')} {recommendation.get('rationale', '')}"
        )
        cred_match = re.search(r"(\w+):(\w+)", text)

        if not cred_match:
            return feedback

        username = cred_match.group(1)
        password = cred_match.group(2)

        # Find/update credential
        creds = self.creds_mgr.list_credentials(engagement_id)
        cred_id = None
        for cred in creds:
            if (
                cred.get("username") == username
                and cred.get("password") == password
                and cred.get("service") == "mysql"
            ):
                cred_id = cred.get("id")
                break

        if cred_id:
            status = "valid" if result.get("credential_valid") else "invalid"
            notes = result.get("details", "")

            self.creds_mgr.update_credential_status(cred_id, status=status, notes=notes)
            feedback["credentials_updated"] = 1
            feedback["notes_added"].append(
                f"Updated MySQL credential {username} status: {status}"
            )

        # Update host notes if connection was successful
        if result.get("credential_valid"):
            notes = f"MySQL access confirmed with {username}:{password}"
            if result.get("databases"):
                notes += f" - Databases: {', '.join(result['databases'][:5])}"

            # Only update if not already compromised with higher access
            current_access = host.get("access_level", "none")
            if current_access == "none":
                self.host_mgr.update_host_status(host["id"], notes=notes)
                feedback["hosts_updated"] = 1
                feedback["notes_added"].append(
                    f"Added MySQL access notes to host {host['ip_address']}"
                )

        return feedback

    def _handle_nmap_feedback(
        self, engagement_id: int, host: Dict[str, Any], result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle feedback for nmap scans."""
        feedback = {"hosts_updated": 0, "services_added": 0, "notes_added": []}

        # Add discovered services
        open_ports = result.get("open_ports", [])
        services_info = result.get("services", {})

        for port in open_ports:
            service_info = services_info.get(str(port), "unknown")

            # Try to parse service name and version
            import re

            service_match = re.match(r"(\S+)(?:\s+(.+))?", service_info)
            if service_match:
                service_name = service_match.group(1)
                service_version = (
                    service_match.group(2) if service_match.group(2) else None
                )
            else:
                service_name = "unknown"
                service_version = None

            # Add service to database
            try:
                self.host_mgr.add_service(
                    host["id"],
                    port=port,
                    protocol="tcp",
                    service_name=service_name,
                    service_version=service_version,
                    state="open",
                )
                feedback["services_added"] += 1
                logger.info(f"Added service {service_name} on port {port}")
            except Exception as e:
                logger.warning(f"Failed to add service {port}: {e}")

        if feedback["services_added"] > 0:
            feedback["notes_added"].append(
                f"Added {feedback['services_added']} services to host {host['ip_address']}"
            )

        return feedback
