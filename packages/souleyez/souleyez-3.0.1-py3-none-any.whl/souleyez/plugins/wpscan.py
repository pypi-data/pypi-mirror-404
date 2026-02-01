#!/usr/bin/env python3
"""
souleyez.plugins.wpscan

WPScan WordPress vulnerability scanner plugin.
"""

import os
import subprocess
import time
from typing import List
from urllib.parse import urlparse, urlunparse

from souleyez.security.validation import ValidationError, validate_url

from .plugin_base import PluginBase

HELP = {
    "name": "WPScan — WordPress Security Scanner",
    "description": (
        "Found a WordPress site? Time to check for vulnerabilities!\n\n"
        "WPScan is the de-facto WordPress vulnerability scanner. It identifies WordPress version, "
        "installed plugins and themes, security misconfigurations, weak passwords, and known vulnerabilities.\n\n"
        "With over 30% of the web running WordPress, this tool is essential for any web application assessment.\n\n"
        "Quick tips:\n"
        "- Detects WordPress version and checks for known vulnerabilities\n"
        "- Enumerates plugins, themes, and users\n"
        "- Tests for common misconfigurations and weak passwords\n"
        "- Uses WPVulnDB for vulnerability information\n"
        "- Can perform brute-force attacks on wp-login.php\n"
    ),
    "usage": "souleyez jobs enqueue wpscan <url>",
    "examples": [
        "souleyez jobs enqueue wpscan http://example.com",
        'souleyez jobs enqueue wpscan http://example.com --args "--enumerate vp"',
        'souleyez jobs enqueue wpscan http://example.com --args "--enumerate u,ap,at"',
        'souleyez jobs enqueue wpscan http://example.com --args "--passwords data/wordlists/top100.txt"',
    ],
    "flags": [
        [
            "--enumerate <opts>",
            "Enumerate: u (users), p (plugins), t (themes), vp (vulnerable plugins), vt (vulnerable themes)",
        ],
        ["--plugins-detection <mode>", "Detection mode: mixed, passive, aggressive"],
        ["--passwords <file>", "Password list for brute-force attacks"],
        ["--usernames <list>", "Usernames to use for brute-force (comma-separated)"],
        ["--random-user-agent", "Use random user-agent for requests"],
        ["--force", "Do not check if the target is running WordPress"],
        ["--api-token <token>", "WPVulnDB API token for vulnerability data"],
    ],
    "presets": [
        {
            "name": "Quick Scan",
            "args": ["--random-user-agent"],
            "desc": "Basic WordPress detection and version check",
        },
        {
            "name": "Full Enumeration",
            "args": ["--enumerate", "ap,at,u", "--random-user-agent"],
            "desc": "Enumerate all plugins, themes, and users",
        },
        {
            "name": "Vulnerable Plugins",
            "args": [
                "--enumerate",
                "vp",
                "--plugins-detection",
                "aggressive",
                "--random-user-agent",
            ],
            "desc": "Find vulnerable plugins only",
        },
        {
            "name": "User Enumeration",
            "args": ["--enumerate", "u", "--random-user-agent"],
            "desc": "Enumerate WordPress users",
        },
    ],
    "help_sections": [
        {
            "title": "What is WPScan?",
            "color": "cyan",
            "content": [
                {
                    "title": "Overview",
                    "desc": "WPScan is the de-facto WordPress vulnerability scanner, identifying WordPress version, plugins, themes, misconfigurations, and known vulnerabilities.",
                },
                {
                    "title": "Use Cases",
                    "desc": "Essential for WordPress security assessments",
                    "tips": [
                        "Detect WordPress version and vulnerabilities",
                        "Enumerate installed plugins and themes",
                        "Find security misconfigurations",
                        "Test for weak passwords via brute-force",
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
                    "desc": "1. Run quick scan to detect WordPress version\n     2. Enumerate vulnerable plugins/themes (vp,vt)\n     3. Check for users and misconfigurations\n     4. Test weak passwords if authorized",
                },
                {
                    "title": "Enumeration Options",
                    "desc": "Key flags for different scans",
                    "tips": [
                        "vp: Vulnerable plugins only",
                        "ap: All plugins (slow but thorough)",
                        "u: User enumeration",
                        "--passwords: Brute-force password file",
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
                        "Always use --random-user-agent to avoid detection",
                        "Start with vulnerable plugins/themes only (vp,vt)",
                        "Use WPVulnDB API token for full vulnerability data",
                        "Document outdated plugins as security findings",
                        "Test password lists only with explicit authorization",
                    ],
                ),
                (
                    "Common Issues:",
                    [
                        "Not WordPress site: Verify URL is a WordPress installation",
                        "Rate limiting: Add delays or reduce enumeration scope",
                        "No vulnerabilities found: Update WPScan or use API token",
                        "Enumeration blocked: Some hosts block automated scanners",
                    ],
                ),
            ],
        },
    ],
}


class WpscanPlugin(PluginBase):
    name = "WPScan"
    tool = "wpscan"
    category = "vulnerability_analysis"
    HELP = HELP

    def _get_base_url(self, url: str) -> str:
        """
        Extract WordPress root URL from a full URL.

        WPScan needs the WordPress root URL, not subpaths like /wp-content.
        For WordPress in subdirectories, we preserve the parent path.

        Examples:
            http://10.0.0.48/wp-content → http://10.0.0.48/
            http://10.0.0.48/blogblog/wp-admin/ → http://10.0.0.48/blogblog/
            http://10.0.0.48/site/wordpress/wp-includes/ → http://10.0.0.48/site/wordpress/
        """
        parsed = urlparse(url)
        path = parsed.path

        # WordPress subdirectory patterns to strip
        # These indicate we're inside the WordPress installation
        wp_subpaths = ["/wp-admin", "/wp-content", "/wp-includes", "/wp-login.php"]

        # Find and strip WordPress-specific subpaths
        for wp_sub in wp_subpaths:
            idx = path.lower().find(wp_sub.lower())
            if idx != -1:
                # Keep everything before the WordPress subpath
                path = path[:idx]
                break

        # Ensure path ends with /
        if not path.endswith("/"):
            path = path + "/"

        # If path is empty, use root
        if not path:
            path = "/"

        base = urlunparse((parsed.scheme, parsed.netloc, path, "", "", ""))
        return base

    def _fix_enumerate_args(self, args: List[str]) -> List[str]:
        """
        Fix incompatible WPScan enumerate options.

        WPScan has mutually exclusive options:
        - vp (vulnerable plugins) and ap (all plugins) cannot be used together
        - vt (vulnerable themes) and at (all themes) cannot be used together

        If both are present, prefer the vulnerable-only option (vp/vt) as it's
        faster and more focused.
        """
        new_args = []
        i = 0
        while i < len(args):
            arg = args[i]
            if arg == "--enumerate" and i + 1 < len(args):
                enum_value = args[i + 1]
                # Parse the enumerate options
                options = [opt.strip() for opt in enum_value.split(",")]

                # Fix incompatible options
                # If both vp and ap, remove ap (prefer vulnerable-only)
                if "vp" in options and "ap" in options:
                    options.remove("ap")
                # If both vt and at, remove at (prefer vulnerable-only)
                if "vt" in options and "at" in options:
                    options.remove("at")

                # Rebuild enumerate value
                new_args.append("--enumerate")
                new_args.append(",".join(options))
                i += 2
            else:
                new_args.append(arg)
                i += 1

        return new_args

    def build_command(
        self, target: str, args: List[str] = None, label: str = "", log_path: str = None
    ):
        """Build command for background execution with PID tracking."""
        if not target:
            if log_path:
                with open(log_path, "w") as f:
                    f.write("ERROR: Target URL is required\n")
            return None

        # Ensure URL format
        if not target.startswith("http://") and not target.startswith("https://"):
            target = f"http://{target}"

        # Validate URL
        try:
            target = validate_url(target)
        except ValidationError as e:
            if log_path:
                with open(log_path, "w") as f:
                    f.write(f"ERROR: Invalid URL: {e}\n")
            return None

        # Strip path to get base URL (WPScan needs WordPress root, not subpaths)
        original_target = target
        target = self._get_base_url(target)

        args = args or []

        # Fix incompatible enumerate options (vp/ap, vt/at are mutually exclusive)
        # vp = vulnerable plugins, ap = all plugins (can't use both)
        # vt = vulnerable themes, at = all themes (can't use both)
        args = self._fix_enumerate_args(args)

        # Add --disable-tls-checks for HTTPS targets (handles self-signed certs)
        if target.startswith("https://") and "--disable-tls-checks" not in args:
            args = ["--disable-tls-checks"] + args

        # Auto-add API token from environment if not already specified
        if "--api-token" not in " ".join(args):
            api_token = os.environ.get("WPSCAN_API_TOKEN")
            if api_token:
                args = ["--api-token", api_token] + args

        # wpscan uses --url flag
        cmd = ["wpscan", "--url", target] + args

        # Log if we modified the URL
        if log_path and original_target != target:
            with open(log_path, "w") as f:
                f.write(
                    f"INFO: Using base URL {target} (original: {original_target})\n\n"
                )

        return {"cmd": cmd, "timeout": 1800}

    def run(
        self, target: str, args: List[str] = None, label: str = "", log_path: str = None
    ) -> int:
        """
        Execute WPScan and write output to log_path.
        """
        if not target:
            raise ValueError("Target URL is required")

        # Ensure URL format
        if not target.startswith("http://") and not target.startswith("https://"):
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

        # Strip path to get base URL (WPScan needs WordPress root, not subpaths)
        target = self._get_base_url(target)

        if args is None:
            args = []

        # Fix incompatible enumerate options (vp/ap, vt/at are mutually exclusive)
        args = self._fix_enumerate_args(args)

        # Add --disable-tls-checks for HTTPS targets (handles self-signed certs)
        if target.startswith("https://") and "--disable-tls-checks" not in args:
            args = ["--disable-tls-checks"] + args

        # Auto-add API token from environment if not already specified
        if "--api-token" not in " ".join(args):
            api_token = os.environ.get("WPSCAN_API_TOKEN")
            if api_token:
                args = ["--api-token", api_token] + args

        cmd = ["wpscan", "--url", target] + args

        if log_path:
            # Redact API token from logged command
            logged_cmd = []
            skip_next = False
            for arg in cmd:
                if skip_next:
                    logged_cmd.append("[REDACTED]")
                    skip_next = False
                elif arg == "--api-token":
                    logged_cmd.append(arg)
                    skip_next = True
                else:
                    logged_cmd.append(arg)

            with open(log_path, "w") as f:
                f.write(f"# WPScan for {target}\n")
                f.write(f"# Command: {' '.join(logged_cmd)}\n")
                f.write(f"# Started: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=600  # 10 minutes
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
                    f.write("\n\n# ERROR: Command timed out after 10 minutes\n")
            return 124
        except Exception as e:
            if log_path:
                with open(log_path, "a") as f:
                    f.write(f"\n\n# ERROR: {str(e)}\n")
            return 1


# Export plugin instance
plugin = WpscanPlugin()
