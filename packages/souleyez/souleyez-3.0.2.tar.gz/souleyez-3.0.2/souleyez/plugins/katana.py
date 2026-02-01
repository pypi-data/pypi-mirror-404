#!/usr/bin/env python3
"""
souleyez.plugins.katana - Web crawling and spidering for parameter discovery

Katana is a next-generation crawling and spidering framework from ProjectDiscovery.
It discovers endpoints, parameters, forms, and JavaScript-rendered routes.
"""

import shutil
import subprocess
from typing import Any, Dict, List, Optional

from souleyez.security.validation import ValidationError, validate_url

from .plugin_base import PluginBase

HELP = {
    "name": "Katana - Web Crawler & Spider",
    "description": (
        "Katana is a fast and configurable web crawler designed for reconnaissance.\n\n"
        "It discovers hidden endpoints, query parameters, forms, and JavaScript-rendered routes "
        "that static tools like gobuster miss. This is essential for finding actual attack surface "
        "before running injection tests with SQLMap.\n\n"
        "Key features:\n"
        "- Headless browser mode for JavaScript-heavy SPAs (React, Angular, Vue)\n"
        "- Automatic parameter extraction from discovered URLs\n"
        "- Form discovery (POST endpoints)\n"
        "- JavaScript parsing for hidden API routes\n"
        "- Configurable crawl depth and scope\n\n"
        "Quick tips:\n"
        "- Default headless mode works best for modern web apps\n"
        "- Use -d to control crawl depth (default: 3)\n"
        "- Results chain automatically to SQLMap for injection testing\n"
    ),
    "usage": "souleyez jobs enqueue katana <target>",
    "examples": [
        "souleyez jobs enqueue katana http://example.com",
        'souleyez jobs enqueue katana http://example.com --args "-d 5"',
        'souleyez jobs enqueue katana http://example.com --args "-no-headless"',
    ],
    "flags": [
        ["-d <depth>", "Maximum crawl depth (default: 3)"],
        ["-headless", "Enable headless browser (default: ON)"],
        ["-no-headless", "Disable headless browser for faster scanning"],
        ["-jc", "Enable JavaScript crawling"],
        ["-timeout <sec>", "Request timeout in seconds (default: 10)"],
        ["-c <num>", "Concurrency level (default: 10)"],
        ["-rl <num>", "Rate limit (requests per second)"],
        ["-scope <regex>", "Regex to filter in-scope URLs"],
        ["-silent", "Suppress banner and info output"],
    ],
    "preset_categories": {
        "crawl_modes": [
            {
                "name": "Standard Crawl",
                "args": ["-d", "3", "-headless", "-jc"],
                "desc": "Default crawl with JavaScript support (recommended)",
            },
            {
                "name": "Deep Crawl",
                "args": ["-d", "5", "-headless", "-jc"],
                "desc": "Deeper crawl for complex applications",
            },
            {
                "name": "Fast Crawl",
                "args": ["-d", "2", "-no-headless"],
                "desc": "Quick scan without headless browser",
            },
            {
                "name": "Aggressive",
                "args": ["-d", "5", "-headless", "-jc", "-c", "20"],
                "desc": "Deep and concurrent crawl",
            },
        ],
        "scope_control": [
            {
                "name": "Same Domain Only",
                "args": ["-headless", "-jc", "-fs", "dn"],
                "desc": "Stay within the same domain",
            },
            {
                "name": "Same Host Only",
                "args": ["-headless", "-jc", "-fs", "sdn"],
                "desc": "Stay on exact subdomain",
            },
        ],
    },
    "presets": [
        {
            "name": "Standard Crawl",
            "args": ["-d", "3", "-headless", "-jc"],
            "desc": "Default crawl with JavaScript support",
        },
        {
            "name": "Deep Crawl",
            "args": ["-d", "5", "-headless", "-jc"],
            "desc": "Thorough crawl for complex apps",
        },
        {
            "name": "Fast (No JS)",
            "args": ["-d", "2", "-no-headless"],
            "desc": "Quick crawl without browser",
        },
    ],
    "help_sections": [
        {
            "title": "How It Fits In The Chain",
            "color": "cyan",
            "content": [
                {
                    "title": "Discovery Flow",
                    "desc": (
                        "1. Gobuster/FFUF find paths (/api, /admin, etc.)\n"
                        "     2. Katana crawls those paths to find parameters\n"
                        "     3. SQLMap tests the parameters for injection\n"
                        "     4. Nuclei scans crawled URLs for other vulns"
                    ),
                }
            ],
        }
    ],
}


