#!/usr/bin/env python3
"""
Gobuster handler.

Consolidates parsing and display logic for Gobuster directory enumeration jobs.
"""

import logging
import os
import re
import socket
import ssl
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, urlparse

import click
import defusedxml.ElementTree as ElementTree  # Safe XML parsing

from souleyez.engine.job_status import (
    STATUS_DONE,
    STATUS_ERROR,
    STATUS_NO_RESULTS,
    STATUS_WARNING,
)
from souleyez.handlers.base import BaseToolHandler

logger = logging.getLogger(__name__)


class GobusterHandler(BaseToolHandler):
    """Handler for Gobuster directory enumeration jobs."""

    tool_name = "gobuster"
    display_name = "Gobuster"

    # All handlers enabled
    has_error_handler = True
    has_warning_handler = True
    has_no_results_handler = True
    has_done_handler = True

    # Security concern patterns for sensitive path detection
    SECURITY_CONCERN_PATTERNS = {
        "home_directory": {
            "patterns": [
                r"\.bashrc$",
                r"\.profile$",
                r"\.bash_profile$",
                r"\.bash_history$",
                r"\.zshrc$",
            ],
            "label": "Home directory exposed (misconfigured web root)",
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

    # High-value directory keywords for auto-chaining
    HIGH_VALUE_DIR_KEYWORDS = [
        "mutillidae",
        "dvwa",
        "bwapp",
        "webgoat",
        "phpmyadmin",
        "juice",
        "juice-shop",
        "hackazon",
        "pentesterlab",
        "vulnhub",
        "api",
        "rest",
        "graphql",
        "drupal",
        "wordpress",
        "joomla",
        "moodle",
        "magento",
        "phpbb",
        "opencart",
        "prestashop",
        "zen-cart",
        "oscommerce",
        # WordPress directory indicators (trigger wpscan chains)
        "wp-content",
        "wp-admin",
        "wp-includes",
    ]

    # Files to extract content from when discovered (for chaining)
    # These files often contain paths that aren't in standard wordlists
    CONTENT_EXTRACTION_FILES = {
        "robots.txt": "_extract_robots_paths",
        "sitemap.xml": "_extract_sitemap_urls",
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
        Parse Gobuster job results.

        Extracts discovered paths and stores them in the database.
        """
        try:
            from souleyez.engine.result_handler import detect_tool_error
            from souleyez.parsers.gobuster_parser import (
                get_paths_stats,
                parse_gobuster_output,
            )

            # Import managers if not provided
            if host_manager is None:
                from souleyez.storage.hosts import HostManager

                host_manager = HostManager()
            if findings_manager is None:
                from souleyez.storage.findings import FindingsManager

                findings_manager = FindingsManager()

            # Read the log file
            with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                log_content = f.read()

            # Parse gobuster output
            target = job.get("target", "")
            parsed = parse_gobuster_output(log_content, target)

            # Get or create host from target URL
            host_id = None
            if parsed["target_url"]:
                parsed_url = urlparse(parsed["target_url"])
                hostname = parsed_url.hostname

                if hostname:
                    hosts = host_manager.list_hosts(engagement_id)
                    for host in hosts:
                        if (
                            host.get("hostname") == hostname
                            or host.get("ip_address") == hostname
                        ):
                            host_id = host["id"]
                            break

                    if not host_id:
                        is_ip = re.match(
                            r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", hostname
                        )
                        if is_ip:
                            result = host_manager.add_or_update_host(
                                engagement_id, {"ip": hostname, "status": "up"}
                            )
                            if isinstance(result, dict):
                                host_id = result.get("id")
                            else:
                                host_id = result

            # Store web paths
            paths_added = 0
            created_findings = []

            if host_id and parsed["paths"]:
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

            stats = get_paths_stats(parsed)

            # Extract PHP files for auto-chaining
            php_files = [
                (path.get("url"), path.get("status_code"))
                for path in parsed["paths"]
                if path.get("url", "").endswith(".php")
                and path.get("status_code") in [200, 401, 403]
            ]

            # Extract ASP/ASPX files
            asp_files = [
                (path.get("url"), path.get("status_code"))
                for path in parsed["paths"]
                if (
                    path.get("url", "").lower().endswith(".asp")
                    or path.get("url", "").lower().endswith(".aspx")
                )
                and path.get("status_code") in [200, 401, 403]
            ]

            # Extract high-value directories from redirects
            # Include all redirect codes: 301, 302, 303, 307, 308
            # 302 is common for CMS paths (e.g., /dashboard -> /wp-admin/)
            high_value_dirs = []
            redirect_codes = [301, 302, 303, 307, 308]
            for path in parsed["paths"]:
                if path.get("status_code") in redirect_codes and path.get("redirect"):
                    url = path.get("url", "").lower()
                    redirect = path.get("redirect", "").lower()
                    if any(
                        keyword in url or keyword in redirect
                        for keyword in self.HIGH_VALUE_DIR_KEYWORDS
                    ):
                        high_value_dirs.append(path.get("redirect"))

            # Check for wildcard response
            wildcard_detected = False
            exclude_length = None
            if "the server returns a status code that matches" in log_content:
                wildcard_detected = True
                length_match = re.search(r"\(Length: (\d+)\)", log_content)
                if length_match:
                    exclude_length = length_match.group(1)

            # Check for host-level redirect
            host_redirect_detected = False
            redirect_target = None
            if "HOST_REDIRECT_TARGET:" in log_content:
                host_redirect_detected = True
                redirect_match = re.search(
                    r"HOST_REDIRECT_TARGET:\s*(\S+)", log_content
                )
                if redirect_match:
                    redirect_target = redirect_match.group(1)

            # Check for gobuster errors
            gobuster_error = detect_tool_error(log_content, "gobuster")

            # Check for home directory exposure (.bashrc, .profile = web root is a home dir)
            home_dir_files = [
                path.get("url")
                for path in parsed["paths"]
                if any(
                    path.get("url", "").endswith(f)
                    for f in [".bashrc", ".profile", ".bash_profile", ".zshrc"]
                )
                and path.get("status_code") == 200
            ]
            home_directory_exposure = len(home_dir_files) > 0

            # Determine status
            if gobuster_error:
                status = STATUS_ERROR
            elif host_redirect_detected:
                status = STATUS_WARNING
            elif wildcard_detected:
                status = STATUS_WARNING
            elif stats["total"] > 0:
                status = STATUS_DONE
            else:
                status = STATUS_NO_RESULTS

            # === CONTENT EXTRACTION (safe/additive) ===
            # Extract paths from robots.txt, sitemap.xml if found
            # This is wrapped in try/except - failures don't affect existing results
            extracted_content = {"extracted_paths": [], "extraction_sources": []}
            try:
                if parsed["paths"] and parsed.get("target_url"):
                    extracted_content = self._extract_content_from_discovered_files(
                        parsed["paths"], parsed["target_url"]
                    )
            except Exception as e:
                # Log but never fail the job
                logger.debug(f"Content extraction skipped: {e}")

            # Build summary for job queue display
            summary_parts = []
            if stats["total"] > 0:
                summary_parts.append(f"{stats['total']} path(s)")
            if len(created_findings) > 0:
                summary_parts.append(f"{len(created_findings)} finding(s)")
            if wildcard_detected:
                summary_parts.append("wildcard")
            summary = " | ".join(summary_parts) if summary_parts else "No paths found"

            result = {
                "tool": "gobuster",
                "status": status,
                "summary": summary,
                "paths_added": paths_added,
                "total_paths": stats["total"],
                "paths_found": stats["total"],
                "redirects_found": stats.get("redirects", 0),
                "by_status": stats["by_status"],
                "target_url": parsed.get("target_url"),
                "findings": created_findings,
                "php_files": php_files,
                "asp_files": asp_files,
                "high_value_dirs": high_value_dirs,
                "home_directory_exposure": home_directory_exposure,
                # New: extracted paths from robots.txt/sitemap.xml for chaining
                "extracted_paths": extracted_content.get("extracted_paths", []),
                "extraction_sources": extracted_content.get("extraction_sources", []),
            }

            if wildcard_detected:
                result["wildcard_detected"] = True
                if exclude_length:
                    result["exclude_length"] = exclude_length

            if host_redirect_detected:
                result["host_redirect_detected"] = True
                if redirect_target:
                    result["redirect_target"] = redirect_target

            return result

        except Exception as e:
            logger.error(f"Error parsing gobuster job: {e}")
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
                                title=f"{concern_info['label']}: {path_entry.get('path', '')}",
                                finding_type="web_path",
                                severity=concern_info["severity"],
                                description=f"Gobuster discovered a potentially sensitive path: {path_entry.get('url', '')}\n"
                                f"Status code: {path_entry.get('status_code', 'unknown')}\n"
                                f"Category: {concern_info['label']}",
                                tool="gobuster",
                            )
                            created_findings.append(
                                {
                                    "url": path_entry.get("url"),
                                    "title": f"{concern_info['label']}: {path_entry.get('path', '')}",
                                    "type": concern_type,
                                    "severity": concern_info["severity"],
                                }
                            )
                        except Exception as e:
                            logger.warning(f"Failed to create finding: {e}")
                        break

        return created_findings

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

    def _extract_content_from_discovered_files(
        self,
        paths: List[Dict],
        base_url: str,
    ) -> Dict[str, Any]:
        """
        Extract additional paths/URLs from discovered files like robots.txt and sitemap.xml.

        This is wrapped in comprehensive error handling - if ANYTHING fails,
        we return empty results and let the normal flow continue.

        Args:
            paths: List of discovered paths from gobuster
            base_url: Base URL of the target

        Returns:
            Dict with extracted_paths list and metadata
        """
        result = {
            "extracted_paths": [],
            "extraction_sources": [],
            "extraction_errors": [],
        }

        try:
            # Find extractable files in discovered paths
            for path_entry in paths:
                url = path_entry.get("url", "")
                status = path_entry.get("status_code")

                # Only process 200 OK responses
                if status != 200:
                    continue

                # Check if this is an extractable file
                for filename, extractor_method in self.CONTENT_EXTRACTION_FILES.items():
                    if url.lower().endswith(filename):
                        try:
                            extractor = getattr(self, extractor_method)
                            extracted = extractor(url, base_url)
                            if extracted:
                                result["extracted_paths"].extend(extracted)
                                result["extraction_sources"].append(
                                    {
                                        "file": filename,
                                        "url": url,
                                        "paths_found": len(extracted),
                                    }
                                )
                                logger.info(
                                    f"Extracted {len(extracted)} paths from {url}"
                                )
                        except Exception as e:
                            # Log but don't fail - this is purely additive
                            logger.warning(f"Failed to extract from {url}: {e}")
                            result["extraction_errors"].append(
                                {
                                    "file": filename,
                                    "url": url,
                                    "error": str(e),
                                }
                            )
                        break

            # Deduplicate extracted paths
            seen = set()
            unique_paths = []
            for path in result["extracted_paths"]:
                if path not in seen:
                    seen.add(path)
                    unique_paths.append(path)
            result["extracted_paths"] = unique_paths

        except Exception as e:
            # Catch-all: if anything unexpected happens, log and return empty
            logger.warning(f"Content extraction failed (non-fatal): {e}")
            result["extraction_errors"].append({"error": str(e)})

        return result

    def _extract_robots_paths(self, robots_url: str, base_url: str) -> List[str]:
        """
        Fetch and parse robots.txt to extract Disallow/Allow paths.

        Args:
            robots_url: Full URL to robots.txt
            base_url: Base URL for constructing full paths

        Returns:
            List of full URLs to scan
        """
        paths = []

        try:
            # Validate URL scheme (security: prevent file:// and other schemes)
            parsed = urlparse(robots_url)
            if parsed.scheme.lower() not in ("http", "https"):
                logger.debug(
                    f"Skipping robots.txt fetch - invalid scheme: {parsed.scheme}"
                )
                return paths

            # Create SSL context that ignores cert errors (for self-signed)
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE

            req = urllib.request.Request(
                robots_url,
                headers={"User-Agent": "Mozilla/5.0 (compatible; SoulEyez/1.0)"},
            )

            with urllib.request.urlopen(
                req, timeout=10, context=ctx
            ) as response:  # nosec B310
                content = response.read().decode("utf-8", errors="replace")

            # Known robots.txt directives to skip
            known_directives = [
                "user-agent:",
                "disallow:",
                "allow:",
                "sitemap:",
                "crawl-delay:",
                "host:",
                "request-rate:",
            ]

            # Parse robots.txt format
            for line in content.split("\n"):
                line = line.strip()

                # Skip comments and empty lines
                if not line or line.startswith("#"):
                    continue

                line_lower = line.lower()

                # Extract Disallow and Allow paths (standard format)
                if line_lower.startswith("disallow:") or line_lower.startswith(
                    "allow:"
                ):
                    _, _, path = line.partition(":")
                    path = path.strip()

                    # Skip empty paths, wildcards, and query strings
                    if not path or path == "/" or "*" in path or "?" in path:
                        continue

                    # Build full URL
                    full_url = urljoin(base_url.rstrip("/") + "/", path.lstrip("/"))

                    if full_url not in paths:
                        paths.append(full_url)

                # Extract bare paths (CTF-style hints like "key-1-of-3.txt")
                # These are non-standard but common in CTFs and some configs
                # Only extract if it looks like a file (has extension) to avoid garbage
                elif not any(line_lower.startswith(d) for d in known_directives):
                    path = line.strip()
                    # Must look like a file with extension (1-5 char extension)
                    # Examples: key-1-of-3.txt, fsocity.dic, backup.sql
                    if path and re.match(r"^[\w\-./]+\.\w{1,5}$", path):
                        # Build full URL
                        full_url = urljoin(base_url.rstrip("/") + "/", path.lstrip("/"))

                        if full_url not in paths:
                            paths.append(full_url)
                            logger.debug(f"Extracted bare path from robots.txt: {path}")

            logger.debug(f"Extracted {len(paths)} paths from robots.txt")

        except Exception as e:
            logger.debug(f"Failed to fetch/parse robots.txt: {e}")
            # Don't raise - just return empty list

        return paths

    def _extract_sitemap_urls(self, sitemap_url: str, base_url: str) -> List[str]:
        """
        Fetch and parse sitemap.xml to extract URLs.

        Args:
            sitemap_url: Full URL to sitemap.xml
            base_url: Base URL (not used but kept for consistent interface)

        Returns:
            List of URLs from sitemap
        """
        urls = []

        try:
            # Validate URL scheme (security: prevent file:// and other schemes)
            parsed = urlparse(sitemap_url)
            if parsed.scheme.lower() not in ("http", "https"):
                logger.debug(
                    f"Skipping sitemap.xml fetch - invalid scheme: {parsed.scheme}"
                )
                return urls

            # Create SSL context that ignores cert errors (for self-signed)
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE

            req = urllib.request.Request(
                sitemap_url,
                headers={"User-Agent": "Mozilla/5.0 (compatible; SoulEyez/1.0)"},
            )

            with urllib.request.urlopen(
                req, timeout=10, context=ctx
            ) as response:  # nosec B310
                content = response.read().decode("utf-8", errors="replace")

            # Parse XML
            try:
                root = ElementTree.fromstring(content)

                # Handle namespace (sitemaps usually have xmlns)
                ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}

                # Try with namespace first
                for loc in root.findall(".//sm:loc", ns):
                    if loc.text:
                        urls.append(loc.text.strip())

                # If no results, try without namespace
                if not urls:
                    for loc in root.findall(".//loc"):
                        if loc.text:
                            urls.append(loc.text.strip())

            except ElementTree.ParseError:
                # Not valid XML - try regex fallback
                loc_matches = re.findall(r"<loc>([^<]+)</loc>", content)
                urls.extend(loc_matches)

            logger.debug(f"Extracted {len(urls)} URLs from sitemap.xml")

        except Exception as e:
            logger.debug(f"Failed to fetch/parse sitemap.xml: {e}")
            # Don't raise - just return empty list

        return urls

    def display_done(
        self,
        job: Dict[str, Any],
        log_path: str,
        show_all: bool = False,
        show_passwords: bool = False,
    ) -> None:
        """Display successful Gobuster scan results."""
        try:
            from souleyez.parsers.gobuster_parser import parse_gobuster_output

            if not log_path or not os.path.exists(log_path):
                return

            with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                log_content = f.read()

            parsed = parse_gobuster_output(log_content, job.get("target", ""))
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

                high_concerns = [
                    c for c in security_concerns if c["severity"] == "high"
                ]
                medium_concerns = [
                    c for c in security_concerns if c["severity"] == "medium"
                ]
                low_concerns = [c for c in security_concerns if c["severity"] == "low"]

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
            click.echo(click.style("DISCOVERED WEB PATHS", bold=True, fg="cyan"))
            click.echo(click.style("=" * 70, fg="cyan"))
            click.echo()
            click.echo(f"Total found: {len(paths)}")
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

            # Show extracted paths from robots.txt/sitemap.xml if any
            try:
                target_url = parsed.get("target_url") or job.get("target", "")
                if target_url and paths:
                    extracted = self._extract_content_from_discovered_files(
                        paths, target_url
                    )
                    extracted_paths = extracted.get("extracted_paths", [])
                    extraction_sources = extracted.get("extraction_sources", [])

                    if extracted_paths:
                        # Format source names from dict list
                        source_names = [
                            s.get("file", "unknown") for s in extraction_sources
                        ]

                        click.echo(click.style("=" * 70, fg="magenta"))
                        click.echo(
                            click.style(
                                "EXTRACTED PATHS (from robots.txt/sitemap.xml)",
                                bold=True,
                                fg="magenta",
                            )
                        )
                        click.echo(click.style("=" * 70, fg="magenta"))
                        click.echo()
                        click.echo(f"Sources: {', '.join(source_names)}")
                        click.echo(f"Paths found: {len(extracted_paths)}")
                        click.echo()
                        click.echo(
                            click.style(
                                "These paths triggered follow-up gobuster scans:",
                                fg="magenta",
                            )
                        )
                        for ep in extracted_paths[:10]:
                            click.echo(f"  {ep}")
                        if len(extracted_paths) > 10:
                            click.echo(f"  ... and {len(extracted_paths) - 10} more")
                        click.echo()
            except Exception as e:
                logger.debug(f"Extraction display failed: {e}")  # Log for debugging

            # Display next steps suggestions
            try:
                from souleyez.parsers.gobuster_parser import generate_next_steps

                next_steps = generate_next_steps(parsed)
                if next_steps:
                    click.echo(click.style("=" * 70, fg="green"))
                    click.echo(
                        click.style("SUGGESTED NEXT STEPS", bold=True, fg="green")
                    )
                    click.echo(click.style("=" * 70, fg="green"))
                    click.echo()
                    for i, step in enumerate(next_steps[:5], 1):
                        click.echo(click.style(f"{i}. {step['title']}", bold=True))
                        click.echo(click.style(f"   Why: {step['reason']}", fg="white"))
                        for cmd in step.get("commands", [])[:2]:
                            click.echo(click.style(f"   $ {cmd}", fg="cyan"))
                        click.echo()
                    if len(next_steps) > 5:
                        click.echo(f"   ... and {len(next_steps) - 5} more suggestions")
                        click.echo()
            except Exception as e:
                logger.debug(f"Next steps display failed: {e}")

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
        """Display warning status for Gobuster scan."""
        # Read log if not provided
        if log_content is None and log_path and os.path.exists(log_path):
            try:
                with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                    log_content = f.read()
            except Exception:
                log_content = ""

        click.echo(click.style("=" * 70, fg="yellow"))
        click.echo(click.style("[WARNING] GOBUSTER SCAN", bold=True, fg="yellow"))
        click.echo(click.style("=" * 70, fg="yellow"))
        click.echo()

        # Check for host redirect
        if log_content and "HOST_REDIRECT_TARGET:" in log_content:
            redirect_match = re.search(r"HOST_REDIRECT_TARGET:\s*(\S+)", log_content)
            if redirect_match:
                redirect_target = redirect_match.group(1)
                click.echo(click.style("Host-Level Redirect Detected", bold=True))
                click.echo(f"  - Original target: {job.get('target', 'unknown')}")
                click.echo(f"  - Redirects to: {redirect_target}")
                click.echo()
                click.echo("  The server redirects ALL requests to a different host.")
                click.echo(
                    "  Results are unreliable due to variable redirect response sizes."
                )
                click.echo()
                click.echo(
                    click.style(
                        "  A retry job was auto-queued with the correct target.",
                        fg="green",
                    )
                )
                click.echo()

        # Check for wildcard response
        elif log_content and (
            "wildcard" in log_content.lower()
            or "the server returns a status code that matches" in log_content.lower()
        ):
            click.echo(click.style("Wildcard Response Detected", bold=True))
            click.echo("  The server returns the same response for ALL URLs.")
            click.echo("  Gobuster cannot differentiate real vs fake paths.")
            click.echo()
            length_match = re.search(r"Length:\s*(\d+)", log_content)
            if length_match:
                click.echo(f"  - Response length: {length_match.group(1)} bytes")
                click.echo()
                click.echo(
                    click.style(
                        "  A retry job was auto-queued with --exclude-length.",
                        fg="green",
                    )
                )
            click.echo()

        else:
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
        """Display error status for Gobuster scan."""
        # Read log if not provided
        if log_content is None and log_path and os.path.exists(log_path):
            try:
                with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                    log_content = f.read()
            except Exception:
                log_content = ""

        click.echo(click.style("=" * 70, fg="red"))
        click.echo(click.style("[ERROR] GOBUSTER SCAN FAILED", bold=True, fg="red"))
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
                    "    - Increase --delay between requests", fg="bright_black"
                )
            )
            click.echo(click.style("    - Reduce threads with -t", fg="bright_black"))
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
        """Display no_results status for Gobuster scan."""
        click.echo(click.style("=" * 70, fg="cyan"))
        click.echo(click.style("GOBUSTER SCAN RESULTS", bold=True, fg="cyan"))
        click.echo(click.style("=" * 70, fg="cyan"))
        click.echo()
        click.echo("  No paths discovered.")
        click.echo()

        # Extract wordlist name from args
        args = job.get("args", [])
        for i, arg in enumerate(args):
            if arg == "-w" and i + 1 < len(args):
                wordlist = os.path.basename(args[i + 1])
                click.echo(f"  Wordlist: {wordlist}")
                break

        # Extract extensions
        for i, arg in enumerate(args):
            if arg == "-x" and i + 1 < len(args):
                click.echo(f"  Extensions: {args[i + 1]}")
                break

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
                "    - Target may be blocking automated requests", fg="bright_black"
            )
        )
        click.echo()
        click.echo(click.style("=" * 70, fg="cyan"))
        click.echo()
