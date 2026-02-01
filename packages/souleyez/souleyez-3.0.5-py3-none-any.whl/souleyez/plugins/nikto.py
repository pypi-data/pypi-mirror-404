#!/usr/bin/env python3
"""
souleyez.plugins.nikto - Web server vulnerability scanner
"""

from __future__ import annotations

import re
import subprocess
import time
from typing import List

from souleyez.security.validation import ValidationError, validate_url

from .plugin_base import PluginBase

HELP = {
    "name": "Nikto - Web Server Vulnerability Scanner",
    "description": (
        "Nikto is a comprehensive web server scanner that checks for dangerous files, "
        "outdated software, version-specific problems, and server configuration issues.\n\n"
        "Unlike Nuclei which focuses on CVEs and templates, Nikto performs deep server-level "
        "checks including:\n"
        "- Outdated server software and frameworks\n"
        "- Dangerous files and CGI scripts\n"
        "- Server misconfigurations\n"
        "- Default files and directories\n"
        "- SSL/TLS issues\n\n"
        "Nikto is noisy by design - it sends many requests to thoroughly test the server. "
        "Use with caution on production systems.\n"
    ),
    "usage": 'souleyez jobs enqueue nikto <target> --args "-h <host> -p <port>"',
    "examples": [
        'souleyez jobs enqueue nikto http://example.com --args "-h example.com"',
        'souleyez jobs enqueue nikto https://example.com --args "-h example.com -ssl"',
        'souleyez jobs enqueue nikto http://example.com:8080 --args "-h example.com -p 8080"',
    ],
    "flags": [
        ["-h <host>", "Target host (required)"],
        ["-p <port>", "Target port (default: 80)"],
        ["-ssl", "Use SSL/HTTPS"],
        ["-Tuning <x>", "Scan tuning (1-9, a-c)"],
        ["-timeout <sec>", "Timeout per request"],
        ["-Pause <sec>", "Pause between requests"],
        ["-no404", "Disable 404 guessing"],
        ["-nointeractive", "Disable interactive features"],
    ],
    "preset_categories": {
        "quick_scans": [
            {
                "name": "Quick Scan",
                "args": ["-h", "<target>", "-nointeractive", "-timeout", "10"],
                "desc": "Fast scan with default checks",
            },
            {
                "name": "Quick Scan (SSL)",
                "args": ["-h", "<target>", "-ssl", "-nointeractive", "-timeout", "10"],
                "desc": "Fast scan for HTTPS sites",
            },
        ],
        "comprehensive": [
            {
                "name": "Full Scan",
                "args": ["-h", "<target>", "-nointeractive", "-Tuning", "123456789abc"],
                "desc": "All scan types enabled",
            },
            {
                "name": "CGI Focus",
                "args": ["-h", "<target>", "-nointeractive", "-Tuning", "5"],
                "desc": "Focus on CGI/script vulnerabilities",
            },
        ],
        "stealth": [
            {
                "name": "Slow & Quiet",
                "args": [
                    "-h",
                    "<target>",
                    "-nointeractive",
                    "-Pause",
                    "3",
                    "-timeout",
                    "15",
                ],
                "desc": "Slower scan to avoid detection",
            }
        ],
    },
    "presets": [
        {
            "name": "Quick Scan",
            "args": ["-h", "<target>", "-nointeractive", "-timeout", "10"],
            "desc": "Fast scan with default checks",
        },
        {
            "name": "Quick Scan (SSL)",
            "args": ["-h", "<target>", "-ssl", "-nointeractive", "-timeout", "10"],
            "desc": "Fast scan for HTTPS sites",
        },
        {
            "name": "Full Scan",
            "args": ["-h", "<target>", "-nointeractive", "-Tuning", "123456789abc"],
            "desc": "All scan types enabled",
        },
        {
            "name": "CGI Focus",
            "args": ["-h", "<target>", "-nointeractive", "-Tuning", "5"],
            "desc": "Focus on CGI/script vulnerabilities",
        },
        {
            "name": "Slow & Quiet",
            "args": [
                "-h",
                "<target>",
                "-nointeractive",
                "-Pause",
                "3",
                "-timeout",
                "15",
            ],
            "desc": "Slower scan to avoid detection",
        },
    ],
    "help_sections": [
        {
            "title": "What is Nikto?",
            "color": "cyan",
            "content": [
                {
                    "title": "Overview",
                    "desc": "Nikto is a web server scanner that performs comprehensive tests against web servers for multiple items including dangerous files, outdated versions, and configuration problems.",
                },
                {
                    "title": "Use Cases",
                    "desc": "Best for initial web server assessment",
                    "tips": [
                        "Find outdated server software",
                        "Detect dangerous default files",
                        "Identify server misconfigurations",
                        "Check for known vulnerable CGI scripts",
                    ],
                },
            ],
        },
        {
            "title": "Tuning Options",
            "color": "green",
            "content": [
                {
                    "title": "Tuning Codes",
                    "desc": "Use -Tuning to focus scans:",
                    "tips": [
                        "1 - Interesting File / Seen in logs",
                        "2 - Misconfiguration / Default File",
                        "3 - Information Disclosure",
                        "4 - Injection (XSS/Script/HTML)",
                        "5 - Remote File Retrieval - Inside Web Root",
                        "6 - Denial of Service",
                        "7 - Remote File Retrieval - Server Wide",
                        "8 - Command Execution / Remote Shell",
                        "9 - SQL Injection",
                        "a - Authentication Bypass",
                        "b - Software Identification",
                        "c - Remote Source Inclusion",
                    ],
                }
            ],
        },
    ],
}


