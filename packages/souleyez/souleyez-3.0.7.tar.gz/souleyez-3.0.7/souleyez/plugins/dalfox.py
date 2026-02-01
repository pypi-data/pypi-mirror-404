#!/usr/bin/env python3
"""
souleyez.plugins.dalfox - XSS vulnerability scanner
"""

from __future__ import annotations

import json
import subprocess
import time
from typing import List

from souleyez.security.validation import ValidationError, validate_url

from .plugin_base import PluginBase

HELP = {
    "name": "Dalfox - XSS Vulnerability Scanner",
    "description": (
        "Dalfox is a powerful XSS (Cross-Site Scripting) vulnerability scanner and "
        "parameter analysis tool written in Go.\n\n"
        "Unlike generic scanners, Dalfox specializes in finding XSS vulnerabilities by:\n"
        "- Analyzing parameters for reflection points\n"
        "- Testing with optimized XSS payloads\n"
        "- Detecting DOM-based XSS\n"
        "- Finding blind XSS opportunities\n"
        "- Bypassing WAF/filters\n\n"
        "Dalfox works best when given URLs with parameters to test. Chain it after "
        "directory discovery (Gobuster/ffuf) to test discovered endpoints.\n"
    ),
    "usage": 'souleyez jobs enqueue dalfox <url> --args "url <target>"',
    "examples": [
        "souleyez jobs enqueue dalfox 'http://example.com/search?q=test' --args \"url 'http://example.com/search?q=test'\"",
        'souleyez jobs enqueue dalfox http://example.com --args "url http://example.com/page?id=1 --deep-domxss"',
        'souleyez jobs enqueue dalfox http://example.com --args "url http://example.com/form?name=test --waf-evasion"',
    ],
    "flags": [
        ["url <url>", "Target URL with parameters (required)"],
        ["--deep-domxss", "Enable deep DOM XSS analysis"],
        ["--waf-evasion", "Enable WAF bypass techniques"],
        ["--blind <callback>", "Blind XSS callback URL"],
        ["--delay <ms>", "Delay between requests (milliseconds)"],
        ["--timeout <sec>", "Request timeout"],
        ["--skip-bav", "Skip BAV (Basic Another Vulnerability) analysis"],
        ["--only-discovery", "Only discover parameters, don't attack"],
        ["--format json", "Output format (json recommended)"],
    ],
    "preset_categories": {
        "quick_scans": [
            {
                "name": "Quick XSS Scan",
                "args": ["url", "<target>", "--format", "json", "--skip-bav"],
                "desc": "Fast XSS scan on target URL",
            },
            {
                "name": "Parameter Discovery",
                "args": ["url", "<target>", "--only-discovery", "--format", "json"],
                "desc": "Find parameters without attacking",
            },
        ],
        "comprehensive": [
            {
                "name": "Deep Scan",
                "args": ["url", "<target>", "--deep-domxss", "--format", "json"],
                "desc": "Include DOM XSS analysis",
            },
            {
                "name": "WAF Bypass",
                "args": ["url", "<target>", "--waf-evasion", "--format", "json"],
                "desc": "Use WAF evasion techniques",
            },
            {
                "name": "Full Scan",
                "args": [
                    "url",
                    "<target>",
                    "--deep-domxss",
                    "--waf-evasion",
                    "--format",
                    "json",
                ],
                "desc": "All techniques enabled",
            },
        ],
        "stealth": [
            {
                "name": "Slow Scan",
                "args": ["url", "<target>", "--delay", "1000", "--format", "json"],
                "desc": "1 second delay between requests",
            }
        ],
    },
    "presets": [
        {
            "name": "Quick XSS Scan",
            "args": ["url", "<target>", "--format", "json", "--skip-bav"],
            "desc": "Fast XSS scan on target URL",
        },
        {
            "name": "Parameter Discovery",
            "args": ["url", "<target>", "--only-discovery", "--format", "json"],
            "desc": "Find parameters without attacking",
        },
        {
            "name": "Deep Scan",
            "args": ["url", "<target>", "--deep-domxss", "--format", "json"],
            "desc": "Include DOM XSS analysis",
        },
        {
            "name": "WAF Bypass",
            "args": ["url", "<target>", "--waf-evasion", "--format", "json"],
            "desc": "Use WAF evasion techniques",
        },
        {
            "name": "Full Scan",
            "args": [
                "url",
                "<target>",
                "--deep-domxss",
                "--waf-evasion",
                "--format",
                "json",
            ],
            "desc": "All techniques enabled",
        },
        {
            "name": "Slow Scan",
            "args": ["url", "<target>", "--delay", "1000", "--format", "json"],
            "desc": "1 second delay between requests",
        },
    ],
    "help_sections": [
        {
            "title": "What is Dalfox?",
            "color": "cyan",
            "content": [
                {
                    "title": "Overview",
                    "desc": "Dalfox (XSS Finder) is a fast, powerful parameter analysis and XSS scanner written in Go. It's designed specifically for finding XSS vulnerabilities.",
                },
                {
                    "title": "Use Cases",
                    "desc": "Perfect for testing web applications",
                    "tips": [
                        "Test form inputs for XSS",
                        "Analyze URL parameters",
                        "Find DOM-based XSS",
                        "Bypass WAF protections",
                        "Detect blind XSS opportunities",
                    ],
                },
            ],
        },
        {
            "title": "Best Practices",
            "color": "green",
            "content": [
                {
                    "title": "Workflow",
                    "desc": "1. Run Gobuster/ffuf to find endpoints\n2. Identify URLs with parameters\n3. Run Dalfox on each parameterized URL\n4. Review findings for exploitability",
                },
                {
                    "title": "Tips",
                    "desc": "Maximize XSS detection",
                    "tips": [
                        "Use --deep-domxss for JavaScript-heavy apps",
                        "Enable --waf-evasion for protected sites",
                        "Check --blind for delayed XSS detection",
                        "Use --delay to avoid rate limiting",
                    ],
                },
            ],
        },
    ],
}


