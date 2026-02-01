#!/usr/bin/env python3
"""
souleyez.ai.action_mapper - Map AI recommendations to executable commands
"""

import logging
import re
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class ActionMapper:
    """
    Maps AI recommendations to executable commands.

    Handles translation of natural language actions into
    concrete shell commands.
    """

    def __init__(self):
        """Initialize action mapper."""
        from ..storage.credentials import CredentialsManager

        self.creds_mgr = CredentialsManager()

    def map_to_command(
        self, recommendation: Dict[str, Any], engagement_id: Optional[int] = None
    ) -> Optional[str]:
        """
        Map AI recommendation to executable command.

        Args:
            recommendation: Dict with keys:
                - action: Human-readable action
                - target: Target host/service
                - rationale: Why this action
                - expected_outcome: Expected result
                - risk_level: Risk level
            engagement_id: Optional engagement ID for credential lookup

        Returns:
            Shell command string or None if can't map
        """
        action = recommendation.get("action", "").lower()
        target = recommendation.get("target", "")
        rationale = recommendation.get("rationale", "").lower()

        # Extract IP and port from target
        ip_match = re.search(r"\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\b", target)
        port_match = re.search(r":(\d+)", target)

        ip = ip_match.group(1) if ip_match else None
        port = port_match.group(1) if port_match else None

        if not ip:
            logger.warning(f"Could not extract IP from target: {target}")
            return None

        # PostgreSQL credential testing (check before MySQL)
        if ("postgres" in action or "postgresql" in action or "psql" in action) and (
            "test" in action or "login" in action or "credential" in action
        ):
            return self._map_postgresql_test(
                ip, port or "5432", recommendation, engagement_id
            )

        # MySQL credential testing (check before SSH)
        if "mysql" in action and (
            "test" in action or "login" in action or "credential" in action
        ):
            return self._map_mysql_test(
                ip, port or "3306", recommendation, engagement_id
            )

        # MySQL enumeration (expanded patterns - check before SSH)
        if "mysql" in action and (
            "enum" in action or "database" in action or "data" in action
        ):
            return self._map_mysql_enum(
                ip, port or "3306", recommendation, engagement_id
            )

        # SMB credential testing
        if (
            "smb" in action
            or "cifs" in action
            or "smb" in target.lower()
            or ("authenticate" in action or "login" in action or "credential" in action)
            and ("445" in target or "139" in target or "smb" in rationale)
        ):
            return self._map_smb_test(ip, port or "445", recommendation, engagement_id)

        # RDP credential testing
        if (
            "rdp" in action
            or "rdp" in target.lower()
            or "remote desktop" in action
            or ("authenticate" in action or "login" in action or "credential" in action)
            and ("3389" in target or "rdp" in rationale)
        ):
            return self._map_rdp_test(ip, port or "3389", recommendation, engagement_id)

        # FTP credential testing
        if (
            "ftp" in action
            or "ftp" in target.lower()
            or ("authenticate" in action or "login" in action or "credential" in action)
            and ("21" in target or "ftp" in rationale)
        ):
            return self._map_ftp_test(ip, port or "21", recommendation, engagement_id)

        # SSH credential testing (expanded patterns)
        if (
            "ssh" in action
            or "ssh" in target.lower()
            or ("authenticate" in action or "login" in action or "credential" in action)
            and ("22" in target or "ssh" in rationale or not port)
        ):
            return self._map_ssh_test(ip, port or "22", recommendation, engagement_id)

        # HTTP/Web enumeration (BEFORE generic nmap scan)
        if (
            "http" in action
            or "web" in action
            or "directory" in action
            or "path" in action
            or "http" in target.lower()
            or "web" in target.lower()
            or ("enumerate" in action or "enum" in action)
            and (
                "http" in rationale
                or "web" in rationale
                or port in ["80", "443", "8080", "8443"]
            )
        ):
            return self._map_http_enum(ip, port, recommendation)

        # Nmap port scan (keep as fallback, but more specific)
        if (
            "nmap" in action
            or "port scan" in action
            or ("scan" in action and "port" in action)
            or ("discover" in action and "port" in action)
        ):
            return self._map_nmap_scan(ip, recommendation)

        # Service enumeration
        if "enumerate" in action and "service" in action:
            return self._map_service_enum(ip, port, recommendation)

        logger.warning(f"No command mapping found for action: {action}")
        return None

    def _find_credentials(
        self, engagement_id: Optional[int], service: str, ip: Optional[str] = None
    ) -> Optional[tuple]:
        """
        Find valid credentials from database.

        Args:
            engagement_id: Engagement ID
            service: Service name (ssh, mysql, etc.)
            ip: Optional IP to filter by

        Returns:
            Tuple of (username, password) or None
        """
        if not engagement_id:
            return None

        try:
            creds = self.creds_mgr.list_credentials(engagement_id)

            # Look for valid credentials for this service
            for cred in creds:
                cred_service = cred.get("service", "").lower()
                cred_status = cred.get("status", "untested")

                if service.lower() in cred_service or cred_service in service.lower():
                    # Prefer valid credentials, but fall back to untested
                    if cred_status == "valid":
                        return (cred.get("username"), cred.get("password"))

            # If no valid creds, try untested for same service
            for cred in creds:
                cred_service = cred.get("service", "").lower()
                cred_status = cred.get("status", "untested")

                if (
                    service.lower() in cred_service or cred_service in service.lower()
                ) and cred_status == "untested":
                    return (cred.get("username"), cred.get("password"))

            # If still nothing and service is mysql, try SSH credentials (common on same host)
            if service.lower() == "mysql":
                for cred in creds:
                    if (
                        cred.get("service", "").lower() == "ssh"
                        and cred.get("status") == "valid"
                    ):
                        logger.info(
                            "Using SSH credentials for MySQL (common username on same host)"
                        )
                        return (cred.get("username"), cred.get("password"))

        except Exception as e:
            logger.error(f"Failed to lookup credentials: {e}")

        return None

    def _map_ssh_test(
        self,
        ip: str,
        port: str,
        rec: Dict[str, Any],
        engagement_id: Optional[int] = None,
    ) -> Optional[str]:
        """Map SSH credential testing to command."""
        # Try to extract credentials from action or rationale
        action = rec.get("action", "")
        rationale = rec.get("rationale", "")
        text = f"{action} {rationale}".lower()

        # Look for credential patterns
        cred_match = re.search(r"(\w+):(\w+)", text)
        if cred_match:
            username = cred_match.group(1)
            password = cred_match.group(2)
        else:
            # Try to find credentials from database
            creds = self._find_credentials(engagement_id, "ssh", ip)
            if not creds:
                logger.warning("SSH test requested but no credentials found")
                return None
            username, password = creds

        return (
            f"sshpass -p '{password}' ssh -o ConnectTimeout=5 "
            f"-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null "
            f"-o HostKeyAlgorithms=+ssh-rsa -o PubkeyAcceptedKeyTypes=+ssh-rsa "
            f"-p {port} {username}@{ip} 'echo SSH_SUCCESS && whoami && id'"
        )

    def _map_ftp_test(
        self,
        ip: str,
        port: str,
        rec: Dict[str, Any],
        engagement_id: Optional[int] = None,
    ) -> Optional[str]:
        """Map FTP credential testing to command."""
        action = rec.get("action", "")
        rationale = rec.get("rationale", "")
        text = f"{action} {rationale}".lower()

        # Look for credential patterns
        cred_match = re.search(r"(\w+):(\w+)", text)
        if cred_match:
            username = cred_match.group(1)
            password = cred_match.group(2)
        else:
            # Try to find credentials from database
            creds = self._find_credentials(engagement_id, "ftp", ip)
            if not creds:
                logger.warning("FTP test requested but no credentials found")
                return None
            username, password = creds

        # Use lftp for testing (more reliable than ftp command)
        return (
            f"lftp -u {username},{password} -e 'ls; bye' {ip}:{port} 2>&1 || "
            f"echo 'FTP_FAILED'"
        )

    def _map_smb_test(
        self,
        ip: str,
        port: str,
        rec: Dict[str, Any],
        engagement_id: Optional[int] = None,
    ) -> Optional[str]:
        """Map SMB credential testing to command."""
        action = rec.get("action", "")
        rationale = rec.get("rationale", "")
        text = f"{action} {rationale}".lower()

        # Look for credential patterns
        cred_match = re.search(r"(\w+):(\w+)", text)
        if cred_match:
            username = cred_match.group(1)
            password = cred_match.group(2)
        else:
            # Try to find credentials from database
            creds = self._find_credentials(engagement_id, "smb", ip)
            if not creds:
                logger.warning("SMB test requested but no credentials found")
                return None
            username, password = creds

        # Use smbclient to list shares (tests authentication)
        return (
            f"smbclient -L //{ip} -U {username}%{password} -p {port} "
            f"-N 2>&1 || echo 'SMB_FAILED'"
        )

    def _map_rdp_test(
        self,
        ip: str,
        port: str,
        rec: Dict[str, Any],
        engagement_id: Optional[int] = None,
    ) -> Optional[str]:
        """Map RDP credential testing to command."""
        action = rec.get("action", "")
        rationale = rec.get("rationale", "")
        text = f"{action} {rationale}".lower()

        # Look for credential patterns
        cred_match = re.search(r"(\w+):(\w+)", text)
        if cred_match:
            username = cred_match.group(1)
            password = cred_match.group(2)
        else:
            # Try to find credentials from database
            creds = self._find_credentials(engagement_id, "rdp", ip)
            if not creds:
                logger.warning("RDP test requested but no credentials found")
                return None
            username, password = creds

        # Use xfreerdp with auth-only mode (doesn't open GUI, just tests auth)
        return (
            f"timeout 10 xfreerdp /v:{ip}:{port} /u:{username} /p:{password} "
            f"/cert-ignore +auth-only /sec:nla 2>&1 || echo 'RDP_FAILED'"
        )

    def _map_mysql_test(
        self,
        ip: str,
        port: str,
        rec: Dict[str, Any],
        engagement_id: Optional[int] = None,
    ) -> Optional[str]:
        """Map MySQL credential testing to command."""
        action = rec.get("action", "")
        rationale = rec.get("rationale", "")
        text = f"{action} {rationale}".lower()

        # Look for credential patterns
        cred_match = re.search(r"(\w+):(\w+)", text)
        if cred_match:
            username = cred_match.group(1)
            password = cred_match.group(2)
        else:
            # Try to find credentials from database
            creds = self._find_credentials(engagement_id, "mysql", ip)
            if not creds:
                logger.warning("MySQL test requested but no credentials found")
                return None
            username, password = creds

        return (
            f"mysql -h {ip} -P {port} -u {username} -p'{password}' "
            f"--skip-ssl "
            f"-e 'SELECT version();' 2>&1"
        )

    def _map_mysql_enum(
        self,
        ip: str,
        port: str,
        rec: Dict[str, Any],
        engagement_id: Optional[int] = None,
    ) -> Optional[str]:
        """Map MySQL enumeration to command."""
        action = rec.get("action", "")
        rationale = rec.get("rationale", "")
        text = f"{action} {rationale}".lower()

        # Look for credentials
        cred_match = re.search(r"(\w+):(\w+)", text)
        if cred_match:
            username = cred_match.group(1)
            password = cred_match.group(2)
        else:
            # Try to find credentials from database
            creds = self._find_credentials(engagement_id, "mysql", ip)
            if not creds:
                logger.warning("MySQL enumeration requested but no credentials found")
                return None
            username, password = creds

        return (
            f"mysql -h {ip} -P {port} -u {username} -p'{password}' "
            f"--skip-ssl "
            f"-e 'SHOW DATABASES; SELECT user,host FROM mysql.user;' 2>&1"
        )

    def _map_postgresql_test(
        self,
        ip: str,
        port: str,
        rec: Dict[str, Any],
        engagement_id: Optional[int] = None,
    ) -> Optional[str]:
        """Map PostgreSQL credential testing to command."""
        action = rec.get("action", "")
        rationale = rec.get("rationale", "")
        text = f"{action} {rationale}".lower()

        # Look for credential patterns
        cred_match = re.search(r"(\w+):(\w+)", text)
        if cred_match:
            username = cred_match.group(1)
            password = cred_match.group(2)
        else:
            # Try to find credentials from database
            creds = self._find_credentials(engagement_id, "postgresql", ip)
            if not creds:
                # Also try 'postgres' service name
                creds = self._find_credentials(engagement_id, "postgres", ip)
            if not creds:
                logger.warning("PostgreSQL test requested but no credentials found")
                return None
            username, password = creds

        return (
            f"PGPASSWORD='{password}' psql -h {ip} -p {port} -U {username} "
            f"-d postgres -c 'SELECT version();' 2>&1 || echo 'PSQL_FAILED'"
        )

    def _map_nmap_scan(self, ip: str, rec: Dict[str, Any]) -> str:
        """Map nmap scanning to command."""
        action = rec.get("action", "").lower()

        # Quick scan by default
        if "full" in action or "all" in action:
            return f"nmap -sV -p- {ip}"
        elif "quick" in action or "fast" in action:
            return f"nmap -F {ip}"
        else:
            # Default: top 1000 ports with version detection
            return f"nmap -sV {ip}"

    def _map_http_enum(self, ip: str, port: Optional[str], rec: Dict[str, Any]) -> str:
        """
        Map HTTP/web enumeration to appropriate tools.

        Uses gobuster for web content discovery and vulnerability identification.
        """
        action = rec.get("action", "").lower()
        target_info = rec.get("target", "").lower()

        # Determine port
        if not port:
            # Try to extract from target or default based on protocol
            if "https" in target_info or "443" in target_info:
                port = "443"
            else:
                port = "80"

        # Build URL
        protocol = "https" if port in ["443", "8443"] else "http"
        url = f"{protocol}://{ip}:{port}"

        # Prefer gobuster for directory/path enumeration
        if (
            "directory" in action
            or "path" in action
            or "dir" in action
            or "file" in action
        ):
            ssl_flag = " -k" if protocol == "https" else ""
            return f"gobuster dir -u {url} -w data/wordlists/web_dirs_common.txt -t 10{ssl_flag}"

        # Use gobuster for web vulnerability and content discovery
        elif "vulnerab" in action or "vuln" in action or "scan" in action:
            ssl_flag = " -k" if protocol == "https" else ""
            return f"gobuster dir -u {url} -w data/wordlists/web_dirs_common.txt -t 10{ssl_flag}"

        # Default to gobuster for general HTTP enumeration
        else:
            ssl_flag = " -k" if protocol == "https" else ""
            return f"gobuster dir -u {url} -w data/wordlists/web_dirs_common.txt -t 10{ssl_flag}"

    def _map_service_enum(
        self, ip: str, port: Optional[str], rec: Dict[str, Any]
    ) -> Optional[str]:
        """Map service enumeration to command."""
        if not port:
            return f"nmap -sV {ip}"

        service = rec.get("target", "").lower()

        if "http" in service or port in ["80", "443", "8080"]:
            return f"curl -I http://{ip}:{port}/ 2>&1"
        elif "ssh" in service or port == "22":
            return f"ssh -V {ip} 2>&1 | head -1"
        elif "mysql" in service or port == "3306":
            return f"nmap -sV -p {port} {ip}"
        else:
            return f"nc -zv {ip} {port} 2>&1"
