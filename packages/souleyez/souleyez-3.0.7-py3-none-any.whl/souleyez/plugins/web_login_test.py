#!/usr/bin/env python3
"""
souleyez.plugins.web_login_test - Web login credential testing

Tests cracked credentials against web login endpoints.
Supports both JSON REST APIs and traditional HTML form logins.
"""

import json
import re
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional

from .plugin_base import PluginBase

HELP = {
    "name": "Web Login Test - Credential Validation",
    "description": (
        "Tests credentials against web login endpoints to validate "
        "that cracked passwords actually work.\n\n"
        "Supports:\n"
        "- JSON REST APIs (Content-Type: application/json)\n"
        "- HTML form submissions\n"
        "- Custom field names via --username-field and --password-field\n"
    ),
    "usage": 'souleyez jobs enqueue web_login_test <login_url> --args "--username <user> --password <pass>"',
    "examples": [
        'souleyez jobs enqueue web_login_test http://target/api/login --args "--username admin --password secret"',
        'souleyez jobs enqueue web_login_test http://target/login.php --args "--username admin --password secret --form"',
    ],
    "flags": [
        ["--username <user>", "Username to test"],
        ["--password <pass>", "Password to test"],
        ["--form", "Use form POST instead of JSON (default: JSON)"],
        ["--username-field <name>", "Custom username field name (default: email)"],
        ["--password-field <name>", "Custom password field name (default: password)"],
    ],
    "presets": [
        {
            "name": "JSON API Login",
            "args": ["--username", "<username>", "--password", "<password>"],
            "desc": "Test JSON API login endpoint",
        },
        {
            "name": "Form Login",
            "args": ["--username", "<username>", "--password", "<password>", "--form"],
            "desc": "Test HTML form login",
        },
    ],
    "help_sections": [
        {
            "title": "How It Works",
            "color": "cyan",
            "content": [
                (
                    "Overview",
                    [
                        "Sends POST request with credentials to login endpoint",
                        "Analyzes response for success/failure indicators",
                        "Supports JSON APIs and form-based authentication",
                    ],
                ),
                (
                    "Success Detection",
                    [
                        "Looks for: token, success, authenticated in response",
                        "HTTP 200/201 with positive indicators = success",
                        "HTTP 401/403 or error messages = failure",
                    ],
                ),
            ],
        },
        {
            "title": "Usage & Examples",
            "color": "green",
            "content": [
                (
                    "JSON API Login (default)",
                    [
                        "souleyez jobs enqueue web_login_test http://target/api/login \\",
                        '  --args "--username admin --password secret"',
                        '  → Sends JSON: {"email": "admin", "password": "secret"}',
                    ],
                ),
                (
                    "HTML Form Login",
                    [
                        "souleyez jobs enqueue web_login_test http://target/login.php \\",
                        '  --args "--username admin --password secret --form"',
                        "  → Sends form data: email=admin&password=secret",
                    ],
                ),
                (
                    "Custom Field Names",
                    [
                        "souleyez jobs enqueue web_login_test http://target/login \\",
                        '  --args "--username admin --password secret --username-field user --password-field pass"',
                        "  → Uses custom field names instead of email/password",
                    ],
                ),
            ],
        },
        {
            "title": "Automatic Chaining",
            "color": "yellow",
            "content": [
                (
                    "When This Tool Runs Automatically",
                    [
                        "After hashcat cracks passwords from SQLMap dumps",
                        "Validates cracked credentials against the original login endpoint",
                        "Auto-detects JSON vs form format from URL patterns",
                    ],
                ),
                (
                    "Chain Flow",
                    [
                        "SQLMap extracts hashed passwords from database",
                        "Hashcat cracks the hashes to plaintext",
                        "Web Login Test validates: do these credentials work?",
                        "Validated credentials are stored for reporting",
                    ],
                ),
            ],
        },
    ],
}


