#!/usr/bin/env python3
"""
souleyez.plugins.msf_auxiliary - Metasploit Framework auxiliary scanner wrapper
"""

import subprocess
import time
from pathlib import Path
from typing import List

from .plugin_base import PluginBase

HELP = {
    "name": "MSF Auxiliary (Metasploit)",
    "description": (
        "Want Metasploit to do the poking while you do the thinking?\n\n"
        "Use the MSF Auxiliary tool to run Metasploit Framework's auxiliary modules in non-interactive mode. "
        "It will scan services, pull banners, run protocol probes, and even try username/password checks — "
        "but it won't spawn meterpreter shells or run post-exploitation antics. Results are saved to the job log "
        "so you can convert them into Findings, build reports, or flex them in standups.\n\n"
        "Play nice: some modules are noisy, so stick to your rules of engagement. 😅\n\n"
        "Quick tips:\n"
        "- Non-interactive only — no sessions will be created.\n"
        "- Ideal for recon, banner grabs, protocol probes, and credential checks.\n"
        "- Capture results to the job log for later triage and reporting.\n"
        "- Beware noisy modules: run noisy checks only with explicit permission.\n"
        "- Convert interesting output into Findings so nothing gets lost.\n\n"
        "💡 Tip: For MSF import/export/console, see Main Menu → [i] MSF Integration\n"
    ),
    "usage": 'souleyez jobs enqueue msf_auxiliary <target> --args "<module_path>"',
    "examples": [
        'souleyez jobs enqueue msf_auxiliary 10.0.0.82 --args "auxiliary/scanner/ssh/ssh_enumusers"',
        'souleyez jobs enqueue msf_auxiliary 10.0.0.82 --args "auxiliary/scanner/smtp/smtp_enum"',
        'souleyez jobs enqueue msf_auxiliary 10.0.0.82 --args "auxiliary/scanner/nfs/nfsmount"',
        'souleyez jobs enqueue msf_auxiliary 10.0.0.82 --args "auxiliary/scanner/smb/smb_enumshares"',
        'souleyez jobs enqueue msf_auxiliary 10.0.0.82 --args "auxiliary/scanner/ssh/ssh_login USERNAME=root PASSWORD=toor"',
        'souleyez jobs enqueue msf_auxiliary 10.0.0.1/24 --args "auxiliary/scanner/ssh/ssh_login USER_FILE=data/wordlists/all_users.txt PASS_FILE=data/wordlists/msf_passwords.txt"',
        'souleyez jobs enqueue msf_auxiliary 10.0.0.82 --args "auxiliary/scanner/mysql/mysql_login USERNAME=root PASS_FILE=data/wordlists/msf_passwords.txt THREADS=5"',
    ],
    "preset_categories": {
        "enumeration": [
            {
                "name": "SMB Shares",
                "args": ["auxiliary/scanner/smb/smb_enumshares"],
                "desc": "Enumerate SMB shares",
                "services": ["smb", "microsoft-ds", "netbios-ssn"],
                "ports": [139, 445],
            },
            {
                "name": "SMB Users",
                "args": ["auxiliary/scanner/smb/smb_enumusers"],
                "desc": "Enumerate SMB users via RID cycling",
                "services": ["smb", "microsoft-ds", "netbios-ssn"],
                "ports": [139, 445],
            },
            {
                "name": "SMB Version Detection",
                "args": ["auxiliary/scanner/smb/smb_version"],
                "desc": "Detect SMB version and OS info",
                "services": ["smb", "microsoft-ds", "netbios-ssn"],
                "ports": [139, 445],
            },
            {
                "name": "SSH Version Detection",
                "args": ["auxiliary/scanner/ssh/ssh_version"],
                "desc": "Detect SSH version and fingerprint",
                "services": ["ssh"],
                "ports": [22],
            },
            {
                "name": "SSH Users",
                "args": [
                    "auxiliary/scanner/ssh/ssh_enumusers",
                    "USER_FILE=data/wordlists/soul_users.txt",
                ],
                "desc": "Enumerate SSH users via timing attack",
                "services": ["ssh"],
                "ports": [22],
            },
            {
                "name": "FTP Anonymous Check",
                "args": ["auxiliary/scanner/ftp/anonymous"],
                "desc": "Check for anonymous FTP access",
                "services": ["ftp"],
                "ports": [21],
            },
            {
                "name": "FTP Version Detection",
                "args": ["auxiliary/scanner/ftp/ftp_version"],
                "desc": "Detect FTP server version",
                "services": ["ftp"],
                "ports": [21],
            },
            {
                "name": "SMTP Users",
                "args": ["auxiliary/scanner/smtp/smtp_enum"],
                "desc": "Enumerate SMTP users via VRFY/EXPN/RCPT",
                "services": ["smtp"],
                "ports": [25, 465, 587],
            },
            {
                "name": "SMTP Version",
                "args": ["auxiliary/scanner/smtp/smtp_version"],
                "desc": "Detect SMTP server version",
                "services": ["smtp"],
                "ports": [25, 465, 587],
            },
            {
                "name": "SNMP Community Scanner",
                "args": ["auxiliary/scanner/snmp/snmp_login"],
                "desc": "Test SNMP community strings",
                "services": ["snmp"],
                "ports": [161],
            },
            {
                "name": "SNMP Enumeration",
                "args": ["auxiliary/scanner/snmp/snmp_enum"],
                "desc": "Extract system info via SNMP",
                "services": ["snmp"],
                "ports": [161],
            },
            {
                "name": "NFS Shares",
                "args": ["auxiliary/scanner/nfs/nfsmount"],
                "desc": "Enumerate NFS mounts",
                "services": ["nfs", "nfsd", "rpcbind"],
                "ports": [111, 2049],
            },
            {
                "name": "VNC None Auth Scanner",
                "args": ["auxiliary/scanner/vnc/vnc_none_auth"],
                "desc": "Find VNC servers with no authentication",
                "services": ["vnc"],
                "ports": [5900, 5901, 5902],
            },
            {
                "name": "RDP Scanner",
                "args": ["auxiliary/scanner/rdp/rdp_scanner"],
                "desc": "Detect RDP and check NLA settings",
                "services": ["rdp", "ms-wbt-server"],
                "ports": [3389],
            },
            {
                "name": "HTTP Version Detection",
                "args": ["auxiliary/scanner/http/http_version"],
                "desc": "Detect HTTP server version and headers",
                "services": ["http", "https", "http-proxy"],
                "ports": [80, 443, 8080, 8443],
            },
            {
                "name": "HTTP Robots.txt Scanner",
                "args": ["auxiliary/scanner/http/robots_txt"],
                "desc": "Check for robots.txt and parse entries",
                "services": ["http", "https"],
                "ports": [80, 443, 8080, 8443],
            },
            {
                "name": "HTTP Directory Scanner",
                "args": ["auxiliary/scanner/http/dir_scanner"],
                "desc": "Brute force common web directories",
                "services": ["http", "https"],
                "ports": [80, 443, 8080, 8443],
            },
            {
                "name": "LDAP Query",
                "args": ["auxiliary/gather/ldap_query"],
                "desc": "Query LDAP for users, groups, computers",
                "services": ["ldap", "ldaps"],
                "ports": [389, 636],
            },
        ],
        "vulnerability_scanning": [
            {
                "name": "SMB MS17-010 EternalBlue",
                "args": ["auxiliary/scanner/smb/smb_ms17_010"],
                "desc": "Check for MS17-010 (EternalBlue) vulnerability",
                "services": ["smb", "microsoft-ds"],
                "ports": [445],
                "priority_trigger": "smb",
            },
            {
                "name": "SSL/TLS Version Scanner",
                "args": ["auxiliary/scanner/ssl/ssl_version"],
                "desc": "Detect SSL/TLS versions and ciphers",
                "services": ["https", "ssl", "tls"],
                "ports": [443, 8443, 993, 995],
            },
            {
                "name": "SSH Weak Algorithms",
                "args": ["auxiliary/scanner/ssh/ssh_identify_pubkeys"],
                "desc": "Identify SSH public keys and weak algorithms",
                "services": ["ssh"],
                "ports": [22],
            },
            {
                "name": "HTTP PUT/DELETE Check",
                "args": ["auxiliary/scanner/http/http_put"],
                "desc": "Check for dangerous HTTP methods",
                "services": ["http", "https"],
                "ports": [80, 443],
            },
        ],
        "login_bruteforce": [
            {
                "name": "SSH Brute Force",
                "args": ["auxiliary/scanner/ssh/ssh_login"],
                "desc": "Brute force SSH authentication",
                "services": ["ssh"],
                "ports": [22],
            },
            {
                "name": "RDP Brute Force",
                "args": ["auxiliary/scanner/rdp/rdp_login"],
                "desc": "Brute force RDP authentication",
                "services": ["rdp", "ms-wbt-server"],
                "ports": [3389],
            },
            {
                "name": "SMB Brute Force",
                "args": ["auxiliary/scanner/smb/smb_login"],
                "desc": "Brute force SMB/Windows authentication",
                "services": ["smb", "microsoft-ds"],
                "ports": [445],
            },
            {
                "name": "MySQL Brute Force",
                "args": ["auxiliary/scanner/mysql/mysql_login"],
                "desc": "Brute force MySQL authentication",
                "services": ["mysql"],
                "ports": [3306],
            },
            {
                "name": "PostgreSQL Brute Force",
                "args": ["auxiliary/scanner/postgres/postgres_login"],
                "desc": "Brute force PostgreSQL authentication",
                "services": ["postgresql", "postgres"],
                "ports": [5432],
            },
            {
                "name": "FTP Brute Force",
                "args": ["auxiliary/scanner/ftp/ftp_login"],
                "desc": "Brute force FTP authentication",
                "services": ["ftp"],
                "ports": [21],
            },
            {
                "name": "Telnet Brute Force",
                "args": ["auxiliary/scanner/telnet/telnet_login"],
                "desc": "Brute force Telnet authentication",
                "services": ["telnet"],
                "ports": [23],
            },
            {
                "name": "VNC Brute Force",
                "args": ["auxiliary/scanner/vnc/vnc_login"],
                "desc": "Brute force VNC authentication",
                "services": ["vnc"],
                "ports": [5900, 5901],
            },
            {
                "name": "HTTP Basic Auth",
                "args": ["auxiliary/scanner/http/http_login"],
                "desc": "Brute force HTTP Basic authentication",
                "services": ["http", "https"],
                "ports": [80, 443, 8080],
            },
        ],
        "database_scanning": [
            {
                "name": "MySQL Version",
                "args": ["auxiliary/scanner/mysql/mysql_version"],
                "desc": "Detect MySQL version",
                "services": ["mysql"],
                "ports": [3306],
            },
            {
                "name": "PostgreSQL Version",
                "args": ["auxiliary/scanner/postgres/postgres_version"],
                "desc": "Detect PostgreSQL version",
                "services": ["postgresql", "postgres"],
                "ports": [5432],
            },
            {
                "name": "MSSQL Ping",
                "args": ["auxiliary/scanner/mssql/mssql_ping"],
                "desc": "Discover MSSQL instances",
                "services": ["mssql", "ms-sql-s"],
                "ports": [1433, 1434],
            },
            {
                "name": "MongoDB Scanner",
                "args": ["auxiliary/scanner/mongodb/mongodb_login"],
                "desc": "Check MongoDB authentication",
                "services": ["mongodb"],
                "ports": [27017],
            },
            {
                "name": "Redis Scanner",
                "args": ["auxiliary/scanner/redis/redis_server"],
                "desc": "Detect Redis server info",
                "services": ["redis"],
                "ports": [6379],
            },
        ],
    },
    "presets": [],
    "common_options": {
        "RHOSTS": "Target host(s) - IP, range, or CIDR (e.g., 10.0.0.1 or 10.0.0.0/24)",
        "RPORT": "Target port (default varies by module)",
        "THREADS": "Number of concurrent threads (default: 1)",
        "USERNAME": "Single username to test",
        "PASSWORD": "Single password to test",
        "USER_FILE": "Path to file containing usernames",
        "PASS_FILE": "Path to file containing passwords",
        "USERPASS_FILE": "Path to file containing username:password pairs",
        "BLANK_PASSWORDS": "Try blank password for each user (true/false)",
        "USER_AS_PASS": "Try username as password (true/false)",
        "STOP_ON_SUCCESS": "Stop on first successful login (true/false)",
        "VERBOSE": "Enable verbose output (true/false)",
    },
    "notes": [
        "Requires Metasploit Framework installed (msfconsole)",
        "Runs modules non-interactively (-q -x flags)",
        "Only works with auxiliary scanner modules",
        "Cannot maintain sessions or run exploits",
    ],
    "help_sections": [
        {
            "title": "What is MSF Auxiliary?",
            "color": "cyan",
            "content": [
                {
                    "title": "Overview",
                    "desc": "MSF Auxiliary runs Metasploit Framework's auxiliary modules non-interactively for scanning, enumeration, and reconnaissance without spawning shells.",
                },
                {
                    "title": "Use Cases",
                    "desc": "Leverage Metasploit for recon and validation",
                    "tips": [
                        "Banner grabbing and service detection",
                        "Protocol probes and version checks",
                        "Credential validation and brute-forcing",
                        "Vulnerability scanning (MS17-010, etc.)",
                    ],
                },
            ],
        },
        {
            "title": "How to Use",
            "color": "green",
            "content": [
                {
                    "title": "Basic Workflow",
                    "desc": "1. Select appropriate auxiliary module\n     2. Set target (RHOSTS) and options\n     3. Run non-interactively and capture output\n     4. Convert results to findings",
                },
                {
                    "title": "Module Categories",
                    "desc": "Common auxiliary module types",
                    "tips": [
                        "Enumeration: SMB shares, users, SSH keys",
                        "Vulnerability: MS17-010, SSL/TLS checks",
                        "Login: SSH, RDP, SMB, MySQL brute-force",
                        "Database: MySQL, PostgreSQL, MSSQL scanning",
                    ],
                },
            ],
        },
        {
            "title": "Tips & Best Practices",
            "color": "yellow",
            "content": [
                (
                    "Best Practices:",
                    [
                        "Use enumeration modules before login attempts",
                        "Set THREADS wisely to avoid lockouts",
                        "Use USER_FILE and PASS_FILE for wordlists",
                        "Save results to job log for documentation",
                        "Check module options with 'show options' first",
                    ],
                ),
                (
                    "Common Issues:",
                    [
                        "Module not found: Update Metasploit (msfupdate)",
                        "No output: Check RHOSTS and module options",
                        "Timeout errors: Increase timeout or reduce THREADS",
                        "Session warnings: Normal for auxiliary modules",
                    ],
                ),
            ],
        },
    ],
}

