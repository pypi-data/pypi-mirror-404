#!/usr/bin/env python3
"""
souleyez.plugins.theharvester

theHarvester OSINT plugin with unified interface.
"""

import subprocess
import time
from typing import List

from souleyez.security.validation import ValidationError, validate_hostname

from .plugin_base import PluginBase

HELP = {
    "name": "theHarvester — Public Recon & Harvesting Tool",
    "description": (
        "Want a nosy little drone that quietly snoops the public web so you don't have to?\n\n"
        "theHarvester pulls together email addresses, subdomains, hostnames, and employee names from public sources (search engines, "
        "public DNS, certificate transparency, social media, and more) to give you a fast reconnaissance snapshot.\n\n"
        "It's perfect for building an external attack surface map and collecting leads before deeper testing — think of it as the "
        "first-pass for OSINT that points you where to probe next. theHarvester doesn't exploit anything; it aggregates publicly "
        "available artifacts so you can triage, add to the job log, and convert useful results into Findings.\n\n"
        "Play nice: gathering lots of public data can trigger rate limits or alerts on some services, so use respectful query rates "
        "and follow your engagement rules. 😇\n\n"
        "Quick tips:\n"
        "- Great for initial external recon: email harvesting, subdomain discovery, host collection, and employee name gathering.\n"
        "- Combine its output with DNS, CT logs, and certificate data for better coverage.\n"
        "- Save results (CSV/JSON) to the job log so you can import them into Findings, asset lists, or follow-up scans.\n"
        "- Respect rate limits and API terms for the public sources you query.\n"
        "- Use findings from theHarvester to feed targeted scans (subdomain -> Nmap -> service checks) or social-engineering risk assessments.\n"
    ),
    "usage": 'souleyez jobs enqueue theharvester <domain> --args "-b bing"',
    "examples": [
        'souleyez jobs enqueue theharvester example.com --args "-b bing"',
        'souleyez jobs enqueue theharvester example.com --args "-b certspotter,crtsh"',
        'souleyez jobs enqueue theharvester example.com --args "-b duckduckgo -l 200"',
        'souleyez jobs enqueue theharvester example.com --args "-b hackertarget,virustotal"',
    ],
    "flags": [
        [
            "-b <source>",
            "Data source (bing, duckduckgo, yahoo, certspotter, crtsh, dnsdumpster, hackertarget, etc.)",
        ],
        ["-l <limit>", "Limit results (default 500)"],
        ["-s <start>", "Start at result number X"],
        ["-f <file>", "Save results to HTML/XML file"],
    ],
    "preset_categories": {
        "active_sources": [
            {
                "name": "Bing Search",
                "args": ["-b", "bing", "-l", "500"],
                "desc": "Search Bing for emails/subdomains/hosts",
            },
            {
                "name": "DuckDuckGo Search",
                "args": ["-b", "duckduckgo", "-l", "500"],
                "desc": "Search DuckDuckGo for emails/subdomains/hosts",
            },
            {
                "name": "URLScan Search",
                "args": ["-b", "urlscan", "-l", "500"],
                "desc": "Search URLScan.io for URLs/subdomains/hosts",
            },
            {
                "name": "Quick Search",
                "args": ["-b", "bing,yahoo", "-l", "100"],
                "desc": "Quick search engine scan (100 results)",
            },
        ],
        "passive_sources": [
            {
                "name": "Certificate Logs",
                "args": ["-b", "certspotter,crtsh"],
                "desc": "Certificate transparency logs (subdomains)",
            },
            {
                "name": "Comprehensive Passive",
                "args": [
                    "-b",
                    "certspotter,crtsh,dnsdumpster,hackertarget,otx,virustotal",
                ],
                "desc": "All passive sources (no active queries)",
            },
        ],
    },
    "presets": [
        # Flattened list for backward compatibility
        {
            "name": "Bing Search",
            "args": ["-b", "bing", "-l", "500"],
            "desc": "Search Bing for emails/subdomains/hosts",
        },
        {
            "name": "DuckDuckGo Search",
            "args": ["-b", "duckduckgo", "-l", "500"],
            "desc": "Search DuckDuckGo for emails/subdomains/hosts",
        },
        {
            "name": "URLScan Search",
            "args": ["-b", "urlscan", "-l", "500"],
            "desc": "Search URLScan.io for URLs/subdomains/hosts",
        },
        {
            "name": "Quick Search",
            "args": ["-b", "bing,yahoo", "-l", "100"],
            "desc": "Quick search engine scan (100 results)",
        },
        {
            "name": "Certificate Logs",
            "args": ["-b", "certspotter,crtsh"],
            "desc": "Certificate transparency logs (subdomains)",
        },
        {
            "name": "Comprehensive Passive",
            "args": ["-b", "certspotter,crtsh,dnsdumpster,hackertarget,otx,virustotal"],
            "desc": "All passive sources (no active queries)",
        },
    ],
    "help_sections": [
        {
            "title": "What is theHarvester?",
            "color": "cyan",
            "content": [
                {
                    "title": "Overview",
                    "desc": "theHarvester aggregates email addresses, subdomains, hostnames, and employee names from public sources to build reconnaissance snapshots for external attack surface mapping.",
                },
                {
                    "title": "Use Cases",
                    "desc": "Perfect for initial OSINT reconnaissance and collecting leads before deeper testing.",
                    "tips": [
                        "Email harvesting and subdomain discovery",
                        "Hostname collection and employee name gathering",
                        "Combine output with DNS, CT logs, and certificate data for better coverage",
                        "Save results (CSV/JSON) to job log for importing into Findings or follow-up scans",
                        "Feed targeted scans (subdomain → Nmap → service checks) or social-engineering assessments",
                        "Respect rate limits and API terms for public sources you query",
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
                    "desc": "1. Select a domain to investigate\n     2. Choose a data source (active or passive)\n     3. Review results and add to job log\n     4. Import findings into engagement",
                },
                {
                    "title": "Data Sources",
                    "desc": "Active sources query search engines directly, passive sources use archived data",
                    "tips": [
                        "Bing/DuckDuckGo: Good for email addresses",
                        "Certificate Logs: Best for subdomain discovery",
                        "Comprehensive Passive: Broadest coverage without active queries",
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
                        "Start with passive sources to avoid detection",
                        "Use comprehensive passive for maximum subdomain coverage",
                        "Save results to job log for later analysis",
                        "Respect rate limits and API terms",
                        "Combine with DNS enumeration for complete coverage",
                    ],
                ),
                (
                    "Common Issues:",
                    [
                        "Rate limiting: Switch to passive sources or reduce query frequency",
                        "No results: Try different data sources or verify domain is valid",
                        "API errors: Check internet connectivity and source availability",
                    ],
                ),
            ],
        },
    ],
}


class TheHarvesterPlugin(PluginBase):
    name = "theHarvester (OSINT)"
    tool = "theHarvester"
    category = "reconnaissance"
    HELP = HELP

    def build_command(
        self, target: str, args: List[str] = None, label: str = "", log_path: str = None
    ):
        """Build command for background execution with PID tracking."""
        args = args or []

        # Validate hostname
        try:
            target = validate_hostname(target)
        except ValidationError as e:
            if log_path:
                with open(log_path, "w") as f:
                    f.write(f"ERROR: Invalid domain: {e}\n")
            return None

        # theHarvester uses -d for domain
        cmd = ["theHarvester", "-d", target] + args

        return {"cmd": cmd, "timeout": 1800}

    def run(
        self, target: str, args: List[str] = None, label: str = "", log_path: str = None
    ) -> int:
        """
        Execute theHarvester scan and write output to log_path.

        Args:
            target: Target domain (e.g. "example.com")
            args: theHarvester arguments (e.g. ["-b", "google"])
            label: Optional label for this scan
            log_path: Path to write output (required for background jobs)

        Returns:
            int: Exit code (0=success, non-zero=error)
        """
        # Validate hostname/domain
        try:
            target = validate_hostname(target)
        except ValidationError as e:
            if log_path:
                with open(log_path, "w") as f:
                    f.write(f"ERROR: Invalid domain: {e}\n")
                return 1
            raise ValueError(f"Invalid domain: {e}")

        args = args or []

        # Build theHarvester command
        # theHarvester uses -d for domain
        cmd = ["theHarvester", "-d", target] + args

        if not log_path:
            # Fallback for direct calls
            try:
                proc = subprocess.run(
                    cmd, capture_output=True, timeout=300, check=False
                )
                return proc.returncode
            except Exception:
                return 1

        # Run with logging
        try:
            with open(log_path, "a", encoding="utf-8", errors="replace") as fh:
                fh.write(f"Command: {' '.join(cmd)}\n")
                fh.write(
                    f"Started: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}\n\n"
                )
                fh.flush()

                proc = subprocess.run(
                    cmd, stdout=fh, stderr=subprocess.STDOUT, timeout=300, check=False
                )

                fh.write(
                    f"\nCompleted: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}\n"
                )
                fh.write(f"Exit Code: {proc.returncode}\n")

                return proc.returncode

        except subprocess.TimeoutExpired:
            with open(log_path, "a", encoding="utf-8", errors="replace") as fh:
                fh.write("\nERROR: theHarvester timed out after 300 seconds\n")
            return 124

        except FileNotFoundError:
            with open(log_path, "a", encoding="utf-8", errors="replace") as fh:
                fh.write("\nERROR: theHarvester not found in PATH\n")
            return 127

        except Exception as e:
            with open(log_path, "a", encoding="utf-8", errors="replace") as fh:
                fh.write(f"\nERROR: {type(e).__name__}: {e}\n")
            return 1


# Export plugin instance
plugin = TheHarvesterPlugin()
