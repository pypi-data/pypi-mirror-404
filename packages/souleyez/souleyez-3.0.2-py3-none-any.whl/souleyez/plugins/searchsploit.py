#!/usr/bin/env python3
"""
souleyez.plugins.searchsploit - Search Exploit-DB for vulnerabilities and exploits
"""

import subprocess
import time
from typing import List

from .plugin_base import PluginBase

HELP = {
    "name": "SearchSploit - Exploit Discovery",
    "description": (
        "Want to find exploits for discovered services and vulnerabilities?\n\n"
        "SearchSploit searches the offline Exploit-DB database for public exploits, "
        "shellcodes, and papers. It's perfect for finding exploits for specific software "
        "versions discovered during reconnaissance.\n\n"
        "Use SearchSploit after nmap finds services to:\n"
        "- Find known exploits for software versions\n"
        "- Search by CVE ID from vulnerability scanners\n"
        "- Get direct links to Exploit-DB\n"
        "- Identify platforms and exploit types\n\n"
        "Quick tips:\n"
        "- Search specific versions: 'Apache 2.4.49'\n"
        "- Search by CVE: 'CVE-2021-41773'\n"
        "- Use -e for exact matches only\n"
        "- Results link to exploit code you can test\n"
    ),
    "usage": "souleyez run searchsploit <search_term>",
    "examples": [
        'souleyez run searchsploit "Apache 2.4.49"',
        'souleyez run searchsploit "CVE-2021-41773"',
        'souleyez run searchsploit "Windows Server 2019" -e',
        'souleyez run searchsploit "ProFTPD 1.3"',
    ],
    "presets": [
        {
            "name": "Basic Search",
            "desc": "Simple search - finds all matches",
            "args": [],
        },
        {"name": "Exact Match", "desc": "Only exact matches", "args": ["-e"]},
        {"name": "Title Search", "desc": "Search titles only (faster)", "args": ["-t"]},
        {"name": "With URLs", "desc": "Include Exploit-DB URLs", "args": ["--www"]},
        {
            "name": "Exact + URLs",
            "desc": "Exact matches with URLs",
            "args": ["-e", "--www"],
        },
    ],
    "help_sections": [
        {
            "title": "What is SearchSploit?",
            "color": "cyan",
            "content": [
                {
                    "title": "Overview",
                    "desc": "SearchSploit searches the offline Exploit-DB database for public exploits, shellcodes, and papers matching software versions or CVE IDs.",
                },
                {
                    "title": "Use Cases",
                    "desc": "Find exploits for discovered services and vulnerabilities",
                    "tips": [
                        "Search by software version (Apache 2.4.49)",
                        "Search by CVE ID (CVE-2021-41773)",
                        "Find platform-specific exploits",
                        "Get direct Exploit-DB links",
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
                    "desc": "1. Get service versions from Nmap or other scans\n     2. Search for exploits matching software/version\n     3. Use -e for exact matches to reduce noise\n     4. Review and test relevant exploits",
                },
                {
                    "title": "Search Tips",
                    "desc": "Effective searching strategies",
                    "tips": [
                        "Include version numbers for better results",
                        "Use CVE IDs from vulnerability scanners",
                        "Try -e for exact matches if too many results",
                        "Use --www to get Exploit-DB URLs",
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
                        "Always verify exploits match your exact target version",
                        "Read exploit code before running (safety check)",
                        "Use Nuclei/WPScan CVE IDs as search terms",
                        "Update Exploit-DB regularly (searchsploit -u)",
                        "Test exploits in controlled environment first",
                    ],
                ),
                (
                    "Common Issues:",
                    [
                        "Too many results: Use -e for exact matches or refine search",
                        "No results: Try broader search terms or different keywords",
                        "Outdated database: Run searchsploit -u to update",
                        "Wrong platform: Filter by platform (Linux, Windows, etc.)",
                    ],
                ),
            ],
        },
    ],
    "flags": [
        ["--json", "JSON output (default for parsing)"],
        ["--www", "Show exploit-db.com URLs"],
        ["--cve <CVE-ID>", "Search by CVE ID"],
        ["-e", "Exact match only"],
        ["-t", "Search in exploit titles only"],
    ],
}


class SearchSploitPlugin(PluginBase):
    name = "SearchSploit"
    tool = "searchsploit"
    category = "vulnerability_analysis"
    HELP = HELP

    def build_command(
        self, target: str, args: List[str] = None, label: str = "", log_path: str = None
    ):
        """Build command for background execution with PID tracking."""
        args = args or []

        # Replace <target> placeholder
        args = [arg.replace("<target>", target) for arg in args]

        # searchsploit syntax: searchsploit [--json] search_term
        cmd = ["searchsploit", "--json"]

        # Determine search term: use args if they contain a non-flag search term,
        # otherwise use target (but skip if target is a URL - not a valid search term)
        non_flag_args = [a for a in args if not a.startswith("-")]

        if non_flag_args:
            # Args contain search term(s) - use those, ignore URL target
            cmd.extend(non_flag_args)
        elif target and not target.startswith(("http://", "https://")):
            # Target is not a URL - use it as search term
            cmd.append(target)
        else:
            raise ValueError(
                "SearchSploit requires a search term. Usage: souleyez run searchsploit 'Apache 2.4.49'"
            )

        # Add remaining flag args (excluding --json which is already added)
        flag_args = [a for a in args if a.startswith("-") and a != "--json"]
        cmd.extend(flag_args)

        return {"cmd": cmd, "timeout": 300}

    def run(
        self, target: str, args: List[str] = None, label: str = "", log_path: str = None
    ) -> int:
        """Execute searchsploit and write JSON output to log_path."""

        # Validate target
        if not target or target.lower() == "none":
            raise ValueError(
                "SearchSploit requires a search term. Usage: souleyez run searchsploit 'Apache 2.4.49'"
            )

        args = args or []

        # Replace <target> placeholder
        args = [arg.replace("<target>", target) for arg in args]

        # Build command
        cmd = ["searchsploit"]

        # Force JSON output for parsing
        if "--json" not in args:
            cmd.append("--json")

        # Add search term
        cmd.append(target)

        # Add user args (after target for searchsploit)
        cmd.extend(args)

        if not log_path:
            try:
                proc = subprocess.run(cmd, capture_output=True, timeout=60, check=False)
                return proc.returncode
            except Exception:
                return 1

        try:
            # Create metadata header
            with open(log_path, "w", encoding="utf-8", errors="replace") as fh:
                fh.write(f"=== Plugin: SearchSploit ===\n")
                fh.write(f"Target: {target}\n")
                fh.write(f"Args: {args}\n")
                fh.write(f"Label: {label}\n")
                fh.write(
                    f"Started: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}\n"
                )
                fh.write(f"Command: {' '.join(cmd)}\n")
                fh.write(
                    f"Started: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}\n\n"
                )

            # Run searchsploit
            proc = subprocess.run(
                cmd, capture_output=True, timeout=60, check=False, text=True
            )

            # Write output
            with open(log_path, "a", encoding="utf-8", errors="replace") as fh:
                if proc.stdout:
                    fh.write(proc.stdout)

                if proc.stderr:
                    fh.write(f"\n\n# Error output:\n{proc.stderr}\n")

                fh.write(
                    f"\nCompleted: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}\n"
                )
                fh.write(f"Exit Code: {proc.returncode}\n")

            return proc.returncode

        except subprocess.TimeoutExpired:
            with open(log_path, "a", encoding="utf-8", errors="replace") as fh:
                fh.write("\n\nERROR: searchsploit timed out after 60 seconds\n")
            return 124

        except FileNotFoundError:
            with open(log_path, "w", encoding="utf-8", errors="replace") as fh:
                fh.write("ERROR: searchsploit not found in PATH\n")
                fh.write("Install: apt install exploitdb\n")
            return 127

        except Exception as e:
            with open(log_path, "a", encoding="utf-8", errors="replace") as fh:
                fh.write(f"\n\nERROR: {type(e).__name__}: {e}\n")
            return 1


plugin = SearchSploitPlugin()
