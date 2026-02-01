#!/usr/bin/env python3
"""
souleyez.plugins.gobuster
"""

from __future__ import annotations

import re
import subprocess
import time
import uuid
from typing import Dict, List, Optional
from urllib.parse import urlparse

import requests

from souleyez.security.validation import ValidationError, validate_url

from .plugin_base import PluginBase

HELP = {
    "name": "Gobuster — Directory, File & DNS/VHost Brute-Force Tool",
    "description": (
        "Need a blunt but useful tool to knock on every web door?\n\n"
        "Gobuster brute-forces directories, files, and DNS/vhost names fast — great for finding hidden admin panels, forgotten endpoints, "
        "and virtual hosts that don't show up in normal browsing. It's a workhorse for directory discovery and DNS enumeration, and pairs "
        "nicely with targeted scanners once you know where the doors are.\n\n"
        "Gobuster doesn't exploit anything — it simply probes paths and names based on wordlists and reports what responds. That means it "
        "can be loud and produce lots of hits, so tune your wordlists and request rate to avoid overwhelm (and to stay polite to targets).\n\n"
        "Quick tips:\n"
        "- Use focused wordlists to reduce noise and false positives; start small, then expand.\n"
        "- Combine with Nmap/service scans: discovered paths → probe with service checks and vulnerability scans.\n"
        "- For vhosts, try common virtual-host wordlists and inspect HTTP response headers for clues.\n"
        "- Respect rate limits and the target's rules of engagement — brute forcing can trigger alerts.\n"
        "- Save findings (responses, status codes, and URLs) to the job log so you can convert them into Findings or follow-up tasks.\n"
    ),
    "usage": 'souleyez jobs enqueue gobuster <target> --args "dir -u <url> -w <wordlist> -t <threads>"',
    "examples": [
        'souleyez jobs enqueue gobuster http://example.com --args "dir -u http://example.com -w data/wordlists/web_dirs_common.txt -t 10"',
        'souleyez jobs enqueue gobuster http://example.com --args "dir -u http://example.com -w data/wordlists/web_dirs_common.txt -x php,txt,html -t 20"',
        'souleyez jobs enqueue gobuster example.com --args "dns --domain example.com -w data/wordlists/subdomains_common.txt -t 15 --timeout 3s"',
        'souleyez jobs enqueue gobuster http://example.com --args "vhost -u http://example.com -w data/wordlists/subdomains_common.txt -t 50"',
    ],
    "flags": [
        ["dir", "Directory/file enumeration mode"],
        ["dns", "DNS subdomain enumeration mode"],
        ["vhost", "Virtual host discovery mode"],
        ["-u <url>", "Target URL (dir/vhost modes)"],
        ["--domain <domain>", "Target domain (dns mode)"],
        ["-w <wordlist>", "Wordlist path"],
        ["-t <threads>", "Number of threads"],
        [
            "--timeout <duration>",
            "DNS timeout per request (e.g., 3s, 5s) - useful to avoid DNS timeouts",
        ],
        ["-x <extensions>", "File extensions to check (comma-separated)"],
        ["-b <codes>", "Status codes to blacklist"],
        ["--wildcard", "Force continued operation when wildcard found"],
    ],
    "preset_categories": {
        "directory_enum": [
            {
                "name": "Quick Scan",
                "args": [
                    "dir",
                    "-u",
                    "<target>",
                    "-w",
                    "data/wordlists/web_dirs_common.txt",
                    "-t",
                    "10",
                ],
                "desc": "Common wordlist (87 entries)",
            },
            {
                "name": "Standard Scan",
                "args": [
                    "dir",
                    "-u",
                    "<target>",
                    "-w",
                    "data/wordlists/web_dirs_extended.txt",
                    "-t",
                    "20",
                ],
                "desc": "Extended wordlist (more coverage)",
            },
            {
                "name": "Common Files (HTML/PHP/TXT)",
                "args": [
                    "dir",
                    "-u",
                    "<target>",
                    "-w",
                    "data/wordlists/web_dirs_common.txt",
                    "-x",
                    "html,htm,php,txt,xml,json",
                    "-t",
                    "15",
                ],
                "desc": "Common paths + web file extensions",
            },
            {
                "name": "PHP Extensions",
                "args": [
                    "dir",
                    "-u",
                    "<target>",
                    "-w",
                    "data/wordlists/web_dirs_common.txt",
                    "-x",
                    "php,phps,php3,php4,php5,phtml",
                    "-t",
                    "15",
                ],
                "desc": "Common paths + PHP variants",
            },
        ],
        "subdomain_enum": [
            {
                "name": "Subdomain Scan (manual domain)",
                "args": [
                    "dns",
                    "--domain",
                    "example.com",
                    "-w",
                    "data/wordlists/subdomains_common.txt",
                    "-t",
                    "15",
                    "--timeout",
                    "3s",
                ],
                "desc": "Subdomain enumeration - EDIT example.com to your domain",
            }
        ],
        "vhost_discovery": [
            {
                "name": "Virtual Hosts",
                "args": [
                    "vhost",
                    "-u",
                    "<target>",
                    "-w",
                    "data/wordlists/subdomains_common.txt",
                    "-t",
                    "50",
                ],
                "desc": "Virtual host discovery",
            }
        ],
    },
    "presets": [
        # Flattened list for backward compatibility
        {
            "name": "Quick Scan",
            "args": [
                "dir",
                "-u",
                "<target>",
                "-w",
                "data/wordlists/web_dirs_common.txt",
                "-t",
                "10",
            ],
            "desc": "Common wordlist (87 entries)",
        },
        {
            "name": "Standard Scan",
            "args": [
                "dir",
                "-u",
                "<target>",
                "-w",
                "data/wordlists/web_dirs_extended.txt",
                "-t",
                "20",
            ],
            "desc": "Extended wordlist (more coverage)",
        },
        {
            "name": "Common Files (HTML/PHP/TXT)",
            "args": [
                "dir",
                "-u",
                "<target>",
                "-w",
                "data/wordlists/web_dirs_common.txt",
                "-x",
                "html,htm,php,txt,xml,json",
                "-t",
                "15",
            ],
            "desc": "Common paths + web file extensions",
        },
        {
            "name": "PHP Extensions",
            "args": [
                "dir",
                "-u",
                "<target>",
                "-w",
                "data/wordlists/web_dirs_common.txt",
                "-x",
                "php,phps,php3,php4,php5,phtml",
                "-t",
                "15",
            ],
            "desc": "Common paths + PHP variants",
        },
        {
            "name": "Subdomain Scan (manual domain)",
            "args": [
                "dns",
                "--domain",
                "example.com",
                "-w",
                "data/wordlists/subdomains_common.txt",
                "-t",
                "15",
                "--timeout",
                "3s",
            ],
            "desc": "Subdomain enumeration - EDIT example.com to your domain",
        },
        {
            "name": "Virtual Hosts",
            "args": [
                "vhost",
                "-u",
                "<target>",
                "-w",
                "data/wordlists/subdomains_common.txt",
                "-t",
                "50",
            ],
            "desc": "Virtual host discovery",
        },
    ],
    "help_sections": [
        {
            "title": "What is Gobuster?",
            "color": "cyan",
            "content": [
                {
                    "title": "Overview",
                    "desc": "Gobuster is a fast directory, file, and DNS/vhost brute-forcing tool perfect for discovering hidden web content and subdomains.",
                },
                {
                    "title": "Use Cases",
                    "desc": "Essential for web application reconnaissance",
                    "tips": [
                        "Find hidden directories and files (admin panels, config files)",
                        "Discover DNS subdomains",
                        "Enumerate virtual hosts",
                        "Identify forgotten endpoints and backups",
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
                    "desc": "1. Start with common wordlist for quick wins\n     2. Use file extensions (-x) for targeted discovery\n     3. Expand to larger wordlists if needed\n     4. Follow up discovered paths with manual testing",
                },
                {
                    "title": "Modes & Features",
                    "desc": "Three main scanning modes",
                    "tips": [
                        "dir: Directory/file enumeration on web servers",
                        "dns: Subdomain brute-forcing",
                        "vhost: Virtual host discovery",
                        "Use -b to blacklist status codes (403, 404)",
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
                        "Start with small wordlists, expand as needed",
                        "Use -x for file extensions (php,txt,html)",
                        "Respect rate limits to avoid overwhelming targets",
                        "Save results and convert findings to job log",
                        "Combine with Nmap service scans for context",
                    ],
                ),
                (
                    "Common Issues:",
                    [
                        "Wildcard responses: Use -b to filter status codes",
                        "Too many results: Filter by size (-fs) or words (-fw)",
                        "DNS timeouts: Add --timeout 3s for DNS mode",
                        "No results: Try different wordlists or extensions",
                    ],
                ),
            ],
        },
    ],
}


class GobusterPlugin(PluginBase):
    name = "Gobuster"
    tool = "gobuster"
    category = "scanning"
    HELP = HELP

    # Minimum required version (v3.x uses subcommands like 'dir', 'dns', 'vhost')
    MIN_VERSION = "3.0.0"

    def _check_version(self) -> tuple:
        """
        Check gobuster version meets minimum requirements.

        Returns:
            (meets_requirement: bool, version: str, error_msg: str or None)
        """
        try:
            # Use -v flag (not 'version' subcommand) - works on v3.x
            result = subprocess.run(
                ["gobuster", "-v"], capture_output=True, text=True, timeout=10
            )
            output = result.stdout + result.stderr

            # Parse version from output like "gobuster version 3.8.2"
            version_match = re.search(
                r"version\s+(\d+\.\d+\.\d+)", output, re.IGNORECASE
            )
            if version_match:
                version = version_match.group(1)
                major = int(version.split(".")[0])
                if major >= 3:
                    return (True, version, None)
                else:
                    return (False, version, self._upgrade_message(version))

            # Also try --version flag as fallback
            result2 = subprocess.run(
                ["gobuster", "--version"], capture_output=True, text=True, timeout=10
            )
            output2 = result2.stdout + result2.stderr
            version_match2 = re.search(
                r"version\s+(\d+\.\d+\.\d+)", output2, re.IGNORECASE
            )
            if version_match2:
                version = version_match2.group(1)
                major = int(version.split(".")[0])
                if major >= 3:
                    return (True, version, None)
                else:
                    return (False, version, self._upgrade_message(version))

            # If neither flag shows version info, check if v2.x by looking for subcommand error
            # v2.x will show "Usage: gobuster [OPTIONS] ..." without subcommands
            if "dir" not in output.lower() and "dns" not in output.lower():
                return (False, "2.x", self._upgrade_message("2.x"))

            # If we see dir/dns subcommands mentioned, assume v3.x
            return (True, "3.x", None)

        except FileNotFoundError:
            return (
                False,
                None,
                "ERROR: gobuster not found. Install with: sudo apt install gobuster",
            )
        except subprocess.TimeoutExpired:
            return (True, "unknown", None)  # Assume it works
        except Exception as e:
            return (True, "unknown", None)  # Assume it works

    def _upgrade_message(self, current_version: str) -> str:
        """Generate upgrade instructions for old gobuster versions."""
        return (
            f"ERROR: gobuster {current_version} is too old. Version 3.0.0+ required.\n\n"
            f"Gobuster v2.x doesn't support the 'dir/dns/vhost' subcommands used by SoulEyez.\n\n"
            f"UPGRADE OPTIONS:\n"
            f"  Option 1 - Install from Go (recommended, gets latest):\n"
            f"    go install github.com/OJ/gobuster/v3@latest\n\n"
            f"  Option 2 - Download binary from GitHub:\n"
            f"    https://github.com/OJ/gobuster/releases\n\n"
            f"  Option 3 - On Kali Linux:\n"
            f"    sudo apt update && sudo apt install gobuster\n\n"
            f"After upgrading, verify with: gobuster version\n"
        )

    def _preflight_check(
        self, base_url: str, timeout: float = 5.0, log_path: str = None
    ) -> Dict[str, Optional[str]]:
        """
        Probe target with random UUID path to detect false positive responses.

        Some servers return 403/401/200 for ALL paths (not just existing ones).
        This causes gobuster to fail or produce false positives. We detect this
        upfront and auto-add --exclude-length to filter them out.

        Also detects host-level redirects (e.g., non-www to www) and warns the user.

        Returns:
            dict with keys:
                - exclude_length: str or None (response length to exclude)
                - exclude_status: str or None (status code detected)
                - reason: str or None (explanation)
                - redirect_host: str or None (suggested target if host redirect detected)
        """
        result = {
            "exclude_length": None,
            "exclude_status": None,
            "reason": None,
            "redirect_host": None,
        }

        # Generate random UUID path that definitely doesn't exist
        test_path = str(uuid.uuid4())
        test_url = f"{base_url.rstrip('/')}/{test_path}"

        # Parse the original target host for comparison
        original_parsed = urlparse(base_url)
        original_host = original_parsed.netloc.lower()

        try:
            resp = requests.get(
                test_url,
                timeout=timeout,
                allow_redirects=False,
                headers={"User-Agent": "gobuster/3.6"},  # Match gobuster's UA
            )

            # 404 is expected for non-existent paths - no action needed
            if resp.status_code == 404:
                return result

            # Check for host-level redirects (301/302/307/308)
            if resp.status_code in [301, 302, 307, 308]:
                location = resp.headers.get("Location", "")
                if location:
                    # Parse the redirect location
                    redirect_parsed = urlparse(location)
                    redirect_host = redirect_parsed.netloc.lower()

                    # If Location is relative, it's not a host redirect
                    if redirect_host and redirect_host != original_host:
                        # This is a host-level redirect (e.g., non-www to www)
                        suggested_url = f"{redirect_parsed.scheme or original_parsed.scheme}://{redirect_host}"
                        result["redirect_host"] = suggested_url
                        result["exclude_status"] = str(resp.status_code)
                        result["reason"] = (
                            f"Host redirect detected: {original_host} → {redirect_host}"
                        )

                        if log_path:
                            with open(log_path, "a") as f:
                                f.write(f"\n{'=' * 70}\n")
                                f.write("⚠️  HOST-LEVEL REDIRECT DETECTED\n")
                                f.write(f"{'=' * 70}\n")
                                f.write(f"Target: {base_url}\n")
                                f.write(f"Redirects to: {redirect_host}\n")
                                f.write(f"Status: {resp.status_code}\n\n")
                                f.write(
                                    "The server redirects ALL requests to a different host.\n"
                                )
                                f.write("This causes unreliable results because:\n")
                                f.write(
                                    "  - Response sizes vary based on path length in redirect URL\n"
                                )
                                f.write(
                                    "  - Gobuster may report false positives or miss real paths\n\n"
                                )
                                # Parseable marker for auto-retry
                                f.write(f"HOST_REDIRECT_TARGET: {suggested_url}\n\n")
                                f.write("Auto-retrying with corrected target...\n")
                                f.write(f"{'=' * 70}\n\n")

                        # Still try to exclude the response length for this scan
                        content_length = len(resp.content)
                        result["exclude_length"] = str(content_length)
                        return result

            # Any other status for a random UUID = false positive indicator
            # Common: 403 (blocked), 401 (auth required), 200 (catch-all), 500 (error page)
            if resp.status_code in [200, 301, 302, 400, 401, 403, 500, 503]:
                content_length = len(resp.content)
                result["exclude_length"] = str(content_length)
                result["exclude_status"] = str(resp.status_code)
                result["reason"] = (
                    f"Pre-flight: Random path returned {resp.status_code} "
                    f"({content_length} bytes) - auto-excluding"
                )

                if log_path:
                    with open(log_path, "a") as f:
                        f.write(f"\n{'=' * 60}\n")
                        f.write("PRE-FLIGHT CHECK\n")
                        f.write(f"{'=' * 60}\n")
                        f.write(f"Tested: {test_url}\n")
                        f.write(
                            f"Result: {resp.status_code} ({content_length} bytes)\n"
                        )
                        f.write(f"Action: Adding --exclude-length {content_length}\n")
                        f.write(f"{'=' * 60}\n\n")

            return result

        except requests.exceptions.Timeout:
            # Target too slow, skip preflight
            if log_path:
                with open(log_path, "a") as f:
                    f.write("Pre-flight: Target timeout, skipping check\n")
            return result
        except requests.exceptions.ConnectionError:
            # Can't connect, let gobuster handle it
            return result
        except Exception:
            # Any other error, continue without exclusions
            return result

    def build_command(
        self, target: str, args: List[str] = None, label: str = "", log_path: str = None
    ):
        """Build gobuster command for background execution with PID tracking."""
        args = args or []

        # Check gobuster version meets requirements (v3.x+ required for subcommands)
        meets_req, version, error_msg = self._check_version()
        if not meets_req:
            if log_path:
                with open(log_path, "w") as f:
                    f.write(error_msg)
            return None

        # Detect the mode from args
        mode = None
        if "dir" in args:
            mode = "dir"
        elif "dns" in args:
            mode = "dns"
        elif "vhost" in args:
            mode = "vhost"

        # Validate target and mode compatibility (same validation as run())
        if mode == "dns":
            if target.startswith(("http://", "https://")):
                if log_path:
                    with open(log_path, "w") as f:
                        f.write("ERROR: DNS mode requires a domain name, not a URL\n")
                return None

            ip_pattern = re.compile(r"^(\d{1,3}\.){3}\d{1,3}$")
            if ip_pattern.match(target):
                if log_path:
                    with open(log_path, "w") as f:
                        f.write(
                            "ERROR: DNS mode requires a domain name, not an IP address\n"
                        )
                return None

        elif mode in ["dir", "vhost"]:
            if not target.startswith(("http://", "https://")):
                target = f"http://{target}"

            try:
                target = validate_url(target)
            except ValidationError as e:
                if log_path:
                    with open(log_path, "w") as f:
                        f.write(f"ERROR: Invalid URL: {e}\n")
                return None

        else:
            if not target.startswith(("http://", "https://")):
                target = f"http://{target}"

            try:
                target = validate_url(target)
            except ValidationError as e:
                if log_path:
                    with open(log_path, "w") as f:
                        f.write(f"ERROR: Invalid URL: {e}\n")
                return None

        processed_args = [arg.replace("<target>", target) for arg in args]

        # Pre-flight check for dir/vhost modes: detect false positive responses
        # This prevents gobuster from failing on servers that return 403/401/200 for all paths
        if mode in ["dir", "vhost", None]:  # None = default to dir behavior
            # Extract base URL from -u argument or use target
            base_url = target
            for i, arg in enumerate(processed_args):
                if arg == "-u" and i + 1 < len(processed_args):
                    base_url = processed_args[i + 1]
                    break

            # Always run preflight - merge detected length with any existing exclusions
            preflight = self._preflight_check(base_url, timeout=5.0, log_path=log_path)

            # If host redirect detected, abort scan immediately
            # Don't waste time running on wrong target - result_handler will spawn retry
            if preflight.get("redirect_host"):
                if log_path:
                    with open(log_path, "a") as f:
                        f.write("\n=== SCAN ABORTED ===\n")
                        f.write(
                            "Host redirect detected. Aborting to avoid wasted scan time.\n"
                        )
                        f.write(
                            "A retry job will be auto-queued with the correct target.\n"
                        )
                        f.write(
                            f"=== Completed: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())} ===\n"
                        )
                return None  # Abort - background.py will check log for HOST_REDIRECT_TARGET

            if preflight["exclude_length"]:
                # Collect existing exclusions
                existing_excludes = set()
                exclude_idx = None
                for i, arg in enumerate(processed_args):
                    if arg == "--exclude-length" and i + 1 < len(processed_args):
                        exclude_idx = i
                        existing_excludes.update(processed_args[i + 1].split(","))

                # Add detected length if not already excluded
                if preflight["exclude_length"] not in existing_excludes:
                    existing_excludes.add(preflight["exclude_length"])
                    merged = ",".join(sorted(existing_excludes))

                    if exclude_idx is not None:
                        # Update existing --exclude-length value
                        processed_args[exclude_idx + 1] = merged
                    else:
                        # Add new --exclude-length
                        processed_args.extend(["--exclude-length", merged])

        # Add --no-progress to suppress verbose progress output (gobuster v3.6+)
        # This prevents thousands of "Progress: X / Y" lines in output
        if "--no-progress" not in processed_args:
            processed_args.append("--no-progress")

        cmd = ["gobuster"] + processed_args

        return {"cmd": cmd, "timeout": 1800}  # 30 minutes

    def run(
        self, target: str, args: List[str] = None, label: str = "", log_path: str = None
    ) -> int:
        """Execute gobuster scan and write output to log_path."""

        args = args or []

        # Check gobuster version meets requirements (v3.x+ required for subcommands)
        meets_req, version, error_msg = self._check_version()
        if not meets_req:
            if log_path:
                with open(log_path, "w") as f:
                    f.write(error_msg)
            return 1

        # Detect the mode from args
        mode = None
        if "dir" in args:
            mode = "dir"
        elif "dns" in args:
            mode = "dns"
        elif "vhost" in args:
            mode = "vhost"

        # Validate target and mode compatibility
        if mode == "dns":
            # DNS mode requires a domain name, not an IP or URL
            if target.startswith(("http://", "https://")):
                error_msg = (
                    "ERROR: DNS mode requires a domain name, not a URL.\n\n"
                    f"You provided: {target}\n"
                    "DNS mode enumerates subdomains of a domain.\n\n"
                    "FIXES:\n"
                    "1. For DNS enumeration:\n"
                    "   - Use: souleyez jobs enqueue gobuster <domain>\n"
                    '   - Example: souleyez jobs enqueue gobuster vulnweb.com --args "dns --domain vulnweb.com -w <wordlist>"\n\n'
                    "2. For directory enumeration of an IP/URL:\n"
                    '   - Use: souleyez jobs enqueue gobuster <ip-or-url> --args "dir -u http://<ip> -w <wordlist>"\n'
                    '   - Example: souleyez jobs enqueue gobuster 44.228.249.3 --args "dir -u http://44.228.249.3 -w <wordlist>"\n'
                )
                if log_path:
                    with open(log_path, "w") as f:
                        f.write(error_msg)
                    return 1
                raise ValueError(error_msg)

            # Check if target is an IP address
            ip_pattern = re.compile(r"^(\d{1,3}\.){3}\d{1,3}$")
            if ip_pattern.match(target):
                error_msg = (
                    f"ERROR: DNS mode requires a domain name, not an IP address.\n\n"
                    f"You provided: {target}\n"
                    "DNS mode enumerates subdomains (e.g., admin.example.com).\n"
                    "IP addresses don't have subdomains.\n\n"
                    "FIXES:\n"
                    "1. For directory enumeration of the IP:\n"
                    f'   souleyez jobs enqueue gobuster {target} --args "dir -u http://{target} -w <wordlist>"\n\n'
                    "2. For DNS enumeration (if you have a domain):\n"
                    '   souleyez jobs enqueue gobuster example.com --args "dns --domain example.com -w <wordlist>"\n'
                )
                if log_path:
                    with open(log_path, "w") as f:
                        f.write(error_msg)
                    return 1
                raise ValueError(error_msg)

        elif mode in ["dir", "vhost"]:
            # Dir/vhost modes need a URL with protocol
            if not target.startswith(("http://", "https://")):
                target = f"http://{target}"

            # Validate URL
            try:
                target = validate_url(target)
            except ValidationError as e:
                if log_path:
                    with open(log_path, "w") as f:
                        f.write(f"ERROR: Invalid URL: {e}\n")
                    return 1
                raise ValueError(f"Invalid URL: {e}")

        else:
            # No mode detected, try to handle as URL
            if not target.startswith(("http://", "https://")):
                target = f"http://{target}"

            try:
                target = validate_url(target)
            except ValidationError as e:
                if log_path:
                    with open(log_path, "w") as f:
                        f.write(f"ERROR: Invalid URL: {e}\n")
                    return 1
                raise ValueError(f"Invalid URL: {e}")

        processed_args = [arg.replace("<target>", target) for arg in args]

        # Pre-flight check for dir/vhost modes: detect false positive responses
        if mode in ["dir", "vhost", None]:
            base_url = target
            for i, arg in enumerate(processed_args):
                if arg == "-u" and i + 1 < len(processed_args):
                    base_url = processed_args[i + 1]
                    break

            # Always run preflight - merge detected length with any existing exclusions
            preflight = self._preflight_check(base_url, timeout=5.0, log_path=log_path)
            if preflight["exclude_length"]:
                existing_excludes = set()
                exclude_idx = None
                for i, arg in enumerate(processed_args):
                    if arg == "--exclude-length" and i + 1 < len(processed_args):
                        exclude_idx = i
                        existing_excludes.update(processed_args[i + 1].split(","))

                if preflight["exclude_length"] not in existing_excludes:
                    existing_excludes.add(preflight["exclude_length"])
                    merged = ",".join(sorted(existing_excludes))

                    if exclude_idx is not None:
                        processed_args[exclude_idx + 1] = merged
                    else:
                        processed_args.extend(["--exclude-length", merged])

        # Add --no-progress to suppress verbose progress output (gobuster v3.6+)
        # This prevents thousands of "Progress: X / Y" lines in output
        if "--no-progress" not in processed_args:
            processed_args.append("--no-progress")

        cmd = ["gobuster"] + processed_args

        if not log_path:
            try:
                proc = subprocess.run(
                    cmd, capture_output=True, timeout=300, check=False
                )
                return proc.returncode
            except Exception:
                return 1

        try:
            with open(log_path, "a", encoding="utf-8", errors="replace") as fh:
                fh.write(f"Command: {' '.join(cmd)}\n")
                fh.write(
                    f"Started: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}\n\n"
                )
                fh.flush()

                proc = subprocess.run(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    timeout=300,
                    check=False,
                    text=True,
                )

                output = proc.stdout
                fh.write(output)

                fh.write(
                    f"\nCompleted: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}\n"
                )
                fh.write(f"Exit Code: {proc.returncode}\n")

                # Check for wildcard error in output
                if (
                    proc.returncode == 1
                    and "the server returns a status code that matches"
                    in output.lower()
                ):
                    # Extract details from error message
                    status_match = re.search(r"=> (\d{3})", output)
                    length_match = re.search(r"\(Length: (\d+)\)", output)

                    status_code = status_match.group(1) if status_match else "403"
                    length = length_match.group(1) if length_match else "unknown"

                    fh.write("\n" + "=" * 70 + "\n")
                    fh.write("⚠️  WILDCARD RESPONSE DETECTED\n")
                    fh.write("=" * 70 + "\n\n")
                    fh.write(
                        "The server is returning the same response for all URLs (wildcard).\n"
                    )
                    fh.write(
                        "Gobuster cannot differentiate between real and fake directories.\n\n"
                    )
                    fh.write(f"Detected Response:\n")
                    fh.write(f"  Status Code: {status_code}\n")
                    fh.write(f"  Response Length: {length} bytes\n\n")
                    fh.write("SUGGESTED FIXES:\n")
                    fh.write("  Option 1: Exclude the status code\n")
                    fh.write(f"    Add: -b {status_code}\n\n")
                    fh.write("  Option 2: Exclude the response length\n")
                    fh.write(f"    Add: --exclude-length {length}\n\n")
                    fh.write("  Option 3: Use wildcard mode (force continue)\n")
                    fh.write("    Add: --wildcard\n\n")
                    fh.write("RETRY COMMAND:\n")
                    retry_cmd = cmd.copy()
                    retry_cmd.extend(["-b", status_code])
                    fh.write(f"  {' '.join(retry_cmd)}\n\n")
                    fh.write(
                        "TIP: You can add these flags when configuring the scan in the\n"
                    )
                    fh.write("     interactive menu under 'Additional flags'.\n")
                    fh.write("=" * 70 + "\n")

                # Treat wildcard detection (exit 1) as informational success
                # since we've provided helpful guidance
                return 0 if proc.returncode in [0, 1] else proc.returncode

        except subprocess.TimeoutExpired:
            with open(log_path, "a", encoding="utf-8", errors="replace") as fh:
                fh.write("\nERROR: Gobuster timed out after 300 seconds\n")
            return 124

        except FileNotFoundError:
            with open(log_path, "a", encoding="utf-8", errors="replace") as fh:
                fh.write("\nERROR: gobuster not found in PATH\n")
            return 127

        except Exception as e:
            with open(log_path, "a", encoding="utf-8", errors="replace") as fh:
                fh.write(f"\nERROR: {type(e).__name__}: {e}\n")
            return 1


plugin = GobusterPlugin()