class NiktoPlugin(PluginBase):
    name = "Nikto"
    tool = "nikto"
    category = "vulnerability_analysis"
    HELP = HELP

    def build_command(
        self, target: str, args: List[str] = None, label: str = "", log_path: str = None
    ):
        """Build nikto command for background execution."""
        args = args or []

        # Extract host from target URL if not in args
        if "-h" not in args:
            # Parse target to get host
            if target.startswith(("http://", "https://")):
                from urllib.parse import urlparse

                parsed = urlparse(target)
                host = parsed.netloc
                if ":" in host:
                    host, port = host.rsplit(":", 1)
                    if "-p" not in args:
                        args.extend(["-p", port])
                args.extend(["-h", host])

                # Add -ssl if https
                if parsed.scheme == "https" and "-ssl" not in args:
                    args.append("-ssl")
            else:
                args.extend(["-h", target])

        # Replace <target> placeholder in args
        processed_args = [arg.replace("<target>", target) for arg in args]

        # Ensure nointeractive mode for background execution
        if "-nointeractive" not in processed_args:
            processed_args.append("-nointeractive")

        cmd = ["nikto"] + processed_args

        return {"cmd": cmd, "timeout": 3600}  # 1 hour (nikto can be slow)

    def run(
        self, target: str, args: List[str] = None, label: str = "", log_path: str = None
    ) -> int:
        """Execute nikto scan and write output to log_path."""
        args = args or []

        # Extract host from target URL if not in args
        if "-h" not in args:
            if target.startswith(("http://", "https://")):
                from urllib.parse import urlparse

                parsed = urlparse(target)
                host = parsed.netloc
                if ":" in host:
                    host, port = host.rsplit(":", 1)
                    if "-p" not in args:
                        args.extend(["-p", port])
                args.extend(["-h", host])

                if parsed.scheme == "https" and "-ssl" not in args:
                    args.append("-ssl")
            else:
                args.extend(["-h", target])

        processed_args = [arg.replace("<target>", target) for arg in args]

        if "-nointeractive" not in processed_args:
            processed_args.append("-nointeractive")

        cmd = ["nikto"] + processed_args

        if not log_path:
            try:
                proc = subprocess.run(
                    cmd, capture_output=True, timeout=3600, check=False
                )
                return proc.returncode
            except Exception:
                return 1

        try:
            with open(log_path, "a", encoding="utf-8", errors="replace") as fh:
                fh.write(f"=== Plugin: Nikto ===\n")
                fh.write(f"Target: {target}\n")
                fh.write(f"Args: {processed_args}\n")
                if label:
                    fh.write(f"Label: {label}\n")
                fh.write(
                    f"Started: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}\n"
                )
                fh.write(f"Command: {' '.join(cmd)}\n")
                fh.write("=" * 60 + "\n\n")
                fh.flush()

                proc = subprocess.run(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    timeout=3600,
                    check=False,
                    text=True,
                )

                fh.write(proc.stdout)
                fh.write(
                    f"\n=== Completed: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())} ===\n"
                )
                fh.write(f"Exit Code: {proc.returncode}\n")

                return proc.returncode

        except subprocess.TimeoutExpired:
            with open(log_path, "a", encoding="utf-8", errors="replace") as fh:
                fh.write("\nERROR: Nikto timed out after 1 hour\n")
            return 124

        except FileNotFoundError:
            with open(log_path, "a", encoding="utf-8", errors="replace") as fh:
                fh.write("\nERROR: nikto not found in PATH\n")
                fh.write("Install with: sudo apt install nikto\n")
            return 127

        except Exception as e:
            with open(log_path, "a", encoding="utf-8", errors="replace") as fh:
                fh.write(f"\nERROR: {type(e).__name__}: {e}\n")
            return 1


plugin = NiktoPlugin()
