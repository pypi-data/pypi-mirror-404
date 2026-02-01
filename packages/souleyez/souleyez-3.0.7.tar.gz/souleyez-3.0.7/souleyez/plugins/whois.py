#!/usr/bin/env python3
"""
souleyez.plugins.whois

WHOIS domain information lookup plugin.
"""

import subprocess
import time
from typing import List

from souleyez.security.validation import ValidationError, validate_target

from .plugin_base import PluginBase

HELP = {
    "name": "WHOIS — Domain Registration Information",
    "description": (
        "Need to know who owns a domain and when it expires?\n\n"
        "WHOIS queries domain registration databases to retrieve registrant information, "
        "registrar details, creation/expiration dates, nameservers, and technical contacts.\n\n"
        "It's essential for reconnaissance to understand domain ownership, identify related domains, "
        "and gather contact information that may be useful for social engineering assessments.\n\n"
        "Quick tips:\n"
        "- Provides domain owner, registrar, and registration dates\n"
        "- Shows nameservers and DNS configuration\n"
        "- Useful for identifying company infrastructure\n"
        "- Some domains have privacy protection hiding owner details\n"
        "- Can reveal email addresses and phone numbers of domain contacts\n"
    ),
    "usage": "souleyez jobs enqueue whois <domain>",
    "examples": [
        "souleyez jobs enqueue whois example.com",
        "souleyez jobs enqueue whois google.com",
        "souleyez jobs enqueue whois microsoft.com",
    ],
    "flags": [
        ["-h <host>", "Query specific WHOIS server"],
        ["-p <port>", "Connect to specific port (default: 43)"],
    ],
    "presets": [
        {
            "name": "Standard Lookup",
            "args": [],
            "desc": "Basic WHOIS query for domain information",
        },
    ],
    "help_sections": [
        {
            "title": "What is WHOIS?",
            "color": "cyan",
            "content": [
                {
                    "title": "Overview",
                    "desc": "WHOIS queries domain registration databases to retrieve registrant information, registrar details, creation/expiration dates, nameservers, and technical contacts.",
                },
                {
                    "title": "Use Cases",
                    "desc": "Essential for reconnaissance to understand domain ownership and gather contact information.",
                    "tips": [
                        "Identify domain owner and organization",
                        "Find registration and expiration dates",
                        "Discover nameservers and DNS configuration",
                        "Gather email addresses and phone numbers for social engineering",
                        "Identify related domains by registrant",
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
                    "desc": "1. Enter target domain name\n     2. Review registration information\n     3. Note nameservers for DNS enumeration\n     4. Save contact information for later use",
                },
                {
                    "title": "What to Look For",
                    "desc": "Key information in WHOIS results",
                    "tips": [
                        "Registrant name and organization",
                        "Creation/expiration dates (helps identify abandoned domains)",
                        "Nameserver configuration",
                        "Technical/admin contact emails",
                        "Registrar information",
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
                        "Query early in reconnaissance phase",
                        "Cross-reference with theHarvester results",
                        "Note privacy-protected domains (limited info)",
                        "Check related TLDs (.com, .net, .org, etc.)",
                        "Document contact information for reporting",
                    ],
                ),
                (
                    "Common Issues:",
                    [
                        "Privacy protection: Many domains hide owner details",
                        "Rate limiting: WHOIS servers may throttle queries",
                        "Different formats: Each TLD registry has different output format",
                    ],
                ),
            ],
        },
    ],
}


class WhoisPlugin(PluginBase):
    name = "WHOIS"
    tool = "whois"
    category = "reconnaissance"
    HELP = HELP

    def build_command(
        self, target: str, args: List[str] = None, label: str = "", log_path: str = None
    ):
        """Build command for background execution with PID tracking."""
        if not target:
            if log_path:
                with open(log_path, "w") as f:
                    f.write("ERROR: Target domain is required\n")
            return None

        # Validate target
        try:
            target = validate_target(target)
        except ValidationError as e:
            if log_path:
                with open(log_path, "w") as f:
                    f.write(f"ERROR: Invalid target: {e}\n")
            return None

        args = args or []

        # whois syntax: whois target [args]
        cmd = ["whois", target] + args

        return {"cmd": cmd, "timeout": 300}

    def run(
        self, target: str, args: List[str] = None, label: str = "", log_path: str = None
    ) -> int:
        """
        Execute WHOIS lookup and write output to log_path.
        """
        if not target:
            raise ValueError("Target domain is required")

        # Validate target (domain or IP)
        try:
            target = validate_target(target)
        except ValidationError as e:
            if log_path:
                with open(log_path, "w") as f:
                    f.write(f"ERROR: Invalid target: {e}\n")
                return 1
            raise ValueError(f"Invalid target: {e}")

        if args is None:
            args = []

        cmd = ["whois", target] + args

        if log_path:
            with open(log_path, "w") as f:
                f.write(f"# WHOIS Lookup for {target}\n")
                f.write(f"# Command: {' '.join(cmd)}\n")
                f.write(f"# Started: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

            if log_path:
                with open(log_path, "a") as f:
                    f.write(result.stdout)
                    if result.stderr:
                        f.write(f"\n\n# Errors:\n{result.stderr}\n")

            return result.returncode

        except subprocess.TimeoutExpired:
            if log_path:
                with open(log_path, "a") as f:
                    f.write("\n\n# ERROR: Command timed out after 60 seconds\n")
            return 124
        except Exception as e:
            if log_path:
                with open(log_path, "a") as f:
                    f.write(f"\n\n# ERROR: {str(e)}\n")
            return 1


# Export plugin instance
plugin = WhoisPlugin()