# Flatten presets from categories
for category_presets in HELP["preset_categories"].values():
    HELP["presets"].extend(category_presets)


class MsfAuxiliaryPlugin(PluginBase):
    name = "Metasploit Auxiliary"
    tool = "msf_auxiliary"
    category = "exploitation"
    HELP = HELP

    # Keys that contain file paths which may need resolution
    FILE_PATH_KEYS = {"USER_FILE", "PASS_FILE", "USERPASS_FILE"}

    def _resolve_path(self, value: str) -> str:
        """Convert relative paths to absolute paths for MSF."""
        if not value or value.startswith("/"):
            return value

        # Get project root (souleyez/)
        project_root = Path(__file__).parent.parent

        # Check if relative path exists from project root
        abs_path = project_root / value
        if abs_path.exists():
            return str(abs_path.absolute())

        # Fallback: check MSF default wordlists
        msf_paths = [
            Path("/usr/share/metasploit-framework") / value,
            Path("/usr/share/metasploit-framework/data/wordlists") / Path(value).name,
        ]
        for msf_path in msf_paths:
            if msf_path.exists():
                return str(msf_path)

        # Return original if nothing found (will fail, but with better error)
        return value

    # SMB modules that need SMBDirect=false for SMB1 compatibility
    SMB_MODULES = [
        "smb_enumshares",
        "smb_enumusers",
        "smb_login",
        "smb_version",
        "smb_ms17_010",
        "smb_lookupsid",
    ]

    def _is_smb_module(self, module_path: str) -> bool:
        """Check if module is an SMB scanner that needs legacy support."""
        return any(smb_mod in module_path for smb_mod in self.SMB_MODULES)

    def build_command(
        self, target: str, args: List[str] = None, label: str = "", log_path: str = None
    ):
        """Build command for background execution with PID tracking."""
        args = args or []

        # First arg should be the module path
        if not args:
            return None

        module_path = args[0]
        extra_opts = args[1:] if len(args) > 1 else []

        # Check if user already specified SMBDirect
        has_smbdirect = any("SMBDIRECT" in opt.upper() for opt in extra_opts)

        # Build msfconsole command
        msf_commands = [
            f"use {module_path}",
            f"set RHOSTS {target}",
        ]

        # Add SMBDirect=false for SMB modules to support SMB1 legacy systems
        # (like Metasploitable2) unless user explicitly set it
        if self._is_smb_module(module_path) and not has_smbdirect:
            msf_commands.append("set SMBDirect false")

        # Add any extra options (e.g., "RPORT=445", "USERNAME=postgres PASSWORD=password")
        for opt in extra_opts:
            if "=" in opt:
                key, value = opt.split("=", 1)
                # Resolve relative file paths to absolute
                if key in self.FILE_PATH_KEYS:
                    value = self._resolve_path(value)
                msf_commands.append(f"set {key} {value}")
            else:
                msf_commands.append(opt)

        msf_commands.append("run")

        # For login modules, dump credentials after run
        # This captures any found credentials in the output
        # Use -a to filter by target host so we don't show all stored creds
        login_modules = [
            "_login",
            "_auth",
            "mysql_login",
            "ssh_login",
            "ftp_login",
            "smb_login",
            "vnc_login",
            "postgres_login",
            "telnet_login",
            "rdp_login",
            "http_login",
            "snmp_login",
        ]
        if any(lm in module_path.lower() for lm in login_modules):
            msf_commands.append(f"creds -a {target}")

        msf_commands.append("exit -y")  # Force exit even with active sessions

        command_string = "; ".join(msf_commands)

        # Note: Removed -n flag to enable database (required for creds command)
        cmd = ["msfconsole", "-q", "-x", command_string]

        return {"cmd": cmd, "timeout": 3600}

    def run(
        self, target: str, args: List[str] = None, label: str = "", log_path: str = None
    ) -> int:
        """Execute MSF auxiliary module non-interactively."""
        args = args or []

        # First arg should be the module path
        if not args:
            if log_path:
                with open(log_path, "w") as f:
                    f.write(
                        "ERROR: No module specified. Example: auxiliary/scanner/smb/smb_version\n"
                    )
            return 1

        module_path = args[0]

        # Additional module options (RPORT, etc.)
        extra_opts = args[1:] if len(args) > 1 else []

        if log_path:
            return self._run_with_logpath(module_path, target, extra_opts, log_path)

        return self._run_legacy(module_path, target, extra_opts)

    def _run_with_logpath(
        self, module_path: str, target: str, extra_opts: List[str], log_path: str
    ) -> int:
        """Run MSF module and write output to log_path."""
        try:
            # Check if user already specified SMBDirect
            has_smbdirect = any("SMBDIRECT" in opt.upper() for opt in extra_opts)

            # Build msfconsole command
            # Use -q (quiet), -x (execute commands), -n (no database)
            msf_commands = [
                f"use {module_path}",
                f"set RHOSTS {target}",
            ]

            # Add SMBDirect=false for SMB modules to support SMB1 legacy systems
            if self._is_smb_module(module_path) and not has_smbdirect:
                msf_commands.append("set SMBDirect false")

            # Add any extra options (e.g., "RPORT=445", "USERNAME=postgres PASSWORD=password")
            for opt in extra_opts:
                # Handle KEY=VALUE format - split and use "set KEY VALUE"
                if "=" in opt:
                    key, value = opt.split("=", 1)
                    # Resolve relative file paths to absolute
                    if key in self.FILE_PATH_KEYS:
                        value = self._resolve_path(value)
                    msf_commands.append(f"set {key} {value}")
                else:
                    # Plain option, just append as-is
                    msf_commands.append(opt)

            # Add run command
            msf_commands.append("run")

            # For login modules, dump credentials after run
            # This captures any found credentials in the output
            # Use -a to filter by target host so we don't show all stored creds
            login_modules = [
                "_login",
                "_auth",
                "mysql_login",
                "ssh_login",
                "ftp_login",
                "smb_login",
                "vnc_login",
                "postgres_login",
                "telnet_login",
                "rdp_login",
                "http_login",
                "snmp_login",
            ]
            if any(lm in module_path.lower() for lm in login_modules):
                msf_commands.append(f"creds -a {target}")

            msf_commands.append("exit -y")  # Force exit even with active sessions

            # Join commands with semicolons
            command_string = "; ".join(msf_commands)

            # Build full command
            # Note: Removed -n flag to enable database (required for creds command)
            cmd = [
                "msfconsole",
                "-q",  # Quiet mode (no banner)
                "-x",  # Execute commands
                command_string,
            ]

            with open(log_path, "w", encoding="utf-8", errors="replace") as fh:
                fh.write("=== Metasploit Auxiliary Module ===\n")
                fh.write(f"Module: {module_path}\n")
                fh.write(f"Target: {target}\n")
                fh.write(
                    f"Options: {', '.join(extra_opts) if extra_opts else 'None'}\n"
                )
                fh.write(
                    f"Started: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}\n\n"
                )
                fh.write(f"Command: {' '.join(cmd)}\n\n")
                fh.flush()

                # Run msfconsole
                proc = subprocess.run(
                    cmd,
                    stdout=fh,
                    stderr=subprocess.STDOUT,
                    timeout=3600,  # 1 hour - MSF modules can be slow
                    check=False,
                )

                fh.write(
                    f"\n\nCompleted: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}\n"
                )
                fh.write(f"Exit Code: {proc.returncode}\n")

                return proc.returncode

        except subprocess.TimeoutExpired:
            with open(log_path, "a", encoding="utf-8", errors="replace") as fh:
                fh.write("\nERROR: MSF module timed out after 3600 seconds\n")
            return 124

        except FileNotFoundError:
            with open(log_path, "a", encoding="utf-8", errors="replace") as fh:
                fh.write("\nERROR: msfconsole not found in PATH\n")
                fh.write("Please install Metasploit Framework\n")
            return 127

        except Exception as e:
            with open(log_path, "a", encoding="utf-8", errors="replace") as fh:
                fh.write(f"\nERROR: {type(e).__name__}: {e}\n")
            return 1

    def _run_legacy(self, module_path: str, target: str, extra_opts: List[str]):
        """Legacy execution without log_path."""
        msf_commands = [
            f"use {module_path}",
            f"set RHOSTS {target}",
        ]

        for opt in extra_opts:
            # Handle KEY=VALUE format
            if "=" in opt:
                key, value = opt.split("=", 1)
                # Resolve relative file paths to absolute
                if key in self.FILE_PATH_KEYS:
                    value = self._resolve_path(value)
                msf_commands.append(f"set {key} {value}")
            else:
                msf_commands.append(opt)

        msf_commands.append("run")

        # For login modules, dump credentials after run
        # Use -a to filter by target host so we don't show all stored creds
        login_modules = [
            "_login",
            "_auth",
            "mysql_login",
            "ssh_login",
            "ftp_login",
            "smb_login",
            "vnc_login",
            "postgres_login",
            "telnet_login",
            "rdp_login",
            "http_login",
            "snmp_login",
        ]
        if any(lm in module_path.lower() for lm in login_modules):
            msf_commands.append(f"creds -a {target}")

        msf_commands.append("exit -y")  # Force exit even with active sessions

        command_string = "; ".join(msf_commands)

        # Note: Removed -n flag to enable database (required for creds command)
        cmd = ["msfconsole", "-q", "-x", command_string]

        try:
            proc = subprocess.run(
                cmd, capture_output=True, timeout=3600, check=False
            )  # 1 hour
            return proc.returncode
        except Exception:
            return 1


plugin = MsfAuxiliaryPlugin()
