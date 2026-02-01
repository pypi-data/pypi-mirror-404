#!/usr/bin/env python3
"""
souleyez.plugins.dnsrecon

DNSRecon DNS enumeration and reconnaissance plugin.
"""

import subprocess
import time
from typing import List

from souleyez.security.validation import ValidationError, validate_target

from .plugin_base import PluginBase

HELP = {
    "name": "DNSRecon — DNS Enumeration Tool",
    "description": (
        "Need to discover subdomains and DNS infrastructure?\n\n"
        "DNSRecon performs comprehensive DNS enumeration including standard record queries, "
        "zone transfers, subdomain brute-forcing, reverse lookups, and more.\n\n"
        "It's essential for reconnaissance to map out an organization's DNS infrastructure, "
        "discover hidden subdomains, identify mail servers, and understand the attack surface.\n\n"
        "Quick tips:\n"
        "- Discovers A, MX, NS, TXT, and other DNS records\n"
        "- Attempts zone transfers (AXFR) when possible\n"
        "- Can brute-force subdomains with wordlists\n"
        "- Finds SPF records and mail infrastructure\n"
        "- Identifies nameservers and DNS configuration\n"
    ),
    "usage": "souleyez jobs enqueue dnsrecon -d <domain> [options]",
    "examples": [
        "souleyez jobs enqueue dnsrecon -d example.com -t std",
        "souleyez jobs enqueue dnsrecon -d example.com -t axfr",
        "souleyez jobs enqueue dnsrecon -d example.com -D data/wordlists/subdomains_common.txt -t brt",
    ],
    "flags": [
        ["-d <domain>", "Target domain"],
        [
            "-t <type>",
            "Enumeration type: std, axfr, brt, srv, rvl, snoop, tld, zonewalk",
        ],
        ["-D <file>", "Dictionary file for subdomain brute force"],
        ["-n <ns>", "Use specific nameserver"],
        ["-a", "Perform AXFR with standard enumeration"],
        ["-s", "Perform reverse lookup of IPv4 ranges in SPF record"],
        ["-k", "Perform crt.sh enumeration"],
        ["-w", "Perform deep WHOIS record analysis"],
        ["--threads <num>", "Number of threads (default: 10)"],
    ],
    "presets": [
        {
            "name": "Standard Enum",
            "args": ["-t", "std"],
            "desc": "Standard DNS enumeration (A, MX, NS, TXT records)",
        },
        {
            "name": "Zone Transfer",
            "args": ["-a"],
            "desc": "Attempt AXFR zone transfer with standard enum",
        },
        {
            "name": "Subdomain Brute",
            "args": ["-t", "brt", "-D", "data/wordlists/subdomains_common.txt"],
            "desc": "Brute force subdomains with wordlist",
        },
        {
            "name": "Full Enum",
            "args": ["-a", "-s", "-k"],
            "desc": "Comprehensive enumeration with all techniques",
        },
    ],
    "help_sections": [
        {
            "title": "What is DNSRecon?",
            "color": "cyan",
            "content": [
                {
                    "title": "Overview",
                    "desc": "DNSRecon performs comprehensive DNS enumeration including standard record queries, zone transfers, subdomain brute-forcing, and reverse lookups.",
                },
                {
                    "title": "Use Cases",
                    "desc": "Essential for mapping DNS infrastructure and discovering hidden subdomains.",
                    "tips": [
                        "Discover all DNS records (A, MX, NS, TXT, etc.)",
                        "Attempt zone transfers (AXFR) for full DNS data",
                        "Brute-force subdomains with wordlists",
                        "Find mail servers and SPF records",
                        "Identify nameserver configuration",
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
                    "desc": "1. Select target domain\n     2. Choose enumeration type (standard, zone transfer, brute force, full)\n     3. Review discovered subdomains and records\n     4. Feed results into next phase (port scanning)",
                },
                {
                    "title": "Enumeration Types",
                    "desc": "Different scan modes for different goals",
                    "tips": [
                        "Standard Enum: Quick record lookup (A, MX, NS, TXT)",
                        "Zone Transfer: Attempt AXFR for complete zone data",
                        "Subdomain Brute: Dictionary-based subdomain discovery",
                        "Full Enum: All techniques combined (zone transfer + SPF + crt.sh)",
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
                        "Start with standard enum to get baseline records",
                        "Always try zone transfer (often misconfigured)",
                        "Use comprehensive wordlists for brute forcing",
                        "Combine with crt.sh for certificate transparency data",
                        "Export results and import into host database",
                    ],
                ),
                (
                    "Common Issues:",
                    [
                        "Zone transfer denied: Expected, try brute force instead",
                        "Slow brute force: Reduce wordlist size or increase threads",
                        "No results: Verify domain is valid and DNS is reachable",
                        "Timeout: Large zones may take time, increase timeout",
                    ],
                ),
            ],
        },
    ],
}


class DnsreconPlugin(PluginBase):
    name = "DNSRecon"
    tool = "dnsrecon"
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

        args = args or ["-t", "std"]

        # Check if -d flag is already in args (from auto-chaining)
        if "-d" in args:
            # Args already contain -d domain, just use them as-is
            cmd = ["dnsrecon"] + args
        else:
            # Add -d flag with target
            cmd = ["dnsrecon", "-d", target] + args

        return {"cmd": cmd, "timeout": 1800}

    def run(
        self, target: str, args: List[str] = None, label: str = "", log_path: str = None
    ) -> int:
        """
        Execute DNSRecon and write output to log_path.
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
            args = ["-t", "std"]  # Default to standard enumeration

        # Build command: dnsrecon -d <domain> <args>
        cmd = ["dnsrecon", "-d", target] + args

        if log_path:
            with open(log_path, "w") as f:
                f.write(f"# DNSRecon enumeration for {target}\n")
                f.write(f"# Command: {' '.join(cmd)}\n")
                f.write(f"# Started: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=600  # 10 minutes max
            )

            if log_path:
                with open(log_path, "a") as f:
                    f.write(result.stdout)
                    if result.stderr:
                        f.write(f"\n\n# Errors:\n{result.stderr}\n")

            return result.returncode

        except subprocess.TimeoutExpired:
            if log_path:
                with open(log_path, "a") as f:
                    f.write("\n\n# ERROR: Command timed out after 600 seconds\n")
            return 124
        except Exception as e:
            if log_path:
                with open(log_path, "a") as f:
                    f.write(f"\n\n# ERROR: {str(e)}\n")
            return 1


# Export plugin instance
plugin = DnsreconPlugin()
