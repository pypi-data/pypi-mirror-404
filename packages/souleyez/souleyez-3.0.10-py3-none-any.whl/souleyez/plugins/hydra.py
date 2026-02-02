#!/usr/bin/env python3
"""
souleyez.plugins.hydra

Hydra network login brute-forcer plugin.
"""

import subprocess
import time
from typing import List
from urllib.parse import urlparse

from souleyez.security.validation import ValidationError, validate_target

from .plugin_base import PluginBase

HELP = {
    "name": "Hydra — Network Login Brute-Forcer",
    "description": (
        "Got credentials to test? Need to brute-force a login?\n\n"
        "Hydra is one of the fastest network login crackers, supporting numerous protocols including "
        "SSH, FTP, HTTP, SMB, RDP, and many more. Perfect for testing weak passwords and credential reuse.\n\n"
        "It's a parallelized login cracker that can test thousands of username/password combinations "
        "across multiple protocols simultaneously.\n\n"
        "Quick tips:\n"
        "- Supports 50+ protocols (SSH, FTP, Telnet, HTTP, SMB, RDP, etc.)\n"
        "- Fast parallel attack with configurable threads\n"
        "- Can use username/password lists or single credentials\n"
        "- Useful for testing credential reuse across services\n"
        "- Be cautious: aggressive brute-forcing may lock accounts\n"
    ),
    "usage": 'souleyez jobs enqueue hydra <target> --args "<service> -l <user> -p <pass>"',
    "examples": [
        'souleyez jobs enqueue hydra 192.168.1.10 --args "ssh -l admin -P data/wordlists/top100.txt"',
        'souleyez jobs enqueue hydra 192.168.1.10 --args "ftp -L data/wordlists/all_users.txt -P data/wordlists/top100.txt"',
        'souleyez jobs enqueue hydra 192.168.1.10 --args "smb -l administrator -p password123"',
        "souleyez jobs enqueue hydra example.com --args \"http-post-form '/login.php:username=^USER^&password=^PASS^:F=incorrect' -L data/wordlists/all_users.txt -P data/wordlists/top100.txt\"",
    ],
    "flags": [
        ["-l <user>", "Single username"],
        ["-L <file>", "Username list file"],
        ["-p <pass>", "Single password"],
        ["-P <file>", "Password list file"],
        ["-t <tasks>", "Number of parallel tasks (default 16)"],
        ["-V", "Verbose mode - show login attempts"],
        ["-f", "Exit when login/pass pair is found"],
        ["-s <port>", "Custom port number"],
        ["-e nsr", "Try: n=null password, s=login as password, r=reversed login"],
    ],
    "preset_categories": {
        "ssh": [
            {
                "name": "SSH Brute-Force",
                "args": [
                    "ssh",
                    "-l",
                    "root",
                    "-P",
                    "data/wordlists/top100.txt",
                    "-t",
                    "1",
                    "-w",
                    "3",
                    "-vV",
                ],
                "desc": "Username(s) + password list (1 thread, 3s delay)",
            },
            {
                "name": "SSH Password Spray",
                "args": [
                    "ssh",
                    "-L",
                    "users.txt",
                    "-p",
                    "Password123!",
                    "-t",
                    "1",
                    "-w",
                    "5",
                    "-vV",
                ],
                "desc": "One password against user list (stealthy)",
            },
            {
                "name": "SSH Quick Check",
                "args": [
                    "ssh",
                    "-L",
                    "users.txt",
                    "-e",
                    "ns",
                    "-t",
                    "4",
                    "-w",
                    "1",
                    "-vV",
                ],
                "desc": "Empty + username-as-password",
            },
        ],
        "ftp": [
            {
                "name": "FTP Anonymous",
                "args": [
                    "ftp",
                    "-l",
                    "anonymous",
                    "-p",
                    "anonymous@",
                    "-t",
                    "1",
                    "-vV",
                ],
                "desc": "Test anonymous login",
            },
            {
                "name": "FTP Brute-Force",
                "args": [
                    "ftp",
                    "-L",
                    "users.txt",
                    "-P",
                    "passwords.txt",
                    "-t",
                    "2",
                    "-w",
                    "1",
                    "-vV",
                ],
                "desc": "Username(s) + password list (2 threads, 1s delay)",
            },
            {
                "name": "FTP Quick Check",
                "args": [
                    "ftp",
                    "-L",
                    "users.txt",
                    "-e",
                    "ns",
                    "-t",
                    "4",
                    "-w",
                    "1",
                    "-vV",
                ],
                "desc": "Empty + username-as-password",
            },
        ],
        "smb": [
            {
                "name": "SMB Brute-Force",
                "args": [
                    "smb",
                    "-l",
                    "administrator",
                    "-P",
                    "data/wordlists/top100.txt",
                    "-t",
                    "1",
                    "-w",
                    "2",
                    "-vV",
                ],
                "desc": "Username(s) + password list (1 thread, 2s delay)",
            },
            {
                "name": "SMB Quick Check",
                "args": [
                    "smb",
                    "-L",
                    "users.txt",
                    "-e",
                    "ns",
                    "-t",
                    "2",
                    "-w",
                    "1",
                    "-vV",
                ],
                "desc": "Empty + username-as-password",
            },
        ],
        "http": [
            {
                "name": "HTTP Basic Auth",
                "args": [
                    "http-get",
                    "/admin",
                    "-l",
                    "admin",
                    "-P",
                    "passwords.txt",
                    "-t",
                    "2",
                    "-vV",
                ],
                "desc": "Username(s) + password list (2 threads)",
            }
        ],
        "wordpress": [
            {
                "name": "WP Username Enum",
                "args": [
                    "-L",
                    "users.txt",
                    "-p",
                    "test",
                    "-t",
                    "2",
                    "-w",
                    "2",
                    "-vV",
                    "http-post-form",
                    "/wp-login.php:log=^USER^&pwd=^PASS^&wp-submit=Log+In:F=Invalid username",
                ],
                "desc": "Find valid usernames (reports success if username exists)",
            },
            {
                "name": "WP Password Attack",
                "args": [
                    "-l",
                    "admin",
                    "-P",
                    "data/wordlists/top100.txt",
                    "-t",
                    "2",
                    "-w",
                    "2",
                    "-vV",
                    "http-post-form",
                    "/wp-login.php:log=^USER^&pwd=^PASS^&wp-submit=Log+In:F=is incorrect",
                ],
                "desc": "Crack password for known user",
            },
            {
                "name": "WP Password Spray",
                "args": [
                    "-L",
                    "users.txt",
                    "-p",
                    "Password123!",
                    "-t",
                    "1",
                    "-w",
                    "3",
                    "-vV",
                    "http-post-form",
                    "/wp-login.php:log=^USER^&pwd=^PASS^&wp-submit=Log+In:F=is incorrect",
                ],
                "desc": "One password against known users",
            },
            {
                "name": "WP Quick Check",
                "args": [
                    "-L",
                    "users.txt",
                    "-e",
                    "ns",
                    "-t",
                    "2",
                    "-w",
                    "2",
                    "-vV",
                    "http-post-form",
                    "/wp-login.php:log=^USER^&pwd=^PASS^&wp-submit=Log+In:F=is incorrect",
                ],
                "desc": "Empty + username-as-password on known users",
            },
        ],
    },
    "presets": [
        # Flattened for backward compatibility
        {
            "name": "SSH Brute-Force",
            "args": [
                "ssh",
                "-l",
                "root",
                "-P",
                "data/wordlists/top100.txt",
                "-t",
                "4",
                "-vV",
            ],
            "desc": "SSH brute-force with wordlist",
        },
        {
            "name": "FTP Anonymous",
            "args": ["ftp", "-l", "anonymous", "-p", "anonymous@", "-t", "1", "-vV"],
            "desc": "Test FTP anonymous login",
        },
        {
            "name": "SMB Brute-Force",
            "args": [
                "smb",
                "-l",
                "administrator",
                "-P",
                "data/wordlists/top100.txt",
                "-t",
                "2",
                "-vV",
            ],
            "desc": "SMB brute-force with wordlist",
        },
        # Router Brute-Force
        {
            "name": "Router HTTP Basic",
            "args": [
                "http-get",
                "/",
                "-L",
                "data/wordlists/router_users.txt",
                "-P",
                "data/wordlists/router_passwords.txt",
                "-t",
                "2",
                "-w",
                "3",
                "-vV",
                "-f",
            ],
            "desc": "Router web admin (HTTP Basic Auth)",
        },
        {
            "name": "Router SSH",
            "args": [
                "ssh",
                "-L",
                "data/wordlists/router_users.txt",
                "-P",
                "data/wordlists/router_passwords.txt",
                "-t",
                "1",
                "-w",
                "5",
                "-vV",
                "-f",
            ],
            "desc": "Router SSH login",
        },
        {
            "name": "Router Telnet",
            "args": [
                "telnet",
                "-L",
                "data/wordlists/router_users.txt",
                "-P",
                "data/wordlists/router_passwords.txt",
                "-t",
                "2",
                "-w",
                "3",
                "-vV",
                "-f",
            ],
            "desc": "Router Telnet login",
        },
        # macOS Brute-Force
        {
            "name": "macOS SSH",
            "args": [
                "ssh",
                "-L",
                "data/wordlists/macos_users.txt",
                "-P",
                "data/wordlists/top100.txt",
                "-t",
                "1",
                "-w",
                "5",
                "-vV",
                "-f",
            ],
            "desc": "macOS Remote Login",
        },
        {
            "name": "AFP Brute",
            "args": [
                "afp",
                "-L",
                "data/wordlists/macos_users.txt",
                "-P",
                "data/wordlists/top100.txt",
                "-s",
                "548",
                "-t",
                "2",
                "-w",
                "3",
                "-vV",
                "-f",
            ],
            "desc": "Apple File Sharing login",
        },
        {
            "name": "VNC Brute",
            "args": [
                "vnc",
                "-P",
                "data/wordlists/vnc_passwords.txt",
                "-s",
                "5900",
                "-t",
                "2",
                "-w",
                "3",
                "-vV",
                "-f",
            ],
            "desc": "VNC/Screen Sharing password",
        },
    ],
    "help_sections": [
        {
            "title": "What is Hydra?",
            "color": "cyan",
            "content": [
                {
                    "title": "Overview",
                    "desc": "Hydra is one of the fastest network login crackers, supporting 50+ protocols including SSH, FTP, HTTP, SMB, RDP, and many more.",
                },
                {
                    "title": "Use Cases",
                    "desc": "Test weak passwords and credential reuse",
                    "tips": [
                        "Brute-force network service logins",
                        "Test password policies and lockout thresholds",
                        "Validate credential reuse across services",
                        "Check for default/weak passwords",
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
                    "desc": "1. Select target service (ssh, ftp, smb, http, etc.)\n     2. Choose attack mode (single user or user list)\n     3. Set low thread count to avoid lockouts\n     4. Monitor for successful credentials",
                },
                {
                    "title": "Attack Modes",
                    "desc": "Different credential testing strategies",
                    "tips": [
                        "Single user: -l user -P passwords.txt",
                        "User list: -L users.txt -P passwords.txt",
                        "Password spray: -L users.txt -p Password123!",
                        "Username as password: -e s (user:user)",
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
                        "Use low thread counts (-t 1-4) to avoid lockouts",
                        "Add delays (-w 2-5) between attempts",
                        "Try username as password first (-e s)",
                        "Password spray (one password, many users) is stealthier",
                        "Stop on first success (-f) to minimize impact",
                    ],
                ),
                (
                    "Common Issues:",
                    [
                        "Account lockouts: Reduce -t threads and add -w delay",
                        "Too slow: Increase threads or reduce wordlist",
                        "Connection refused: Verify service is running",
                        "No results: Check credentials format and service type",
                    ],
                ),
            ],
        },
    ],
}


class HydraPlugin(PluginBase):
    name = "Hydra"
    tool = "hydra"
    category = "exploitation"
    HELP = HELP

    def _check_ssh_password_auth(self, host: str, port: int = 22) -> tuple:
        """
        Check if SSH server supports password authentication.

        Returns:
            Tuple of (supports_password: bool, message: str)
        """
        import subprocess

        try:
            # Use ssh -o with PreferredAuthentications to test
            # If password auth is disabled, SSH will fail with specific error
            result = subprocess.run(
                [
                    "ssh",
                    "-o",
                    "BatchMode=yes",
                    "-o",
                    "ConnectTimeout=5",
                    "-o",
                    "PreferredAuthentications=password",
                    "-o",
                    "StrictHostKeyChecking=no",
                    "-o",
                    "UserKnownHostsFile=/dev/null",
                    "-p",
                    str(port),
                    f"root@{host}",
                    "exit",
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )

            stderr = result.stderr.lower()

            # Check for common error messages
            if "permission denied" in stderr:
                # Password auth is available but wrong password
                return True, "Password authentication available"
            elif "no more authentication methods" in stderr:
                return False, "Password authentication disabled (key-only)"
            elif "connection refused" in stderr:
                return False, "SSH connection refused (service not running?)"
            elif "connection timed out" in stderr or "timed out" in stderr:
                return False, "SSH connection timed out"
            elif "could not resolve" in stderr or "no route" in stderr:
                return False, "Cannot reach host"
            else:
                # Assume password auth is available if we can't determine otherwise
                return True, "Password authentication likely available"

        except subprocess.TimeoutExpired:
            return False, "SSH connection timed out"
        except FileNotFoundError:
            # ssh command not found - can't check, assume yes
            return True, "Cannot verify (ssh not found)"
        except Exception as e:
            return True, f"Cannot verify: {e}"

    def _is_http_service(self, args: List[str]) -> bool:
        """Check if args contain HTTP/HTTPS service."""
        http_services = {
            "http-get",
            "http-post",
            "http-head",
            "http-get-form",
            "http-post-form",
            "https-get",
            "https-post",
            "https-head",
            "https-get-form",
            "https-post-form",
            "http-proxy",
        }
        return any(arg in http_services for arg in args)

    def _inject_path_into_args(self, args: List[str], path: str) -> List[str]:
        """
        Inject URL path into HTTP service arguments.

        For http-get/https-get: Add path after service name
        For http-post-form/https-post-form: Insert at beginning of form string

        Args:
            args: Original args list
            path: URL path to inject (e.g., '/wp-login.php')

        Returns:
            Modified args list with path injected
        """
        if not path or path == "/":
            return args  # No path to inject

        new_args = []
        form_services = {
            "http-post-form",
            "https-post-form",
            "http-get-form",
            "https-get-form",
        }
        get_services = {
            "http-get",
            "https-get",
            "http-post",
            "https-post",
            "http-head",
            "https-head",
        }

        i = 0
        while i < len(args):
            arg = args[i]

            # Handle http-get style services
            if arg in get_services:
                new_args.append(arg)
                # Check if next arg is already a path
                if i + 1 < len(args) and args[i + 1].startswith("/"):
                    # Path already exists, don't inject
                    new_args.append(args[i + 1])
                    i += 2
                else:
                    # Inject path after service name
                    new_args.append(path)
                    i += 1

            # Handle http-post-form style services
            elif arg in form_services:
                new_args.append(arg)
                # Next arg should be the form string
                if i + 1 < len(args):
                    form_string = args[i + 1]
                    # Strip quotes for checking
                    cleaned_check = form_string.lstrip("'\"")

                    if cleaned_check.startswith("/"):
                        # Form string has absolute path (e.g., /wp-login.php:...)
                        # Combine URL base path with form path for subpath installs
                        # e.g., URL path=/blogblog/ + form=/wp-login.php -> /blogblog/wp-login.php
                        if path != "/" and not path.endswith("/"):
                            path = path + "/"

                        # Extract form path and rest
                        if ":" in cleaned_check:
                            form_path, rest = cleaned_check.split(":", 1)
                        else:
                            form_path = cleaned_check
                            rest = ""

                        # Combine paths: /blogblog/ + /wp-login.php -> /blogblog/wp-login.php
                        # Strip trailing slash from URL path and leading slash from form path
                        combined_path = path.rstrip("/") + form_path
                        form_string = (
                            f"{combined_path}:{rest}" if rest else combined_path
                        )
                    else:
                        # No absolute path - inject URL path at beginning
                        cleaned = form_string.lstrip("':\"")
                        form_string = f"{path}:{cleaned}"

                    new_args.append(form_string)
                    i += 2
                else:
                    i += 1
            else:
                new_args.append(arg)
                i += 1

        return new_args

    def _parse_url_for_hydra(self, url: str) -> dict:
        """Parse URL and extract components for Hydra."""
        try:
            parsed = urlparse(url)
        except Exception as e:
            raise ValidationError(f"Failed to parse URL: {e}")

        if not parsed.scheme or not parsed.netloc:
            raise ValidationError(
                f"Invalid URL format: {url}. "
                "Must include scheme and host (e.g., http://example.com)"
            )

        host = parsed.hostname
        if not host:
            raise ValidationError(f"Could not extract hostname from URL: {url}")

        port = parsed.port
        if port is None:
            port = 443 if parsed.scheme == "https" else 80

        path = parsed.path or ""
        if parsed.query:
            path += f"?{parsed.query}"

        is_default = (parsed.scheme == "http" and port == 80) or (
            parsed.scheme == "https" and port == 443
        )

        return {
            "host": host,
            "port": port,
            "path": path,
            "scheme": parsed.scheme,
            "is_default_port": is_default,
        }

    def _parse_host_port(self, target: str) -> tuple:
        """
        Parse host:port format and return (host, port).

        Args:
            target: Target string (may be IP, hostname, IP:port, or hostname:port)

        Returns:
            Tuple of (host, port) where port may be None
        """
        import re

        # Check for IPv6 with port: [::1]:8080
        ipv6_port_match = re.match(r"^\[([^\]]+)\]:(\d+)$", target)
        if ipv6_port_match:
            return ipv6_port_match.group(1), int(ipv6_port_match.group(2))

        # Check for IPv6 without port: ::1 or [::1]
        if ":" in target and not target.count(":") == 1:
            # Multiple colons = IPv6, strip brackets if present
            return target.strip("[]"), None

        # Check for host:port format (single colon)
        if ":" in target:
            parts = target.rsplit(":", 1)
            host = parts[0]
            try:
                port = int(parts[1])
                if 1 <= port <= 65535:
                    return host, port
            except ValueError:
                pass

        # No port found
        return target, None

    def build_command(
        self, target: str, args: List[str] = None, label: str = "", log_path: str = None
    ):
        """Build Hydra command for background execution with PID tracking."""
        if not target:
            if log_path:
                with open(log_path, "w") as f:
                    f.write("ERROR: Target host is required\n")
            return None

        if args is None:
            args = []

        # Handle host:port format (e.g., 10.0.0.73:80)
        # Extract port and add -s flag if not already present
        extracted_port = None
        if not target.startswith(("http://", "https://")):
            host, port = self._parse_host_port(target)
            if port is not None:
                target = host  # Use just the host part
                extracted_port = port
                # Add -s PORT if not already in args
                if "-s" not in args:
                    args = ["-s", str(port)] + args
                    if log_path:
                        with open(log_path, "a") as f:
                            f.write(
                                f"INFO: Extracted port {port} from target, using -s flag\n\n"
                            )

        # Handle URL parsing for HTTP services
        if args and self._is_http_service(args):
            # Check for URL format (single target only)
            if target.startswith(("http://", "https://")):
                # Reject if multiple targets
                if " " in target:
                    if log_path:
                        with open(log_path, "w") as f:
                            f.write(
                                "ERROR: URL format not supported with multiple targets\n"
                            )
                            f.write(
                                "For multi-target attacks, use hostnames/IPs without URLs\n"
                            )
                    return None

                # Parse URL
                try:
                    parsed = self._parse_url_for_hydra(target)
                except ValidationError as e:
                    if log_path:
                        with open(log_path, "w") as f:
                            f.write(f"ERROR: {e}\n")
                    return None

                # Replace target with extracted host
                target = parsed["host"]

                # Inject -s PORT if non-default and -s not already in args
                if not parsed["is_default_port"]:
                    if "-s" not in args:
                        args = ["-s", str(parsed["port"])] + args
                    elif log_path:
                        # Warn about port conflict
                        with open(log_path, "a") as f:
                            f.write(f"INFO: Port conflict detected\n")
                            f.write(f"  URL port: {parsed['port']}\n")
                            f.write(
                                f"  Using -s flag value (explicit flag takes precedence)\n\n"
                            )

                # Inject path into args if present
                if parsed["path"] and parsed["path"] != "/":
                    args = self._inject_path_into_args(args, parsed["path"])
                    if log_path:
                        with open(log_path, "a") as f:
                            f.write(
                                f"INFO: Auto-injected path from URL: {parsed['path']}\n\n"
                            )

        elif target.startswith(("http://", "https://")):
            # URL provided but not HTTP service - reject
            if log_path:
                with open(log_path, "w") as f:
                    f.write(
                        "ERROR: URL format only supported for HTTP/HTTPS services\n"
                    )
                    f.write(f"Target: {target}\n")
                    f.write(
                        "For HTTP services, use: http-get, http-post, http-post-form, etc.\n"
                    )
                    f.write(
                        "For non-HTTP services (ssh, ftp, smb), use hostname or IP only\n"
                    )
            return None

        # Handle multiple targets (space-separated)
        targets = target.split()
        validated_targets = []

        try:
            for t in targets:
                validated_targets.append(validate_target(t.strip()))
        except ValidationError as e:
            if log_path:
                with open(log_path, "w") as f:
                    f.write(f"ERROR: Invalid target: {e}\n")
            return None

        # If multiple targets, create a temporary file and use -M flag
        import os
        import tempfile

        # Hydra syntax: hydra [OPTIONS] target service [SERVICE-OPTIONS]
        # Need to split args into: global options, service type, and service options
        global_opts = []
        service_type = None
        service_opts = []

        i = 0
        while i < len(args):
            arg = args[i]
            # Service types (these go after target)
            if arg in [
                "ssh",
                "ftp",
                "smb",
                "rdp",
                "telnet",
                "vnc",
                "mysql",
                "postgres",
                "mssql",
                "oracle",
                "http-get",
                "http-post",
                "http-head",
                "http-get-form",
                "http-post-form",
                "https-get",
                "https-post",
                "https-head",
                "https-get-form",
                "https-post-form",
                "http-proxy",
            ]:
                service_type = arg
                # Everything after service type is service options
                service_opts = args[i + 1 :]
                break
            else:
                # Global options (go before target)
                global_opts.append(arg)
                i += 1

        # Add legacy SSH algorithm support for older servers
        if service_type == "ssh":
            # Check if SSH supports password authentication before wasting time
            ssh_port = extracted_port or 22
            # Find -s port in args if specified
            for i, arg in enumerate(global_opts):
                if arg == "-s" and i + 1 < len(global_opts):
                    try:
                        ssh_port = int(global_opts[i + 1])
                    except ValueError:
                        pass
                    break

            # Check first target for password auth support
            check_host = validated_targets[0] if validated_targets else target
            supports_password, msg = self._check_ssh_password_auth(check_host, ssh_port)

            if not supports_password:
                if log_path:
                    with open(log_path, "w") as f:
                        f.write(f"ERROR: SSH brute-force aborted: {msg}\n")
                        f.write(f"Target: {check_host}:{ssh_port}\n")
                        f.write(
                            "\nThe SSH server does not support password authentication.\n"
                        )
                        f.write(
                            "Password brute-forcing is not possible on key-only SSH servers.\n"
                        )
                return None

            if log_path:
                with open(log_path, "a") as f:
                    f.write(f"INFO: SSH password auth check: {msg}\n\n")

        if len(validated_targets) > 1:
            # Create temp file with targets
            fd, temp_target_file = tempfile.mkstemp(
                suffix=".txt", prefix="hydra_targets_"
            )
            try:
                with os.fdopen(fd, "w") as f:
                    f.write("\n".join(validated_targets))

                # Build: hydra [global_opts] -M target_file service [service_opts]
                cmd = ["hydra"] + global_opts + ["-M", temp_target_file]
                if service_type:
                    cmd += [service_type] + service_opts
            except Exception as e:
                os.unlink(temp_target_file)
                if log_path:
                    with open(log_path, "w") as f:
                        f.write(f"ERROR: Failed to create target file: {e}\n")
                return None
        else:
            # Build: hydra [global_opts] target service [service_opts]
            cmd = ["hydra"] + global_opts + [validated_targets[0]]
            if service_type:
                cmd += [service_type] + service_opts

        return {"cmd": cmd, "timeout": 3600}  # 1 hour timeout

    def run(
        self, target: str, args: List[str] = None, label: str = "", log_path: str = None
    ) -> int:
        """
        Execute Hydra and write output to log_path.
        """
        if not target:
            raise ValueError("Target host is required")

        if args is None:
            args = []

        # Handle host:port format (e.g., 10.0.0.73:80)
        if not target.startswith(("http://", "https://")):
            host, port = self._parse_host_port(target)
            if port is not None:
                target = host
                if "-s" not in args:
                    args = ["-s", str(port)] + args

        # Handle multiple targets (space-separated)
        targets = target.split()
        validated_targets = []

        try:
            for t in targets:
                # Also parse host:port for each target in multi-target mode
                h, p = self._parse_host_port(t.strip())
                validated_targets.append(validate_target(h))
        except ValidationError as e:
            if log_path:
                with open(log_path, "w") as f:
                    f.write(f"ERROR: Invalid target: {e}\n")
                return 1
            raise ValueError(f"Invalid target: {e}")

        # If multiple targets, create a temporary file and use -M flag
        import os
        import tempfile

        if len(validated_targets) > 1:
            # Create temp file with targets
            fd, temp_target_file = tempfile.mkstemp(
                suffix=".txt", prefix="hydra_targets_"
            )
            try:
                with os.fdopen(fd, "w") as f:
                    f.write("\n".join(validated_targets))

                cmd = ["hydra", "-M", temp_target_file] + args
                target_display = " ".join(validated_targets)
            except Exception as e:
                os.unlink(temp_target_file)
                raise e
        else:
            # Single target - use normal syntax
            cmd = ["hydra", validated_targets[0]] + args
            target_display = validated_targets[0]
            temp_target_file = None

        if log_path:
            with open(log_path, "w") as f:
                f.write(f"# Hydra attack on {target_display}\n")
                f.write(f"# Command: {' '.join(cmd)}\n")
                f.write(f"# Started: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=3600  # 1 hour
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
                    f.write("\n\n# ERROR: Command timed out after 1 hour\n")
            return 124
        except Exception as e:
            if log_path:
                with open(log_path, "a") as f:
                    f.write(f"\n\n# ERROR: {str(e)}\n")
            return 1
        finally:
            # Clean up temp file if created
            if temp_target_file and os.path.exists(temp_target_file):
                try:
                    os.unlink(temp_target_file)
                except:
                    pass


# Export plugin instance
plugin = HydraPlugin()
