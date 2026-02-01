#!/usr/bin/env python3
"""
souleyez.plugins.sqlmap

SQLMap SQL injection detection and exploitation plugin with unified interface.
"""

import subprocess
import time
from typing import List

from souleyez.security.validation import ValidationError, validate_url

from .plugin_base import PluginBase

HELP = {
    "name": "SQLMap — Automated SQL Injection Detection & Exploitation Tool",
    "description": (
        "Want a sharp-eyed script kiddie that knows SQL like a bartender knows cocktails?\n\n"
        "SQLMap is an automated tool that detects and (when authorized) exploits SQL injection flaws in web applications. It identifies "
        "injectable parameters, fingerprints the database engine, extracts data (tables, columns, rows), and can even test fingerprinting, "
        "file read/write, and limited command execution where permitted. Think of it as an advanced reconnaissance and verification tool for "
        "database-backed issues — powerful, efficient, and definitely not something to use without permission. 🚨\n\n"
        "Use cases: confirm suspected SQLi findings, extract schema metadata for vulnerability triage, validate fix effectiveness, or power a "
        "controlled penetration test where database-level checks are in-scope.\n\n"
        "Play nice & legalese: SQLMap can be destructive and noisy. Only run it against targets you own or have explicit authorization to test. "
        "Misuse can break systems and may be illegal.\n\n"
        "Quick tips:\n"
        "- Start in detection-only mode (--batch + --risk/--level tuned low) to identify probable injections before extracting data.\n"
        "- Fingerprint the DB (--dbs, --current-db) to understand impact and plan safe verification steps.\n"
        "- Use safe extraction flags and limits (e.g., --limit, --threads) to avoid overwhelming the target.\n"
        "- Prefer time-based or blind techniques only when safer options aren't available; they are slower and can be heavier on resources.\n"
        "- Capture output to a job log and convert confirmed issues into Findings — include proof-of-concept details and remediation guidance.\n"
        "- Always follow rules of engagement and consider getting explicit written permission for DB-level testing.\n"
    ),
    "usage": 'souleyez jobs enqueue sqlmap <target_url> --args "--batch"',
    "examples": [
        'souleyez jobs enqueue sqlmap "http://example.com/page.php?id=1" --args "--batch"',
        'souleyez jobs enqueue sqlmap "http://example.com/page.php?id=1" --args "--batch --dbs"',
        'souleyez jobs enqueue sqlmap "http://example.com/login" --args "--batch --forms"',
        'souleyez jobs enqueue sqlmap "http://example.com/page.php?id=1" --args "--batch --level=5 --risk=3"',
        'souleyez jobs enqueue sqlmap "http://example.com/page.php" --args "--batch --data=\'username=admin&password=pass\' -p username"',
    ],
    "flags": [
        ["--batch", "Never ask for user input, use default behavior"],
        ["--dbs", "Enumerate databases"],
        ["--tables", "Enumerate tables"],
        ["--columns", "Enumerate columns"],
        ["--dump", "Dump database table entries"],
        ["--dump-all", "Dump all database tables"],
        ["--forms", "Parse and test forms"],
        ["--crawl=N", "Crawl website starting from target URL (depth N)"],
        ["-p <param>", "Testable parameter(s)"],
        ["--data=<data>", "Data string to be sent through POST"],
        ["--cookie=<cookie>", "HTTP Cookie header value"],
        ["--level <1-5>", "Level of tests (1-5, default 1)"],
        ["--risk <1-3>", "Risk of tests (1-3, default 1)"],
        ["--technique=<tech>", "SQL injection techniques to use (default BEUSTQ)"],
        ["--dbms=<dbms>", "Force back-end DBMS (MySQL, Oracle, PostgreSQL, etc.)"],
        ["--os-shell", "Prompt for an interactive OS shell"],
        ["--sql-shell", "Prompt for an SQL shell"],
        ["--tamper=<script>", "Use tamper script(s) for WAF/IPS evasion"],
    ],
    "preset_categories": {
        "basic_detection": [
            {
                "name": "Quick Test",
                "args": ["--batch", "--level=1", "--risk=1"],
                "desc": "Quick SQL injection test (safe, low risk)",
            },
            {
                "name": "Standard Test",
                "args": ["--batch", "--level=2", "--risk=1"],
                "desc": "Standard detection (includes cookies/headers)",
            },
            {
                "name": "Extensive Test",
                "args": ["--batch", "--crawl=2", "--risk=2", "--level=3"],
                "desc": "Deep detection (includes cookies/headers and crawl 2 levels)",
            },
        ],
        "form_crawl": [
            {
                "name": "Forms Quick",
                "args": ["--batch", "--forms", "--level=1"],
                "desc": "Test forms only (no crawl)",
            },
            {
                "name": "Forms + Crawl",
                "args": ["--batch", "--forms", "--crawl=2"],
                "desc": "Test forms and crawl 2 levels",
            },
        ],
        "enumeration": [
            {
                "name": "Current User Info",
                "args": ["--batch", "--current-user", "--current-db", "--hostname"],
                "desc": "Get current user, database, and hostname",
            },
            {
                "name": "Discover Databases",
                "args": [
                    "--batch",
                    "--dbs",
                    "--forms",
                    "--level=3",
                    "--crawl=2",
                    "--risk=2",
                ],
                "desc": "Enumerate databases with deep crawl",
            },
            {
                "name": "Enumerate Tables",
                "args": ["--batch", "-D", "<DB_NAME>", "--tables", "--crawl=2"],
                "desc": "List tables in database (replace <DB_NAME>)",
            },
            {
                "name": "Enumerate Columns",
                "args": [
                    "--batch",
                    "-D",
                    "<DB_NAME>",
                    "-T",
                    "<TABLE>",
                    "--columns",
                    "--crawl=2",
                ],
                "desc": "List columns in table (replace <DB_NAME> and <TABLE>)",
            },
            {
                "name": "Check Privileges",
                "args": ["--batch", "--privileges"],
                "desc": "Check DB user privileges",
            },
            {
                "name": "Is DBA",
                "args": ["--batch", "--is-dba"],
                "desc": "Check if current user is DBA",
            },
        ],
        "data_extraction": [
            {
                "name": "Extract Table Data",
                "args": [
                    "--batch",
                    "-D",
                    "<DB_NAME>",
                    "-T",
                    "<TABLE>",
                    "--dump",
                    "--crawl=2",
                ],
                "desc": "Dump entire table (replace <DB_NAME> and <TABLE>)",
            },
            {
                "name": "Extract Column Data",
                "args": [
                    "--batch",
                    "-D",
                    "<DB_NAME>",
                    "-T",
                    "<TABLE>",
                    "-C",
                    "<COLUMNS>",
                    "--dump",
                    "--crawl=2",
                ],
                "desc": "Dump specific columns (e.g., username,password)",
            },
            {
                "name": "Dump Users & Passwords",
                "args": ["--batch", "--users", "--passwords"],
                "desc": "Dump all DB users and password hashes",
            },
        ],
        "exploitation": [
            {
                "name": "OS Shell",
                "args": ["--batch", "--os-shell"],
                "desc": "Get interactive OS shell via SQLi",
            },
            {
                "name": "OS Command",
                "args": ["--batch", "--os-cmd=whoami"],
                "desc": "Execute single OS command (replace whoami)",
            },
            {
                "name": "Read File",
                "args": ["--batch", "--file-read=/etc/passwd"],
                "desc": "Read server files via SQLi (replace path)",
            },
            {
                "name": "Write File",
                "args": [
                    "--batch",
                    "--file-write=<local_file>",
                    "--file-dest=<remote_path>",
                ],
                "desc": "Upload files to server (replace paths)",
            },
        ],
        "waf_bypass": [
            {
                "name": "WAF Bypass - Space",
                "args": ["--batch", "--tamper=space2comment"],
                "desc": "Bypass space-based WAF detection",
            },
            {
                "name": "WAF Bypass - Generic",
                "args": ["--batch", "--tamper=between,randomcase"],
                "desc": "Generic WAF evasion techniques",
            },
            {
                "name": "WAF Bypass - Full",
                "args": [
                    "--batch",
                    "--tamper=space2comment,between,randomcase,charencode",
                ],
                "desc": "Aggressive WAF bypass (multiple tampers)",
            },
        ],
    },
    "presets": [
        # Flattened list for backward compatibility - matches preset_categories order
        # Basic Detection
        {
            "name": "Quick Test",
            "args": ["--batch", "--level=1", "--risk=1"],
            "desc": "Quick SQL injection test (safe, low risk)",
        },
        {
            "name": "Standard Test",
            "args": ["--batch", "--level=2", "--risk=1"],
            "desc": "Standard detection (includes cookies/headers)",
        },
        {
            "name": "Extensive Test",
            "args": ["--batch", "--crawl=2", "--risk=2", "--level=3"],
            "desc": "Deep detection (includes cookies/headers and crawl 2 levels)",
        },
        # Form Crawl
        {
            "name": "Forms Quick",
            "args": ["--batch", "--forms", "--level=1"],
            "desc": "Test forms only (no crawl)",
        },
        {
            "name": "Forms + Crawl",
            "args": ["--batch", "--forms", "--crawl=2"],
            "desc": "Test forms and crawl 2 levels",
        },
        # Enumeration
        {
            "name": "Current User Info",
            "args": ["--batch", "--current-user", "--current-db", "--hostname"],
            "desc": "Get current user, database, and hostname",
        },
        {
            "name": "Discover Databases",
            "args": [
                "--batch",
                "--dbs",
                "--forms",
                "--level=3",
                "--crawl=2",
                "--risk=2",
            ],
            "desc": "Enumerate databases with deep crawl",
        },
        {
            "name": "Enumerate Tables",
            "args": ["--batch", "-D", "<DB_NAME>", "--tables", "--crawl=2"],
            "desc": "List tables in database (replace <DB_NAME>)",
        },
        {
            "name": "Enumerate Columns",
            "args": [
                "--batch",
                "-D",
                "<DB_NAME>",
                "-T",
                "<TABLE>",
                "--columns",
                "--crawl=2",
            ],
            "desc": "List columns in table (replace <DB_NAME> and <TABLE>)",
        },
        {
            "name": "Check Privileges",
            "args": ["--batch", "--privileges"],
            "desc": "Check DB user privileges",
        },
        {
            "name": "Is DBA",
            "args": ["--batch", "--is-dba"],
            "desc": "Check if current user is DBA",
        },
        # Data Extraction
        {
            "name": "Extract Table Data",
            "args": [
                "--batch",
                "-D",
                "<DB_NAME>",
                "-T",
                "<TABLE>",
                "--dump",
                "--crawl=2",
            ],
            "desc": "Dump entire table (replace <DB_NAME> and <TABLE>)",
        },
        {
            "name": "Extract Column Data",
            "args": [
                "--batch",
                "-D",
                "<DB_NAME>",
                "-T",
                "<TABLE>",
                "-C",
                "<COLUMNS>",
                "--dump",
                "--crawl=2",
            ],
            "desc": "Dump specific columns (e.g., username,password)",
        },
        {
            "name": "Dump Users & Passwords",
            "args": ["--batch", "--users", "--passwords"],
            "desc": "Dump all DB users and password hashes",
        },
        # Exploitation
        {
            "name": "OS Shell",
            "args": ["--batch", "--os-shell"],
            "desc": "Get interactive OS shell via SQLi",
        },
        {
            "name": "OS Command",
            "args": ["--batch", "--os-cmd=whoami"],
            "desc": "Execute single OS command (replace whoami)",
        },
        {
            "name": "Read File",
            "args": ["--batch", "--file-read=/etc/passwd"],
            "desc": "Read server files via SQLi (replace path)",
        },
        {
            "name": "Write File",
            "args": [
                "--batch",
                "--file-write=<local_file>",
                "--file-dest=<remote_path>",
            ],
            "desc": "Upload files to server (replace paths)",
        },
        # WAF Bypass
        {
            "name": "WAF Bypass - Space",
            "args": ["--batch", "--tamper=space2comment"],
            "desc": "Bypass space-based WAF detection",
        },
        {
            "name": "WAF Bypass - Generic",
            "args": ["--batch", "--tamper=between,randomcase"],
            "desc": "Generic WAF evasion techniques",
        },
        {
            "name": "WAF Bypass - Full",
            "args": ["--batch", "--tamper=space2comment,between,randomcase,charencode"],
            "desc": "Aggressive WAF bypass (multiple tampers)",
        },
    ],
    "help_sections": [
        {
            "title": "What is SQLMap?",
            "color": "cyan",
            "content": [
                {
                    "title": "Overview",
                    "desc": "SQLMap is the industry-standard automated SQL injection detection and exploitation tool that identifies injectable parameters and extracts database contents.",
                },
                {
                    "title": "Use Cases",
                    "desc": "SQL injection testing and validation",
                    "tips": [
                        "Detect and confirm SQL injection vulnerabilities",
                        "Fingerprint database engines (MySQL, PostgreSQL, etc.)",
                        "Extract database schemas and data",
                        "Test fix effectiveness after remediation",
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
                    "desc": "1. Start with detection mode (--batch --level=1)\n     2. Fingerprint database (--dbs, --current-db)\n     3. Enumerate schema (--tables, --columns)\n     4. Extract data with limits (--dump --limit 100)",
                },
                {
                    "title": "Key Options",
                    "desc": "Essential SQLMap parameters",
                    "tips": [
                        "--batch: Non-interactive mode (required)",
                        "--dbs: List all databases",
                        "--forms: Auto-detect and test forms",
                        "--level/--risk: Control test intensity (1-5/1-3)",
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
                        "Always use --batch for non-interactive mode",
                        "Start with low --risk and --level, increase if needed",
                        "Use --limit to avoid extracting entire databases",
                        "Save proof-of-concept to job log for findings",
                        "ONLY run with explicit written authorization",
                    ],
                ),
                (
                    "Common Issues:",
                    [
                        "No injection found: Try higher --level or --risk",
                        "Too slow: Reduce --level or use specific techniques",
                        "WAF blocking: Use --tamper scripts for evasion",
                        "False positives: Manually verify all findings",
                    ],
                ),
            ],
        },
    ],
}


class SqlmapPlugin(PluginBase):
    name = "SQLMap"
    tool = "sqlmap"
    category = "exploitation"
    HELP = HELP

    def build_command(
        self, target: str, args: List[str] = None, label: str = "", log_path: str = None
    ):
        """Build sqlmap command for background execution with PID tracking."""
        args = args or []

        # Handle plain IP/hostname - add protocol if missing
        if not target.startswith(("http://", "https://")):
            target = f"http://{target}"

        # Validate URL
        try:
            target = validate_url(target)
        except ValidationError as e:
            if log_path:
                with open(log_path, "w") as f:
                    f.write(f"ERROR: Invalid URL: {e}\n")
            return None

        # Always add --batch if not present to avoid interactive prompts
        if "--batch" not in args:
            args = ["--batch"] + args

        # Build sqlmap command
        if "-u" not in args:
            cmd = ["sqlmap", "-u", target] + args
        else:
            cmd = ["sqlmap"] + args

        # Replace <target> placeholder if present in args
        cmd = [arg.replace("<target>", target) for arg in cmd]

        return {"cmd": cmd, "timeout": 3600}  # 1 hour timeout for deep scans

    def run(
        self, target: str, args: List[str] = None, label: str = "", log_path: str = None
    ) -> int:
        """
        Execute sqlmap scan and write output to log_path.

        Args:
            target: Target URL (e.g. "http://example.com/page.php?id=1")
            args: SQLMap arguments (e.g. ["--batch", "--dbs"])
            label: Optional label for this scan
            log_path: Path to write output (required for background jobs)

        Returns:
            int: Exit code (0=success, non-zero=error)
        """
        args = args or []

        # Handle plain IP/hostname - add protocol if missing
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

        # Always add --batch if not present to avoid interactive prompts
        if "--batch" not in args:
            args = ["--batch"] + args

        # Build sqlmap command
        # SQLMap takes URL as -u parameter
        if "-u" not in args:
            # Target not in args, add -u parameter
            cmd = ["sqlmap", "-u", target] + args
        else:
            # -u already in args, don't add target again
            cmd = ["sqlmap"] + args

        # Replace <target> placeholder if present in args
        cmd = [arg.replace("<target>", target) for arg in cmd]

        if not log_path:
            # Fallback for direct calls (shouldn't happen in background jobs)
            try:
                proc = subprocess.run(
                    cmd, capture_output=True, timeout=3600, check=False
                )  # 1 hour
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
                    cmd,
                    stdout=fh,
                    stderr=subprocess.STDOUT,
                    timeout=3600,  # SQLMap can take 1+ hours for deep scans
                    check=False,
                )

                fh.write(
                    f"\nCompleted: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}\n"
                )
                fh.write(f"Exit Code: {proc.returncode}\n")

                return proc.returncode

        except subprocess.TimeoutExpired:
            with open(log_path, "a", encoding="utf-8", errors="replace") as fh:
                fh.write("\nERROR: SQLMap timed out after 3600 seconds (1 hour)\n")
            return 124

        except FileNotFoundError:
            with open(log_path, "a", encoding="utf-8", errors="replace") as fh:
                fh.write("\nERROR: sqlmap not found in PATH\n")
            return 127

        except Exception as e:
            with open(log_path, "a", encoding="utf-8", errors="replace") as fh:
                fh.write(f"\nERROR: {type(e).__name__}: {e}\n")
            return 1


# Export plugin instance
plugin = SqlmapPlugin()