class WebLoginTestPlugin(PluginBase):
    """Plugin for testing web login credentials."""

    name = "Web Login Test"
    tool = "web_login_test"
    category = "credential_access"
    HELP = HELP

    # Success indicators in response body
    SUCCESS_INDICATORS = [
        "token",
        "access_token",
        "jwt",
        "session",
        "authenticated",
        "success",
        "welcome",
        "dashboard",
        "logged in",
    ]

    # Failure indicators in response body
    FAILURE_INDICATORS = [
        "invalid",
        "incorrect",
        "failed",
        "error",
        "unauthorized",
        "denied",
        "wrong password",
        "bad credentials",
        "authentication failed",
    ]

    def build_command(
        self,
        target: str,
        args: List[str] = None,
        label: str = "",
        log_path: str = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Web login test runs in Python, not via external command.
        Return None to use run() method instead.
        """
        return None

    def run(
        self,
        target: str,
        args: List[str] = None,
        label: str = "",
        log_path: str = None,
    ) -> int:
        """Execute web login credential test."""
        args = args or []

        # Parse arguments
        username = None
        password = None
        use_form = False
        username_field = "email"
        password_field = "password"

        i = 0
        while i < len(args):
            arg = args[i]
            if arg == "--username" and i + 1 < len(args):
                username = args[i + 1]
                i += 2
            elif arg == "--password" and i + 1 < len(args):
                password = args[i + 1]
                i += 2
            elif arg == "--form":
                use_form = True
                i += 1
            elif arg == "--username-field" and i + 1 < len(args):
                username_field = args[i + 1]
                i += 2
            elif arg == "--password-field" and i + 1 < len(args):
                password_field = args[i + 1]
                i += 2
            else:
                i += 1

        if not username or not password:
            self._write_log(
                log_path,
                target,
                username,
                error="Missing --username or --password argument",
            )
            return 1

        # Ensure target has scheme
        if not target.startswith(("http://", "https://")):
            target = f"http://{target}"

        try:
            result = self._test_login(
                url=target,
                username=username,
                password=password,
                use_form=use_form,
                username_field=username_field,
                password_field=password_field,
            )

            self._write_log(log_path, target, username, result=result)

            # Return 0 for success, 1 for failure
            return 0 if result.get("success") else 1

        except Exception as e:
            self._write_log(log_path, target, username, error=str(e))
            return 1

    def _test_login(
        self,
        url: str,
        username: str,
        password: str,
        use_form: bool = False,
        username_field: str = "email",
        password_field: str = "password",
        timeout: int = 15,
    ) -> Dict[str, Any]:
        """
        Test login credentials against a web endpoint.

        Returns dict with:
        - success: bool
        - http_code: int
        - response: str (truncated)
        - reason: str (why success/failure was determined)
        """
        result = {
            "success": False,
            "http_code": None,
            "response": None,
            "reason": None,
        }

        # Create SSL context that accepts self-signed certs
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        # Build request data
        if use_form:
            # Form-encoded POST
            data = urllib.parse.urlencode(
                {username_field: username, password_field: password}
            ).encode("utf-8")
            content_type = "application/x-www-form-urlencoded"
        else:
            # JSON POST
            data = json.dumps(
                {username_field: username, password_field: password}
            ).encode("utf-8")
            content_type = "application/json"

        # Create request
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Content-Type": content_type,
                "Accept": "application/json, text/html, */*",
            },
            method="POST",
        )

        try:
            response = urllib.request.urlopen(req, timeout=timeout, context=ctx)
            result["http_code"] = response.getcode()
            body = response.read().decode("utf-8", errors="replace")
            result["response"] = body[:500] if body else ""

            # Analyze response
            body_lower = body.lower()

            # Check for success indicators
            for indicator in self.SUCCESS_INDICATORS:
                if indicator in body_lower:
                    result["success"] = True
                    result["reason"] = f"Found success indicator: '{indicator}'"
                    return result

            # HTTP 200/201 without explicit failure = possible success
            if result["http_code"] in (200, 201):
                # Check for failure indicators
                for indicator in self.FAILURE_INDICATORS:
                    if indicator in body_lower:
                        result["success"] = False
                        result["reason"] = f"Found failure indicator: '{indicator}'"
                        return result

                # No failure indicators, consider it possible success
                result["success"] = True
                result["reason"] = (
                    f"HTTP {result['http_code']} with no failure indicators"
                )
                return result

            # Other status codes
            result["reason"] = f"HTTP {result['http_code']} - unclear result"
            return result

        except urllib.error.HTTPError as e:
            result["http_code"] = e.code
            try:
                body = e.read().decode("utf-8", errors="replace")
                result["response"] = body[:500] if body else ""
            except Exception:
                result["response"] = ""

            # 401/403 = auth failed
            if e.code in (401, 403):
                result["reason"] = f"HTTP {e.code} - Authentication failed"
            else:
                result["reason"] = f"HTTP {e.code} - Request failed"
            return result

        except urllib.error.URLError as e:
            result["reason"] = f"Connection error: {e.reason}"
            return result

        except Exception as e:
            result["reason"] = f"Error: {type(e).__name__}: {e}"
            return result

    def _write_log(
        self,
        log_path: str,
        target: str,
        username: str,
        result: Dict[str, Any] = None,
        error: str = None,
    ) -> None:
        """Write test results to log file."""
        if not log_path:
            return

        try:
            with open(log_path, "w", encoding="utf-8", errors="replace") as fh:
                fh.write("=== Plugin: Web Login Test ===\n")
                fh.write(f"Target: {target}\n")
                fh.write(f"Username: {username}\n")
                fh.write(
                    f"Started: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}\n"
                )
                fh.write("=" * 60 + "\n\n")

                if error:
                    fh.write(f"ERROR: {error}\n")
                    fh.write("\n=== JSON_RESULT ===\n")
                    fh.write(json.dumps({"error": error}, indent=2))
                    fh.write("\n=== END_JSON_RESULT ===\n")
                    return

                if result:
                    if result.get("success"):
                        fh.write("[+] LOGIN SUCCESS\n")
                    else:
                        fh.write("[-] LOGIN FAILED\n")

                    fh.write(f"\nHTTP Code: {result.get('http_code', 'N/A')}\n")
                    fh.write(f"Reason: {result.get('reason', 'Unknown')}\n")

                    if result.get("response"):
                        fh.write(
                            f"\nResponse (truncated):\n{result['response'][:200]}\n"
                        )

                    fh.write("\n=== JSON_RESULT ===\n")
                    fh.write(json.dumps(result, indent=2))
                    fh.write("\n=== END_JSON_RESULT ===\n")

        except Exception:
            pass


plugin = WebLoginTestPlugin()