class DalfoxPlugin(PluginBase):
    name = "Dalfox"
    tool = "dalfox"
    category = "vulnerability_analysis"
    HELP = HELP

    def _ensure_url_scheme(self, target: str) -> str:
        """Ensure target has http:// or https:// scheme."""
        if not target.startswith(("http://", "https://")):
            return f"http://{target}"
        return target

    def build_command(
        self, target: str, args: List[str] = None, label: str = "", log_path: str = None
    ):
        """Build dalfox command for background execution."""
        args = args or []

        # Ensure target has URL scheme for dalfox
        target = self._ensure_url_scheme(target)

        # If no mode specified, add 'url' mode with target
        if "url" not in args and "file" not in args and "pipe" not in args:
            args = ["url", target] + args

        # Replace <target> placeholder (also ensure scheme in placeholder)
        processed_args = [arg.replace("<target>", target) for arg in args]

        # Add JSON output format if not specified
        if "--format" not in processed_args and "-format" not in processed_args:
            processed_args.extend(["--format", "json"])

        cmd = ["dalfox"] + processed_args

        return {"cmd": cmd, "timeout": 1800}  # 30 minutes

    def run(
        self, target: str, args: List[str] = None, label: str = "", log_path: str = None
    ) -> int:
        """Execute dalfox scan and write output to log_path."""
        args = args or []

        # Ensure target has URL scheme for dalfox
        target = self._ensure_url_scheme(target)

        # If no mode specified, add 'url' mode with target
        if "url" not in args and "file" not in args and "pipe" not in args:
            args = ["url", target] + args

        # Replace <target> placeholder (also ensure scheme in placeholder)
        processed_args = [arg.replace("<target>", target) for arg in args]

        # Add JSON output format if not specified
        if "--format" not in processed_args and "-format" not in processed_args:
            processed_args.extend(["--format", "json"])

        cmd = ["dalfox"] + processed_args

        if not log_path:
            try:
                proc = subprocess.run(
                    cmd, capture_output=True, timeout=1800, check=False
                )
                return proc.returncode
            except Exception:
                return 1

        try:
            with open(log_path, "a", encoding="utf-8", errors="replace") as fh:
                fh.write(f"=== Plugin: Dalfox ===\n")
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
                    timeout=1800,
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
                fh.write("\nERROR: Dalfox timed out after 30 minutes\n")
            return 124

        except FileNotFoundError:
            with open(log_path, "a", encoding="utf-8", errors="replace") as fh:
                fh.write("\nERROR: dalfox not found in PATH\n")
                fh.write(
                    "Install with: go install github.com/hahwul/dalfox/v2@latest\n"
                )
            return 127

        except Exception as e:
            with open(log_path, "a", encoding="utf-8", errors="replace") as fh:
                fh.write(f"\nERROR: {type(e).__name__}: {e}\n")
            return 1


plugin = DalfoxPlugin()
