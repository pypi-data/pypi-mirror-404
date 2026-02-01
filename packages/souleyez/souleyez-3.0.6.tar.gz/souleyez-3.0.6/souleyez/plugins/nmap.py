#!/usr/bin/env python3
"""
souleyez.plugins.nmap
"""

import subprocess
import time
from typing import List

from souleyez.security.validation import (
    ValidationError,
    validate_nmap_args,
    validate_target,
)

from .plugin_base import PluginBase

HELP = {
    "name": "Nmap — Network Scanner",
    "description": (
        "Nmap is your trusty network prober — fast host discovery, port/service scanning, and fingerprinting wrapped in a "
        "friendly interface so you can scan like a pro with a single command.\n\n"
        "Let Nmap do the heavy lifting: discover live hosts, map open ports, identify running services and versions, and "
        "fingerprint operating systems and network stacks. This wrapped Nmap tool makes common scan types easy to run without "
        "memorizing flags, and captures results in the job log for later triage, correlation, and conversion into Findings — "
        "perfect for building a reconnaissance baseline before you dig deeper.\n\n"
        "Nmap is wildly flexible: run a quick sweep to see what's alive, do a targeted service/version scan for a handful of "
        "hosts, or launch a thorough TCP/UDP probe to find everything that answers. Heads up — deeper scans (UDP, full port "
        "ranges, OS detection) can be slow and noisy, so match your scan intensity to your rules of engagement.\n\n"
        "Quick tips:\n"
        "- Start with a simple discovery sweep to limit your attack surface before deeper scans.\n"
        "- Save XML/grepable output so parsers and the Findings manager can ingest results easily.\n"
        "- UDP and OS detection are powerful but slower and noisier — use them judiciously.\n"
        "- Use --host-timeout to skip unresponsive hosts (e.g., --host-timeout 10m).\n"
        "- Combine Nmap output with service-specific checks (banner grabs, vuln scanners) for richer context.\n"
        "- Always scan with permission — loud scans get noticed.\n"
    ),
    "usage": 'souleyez jobs enqueue nmap <target> --args "<nmap flags>"',
    "examples": [
        'souleyez jobs enqueue nmap 10.0.0.0/24 --args "-vv -sn"',
        'souleyez jobs enqueue nmap 10.0.0.82 --args "-v -PS -F"',
        'souleyez jobs enqueue nmap 10.0.0.82 --args "-vv -sV -O -p1-65535"',
        'souleyez jobs enqueue nmap 10.0.0.82 --args "-sU -sV --top-ports 100"',
        'souleyez jobs enqueue nmap 10.0.0.82 --args "--script vuln"',
    ],
    "flags": [
        ["-sn", "Ping scan (no port scan)"],
        ["-sS", "TCP SYN scan (stealth)"],
        ["-sU", "UDP scan"],
        ["-sV", "Service/version detection"],
        ["-O", "OS detection"],
        ["-v/-vv", "Verbose/Very verbose output"],
        ["-F", "Fast scan (top 100 ports)"],
        ["-p1-65535", "Scan all TCP ports"],
        ["--top-ports N", "Scan N most common ports"],
        ["-sC/--script", "Run default/specific NSE scripts"],
        ["-T0 to -T5", "Timing template (0=slowest, 5=fastest)"],
    ],
    "preset_categories": {
        "discovery": [
            {
                "name": "Ping Sweep",
                "args": ["-vv", "-sn"],
                "desc": "Host discovery (no port scan)",
            }
        ],
        "port_scanning": [
            {
                "name": "Fast Scan",
                "args": ["-Pn", "-v", "-PS", "-F", "-T4", "--host-timeout", "90s"],
                "desc": "Top 100 ports, quick sweep",
            },
            {
                "name": "Stealth Scan",
                "args": ["-Pn", "-sS", "-T4", "--open"],
                "desc": "SYN scan only (quiet, no version detection)",
            },
            {
                "name": "Full TCP Scan",
                "args": [
                    "-Pn",
                    "-vv",
                    "-sS",
                    "-sV",
                    "-sC",
                    "-O",
                    "-p-",
                    "--script",
                    "vuln",
                    "-T4",
                    "--host-timeout",
                    "20m",
                    "--open",
                ],
                "desc": "All 65535 ports with versions, OS, vulns",
            },
        ],
        "service_detection": [
            {
                "name": "Service & Version",
                "args": ["-Pn", "-sV", "-sC", "--open", "-T4"],
                "desc": "Service detection + safe NSE scripts",
            },
            {
                "name": "Vulnerability Scan",
                "args": ["-Pn", "-sV", "--script", "vuln", "--open"],
                "desc": "Detect known vulnerabilities (CVEs)",
            },
        ],
        "udp_scanning": [
            {
                "name": "UDP Quick",
                "args": ["-Pn", "-sU", "-sV", "--top-ports", "100"],
                "desc": "Top 100 UDP ports",
            },
            {
                "name": "UDP Deep",
                "args": [
                    "-sU",
                    "-sV",
                    "--top-ports",
                    "1000",
                    "-T4",
                    "--host-timeout",
                    "20m",
                    "--open",
                ],
                "desc": "Top 1000 UDP ports (slow)",
            },
        ],
        "protocol_enumeration": [
            {
                "name": "SMB Enumeration",
                "args": [
                    "-p445",
                    "--script",
                    "smb-enum-shares,smb-enum-users,smb-os-discovery",
                ],
                "desc": "Shares, users, OS discovery",
            },
            {
                "name": "HTTP Enumeration",
                "args": [
                    "-p80,443,8080,8443",
                    "--script",
                    "http-enum,http-headers,http-methods,http-title",
                ],
                "desc": "Web server info, directories, headers",
            },
        ],
    },
    "presets": [
        # Flattened list for backward compatibility - matches preset_categories order
        # Discovery
        {
            "name": "Ping Sweep",
            "args": ["-vv", "-sn"],
            "desc": "Host discovery (no port scan)",
        },
        # Port Scanning (all include -Pn to skip host discovery - many targets block ICMP)
        {
            "name": "Fast Scan",
            "args": ["-Pn", "-v", "-PS", "-F", "-T4", "--host-timeout", "90s"],
            "desc": "Top 100 ports, quick sweep",
        },
        {
            "name": "Stealth Scan",
            "args": ["-Pn", "-sS", "-T4", "--open"],
            "desc": "SYN scan only (quiet, no version detection)",
        },
        {
            "name": "Full TCP Scan",
            "args": [
                "-Pn",
                "-vv",
                "-sS",
                "-sV",
                "-sC",
                "-O",
                "-p-",
                "--script",
                "vuln",
                "-T4",
                "--host-timeout",
                "20m",
                "--open",
            ],
            "desc": "All 65535 ports with versions, OS, vulns",
        },
        # Service Detection
        {
            "name": "Service & Version",
            "args": ["-Pn", "-sV", "-sC", "--open", "-T4"],
            "desc": "Service detection + safe NSE scripts",
        },
        {
            "name": "Vulnerability Scan",
            "args": ["-Pn", "-sV", "--script", "vuln", "--open"],
            "desc": "Detect known vulnerabilities (CVEs)",
        },
        # UDP Scanning
        {
            "name": "UDP Quick",
            "args": ["-Pn", "-sU", "-sV", "--top-ports", "100"],
            "desc": "Top 100 UDP ports",
        },
        {
            "name": "UDP Deep",
            "args": [
                "-sU",
                "-sV",
                "--top-ports",
                "1000",
                "-T4",
                "--host-timeout",
                "20m",
                "--open",
            ],
            "desc": "Top 1000 UDP ports (slow)",
        },
        # Protocol Enumeration
        {
            "name": "SMB Enumeration",
            "args": [
                "-p445",
                "--script",
                "smb-enum-shares,smb-enum-users,smb-os-discovery",
            ],
            "desc": "Shares, users, OS discovery",
        },
        {
            "name": "HTTP Enumeration",
            "args": [
                "-p80,443,8080,8443",
                "--script",
                "http-enum,http-headers,http-methods,http-title",
            ],
            "desc": "Web server info, directories, headers",
        },
        # Router/IoT Discovery
        {
            "name": "UPnP Discovery",
            "args": [
                "-sU",
                "-sS",
                "-p",
                "U:1900,T:49152-49156,5000,2869",
                "--script",
                "upnp-info",
                "-T4",
                "--open",
            ],
            "desc": "UPnP services on routers/IoT",
        },
        {
            "name": "TR-069 Detection",
            "args": ["-sV", "-p", "7547,4567,5555,8089", "-T4", "--open"],
            "desc": "ISP remote management (CWMP)",
        },
        # macOS Discovery
        {
            "name": "macOS Services",
            "args": [
                "-sV",
                "-p",
                "548,5900,3283,5353",
                "--script",
                "afp-serverinfo,vnc-info",
                "-T4",
                "--open",
            ],
            "desc": "AFP, VNC, ARD, Bonjour",
        },
        {
            "name": "mDNS/Bonjour",
            "args": [
                "-sU",
                "-p",
                "5353",
                "--script",
                "dns-service-discovery,broadcast-dns-service-discovery",
                "-T4",
                "--open",
            ],
            "desc": "Discover Apple devices via mDNS",
        },
    ],
    "help_sections": [
        {
            "title": "What is Nmap?",
            "color": "cyan",
            "content": [
                {
                    "title": "Overview",
                    "desc": "Nmap is the industry-standard network scanner for host discovery, port scanning, service detection, and OS fingerprinting.",
                },
                {
                    "title": "Use Cases",
                    "desc": "Essential for network reconnaissance and security assessments",
                    "tips": [
                        "Discover live hosts on the network",
                        "Identify open ports and running services",
                        "Fingerprint operating systems and service versions",
                        "Find potential vulnerabilities with NSE scripts",
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
                    "desc": "1. Start with discovery sweep (-sn) to find live hosts\n     2. Run fast scan (-F) to identify open ports\n     3. Deep scan with version detection (-sV -O) for detailed info\n     4. Run vulnerability scripts (--script vuln) on targets",
                },
                {
                    "title": "Scan Types",
                    "desc": "Different scans for different needs",
                    "tips": [
                        "Discovery: Quick ping sweep (no ports)",
                        "Fast Scan: Top 100 ports with 90s timeout",
                        "Full Scan: All 65535 ports with OS/version detection",
                        "UDP Scan: Check for UDP services (slower)",
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
                        "Start with quick discovery before deep scans",
                        "Use --host-timeout to skip slow/dead hosts",
                        "Save XML output for parsing (-oX output.xml)",
                        "Match scan intensity to your authorization level",
                        "Combine with service-specific checks for full coverage",
                    ],
                ),
                (
                    "Common Issues:",
                    [
                        "Slow scans: Use -F for fast mode or increase -T timing",
                        "UDP timeout: Add --host-timeout 10m for UDP scans",
                        "Missed hosts: Try different ping techniques (-PS, -PA, -PU)",
                        "Permission denied: Some scan types require root/sudo",
                    ],
                ),
            ],
        },
    ],
}


class NmapPlugin(PluginBase):
    name = "Nmap"
    tool = "nmap"
    category = "scanning"
    HELP = HELP

    def _requires_root(self, args: List[str]) -> bool:
        """Check if the nmap arguments require root/sudo privileges."""
        # UDP scans (-sU) and some other scan types require root
        root_required_flags = [
            "-sU",
            "-sS",
            "-sA",
            "-sW",
            "-sM",
            "-sN",
            "-sF",
            "-sX",
            "-O",
        ]
        return any(flag in args for flag in root_required_flags)

    def _is_root(self) -> bool:
        """Check if running as root."""
        import os

        return os.geteuid() == 0

    def build_command(
        self, target: str, args: List[str] = None, label: str = "", log_path: str = None
    ):
        """Build nmap command for background execution with PID tracking."""
        args = args or []

        # Validate and sanitize arguments
        try:
            if args:
                args = validate_nmap_args(args)
        except ValidationError as e:
            if log_path:
                with open(log_path, "w", encoding="utf-8") as fh:
                    fh.write(f"ERROR: Invalid nmap arguments: {e}\n")
            return None

        # Split target on whitespace to handle multiple IPs/hosts
        target_list = target.split()

        # Validate each target (IP, CIDR, or hostname)
        validated_targets = []
        for t in target_list:
            try:
                validated_targets.append(validate_target(t))
            except ValidationError as e:
                if log_path:
                    with open(log_path, "w", encoding="utf-8") as fh:
                        fh.write(f"ERROR: Invalid target '{t}': {e}\n")
                return None

        cmd = ["nmap"] + args + validated_targets

        # Use sudo for privileged scans when not running as root
        if self._requires_root(args) and not self._is_root():
            cmd = ["sudo", "-n"] + cmd  # -n = non-interactive (no password prompt)

        return {"cmd": cmd, "timeout": 3600}  # 1 hour timeout

    def run(
        self, target: str, args: List[str] = None, label: str = "", log_path: str = None
    ) -> int:
        """Execute nmap scan and write output to log_path."""
        args = args or []

        # Validate and sanitize arguments
        try:
            if args:
                args = validate_nmap_args(args)
        except ValidationError as e:
            if log_path:
                with open(log_path, "w", encoding="utf-8") as fh:
                    fh.write(f"ERROR: Invalid nmap arguments: {e}\n")
                return 1
            raise

        # Split target on whitespace to handle multiple IPs/hosts
        # e.g., "10.0.0.1 10.0.0.2 10.0.0.3" -> ["10.0.0.1", "10.0.0.2", "10.0.0.3"]
        target_list = target.split()

        # Validate each target (IP, CIDR, or hostname)
        validated_targets = []
        for t in target_list:
            try:
                validated_targets.append(validate_target(t))
            except ValidationError as e:
                if log_path:
                    with open(log_path, "w", encoding="utf-8") as fh:
                        fh.write(f"ERROR: Invalid target '{t}': {e}\n")
                    return 1
                raise ValueError(f"Invalid target '{t}': {e}")

        cmd = ["nmap"] + args + validated_targets

        # Use sudo for privileged scans when not running as root
        if self._requires_root(args) and not self._is_root():
            cmd = ["sudo", "-n"] + cmd  # -n = non-interactive (no password prompt)

        if log_path:
            return self._run_with_logpath(cmd, log_path)

        return self._run_legacy(target, args, label)

    def _run_with_logpath(self, cmd: List[str], log_path: str) -> int:
        """New-style: write directly to log_path."""
        try:
            with open(log_path, "a", encoding="utf-8", errors="replace") as fh:
                fh.write(f"Command: {' '.join(cmd)}\n")
                fh.write(
                    f"Started: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}\n\n"
                )
                fh.flush()

                proc = subprocess.run(
                    cmd,
                    stdout=fh,
                    stderr=subprocess.STDOUT,
                    timeout=3600,  # 1 hour timeout
                    check=False,
                )

                fh.write(
                    f"\nCompleted: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}\n"
                )
                fh.write(f"Exit Code: {proc.returncode}\n")

                return proc.returncode

        except subprocess.TimeoutExpired:
            with open(log_path, "a", encoding="utf-8", errors="replace") as fh:
                fh.write("\nERROR: Nmap timed out after 3600 seconds (1 hour)\n")
            return 124

        except FileNotFoundError:
            with open(log_path, "a", encoding="utf-8", errors="replace") as fh:
                fh.write("\nERROR: nmap not found in PATH\n")
            return 127

        except Exception as e:
            with open(log_path, "a", encoding="utf-8", errors="replace") as fh:
                fh.write(f"\nERROR: {type(e).__name__}: {e}\n")
            return 1

    def _run_legacy(self, target: str, args: List[str], label: str):
        """Old-style execution for backward compatibility."""
        try:
            from ..scanner import run_nmap

            logpath, rc, xmlpath, summary = run_nmap(
                target, args, label, save_xml=False
            )
            return rc
        except ImportError:
            # Split target on whitespace to handle multiple IPs/hosts
            target_list = target.split()
            cmd = ["nmap"] + (args or []) + target_list
            try:
                proc = subprocess.run(
                    cmd, capture_output=True, timeout=3600, check=False
                )
                return proc.returncode
            except Exception:
                return 1


plugin = NmapPlugin()
