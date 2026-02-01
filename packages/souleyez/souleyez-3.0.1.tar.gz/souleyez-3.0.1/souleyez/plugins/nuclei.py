#!/usr/bin/env python3
"""
souleyez.plugins.nuclei - Modern vulnerability scanner with 5000+ templates
"""

import subprocess
import time
from typing import List

from souleyez.security.validation import ValidationError, validate_url

from .plugin_base import PluginBase

HELP = {
    "name": "Nuclei - Modern Vulnerability Scanner",
    "description": (
        "Want a modern, fast, and accurate web vulnerability scanner?\n\n"
        "Nuclei is the industry-standard vulnerability scanner with 5000+ community-maintained templates "
        "that are updated daily. It detects CVEs, exposures, misconfigurations, and default logins with "
        "high accuracy and low false positives.\n\n"
        "Nuclei uses YAML-based templates that are easy to customize,"
        "share, and update. Templates include severity ratings, CVE IDs, CVSS scores, and proof-of-concept "
        "exploits - making it perfect for both detection and verification.\n\n"
        "Quick tips:\n"
        "- Filter by severity (-severity critical,high) to focus on important findings\n"
        "- Use tags (-tags cve,exposure) to run specific template categories\n"
        "- Templates auto-update daily (nuclei -update-templates)\n"
        "- Results include CVE IDs that link to SearchSploit for exploit discovery\n"
        "- Fast and concurrent - use -rate-limit to avoid overwhelming targets\n"
    ),
    "usage": 'souleyez jobs enqueue nuclei <target> --args "-severity critical,high"',
    "examples": [
        'souleyez jobs enqueue nuclei http://example.com --args "-severity critical,high"',
        'souleyez jobs enqueue nuclei http://example.com --args "-tags cve,exposure"',
        'souleyez jobs enqueue nuclei http://example.com --args "-tags default-login"',
    ],
    "flags": [
        ["-severity <level>", "Filter by severity (critical,high,medium,low,info)"],
        ["-tags <tags>", "Filter by tags (cve,exposure,misconfiguration,etc)"],
        ["-timeout <seconds>", "Request timeout (default: 10)"],
        ["-rate-limit <num>", "Max requests per second"],
        ["-no-color", "Disable color output"],
    ],
    "preset_categories": {
        "by_severity": [
            {
                "name": "Critical Only",
                "args": ["-severity", "critical"],
                "desc": "Critical severity vulnerabilities only",
            },
            {
                "name": "High + Critical",
                "args": ["-severity", "critical,high"],
                "desc": "High and critical vulnerabilities (recommended)",
            },
            {
                "name": "Full Scan",
                "args": ["-severity", "critical,high,medium"],
                "desc": "Comprehensive scan (critical, high, medium)",
            },
        ],
        "by_category": [
            {
                "name": "CVE Detection",
                "args": ["-tags", "cve"],
                "desc": "Scan for known CVEs",
            },
            {
                "name": "Exposure Detection",
                "args": ["-tags", "exposure"],
                "desc": "Detect sensitive file exposures",
            },
            {
                "name": "Default Credentials",
                "args": ["-tags", "default-login"],
                "desc": "Check for default login panels",
            },
            {
                "name": "Misconfigurations",
                "args": ["-tags", "misconfiguration"],
                "desc": "Detect common misconfigurations",
            },
        ],
        "owasp_injection": [
            {
                "name": "XSS Scan",
                "args": ["-tags", "xss,rxss"],
                "desc": "Reflected/Stored XSS detection",
            },
            {
                "name": "SSTI Scan",
                "args": ["-tags", "ssti"],
                "desc": "Server-Side Template Injection",
            },
            {
                "name": "SSRF Scan",
                "args": ["-tags", "ssrf"],
                "desc": "Server-Side Request Forgery",
            },
            {
                "name": "Command Injection",
                "args": ["-tags", "rce,cmdi"],
                "desc": "Remote Code/Command Execution",
            },
            {
                "name": "LFI/RFI Scan",
                "args": ["-tags", "lfi,rfi"],
                "desc": "Local/Remote File Inclusion",
            },
            {
                "name": "Open Redirect",
                "args": ["-tags", "redirect"],
                "desc": "Open redirect vulnerabilities",
            },
            {
                "name": "Full OWASP",
                "args": ["-severity", "critical,high", "-tags", "owasp"],
                "desc": "All OWASP-tagged templates",
            },
        ],
    },
    "presets": [
        {
            "name": "Critical Only",
            "args": ["-severity", "critical"],
            "desc": "Critical severity vulnerabilities only",
        },
        {
            "name": "High + Critical",
            "args": ["-severity", "critical,high"],
            "desc": "High and critical vulnerabilities (recommended)",
        },
        {
            "name": "Full Scan",
            "args": ["-severity", "critical,high,medium"],
            "desc": "Comprehensive scan (critical, high, medium)",
        },
        {
            "name": "CVE Detection",
            "args": ["-tags", "cve"],
            "desc": "Scan for known CVEs",
        },
        {
            "name": "Exposure Detection",
            "args": ["-tags", "exposure"],
            "desc": "Detect sensitive file exposures",
        },
        {
            "name": "Default Credentials",
            "args": ["-tags", "default-login"],
            "desc": "Check for default login panels",
        },
        {
            "name": "Misconfigurations",
            "args": ["-tags", "misconfiguration"],
            "desc": "Detect common misconfigurations",
        },
        # OWASP Injection presets
        {
            "name": "XSS Scan",
            "args": ["-tags", "xss,rxss"],
            "desc": "Reflected/Stored XSS detection",
        },
        {
            "name": "SSTI Scan",
            "args": ["-tags", "ssti"],
            "desc": "Server-Side Template Injection",
        },
        {
            "name": "SSRF Scan",
            "args": ["-tags", "ssrf"],
            "desc": "Server-Side Request Forgery",
        },
        {
            "name": "Command Injection",
            "args": ["-tags", "rce,cmdi"],
            "desc": "Remote Code/Command Execution",
        },
        {
            "name": "LFI/RFI Scan",
            "args": ["-tags", "lfi,rfi"],
            "desc": "Local/Remote File Inclusion",
        },
        {
            "name": "Open Redirect",
            "args": ["-tags", "redirect"],
            "desc": "Open redirect vulnerabilities",
        },
        {
            "name": "Full OWASP",
            "args": ["-severity", "critical,high", "-tags", "owasp"],
            "desc": "All OWASP-tagged templates",
        },
    ],
    "help_sections": [
        {
            "title": "What is Nuclei?",
            "color": "cyan",
            "content": [
                {
                    "title": "Overview",
                    "desc": "Nuclei is the modern, industry-standard vulnerability scanner with 5000+ community-maintained templates updated daily, providing high accuracy and low false positives.",
                },
                {
                    "title": "Use Cases",
                    "desc": "Essential for web vulnerability detection",
                    "tips": [
                        "Detect CVEs with daily-updated templates",
                        "Find exposed sensitive files and configurations",
                        "Check for default credentials and logins",
                        "Identify misconfigurations and security issues",
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
                    "desc": "1. Update templates (nuclei -update-templates)\n     2. Filter by severity (-severity critical,high)\n     3. Use tags for specific categories (-tags cve,exposure)\n     4. Review findings and verify manually",
                },
                {
                    "title": "Key Features",
                    "desc": "Powerful template-based scanning",
                    "tips": [
                        "Severity filtering: -severity critical,high",
                        "Tag filtering: -tags cve,exposure,misconfiguration",
                        "Fast and concurrent with customizable rate limits",
                        "Results include CVE IDs and CVSS scores",
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
                        "Update templates regularly for latest CVEs",
                        "Start with critical/high severity only",
                        "Use -rate-limit to avoid overwhelming targets",
                        "Verify findings manually before reporting",
                        "Link CVE IDs to SearchSploit for exploits",
                    ],
                ),
                (
                    "Common Issues:",
                    [
                        "Too many results: Filter by severity or tags",
                        "Rate limiting: Add -rate-limit or reduce concurrency",
                        "False positives: Always verify critical findings",
                        "Outdated templates: Run -update-templates regularly",
                    ],
                ),
            ],
        },
    ],
}


class NucleiPlugin(PluginBase):
    name = "Nuclei"
    tool = "nuclei"
    category = "vulnerability_analysis"
    HELP = HELP

    def _check_templates_exist(self) -> bool:
        """Check if nuclei templates are installed."""
        import os
        from pathlib import Path

        # Check common template locations (nuclei v3 uses ~/.local/nuclei-templates)
        template_paths = [
            Path.home() / ".local" / "nuclei-templates",  # nuclei v3 default
            Path.home() / "nuclei-templates",
            Path.home() / ".nuclei-templates",
            Path("/usr/share/nuclei-templates"),
        ]

        for path in template_paths:
            if path.exists() and any(path.glob("**/*.yaml")):
                return True
        return False

    def _normalize_target(
        self, target: str, args: List[str] = None, log_path: str = None
    ) -> str:
        """
        Normalize target for Nuclei scanning.

        - URLs are validated and passed through
        - Bare IPs/domains get http:// prepended for web scanning

        This fixes the issue where nmap chains pass bare IPs but Nuclei
        needs URLs to properly scan web services.
        """
        import re

        # Already a URL - validate and return
        if target.startswith(("http://", "https://")):
            try:
                return validate_url(target)
            except ValidationError as e:
                if log_path:
                    with open(log_path, "w") as f:
                        f.write(f"ERROR: Invalid URL: {e}\n")
                return None

        # Bare IP or domain - prepend http:// for web scanning
        # This is needed because Nuclei web templates require a URL
        ip_pattern = r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(:\d+)?$"
        domain_pattern = r"^[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?)*$"

        if re.match(ip_pattern, target) or re.match(domain_pattern, target):
            # Log the conversion
            if log_path:
                with open(log_path, "a") as f:
                    f.write(
                        f"NOTE: Converting bare target '{target}' to 'http://{target}' for web scanning\n"
                    )
            return f"http://{target}"

        # Unknown format - return as-is
        return target

    def build_command(
        self, target: str, args: List[str] = None, label: str = "", log_path: str = None
    ):
        """Build nuclei command for background execution with PID tracking."""
        args = args or []

        # Normalize target (convert bare IPs to URLs)
        target = self._normalize_target(target, args, log_path)
        if target is None:
            return None
        args = [arg.replace("<target>", target) for arg in args]

        cmd = ["nuclei", "-target", target]

        # Check if templates exist - if not, add -update-templates flag
        if not self._check_templates_exist():
            if log_path:
                with open(log_path, "a") as f:
                    f.write(
                        "NOTE: Nuclei templates not found. Will attempt to download...\n\n"
                    )
            cmd.append("-update-templates")

        if "-json" not in args and "-jsonl" not in args:
            cmd.extend(["-jsonl"])

        if log_path and "-o" not in args:
            cmd.extend(["-o", log_path])

        cmd.extend(args)

        if "-severity" not in args and "-tags" not in args:
            cmd.extend(["-severity", "critical,high,medium"])

        if "-timeout" not in args:
            cmd.extend(["-timeout", "10"])

        return {"cmd": cmd, "timeout": 3600}  # 1 hour

    def run(
        self, target: str, args: List[str] = None, label: str = "", log_path: str = None
    ) -> int:
        """Execute nuclei scan and write JSON output to log_path."""
        args = args or []

        # Normalize target (convert bare IPs to URLs)
        target = self._normalize_target(target, args, log_path)
        if target is None:
            return 1

        # Replace <target> placeholder
        args = [arg.replace("<target>", target) for arg in args]

        # Build nuclei command
        cmd = ["nuclei", "-target", target]

        # Check if templates exist - if not, add -update-templates flag
        if not self._check_templates_exist():
            if log_path:
                with open(log_path, "a") as f:
                    f.write(
                        "NOTE: Nuclei templates not found. Will attempt to download...\n\n"
                    )
            cmd.append("-update-templates")

        # Force JSON output for parsing
        if "-json" not in args and "-jsonl" not in args:
            cmd.extend(["-jsonl"])

        # Add log output
        if log_path and "-o" not in args:
            cmd.extend(["-o", log_path])

        # Add user args
        cmd.extend(args)

        # Set defaults if not specified
        if "-severity" not in args and "-tags" not in args:
            cmd.extend(["-severity", "critical,high,medium"])

        if "-timeout" not in args:
            cmd.extend(["-timeout", "10"])

        if not log_path:
            try:
                proc = subprocess.run(
                    cmd, capture_output=True, timeout=3600, check=False
                )
                return proc.returncode
            except Exception:
                return 1

        try:
            # Create metadata header
            with open(log_path, "w", encoding="utf-8", errors="replace") as fh:
                fh.write(f"# Nuclei Scan\n")
                fh.write(f"# Command: {' '.join(cmd)}\n")
                fh.write(
                    f"# Started: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}\n"
                )
                fh.write(f"# Target: {target}\n\n")

            # Run nuclei (it will append JSONL to the file)
            proc = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=3600,  # 1 hour timeout
                check=False,
                text=True,
            )

            # Append completion metadata
            with open(log_path, "a", encoding="utf-8", errors="replace") as fh:
                fh.write(
                    f"\n\n# Completed: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}\n"
                )
                fh.write(f"# Exit Code: {proc.returncode}\n")

                # Also capture stderr for errors
                if proc.stdout:
                    fh.write(f"\n# Output:\n{proc.stdout}\n")

            return proc.returncode

        except subprocess.TimeoutExpired:
            with open(log_path, "a", encoding="utf-8", errors="replace") as fh:
                fh.write("\n\nERROR: Nuclei timed out after 3600 seconds\n")
            return 124

        except FileNotFoundError:
            with open(log_path, "a", encoding="utf-8", errors="replace") as fh:
                fh.write("\n\nERROR: nuclei not found in PATH\n")
                fh.write("Install: https://github.com/projectdiscovery/nuclei\n")
            return 127

        except Exception as e:
            with open(log_path, "a", encoding="utf-8", errors="replace") as fh:
                fh.write(f"\n\nERROR: {type(e).__name__}: {e}\n")
            return 1


plugin = NucleiPlugin()
