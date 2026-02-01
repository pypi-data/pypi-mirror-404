#!/usr/bin/env python3
"""
Bloodhound plugin - Active Directory attack path mapping.
"""

import json
import subprocess
from datetime import datetime
from pathlib import Path

HELP = {
    "name": "Bloodhound - Active Directory Attack Path Mapping",
    "description": (
        "Need to find the path from user to Domain Admin?\n\n"
        "Bloodhound uses graph theory to analyze Active Directory relationships and identify "
        "complex attack paths that would be impossible to find manually. It shows you the "
        "shortest path from your compromised account to domain admin privileges.\n\n"
        "Use Bloodhound after getting domain credentials to:\n"
        "- Map all AD users, groups, computers, and GPOs\n"
        "- Identify path to Domain Admin (user → group → computer → DA)\n"
        "- Find Kerberoastable users (SPN accounts)\n"
        "- Discover high-value targets (admins, DAs, servers)\n"
        "- Identify misconfigurations (unconstrained delegation, etc.)\n\n"
        "Quick tips:\n"
        "- Requires valid domain credentials (any user account)\n"
        "- Data collection takes 5-15 minutes for typical domains\n"
        "- Use 'Full Enumeration' for complete picture\n"
        "- Use 'DCOnly' for quick initial recon\n"
        "- Import ZIP files into Bloodhound GUI for visualization\n"
        "- Pre-built queries: 'Shortest path to Domain Admins'\n\n"
        "💡 Pro tip: Run from Linux with bloodhound-python (no need to touch DC directly)\n"
    ),
    "usage": 'souleyez jobs enqueue bloodhound <dc_ip> --args "-u user -p pass -d domain.com"',
    "examples": [
        'souleyez jobs enqueue bloodhound 10.0.0.82 --args "-u jdoe -p Password123! -d CONTOSO.LOCAL"',
        'souleyez jobs enqueue bloodhound 10.0.0.82 --args "-u admin -p pass -d CORP.COM -c All"',
        'souleyez jobs enqueue bloodhound 10.0.0.82 --args "-u user@domain.com -p pass -d domain.com -c DCOnly"',
    ],
    "presets": [
        {
            "name": "Full Enumeration",
            "desc": "Complete AD collection - all data (recommended)",
            "args": ["-c", "All", "--zip"],
        },
        {
            "name": "DCOnly (Fast)",
            "desc": "DC data only - fast, low footprint",
            "args": ["-c", "DCOnly", "--zip"],
        },
        {
            "name": "Users & Groups",
            "desc": "User/group memberships and local admins",
            "args": ["-c", "Group,LocalAdmin", "--zip"],
        },
        {
            "name": "Sessions Only",
            "desc": "Active sessions and logged-in users",
            "args": ["-c", "Session", "--zip"],
        },
        {
            "name": "Trust Relationships",
            "desc": "Domain trusts enumeration",
            "args": ["-c", "Trusts", "--zip"],
        },
    ],
    "flags": [
        ["-u <username>", "Domain username (required)"],
        ["-p <password>", "Domain password (required)"],
        ["-d <domain>", "Domain name (e.g., CONTOSO.LOCAL) (required)"],
        ["-ns <dc_ip>", "Domain Controller IP (nameserver)"],
        [
            "-c <collection>",
            "Collection method: All, DCOnly, Group, LocalAdmin, Session, Trusts",
        ],
        ["--zip", "Compress output to ZIP file (recommended)"],
    ],
    "presets_explained": {
        "Full Enumeration": "Complete AD data collection - all users, groups, computers, sessions, GPOs (slowest, most data)",
        "Users & Groups Only": "Quick enumeration - user/group memberships, local admins, sessions (faster, good for initial recon)",
        "DCOnly": "Domain Controller data only - fastest, minimal footprint, misses workstation relationships",
    },
    "notes": [
        "Requires bloodhound-python installed: pip3 install bloodhound",
        "Output saved to ~/.souleyez/bloodhound_data/",
        "Collection takes 5-15 minutes depending on domain size",
        "Import ZIP files into Bloodhound GUI for analysis",
        "Start Bloodhound GUI: bloodhound",
        "Default Neo4j credentials: neo4j / neo4j (change on first login)",
        "Pre-built queries available in GUI: 'Shortest path to Domain Admins'",
    ],
    "help_sections": [
        {
            "title": "What is Bloodhound?",
            "color": "cyan",
            "content": [
                {
                    "title": "Overview",
                    "desc": "Bloodhound uses graph theory to analyze Active Directory relationships and identify complex attack paths that would be impossible to find manually.",
                },
                {
                    "title": "Use Cases",
                    "desc": "Find the path from user to Domain Admin",
                    "tips": [
                        "Map all AD users, groups, computers, and GPOs",
                        "Identify shortest path to Domain Admin",
                        "Find Kerberoastable users (SPN accounts)",
                        "Discover high-value targets and misconfigurations",
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
                    "desc": "1. Collect AD data with valid credentials\n     2. Import ZIP files into Bloodhound GUI\n     3. Run pre-built queries for attack paths\n     4. Identify and document exploitation path",
                },
                {
                    "title": "Collection Methods",
                    "desc": "Different levels of data collection",
                    "tips": [
                        "All: Complete AD collection (recommended)",
                        "DCOnly: Fast, minimal footprint",
                        "Group,LocalAdmin: User/group memberships only",
                        "Session: Active sessions and logged-in users",
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
                        "Requires valid domain credentials (any user)",
                        "Data collection takes 5-15 minutes",
                        "Use 'Full Enumeration' for complete picture",
                        "Import ZIP into Bloodhound GUI for visualization",
                        "Pre-built queries: 'Shortest path to Domain Admins'",
                    ],
                ),
                (
                    "Common Issues:",
                    [
                        "No data collected: Verify credentials and DC connectivity",
                        "Timeout: Domain may be large, increase timeout",
                        "Permission denied: Check domain user credentials",
                        "Neo4j errors: Ensure Bloodhound database is running",
                    ],
                ),
            ],
        },
    ],
}


class BloodhoundPlugin:
    """Bloodhound AD enumeration and attack path mapping."""

    name = "bloodhound"
    category = "discovery_collection"
    description = "Active Directory enumeration and attack path visualization"
    requires_credentials = True
    HELP = HELP

    def __init__(self):
        self.output_dir = Path.home() / ".souleyez" / "bloodhound_data"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def run(self, target, args, label, log_path):
        """
        Run bloodhound-python collector.

        Args:
            target: Domain controller IP or domain name
            args: Format: "-u username -p password -d domain.com"
            label: Job label
            log_path: Path to job log

        Returns:
            0 on success, non-zero on error
        """
        result = subprocess.run(["which", "bloodhound-python"], capture_output=True)
        if result.returncode != 0:
            with open(log_path, "w") as f:
                f.write("ERROR: bloodhound-python not found. Install with:\n")
                f.write("pip3 install bloodhound\n")
            return 1

        # Handle both string and list args
        if isinstance(args, list):
            arg_list = args
        elif isinstance(args, str):
            arg_list = args.split() if args else []
        else:
            arg_list = []

        username, password, domain = self._parse_creds(arg_list)

        if not all([username, password, domain]):
            with open(log_path, "w") as f:
                f.write("ERROR: Missing required arguments\n")
                f.write("Usage: -u username -p password -d domain.com\n")
            return 1

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = self.output_dir / f"{domain}_{timestamp}"
        output_path.mkdir(parents=True, exist_ok=True)

        cmd = [
            "bloodhound-python",
            "-u",
            username,
            "-p",
            password,
            "-d",
            domain,
            "-ns",
            target,
            "-c",
            "All",
            "--zip",
        ]

        with open(log_path, "w") as f:
            f.write(f"Running Bloodhound collector...\n")
            f.write(f"Domain: {domain}\n")
            f.write(f"DC: {target}\n")
            f.write(f"Username: {username}\n")
            f.write(f"Output: {output_path}\n\n")

        try:
            result = subprocess.run(
                cmd,
                cwd=str(output_path),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=600,
            )

            with open(log_path, "a") as f:
                f.write(result.stdout)

                if result.returncode == 0:
                    f.write(f"\n\nData collection complete!\n")
                    f.write(f"Output saved to: {output_path}\n")
                    f.write(f"\nNext steps:\n")
                    f.write(f"1. Start Bloodhound GUI: bloodhound\n")
                    f.write(f"2. Import zip files from: {output_path}\n")
                    f.write(f"3. Run queries to find attack paths\n")

            return result.returncode

        except subprocess.TimeoutExpired:
            with open(log_path, "a") as f:
                f.write("\n\nERROR: Bloodhound collector timeout (10 minutes)\n")
            return 1

    def _parse_creds(self, args):
        """Parse username, password, domain from args."""
        username = password = domain = None

        for i, arg in enumerate(args):
            if arg == "-u" and i + 1 < len(args):
                username = args[i + 1]
            elif arg == "-p" and i + 1 < len(args):
                password = args[i + 1]
            elif arg == "-d" and i + 1 < len(args):
                domain = args[i + 1]

        return username, password, domain

    def get_presets(self):
        """Return Bloodhound presets."""
        return {
            "Full Enumeration": {
                "description": "Collect all AD data (users, groups, computers, GPOs)",
                "args": "-c All",
            },
            "Users & Groups Only": {
                "description": "Quick enumeration (users and group memberships)",
                "args": "-c Group,LocalAdmin,Session",
            },
            "DCOnly": {
                "description": "Domain Controller data only (fastest)",
                "args": "-c DCOnly",
            },
        }


plugin = BloodhoundPlugin()
