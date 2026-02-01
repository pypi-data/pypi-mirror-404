#!/usr/bin/env python3
"""
souleyez.plugins.ffuf - Fast web fuzzer
"""

import subprocess
from typing import List

from souleyez.security.validation import ValidationError, validate_url

from .plugin_base import PluginBase

HELP = {
    "name": "ffuf - Fast Web Fuzzer",
    "description": (
        "Need advanced web fuzzing for parameters, headers, or POST data?\n\n"
        "ffuf (Fuzz Faster U Fool) is a modern web fuzzer that excels at finding hidden endpoints, "
        "parameters, virtual hosts, and more. Unlike simple directory brute-forcers, ffuf can fuzz "
        "any part of an HTTP request - perfect for discovering parameter-based vulnerabilities.\n\n"
        "Use ffuf after gobuster finds directories to:\n"
        "- Fuzz for files with specific extensions\n"
        "- Discover GET/POST parameters\n"
        "- Find virtual hosts\n"
        "- Test for IDOR vulnerabilities\n\n"
        "Quick tips:\n"
        "- Use FUZZ keyword in URL/headers/data to mark fuzz position\n"
        "- Filter responses with -fc, -fs, -fw to reduce noise\n"
        "- Use -e flag to append extensions automatically\n"
        "- Results are JSON-formatted for easy parsing\n"
    ),
    "usage": 'souleyez jobs enqueue ffuf <target> --args "-w wordlist.txt"',
    "examples": [
        'souleyez jobs enqueue ffuf http://example.com/FUZZ --args "-w data/wordlists/web_dirs_common.txt"',
        'souleyez jobs enqueue ffuf http://example.com/FUZZ --args "-w wordlist.txt -e .php,.html,.txt"',
        'souleyez jobs enqueue ffuf http://example.com/?id=FUZZ --args "-w numbers.txt"',
    ],
    "flags": [
        ["-w <wordlist>", "Wordlist file path"],
        ["-e <extensions>", "Comma-separated extensions to append"],
        ["-t <threads>", "Number of threads (default: 40)"],
        ["-mc <codes>", "Match HTTP status codes"],
        ["-fc <codes>", "Filter HTTP status codes"],
        ["-fs <size>", "Filter response size"],
        ["-fw <words>", "Filter word count"],
    ],
    "preset_categories": {
        "directory_fuzzing": [
            {
                "name": "Directory Fuzzing",
                "args": ["-w", "data/wordlists/web_dirs_common.txt"],
                "desc": "Basic directory discovery",
            },
            {
                "name": "File Fuzzing (PHP)",
                "args": [
                    "-w",
                    "data/wordlists/web_files_common.txt",
                    "-e",
                    ".php,.phps,.php3,.php4,.php5",
                ],
                "desc": "Fuzz for PHP files",
            },
        ],
        "parameter_fuzzing": [
            {
                "name": "GET Parameters",
                "args": ["-w", "data/wordlists/web_files_common.txt"],
                "desc": "Discover GET parameters (add ?FUZZ=test to URL)",
            },
            {
                "name": "POST Parameters",
                "args": [
                    "-w",
                    "data/wordlists/web_files_common.txt",
                    "-X",
                    "POST",
                    "-d",
                    "FUZZ=test",
                ],
                "desc": "Discover POST parameters",
            },
            {
                "name": "Header Fuzzing",
                "args": [
                    "-w",
                    "data/wordlists/web_files_common.txt",
                    "-H",
                    "FUZZ: test",
                ],
                "desc": "Find header-based vulnerabilities",
            },
            {
                "name": "Value Fuzzing",
                "args": ["-w", "data/wordlists/web_files_common.txt"],
                "desc": "Test parameter values (use ?param=FUZZ)",
            },
        ],
        "vhost_fuzzing": [
            {
                "name": "Virtual Hosts",
                "args": [
                    "-w",
                    "data/wordlists/subdomains_common.txt",
                    "-H",
                    "Host: FUZZ.target.com",
                ],
                "desc": "Discover virtual hosts",
            }
        ],
    },
    "presets": [
        {
            "name": "Directory Fuzzing",
            "args": ["-w", "data/wordlists/web_dirs_common.txt"],
            "desc": "Basic directory discovery",
        },
        {
            "name": "File Fuzzing (PHP)",
            "args": [
                "-w",
                "data/wordlists/web_files_common.txt",
                "-e",
                ".php,.phps,.php3,.php4,.php5",
            ],
            "desc": "Fuzz for PHP files",
        },
        {
            "name": "GET Parameters",
            "args": ["-w", "data/wordlists/web_files_common.txt"],
            "desc": "Discover GET parameters (add ?FUZZ=test to URL)",
        },
        {
            "name": "POST Parameters",
            "args": [
                "-w",
                "data/wordlists/web_files_common.txt",
                "-X",
                "POST",
                "-d",
                "FUZZ=test",
            ],
            "desc": "Discover POST parameters",
        },
        {
            "name": "Header Fuzzing",
            "args": ["-w", "data/wordlists/web_files_common.txt", "-H", "FUZZ: test"],
            "desc": "Find header-based vulnerabilities",
        },
        {
            "name": "Value Fuzzing",
            "args": ["-w", "data/wordlists/web_files_common.txt"],
            "desc": "Test parameter values (use ?param=FUZZ)",
        },
    ],
    "help_sections": [
        {
            "title": "What is ffuf?",
            "color": "cyan",
            "content": [
                {
                    "title": "Overview",
                    "desc": "ffuf (Fuzz Faster U Fool) is a modern, fast web fuzzer that can fuzz any part of an HTTP request - URLs, headers, POST data, and more.",
                },
                {
                    "title": "Use Cases",
                    "desc": "Advanced web fuzzing beyond simple directory scans",
                    "tips": [
                        "Fuzz for hidden files with specific extensions",
                        "Discover GET/POST parameters",
                        "Find virtual hosts",
                        "Test for IDOR vulnerabilities",
                        "Fuzz headers and cookies",
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
                    "desc": "1. Use FUZZ keyword to mark position to fuzz\n     2. Apply filters (-fc, -fs, -fw) to reduce noise\n     3. Use -e flag to append extensions automatically\n     4. Review JSON output for results",
                },
                {
                    "title": "Key Features",
                    "desc": "Powerful fuzzing capabilities",
                    "tips": [
                        "Directory fuzzing: ffuf -u http://site/FUZZ -w wordlist.txt",
                        "Parameter fuzzing: ffuf -u http://site/?FUZZ=value -w params.txt",
                        "Extension fuzzing: ffuf -u http://site/FUZZ -w words.txt -e .php,.html",
                        "Filter results: -fc 404 (filter code), -fs 1234 (filter size)",
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
                        "Use filters early to reduce noise (-fc 404,403)",
                        "Start with common wordlists, expand as needed",
                        "Match response codes carefully (-mc 200,204,301,302)",
                        "Save JSON output for parsing and analysis",
                        "Use -t to control threads (default 40)",
                    ],
                ),
                (
                    "Common Issues:",
                    [
                        "Too many results: Add -fc or -fs filters",
                        "Missing FUZZ keyword: Add FUZZ to URL or headers",
                        "Rate limiting: Reduce -t threads or add delays",
                        "No matches: Check filters aren't too restrictive",
                    ],
                ),
            ],
        },
    ],
}


class FfufPlugin(PluginBase):
    name = "ffuf"
    tool = "ffuf"
    category = "scanning"
    HELP = HELP

    def build_command(
        self, target: str, args: List[str] = None, label: str = "", log_path: str = None
    ):
        """Build command for background execution with PID tracking."""
        if not target:
            if log_path:
                with open(log_path, "w") as f:
                    f.write("ERROR: Target URL is required\n")
            return None

        # Add FUZZ placeholder if not present
        if "FUZZ" not in target:
            target = target.rstrip("/") + "/FUZZ"

        # Validate URL (skip if FUZZ is present)
        if "FUZZ" not in target:
            try:
                target = validate_url(target)
            except ValidationError as e:
                if log_path:
                    with open(log_path, "w") as f:
                        f.write(f"ERROR: Invalid URL: {e}\n")
                return None

        args = args or []

        # Replace <target> placeholder
        args = [arg.replace("<target>", target) for arg in args]

        # ffuf uses -u flag for URL
        cmd = ["ffuf", "-u", target]

        # Force JSON output
        if log_path and "-o" not in args:
            cmd.extend(["-o", log_path, "-of", "json"])

        # Add user args
        cmd.extend(args)

        # Set defaults if not in args
        if "-mc" not in args and "-fc" not in args:
            cmd.extend(["-mc", "200,204,301,302,307,401,403"])

        if "-t" not in args:
            cmd.extend(["-t", "40"])

        return {"cmd": cmd, "timeout": 1800}

    def run(
        self, target: str, args: List[str] = None, label: str = "", log_path: str = None
    ) -> int:
        """Execute ffuf and write JSON output to log_path."""

        # Validate URL
        if not target.startswith(("http://", "https://")):
            target = f"http://{target}"

        # ffuf needs FUZZ keyword in URL
        if "FUZZ" not in target:
            target = target.rstrip("/") + "/FUZZ"

        try:
            # Don't validate if FUZZ is in URL (it's not a real URL)
            if "FUZZ" not in target:
                target = validate_url(target)
        except ValidationError as e:
            if log_path:
                with open(log_path, "w") as f:
                    f.write(f"ERROR: Invalid URL: {e}\n")
                return 1
            raise ValueError(f"Invalid URL: {e}")

        args = args or []

        # Replace <target> placeholder
        args = [arg.replace("<target>", target) for arg in args]

        # Build ffuf command
        cmd = ["ffuf", "-u", target]

        # Force JSON output
        if log_path and "-o" not in args:
            cmd.extend(["-o", log_path, "-of", "json"])

        # Add user args
        cmd.extend(args)

        # Set defaults
        if "-mc" not in args and "-fc" not in args:
            cmd.extend(["-mc", "200,204,301,302,307,401,403"])

        if "-t" not in args:
            cmd.extend(["-t", "40"])

        if not log_path:
            try:
                proc = subprocess.run(
                    cmd, capture_output=True, timeout=600, check=False
                )
                return proc.returncode
            except Exception:
                return 1

        try:
            # ffuf writes JSON directly to output file
            proc = subprocess.run(
                cmd, capture_output=True, timeout=600, check=False, text=True
            )

            # If there was an error, write it to log
            if proc.returncode != 0 or proc.stderr:
                with open(log_path, "a", encoding="utf-8") as fh:
                    fh.write(f"\n\n# Error output:\n")
                    fh.write(proc.stderr if proc.stderr else "Unknown error")

            return proc.returncode

        except subprocess.TimeoutExpired:
            with open(log_path, "w", encoding="utf-8") as fh:
                fh.write("ERROR: ffuf timed out after 600 seconds\n")
            return 124

        except FileNotFoundError:
            with open(log_path, "w", encoding="utf-8") as fh:
                fh.write("ERROR: ffuf not found in PATH\n")
                fh.write("Install: https://github.com/ffuf/ffuf\n")
            return 127

        except Exception as e:
            with open(log_path, "w", encoding="utf-8") as fh:
                fh.write(f"ERROR: {type(e).__name__}: {e}\n")
            return 1


plugin = FfufPlugin()