class KatanaPlugin(PluginBase):
    name = "Katana"
    tool = "katana"
    category = "vulnerability_analysis"
    HELP = HELP

    def _is_snap_chromium(self) -> bool:
        """
        Check if chromium is installed via snap.

        Snap chromium has sandboxing that breaks headless mode with katana.
        Returns True if chromium path contains 'snap'.
        """
        chromium_binaries = ["chromium", "chromium-browser", "google-chrome", "chrome"]
        for binary in chromium_binaries:
            path = shutil.which(binary)
            if path and "snap" in path:
                return True
        return False

    def _is_arm64_linux(self) -> bool:
        """
        Check if running on ARM64 Linux.

        go-rod (katana's headless library) doesn't have ARM64 chromium binaries
        available for download, so headless mode fails silently on ARM64.
        """
        import platform

        return platform.system() == "Linux" and platform.machine() in (
            "aarch64",
            "arm64",
        )

    def check_tool_available(self) -> tuple:
        """
        Check if katana and chromium are installed.

        Returns:
            (is_available: bool, error_message: str or None)
        """
        # Check katana
        if not shutil.which("katana"):
            return (False, "Katana not found. Install with: sudo apt install katana")

        # Check chromium for headless mode
        chromium_binaries = ["chromium", "chromium-browser", "google-chrome", "chrome"]
        chromium_found = any(shutil.which(b) for b in chromium_binaries)

        if not chromium_found:
            return (
                False,
                "Chromium not found (required for headless mode). Install with: sudo apt install chromium",
            )

        return (True, None)

    def _normalize_target(self, target: str, log_path: str = None) -> Optional[str]:
        """
        Normalize target URL for Katana.

        Katana requires a full URL - bare IPs/domains get http:// prepended.
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

        # Bare IP or domain - prepend http://
        ip_pattern = r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(:\d+)?$"
        domain_pattern = r"^[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?)*$"

        if re.match(ip_pattern, target) or re.match(domain_pattern, target):
            if log_path:
                with open(log_path, "a") as f:
                    f.write(
                        f"NOTE: Converting bare target '{target}' to 'http://{target}'\n"
                    )
            return f"http://{target}"

        return target

    def build_command(
        self, target: str, args: List[str] = None, label: str = "", log_path: str = None
    ) -> Optional[Dict[str, Any]]:
        """
        Build katana command for background execution.

        Args:
            target: Target URL to crawl
            args: Additional command line arguments
            label: Job label
            log_path: Path to write output

        Returns:
            Dict with 'cmd' and 'timeout' keys, or None on error
        """
        args = args or []

        # Normalize target
        target = self._normalize_target(target, log_path)
        if target is None:
            return None

        # Replace <target> placeholder in args
        args = [arg.replace("<target>", target) for arg in args]

        # Build base command
        cmd = ["katana", "-u", target]

        # Force JSONL output for parsing
        if "-jsonl" not in args and "-json" not in args:
            cmd.append("-jsonl")

        # Output to log file
        if log_path and "-o" not in args:
            cmd.extend(["-o", log_path])

        # Add user args
        cmd.extend(args)

        # Set defaults if not specified
        # Headless mode by default - required for proper JavaScript execution
        # However, ARM64 Linux doesn't have go-rod chromium binaries available,
        # so we skip headless mode and rely on JavaScript endpoint extraction instead
        if "-headless" not in args:
            if self._is_arm64_linux():
                # ARM64: go-rod can't find chromium binary, headless silently fails
                # Skip headless mode - the handler will extract endpoints from JS files
                if log_path:
                    with open(log_path, "a") as f:
                        f.write(
                            "NOTE: ARM64 Linux detected, using standard crawl mode. "
                            "API endpoints will be extracted from JavaScript files.\n"
                        )
            else:
                cmd.append("-headless")

        # JavaScript crawling by default
        if "-jc" not in args:
            cmd.append("-jc")

        # Default crawl depth
        if "-d" not in args and "-depth" not in args:
            cmd.extend(["-d", "3"])

        # Request timeout
        if "-timeout" not in args:
            cmd.extend(["-timeout", "10"])

        # Silent mode to reduce noise
        if "-silent" not in args:
            cmd.append("-silent")

        return {"cmd": cmd, "timeout": 1800}  # 30 minutes for crawling

    def run(
        self, target: str, args: List[str] = None, label: str = "", log_path: str = None
    ) -> int:
        """
        Execute katana crawl synchronously.

        Args:
            target: Target URL
            args: Command line arguments
            label: Job label
            log_path: Output file path

        Returns:
            Exit code (0 = success)
        """
        cmd_spec = self.build_command(target, args, label, log_path)
        if cmd_spec is None:
            return 1

        cmd = cmd_spec["cmd"]
        timeout = cmd_spec.get("timeout", 1800)

        try:
            if log_path:
                # Write metadata header
                with open(log_path, "w") as f:
                    f.write(f"=== Plugin: Katana ===\n")
                    f.write(f"Target: {target}\n")
                    f.write(f"Args: {args}\n")
                    f.write(f"Label: {label}\n")
                    f.write(f"Command: {' '.join(cmd)}\n\n")

                # Run katana
                proc = subprocess.run(
                    cmd, capture_output=True, timeout=timeout, check=False
                )

                # Append completion marker
                with open(log_path, "a") as f:
                    f.write(f"\n=== Completed ===\n")
                    f.write(f"Exit Code: {proc.returncode}\n")
                    if proc.stderr:
                        f.write(
                            f"Stderr: {proc.stderr.decode('utf-8', errors='replace')}\n"
                        )

                return proc.returncode
            else:
                proc = subprocess.run(
                    cmd, capture_output=True, timeout=timeout, check=False
                )
                return proc.returncode

        except subprocess.TimeoutExpired:
            if log_path:
                with open(log_path, "a") as f:
                    f.write(f"\nERROR: Crawl timed out after {timeout} seconds\n")
            return 124

        except Exception as e:
            if log_path:
                with open(log_path, "a") as f:
                    f.write(f"\nERROR: {str(e)}\n")
            return 1


# Export plugin instance for auto-discovery
plugin = KatanaPlugin()
