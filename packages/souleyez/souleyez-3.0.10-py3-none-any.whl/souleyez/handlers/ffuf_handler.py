#!/usr/bin/env python3
"""
Ffuf handler.

Consolidates parsing and display logic for ffuf fuzzing jobs.
"""

import logging
import os
import re
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import click

from souleyez.engine.job_status import (
    STATUS_DONE,
    STATUS_ERROR,
    STATUS_NO_RESULTS,
    STATUS_WARNING,
)
from souleyez.handlers.base import BaseToolHandler

logger = logging.getLogger(__name__)


class FfufHandler(BaseToolHandler):
    """Handler for ffuf fuzzing jobs."""

    tool_name = "ffuf"
    display_name = "Ffuf"

    # All handlers enabled
    has_error_handler = True
    has_warning_handler = True
    has_no_results_handler = True
    has_done_handler = True

    # Security concern patterns (shared with gobuster)
    SECURITY_CONCERN_PATTERNS = {
        "lfi_php_wrapper": {
            "patterns": [r"php://filter", r"php://input", r"data://", r"expect://"],
            "label": "LFI via PHP wrapper (SOURCE CODE EXPOSURE)",
            "severity": "critical",
        },
        "lfi_etc_passwd": {
            "patterns": [r"/etc/passwd", r"/etc/shadow", r"/etc/group"],
            "label": "LFI - System file readable",
            "severity": "critical",
        },
        "lfi_traversal": {
            "patterns": [
                r"\.\./.*passwd",
                r"\.\./.*shadow",
                r"\.\./.*config",
                r"\.\.[\\/]",
            ],
            "label": "LFI via directory traversal",
            "severity": "critical",
        },
        "lfi_log_files": {
            "patterns": [
                r"/var/log/",
                r"/var/mail/",
                r"/proc/self/",
                r"access\.log",
                r"error\.log",
                r"auth\.log",
            ],
            "label": "LFI - Log/proc file readable",
            "severity": "high",
        },
        "lfi_ssh_keys": {
            "patterns": [r"\.ssh/id_rsa", r"\.ssh/authorized_keys", r"\.bash_history"],
            "label": "LFI - SSH keys/history exposed",
            "severity": "critical",
        },
        "database_files": {
            "patterns": [
                r"\.sql$",
                r"\.db$",
                r"\.mdb$",
                r"\.sqlite",
                r"/db\.",
                r"/database\.",
                r"\.bak\.sql",
                r"database\.yml",
            ],
            "label": "Database file exposed",
            "severity": "high",
        },
        "backup_files": {
            "patterns": [
                r"\.bak$",
                r"\.old$",
                r"\.backup$",
                r"\.orig$",
                r"\.save$",
                r"\.swp$",
                r"~$",
                r"\.zip$",
                r"\.tar",
                r"\.gz$",
                r"\.rar$",
            ],
            "label": "Backup/archive file",
            "severity": "high",
        },
        "config_files": {
            "patterns": [
                r"web\.config",
                r"\.htaccess",
                r"\.htpasswd",
                r"\.env$",
                r"config\.php",
                r"config\.inc",
                r"settings\.py",
                r"\.ini$",
                r"\.conf$",
                r"\.cfg$",
                r"wp-config\.php",
            ],
            "label": "Configuration file exposed",
            "severity": "high",
        },
        "source_files": {
            "patterns": [
                r"\.git(/|$)",
                r"\.svn(/|$)",
                r"\.DS_Store",
                r"\.vscode(/|$)",
                r"\.idea(/|$)",
                r"Thumbs\.db",
                r"\.log$",
                r"debug\.",
                r"test\.php",
                r"phpinfo",
            ],
            "label": "Development/debug file",
            "severity": "medium",
        },
        "legacy_dirs": {
            "patterns": [
                r"_vti_",
                r"/cgi-bin(/|$)",
                r"/cgi(/|$)",
                r"/fcgi(/|$)",
                r"/admin(/|$)",
                r"/administrator(/|$)",
                r"/phpmyadmin(/|$)",
                r"/pma(/|$)",
                r"/myadmin(/|$)",
            ],
            "label": "Legacy/admin directory",
            "severity": "medium",
        },
        "sensitive_endpoints": {
            "patterns": [
                r"/upload(/|$)",
                r"/uploads(/|$)",
                r"/file(/|$)",
                r"/files(/|$)",
                r"/tmp(/|$)",
                r"/temp(/|$)",
                r"/private(/|$)",
                r"/internal(/|$)",
                r"/api(/|$)",
                r"/bank(/|$)",
            ],
            "label": "Potentially sensitive directory",
            "severity": "low",
        },
    }

    def parse_job(
        self,
        engagement_id: int,
        log_path: str,
        job: Dict[str, Any],
        host_manager: Optional[Any] = None,
        findings_manager: Optional[Any] = None,
        credentials_manager: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        Parse ffuf job results.

        Extracts discovered paths and stores them in the database.
        """
        try:
            from souleyez.engine.result_handler import detect_tool_error
            from souleyez.parsers.ffuf_parser import parse_ffuf

            # Import managers if not provided
            if host_manager is None:
                from souleyez.storage.hosts import HostManager

                host_manager = HostManager()
            if findings_manager is None:
                from souleyez.storage.findings import FindingsManager

                findings_manager = FindingsManager()

            target = job.get("target", "")
            parsed = parse_ffuf(log_path, target)

            if "error" in parsed:
                return parsed

            # Extract base target for host tracking
            parsed_url = urlparse(target.replace("FUZZ", ""))
            target_host = parsed_url.hostname or target

            host_id = None
            if target_host:
                result = host_manager.add_or_update_host(
                    engagement_id, {"ip": target_host, "status": "up"}
                )
                if isinstance(result, dict):
                    host_id = result.get("id")
                else:
                    host_id = result

            # Store web paths
            paths_added = 0
            created_findings = []

            if host_id and parsed.get("paths"):
                try:
                    from souleyez.storage.web_paths import WebPathsManager

                    wpm = WebPathsManager()
                    paths_added = wpm.bulk_add_web_paths(host_id, parsed["paths"])
                except Exception as e:
                    logger.warning(f"Failed to store web paths: {e}")

                # Create findings for sensitive paths
                created_findings = self._create_findings_for_sensitive_paths(
                    engagement_id, host_id, parsed["paths"], findings_manager
                )

                # Auto-extract credentials from PHP filter LFI results
                if credentials_manager is None:
                    from souleyez.storage.credentials import CredentialsManager

                    credentials_manager = CredentialsManager()

                extracted_creds = self._extract_lfi_credentials(
                    engagement_id,
                    host_id,
                    parsed["paths"],
                    credentials_manager,
                    findings_manager,
                )
                if extracted_creds:
                    logger.info(
                        f"LFI auto-extraction: Found {len(extracted_creds)} credential(s)"
                    )

            # Check for ffuf errors
            with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                log_content = f.read()
            ffuf_error = detect_tool_error(log_content, "ffuf")

            # Determine status
            if ffuf_error:
                status = STATUS_ERROR
            elif parsed.get("results_found", 0) > 0:
                status = STATUS_DONE
            else:
                status = STATUS_NO_RESULTS

            # Build summary for job queue display
            summary_parts = []
            results_found = parsed.get("results_found", 0)
            if results_found > 0:
                summary_parts.append(f"{results_found} result(s)")
            if len(created_findings) > 0:
                summary_parts.append(f"{len(created_findings)} finding(s)")
            summary = " | ".join(summary_parts) if summary_parts else "No results"

            return {
                "tool": "ffuf",
                "status": status,
                "summary": summary,
                "target": target,
                "results_found": parsed.get("results_found", 0),
                "paths_added": paths_added,
                "findings_added": len(created_findings),
                "method": parsed.get("method"),
                "parameters_found": parsed.get("paths", []),
            }

        except Exception as e:
            logger.error(f"Error parsing ffuf job: {e}")
            return {"error": str(e)}

    def _create_findings_for_sensitive_paths(
        self, engagement_id: int, host_id: int, paths: List[Dict], findings_manager: Any
    ) -> List[Dict]:
        """Create findings for sensitive/interesting paths discovered."""
        created_findings = []

        for path_entry in paths:
            url = path_entry.get("url", "").lower()
            for concern_type, concern_info in self.SECURITY_CONCERN_PATTERNS.items():
                for pattern in concern_info["patterns"]:
                    if re.search(pattern, url, re.IGNORECASE):
                        try:
                            findings_manager.add_finding(
                                engagement_id=engagement_id,
                                host_id=host_id,
                                title=f"{concern_info['label']}: {url.split('/')[-1]}",
                                finding_type="web_path",
                                severity=concern_info["severity"],
                                description=f"Ffuf discovered a potentially sensitive path: {path_entry.get('url', '')}\n"
                                f"Status code: {path_entry.get('status_code', 'unknown')}\n"
                                f"Category: {concern_info['label']}",
                                tool="ffuf",
                            )
                            created_findings.append(
                                {
                                    "url": path_entry.get("url"),
                                    "type": concern_type,
                                    "severity": concern_info["severity"],
                                }
                            )
                        except Exception as e:
                            logger.warning(f"Failed to create finding: {e}")
                        break

        return created_findings

    def _extract_lfi_credentials(
        self,
        engagement_id: int,
        host_id: int,
        paths: List[Dict],
        credentials_manager: Any,
        findings_manager: Any,
    ) -> List[Dict]:
        """
        Auto-extract credentials from successful PHP filter LFI results.

        When php://filter/convert.base64-encode URLs are found, fetch them,
        decode the base64, and parse for credentials.
        """
        import base64

        import requests

        extracted_creds = []

        # Find PHP filter URLs (config files are most valuable)
        php_filter_urls = []
        for path_entry in paths:
            url = path_entry.get("url", "")
            if "php://filter" in url and "base64-encode" in url:
                # Prioritize config files
                if any(
                    kw in url.lower()
                    for kw in ["config", "database", "settings", "db", "connect"]
                ):
                    php_filter_urls.insert(0, url)  # High priority
                else:
                    php_filter_urls.append(url)

        if not php_filter_urls:
            return []

        logger.info(
            f"LFI auto-extraction: Found {len(php_filter_urls)} PHP filter URL(s)"
        )

        # Credential patterns to search for in decoded PHP
        cred_patterns = [
            # PHP variable assignments
            (r'\$(?:password|passwd|pass|pwd)\s*=\s*["\']([^"\']+)["\']', "password"),
            (r'\$(?:username|user|usr|login)\s*=\s*["\']([^"\']+)["\']', "username"),
            (r'\$(?:database|db|dbname|db_name)\s*=\s*["\']([^"\']+)["\']', "database"),
            (r'\$(?:server|host|hostname|db_host)\s*=\s*["\']([^"\']+)["\']', "host"),
            # Array-style configs
            (r'["\']password["\']\s*=>\s*["\']([^"\']+)["\']', "password"),
            (r'["\']username["\']\s*=>\s*["\']([^"\']+)["\']', "username"),
            (r'["\']database["\']\s*=>\s*["\']([^"\']+)["\']', "database"),
            (r'["\']host["\']\s*=>\s*["\']([^"\']+)["\']', "host"),
            # Define constants
            (
                r"define\s*\(\s*['\"]DB_PASSWORD['\"]\s*,\s*['\"]([^'\"]+)['\"]\s*\)",
                "password",
            ),
            (
                r"define\s*\(\s*['\"]DB_USER['\"]\s*,\s*['\"]([^'\"]+)['\"]\s*\)",
                "username",
            ),
            (
                r"define\s*\(\s*['\"]DB_NAME['\"]\s*,\s*['\"]([^'\"]+)['\"]\s*\)",
                "database",
            ),
            (r"define\s*\(\s*['\"]DB_HOST['\"]\s*,\s*['\"]([^'\"]+)['\"]\s*\)", "host"),
        ]

        # Try to fetch and parse each URL (limit to prevent abuse)
        max_fetch = 5
        for url in php_filter_urls[:max_fetch]:
            try:
                logger.info(f"  Fetching: {url}")
                resp = requests.get(
                    url, timeout=10, verify=False
                )  # nosec B501 - pentesting tool

                if resp.status_code != 200:
                    continue

                # Extract base64 from response (usually in HTML body)
                html = resp.text

                # Look for base64 content - usually a long string of alphanumeric + /+=
                base64_pattern = r"([A-Za-z0-9+/]{50,}={0,2})"
                matches = re.findall(base64_pattern, html)

                for b64_match in matches:
                    try:
                        decoded = base64.b64decode(b64_match).decode(
                            "utf-8", errors="ignore"
                        )

                        # Skip if it doesn't look like PHP
                        if "<?php" not in decoded and "$" not in decoded:
                            continue

                        logger.info(f"  Decoded PHP source ({len(decoded)} bytes)")

                        # Extract credentials
                        creds = {"source": url, "source_file": "config.php"}
                        for pattern, field in cred_patterns:
                            match = re.search(pattern, decoded, re.IGNORECASE)
                            if match:
                                creds[field] = match.group(1)

                        # If we found at least username and password, store it
                        if creds.get("username") and creds.get("password"):
                            logger.info(
                                f"  Found credentials: {creds.get('username')}:***"
                            )

                            # Store in credentials manager
                            try:
                                credentials_manager.add_credential(
                                    engagement_id=engagement_id,
                                    host_id=host_id,
                                    username=creds.get("username"),
                                    password=creds.get("password"),
                                    credential_type="database",
                                    service=creds.get("database", "mysql"),
                                    source="LFI auto-extraction",
                                    notes=f"Extracted from {url}\nDatabase: {creds.get('database', 'unknown')}\nHost: {creds.get('host', 'localhost')}",
                                )
                                extracted_creds.append(creds)
                            except Exception as e:
                                logger.warning(f"Failed to store credential: {e}")

                            # Also create a critical finding
                            try:
                                findings_manager.add_finding(
                                    engagement_id=engagement_id,
                                    host_id=host_id,
                                    title=f"LFI Credential Extraction: {creds.get('username')}@{creds.get('database', 'database')}",
                                    finding_type="credential",
                                    severity="critical",
                                    description=f"Credentials automatically extracted via LFI:\n\n"
                                    f"Username: {creds.get('username')}\n"
                                    f"Database: {creds.get('database', 'unknown')}\n"
                                    f"Host: {creds.get('host', 'localhost')}\n\n"
                                    f"Source URL: {url}\n\n"
                                    f"This indicates a critical LFI vulnerability that exposes database credentials.",
                                    tool="ffuf",
                                )
                            except Exception as e:
                                logger.warning(f"Failed to create finding: {e}")

                            break  # Found creds in this URL, move to next

                    except Exception as e:
                        logger.debug(f"Failed to decode base64: {e}")
                        continue

            except requests.RequestException as e:
                logger.warning(f"Failed to fetch {url}: {e}")
                continue
            except Exception as e:
                logger.warning(f"Error processing {url}: {e}")
                continue

        return extracted_creds

    def _identify_security_concerns(self, paths: List[Dict]) -> List[Dict]:
        """Identify security concerns in discovered paths."""
        concerns = []

        for path_entry in paths:
            url = path_entry.get("url", "").lower()
            for concern_type, concern_info in self.SECURITY_CONCERN_PATTERNS.items():
                for pattern in concern_info["patterns"]:
                    if re.search(pattern, url, re.IGNORECASE):
                        concerns.append(
                            {
                                "url": path_entry.get("url", ""),
                                "type": concern_type,
                                "label": concern_info["label"],
                                "severity": concern_info["severity"],
                                "status_code": path_entry.get("status_code", "unknown"),
                            }
                        )
                        break

        return concerns

    def display_done(
        self,
        job: Dict[str, Any],
        log_path: str,
        show_all: bool = False,
        show_passwords: bool = False,
    ) -> None:
        """Display successful ffuf scan results."""
        try:
            from souleyez.parsers.ffuf_parser import parse_ffuf

            if not log_path or not os.path.exists(log_path):
                return

            parsed = parse_ffuf(log_path, job.get("target", ""))
            paths = parsed.get("paths", [])

            if not paths:
                self.display_no_results(job, log_path)
                return

            # Identify security concerns
            security_concerns = self._identify_security_concerns(paths)

            # Display security concerns if found
            if security_concerns:
                click.echo(click.style("=" * 70, fg="red"))
                click.echo(click.style("SECURITY CONCERNS", bold=True, fg="red"))
                click.echo(click.style("=" * 70, fg="red"))
                click.echo()

                critical_concerns = [
                    c for c in security_concerns if c["severity"] == "critical"
                ]
                high_concerns = [
                    c for c in security_concerns if c["severity"] == "high"
                ]
                medium_concerns = [
                    c for c in security_concerns if c["severity"] == "medium"
                ]
                low_concerns = [c for c in security_concerns if c["severity"] == "low"]

                if critical_concerns:
                    click.echo(
                        click.style(
                            "[CRITICAL] LFI VULNERABILITY CONFIRMED:",
                            fg="red",
                            bold=True,
                            blink=True,
                        )
                    )
                    by_label = {}
                    for c in critical_concerns:
                        if c["label"] not in by_label:
                            by_label[c["label"]] = []
                        by_label[c["label"]].append(c["url"])
                    for label, urls in by_label.items():
                        click.echo(click.style(f"  - {label}:", fg="red"))
                        for url in urls[:5]:
                            click.echo(f"    {url}")
                        if len(urls) > 5:
                            click.echo(f"    ... and {len(urls) - 5} more")
                    click.echo()

                if high_concerns:
                    click.echo(
                        click.style("[HIGH] Critical findings:", fg="red", bold=True)
                    )
                    by_label = {}
                    for c in high_concerns:
                        if c["label"] not in by_label:
                            by_label[c["label"]] = []
                        by_label[c["label"]].append(c["url"])
                    for label, urls in by_label.items():
                        click.echo(click.style(f"  - {label}:", fg="red"))
                        for url in urls[:5]:
                            click.echo(f"    {url}")
                        if len(urls) > 5:
                            click.echo(f"    ... and {len(urls) - 5} more")
                    click.echo()

                if medium_concerns:
                    click.echo(
                        click.style(
                            "[MEDIUM] Notable findings:", fg="yellow", bold=True
                        )
                    )
                    by_label = {}
                    for c in medium_concerns:
                        if c["label"] not in by_label:
                            by_label[c["label"]] = []
                        by_label[c["label"]].append(c["url"])
                    for label, urls in by_label.items():
                        click.echo(click.style(f"  - {label}:", fg="yellow"))
                        for url in urls[:5]:
                            click.echo(f"    {url}")
                        if len(urls) > 5:
                            click.echo(f"    ... and {len(urls) - 5} more")
                    click.echo()

                if low_concerns:
                    click.echo(
                        click.style("[LOW] Worth investigating:", fg="cyan", bold=True)
                    )
                    by_label = {}
                    for c in low_concerns:
                        if c["label"] not in by_label:
                            by_label[c["label"]] = []
                        by_label[c["label"]].append(c["url"])
                    for label, urls in by_label.items():
                        click.echo(f"  - {label}: {len(urls)} path(s)")
                    click.echo()

            # Display discovered paths
            click.echo(click.style("=" * 70, fg="cyan"))
            click.echo(click.style("FFUF DISCOVERED PATHS", bold=True, fg="cyan"))
            click.echo(click.style("=" * 70, fg="cyan"))
            click.echo()
            click.echo(f"Total found: {len(paths)}")
            if parsed.get("method"):
                click.echo(f"Method: {parsed.get('method')}")
            click.echo()

            # Group by status code
            status_groups = {}
            for path in paths:
                status = path.get("status_code", "unknown")
                if status not in status_groups:
                    status_groups[status] = []
                status_groups[status].append(path)

            # Display by status code
            for status in sorted(status_groups.keys()):
                status_color = (
                    "green"
                    if status == 200
                    else "cyan" if status in [301, 302] else "yellow"
                )
                click.echo(
                    click.style(
                        f"[{status}] ({len(status_groups[status])} paths)",
                        bold=True,
                        fg=status_color,
                    )
                )

                paths_to_show = (
                    status_groups[status] if show_all else status_groups[status][:10]
                )

                for path in paths_to_show:
                    url = path.get("url", "")
                    size = path.get("size", "")
                    redirect = path.get("redirect", "")

                    if redirect:
                        click.echo(f"  {url} -> {redirect}")
                    elif size:
                        click.echo(f"  {url} ({size} bytes)")
                    else:
                        click.echo(f"  {url}")

                if not show_all and len(status_groups[status]) > 10:
                    click.echo(f"  ... and {len(status_groups[status]) - 10} more")
                click.echo()

            click.echo(click.style("=" * 70, fg="cyan"))
            click.echo()

        except Exception as e:
            logger.debug(f"Error in display_done: {e}")

    def display_warning(
        self,
        job: Dict[str, Any],
        log_path: str,
        log_content: Optional[str] = None,
    ) -> None:
        """Display warning status for ffuf scan."""
        click.echo(click.style("=" * 70, fg="yellow"))
        click.echo(click.style("[WARNING] FFUF SCAN", bold=True, fg="yellow"))
        click.echo(click.style("=" * 70, fg="yellow"))
        click.echo()
        click.echo("  Scan completed with warnings. Check raw logs for details.")
        click.echo("  Press [r] to view raw logs.")
        click.echo()
        click.echo(click.style("=" * 70, fg="yellow"))
        click.echo()

    def display_error(
        self,
        job: Dict[str, Any],
        log_path: str,
        log_content: Optional[str] = None,
    ) -> None:
        """Display error status for ffuf scan."""
        # Read log if not provided
        if log_content is None and log_path and os.path.exists(log_path):
            try:
                with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                    log_content = f.read()
            except Exception:
                log_content = ""

        click.echo(click.style("=" * 70, fg="red"))
        click.echo(click.style("[ERROR] FFUF SCAN FAILED", bold=True, fg="red"))
        click.echo(click.style("=" * 70, fg="red"))
        click.echo()

        # Check if it was a timeout
        if log_content and (
            "timed out" in log_content.lower() or "Command timed out" in log_content
        ):
            click.echo("  Scan reached timeout before completing.")
            click.echo()
            click.echo(click.style("  Possible causes:", fg="bright_black"))
            click.echo(
                click.style("    - Target is rate limiting requests", fg="bright_black")
            )
            click.echo(
                click.style(
                    "    - Wordlist too large for timeout window", fg="bright_black"
                )
            )
            click.echo(click.style("    - Network latency issues", fg="bright_black"))
            click.echo()
            click.echo(click.style("  Suggestions:", fg="bright_black"))
            click.echo(click.style("    - Try smaller wordlist", fg="bright_black"))
            click.echo(
                click.style(
                    "    - Increase -p (delay) between requests", fg="bright_black"
                )
            )
            click.echo(click.style("    - Reduce -t (threads)", fg="bright_black"))
        else:
            error_msg = None
            if log_content and "ERROR:" in log_content:
                match = re.search(r"ERROR:\s*(.+?)(?:\n|$)", log_content)
                if match:
                    error_msg = match.group(1).strip()

            if error_msg:
                click.echo(f"  Error: {error_msg}")
            else:
                click.echo("  Scan failed - see raw logs for details.")
                click.echo("  Press [r] to view raw logs.")

        click.echo()
        click.echo(click.style("=" * 70, fg="red"))
        click.echo()

    def display_no_results(
        self,
        job: Dict[str, Any],
        log_path: str,
    ) -> None:
        """Display no_results status for ffuf scan."""
        click.echo(click.style("=" * 70, fg="cyan"))
        click.echo(click.style("FFUF SCAN RESULTS", bold=True, fg="cyan"))
        click.echo(click.style("=" * 70, fg="cyan"))
        click.echo()
        click.echo("  No paths discovered.")
        click.echo()

        # Try to get config info from parsed results
        if log_path and os.path.exists(log_path):
            try:
                from souleyez.parsers.ffuf_parser import parse_ffuf

                parsed = parse_ffuf(log_path, job.get("target", ""))
                if parsed.get("wordlist"):
                    click.echo(f"  Wordlist: {os.path.basename(parsed['wordlist'])}")
                if parsed.get("method"):
                    click.echo(f"  Method: {parsed['method']}")
            except Exception:
                pass

        click.echo()
        click.echo(click.style("  This could mean:", fg="bright_black"))
        click.echo(
            click.style(
                "    - Target has good security (no exposed paths)", fg="bright_black"
            )
        )
        click.echo(
            click.style("    - Try a different/larger wordlist", fg="bright_black")
        )
        click.echo(
            click.style(
                "    - Check filter settings (-fc, -fs, -fw)", fg="bright_black"
            )
        )
        click.echo(
            click.style(
                "    - Target may be blocking automated requests", fg="bright_black"
            )
        )
        click.echo()
        click.echo(click.style("=" * 70, fg="cyan"))
        click.echo()
