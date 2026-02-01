#!/usr/bin/env python3
"""
Katana handler.

Consolidates parsing and display logic for katana web crawling jobs.
"""

import logging
import os
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


class KatanaHandler(BaseToolHandler):
    """Handler for Katana web crawling jobs."""

    tool_name = "katana"
    display_name = "Katana"

    # All handlers enabled
    has_error_handler = True
    has_warning_handler = True
    has_no_results_handler = True
    has_done_handler = True

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
        Parse katana crawl results.

        Extracts discovered URLs, parameters, forms, and JS endpoints.
        """
        try:
            from souleyez.engine.result_handler import detect_tool_error
            from souleyez.parsers.katana_parser import (
                extract_injectable_urls,
                parse_katana_output,
            )

            # Import managers if not provided
            if host_manager is None:
                from souleyez.storage.hosts import HostManager

                host_manager = HostManager()

            target = job.get("target", "")
            parsed = parse_katana_output(log_path)

            if parsed.get("error"):
                return {
                    "tool": "katana",
                    "status": STATUS_ERROR,
                    "target": target,
                    "error": parsed["error"],
                }

            # Extract host for tracking
            parsed_url = urlparse(target)
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

            # Store web paths discovered by katana
            paths_added = 0
            if host_id and parsed.get("urls"):
                try:
                    from souleyez.storage.web_paths import WebPathsManager

                    wpm = WebPathsManager()

                    # Convert URLs to path format
                    web_paths = []
                    for url in parsed["urls"]:
                        url_parsed = urlparse(url)
                        path = url_parsed.path or "/"
                        if url_parsed.query:
                            path += "?" + url_parsed.query

                        web_paths.append(
                            {
                                "path": path,
                                "url": url,
                                "status_code": 200,  # Katana only returns accessible URLs
                                "method": "GET",
                                "source": "katana",
                            }
                        )

                    if web_paths:
                        paths_added = wpm.bulk_add_web_paths(host_id, web_paths)
                except Exception as e:
                    logger.warning(f"Failed to store web paths: {e}")

            # Check for katana errors in log
            katana_error = None
            try:
                with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                    log_content = f.read()
                katana_error = detect_tool_error(log_content, "katana")
            except Exception:
                pass

            # Get injectable URLs for chaining (excludes LFI-only params)
            injectable_urls = extract_injectable_urls(parsed)

            # Get LFI candidate URLs for LFI-specific scanning
            from souleyez.parsers.katana_parser import extract_lfi_urls

            lfi_urls = extract_lfi_urls(parsed)

            # ARM64/headless workaround: If we have JS files but few parameterized URLs,
            # extract endpoints directly from JavaScript source code
            js_files = [u for u in parsed.get("urls", []) if u.endswith(".js")]
            urls_with_params_list = parsed.get("urls_with_params", [])
            sqli_candidates = parsed.get("sqli_candidate_urls", [])

            if js_files and len(urls_with_params_list) < 10:
                try:
                    from souleyez.parsers.katana_parser import (
                        fetch_and_extract_js_endpoints,
                    )

                    logger.info(
                        f"Extracting endpoints from {len(js_files)} JavaScript files..."
                    )
                    js_endpoints = fetch_and_extract_js_endpoints(target, js_files)

                    if js_endpoints:
                        logger.info(
                            f"Found {len(js_endpoints)} additional endpoints from JavaScript"
                        )
                        # Add to parsed results
                        for ep in js_endpoints:
                            if ep not in urls_with_params_list:
                                urls_with_params_list.append(ep)
                            if ep not in sqli_candidates:
                                sqli_candidates.append(ep)
                            if ep not in injectable_urls:
                                injectable_urls.append(ep)

                        # Update parsed dict for display
                        parsed["urls_with_params"] = urls_with_params_list
                        parsed["sqli_candidate_urls"] = sqli_candidates
                except Exception as e:
                    logger.warning(f"JavaScript endpoint extraction failed: {e}")

            # Determine status
            urls_list = parsed.get("urls", [])
            urls_with_params_list = parsed.get("urls_with_params", [])
            lfi_candidate_list = parsed.get("lfi_candidate_urls", [])
            sqli_candidate_list = parsed.get("sqli_candidate_urls", [])
            forms_list = parsed.get("forms_found", [])
            js_list = parsed.get("js_endpoints", [])
            lfi_params_list = parsed.get("lfi_params_found", [])

            if katana_error:
                status = STATUS_ERROR
            elif len(urls_list) > 0:
                status = STATUS_DONE
            else:
                status = STATUS_NO_RESULTS

            return {
                "tool": "katana",
                "status": status,
                "target": target,
                "target_host": target_host,
                # Counts for display
                "urls_found": len(urls_list),
                "urls_with_params_count": len(urls_with_params_list),
                "lfi_candidate_count": len(lfi_candidate_list),
                "sqli_candidate_count": len(sqli_candidate_list),
                "forms_found_count": len(forms_list),
                "js_endpoints_count": len(js_list),
                "unique_parameters": parsed.get("unique_parameters", []),
                "lfi_params_found": lfi_params_list,
                "paths_added": paths_added,
                # Lists for chaining (chain rules expect these)
                "urls_with_params": urls_with_params_list,  # For has:urls_with_params
                "lfi_candidate_urls": lfi_candidate_list,  # For has:lfi_candidate_urls (LFI scan)
                "sqli_candidate_urls": sqli_candidate_list,  # For has:sqli_candidate_urls (SQLMap)
                "forms_found": forms_list,  # For has:forms_found
                "injectable_urls": injectable_urls,  # SQLi candidates only (excludes LFI-only)
                "crawled_urls": urls_list,
                "parameterized_urls": urls_with_params_list,
                "post_endpoints": forms_list,
            }

        except Exception as e:
            logger.exception(f"Failed to parse katana results: {e}")
            return {
                "tool": "katana",
                "status": STATUS_ERROR,
                "target": job.get("target", ""),
                "error": str(e),
            }

    def display_done(
        self,
        job: Dict[str, Any],
        log_path: str,
        show_all: bool = False,
        show_passwords: bool = False,
    ) -> None:
        """Display successful katana crawl results."""
        from souleyez.parsers.katana_parser import parse_katana_output

        target = job.get("target", "Unknown")
        parse_result = job.get("parse_result", {})

        # Re-parse for full details if needed
        parsed = parse_katana_output(log_path)

        click.echo(click.style("=" * 70, fg="green"))
        click.echo(click.style("KATANA WEB CRAWLER RESULTS", bold=True, fg="green"))
        click.echo(click.style("=" * 70, fg="green"))
        click.echo()
        click.echo(f"  Target: {target}")
        click.echo()

        # Summary stats
        urls_found = len(parsed.get("urls", []))
        urls_with_params = parsed.get("urls_with_params", [])
        forms_found = parsed.get("forms_found", [])
        js_endpoints = parsed.get("js_endpoints", [])
        unique_params = parsed.get("unique_parameters", [])

        click.echo(click.style("  SUMMARY", bold=True))
        click.echo(f"    Total URLs discovered: {urls_found}")
        click.echo(f"    URLs with parameters:  {len(urls_with_params)}")
        click.echo(f"    POST endpoints (forms): {len(forms_found)}")
        click.echo(f"    JavaScript endpoints:  {len(js_endpoints)}")
        click.echo(f"    Unique parameters:     {len(unique_params)}")
        click.echo()

        # All discovered URLs
        all_urls = parsed.get("urls", [])
        if all_urls:
            click.echo(click.style("  DISCOVERED URLs", bold=True, fg="cyan"))
            display_limit = None if show_all else 15
            for url in all_urls[:display_limit]:
                click.echo(f"    {url}")
            if not show_all and len(all_urls) > 15:
                click.echo(
                    f"    ... and {len(all_urls) - 15} more (use 'a' to show all)"
                )
            click.echo()

        # URLs with parameters (most important for SQLi)
        if urls_with_params:
            click.echo(
                click.style(
                    "  URLS WITH PARAMETERS (SQLi Candidates)", bold=True, fg="yellow"
                )
            )
            display_limit = None if show_all else 10
            for i, url in enumerate(urls_with_params[:display_limit]):
                click.echo(f"    {url}")
            if not show_all and len(urls_with_params) > 10:
                click.echo(
                    f"    ... and {len(urls_with_params) - 10} more (use 'a' to show all)"
                )
            click.echo()

        # POST endpoints
        if forms_found:
            click.echo(
                click.style("  POST ENDPOINTS (Form Submissions)", bold=True, fg="cyan")
            )
            display_limit = None if show_all else 5
            for url in forms_found[:display_limit]:
                click.echo(f"    [POST] {url}")
            if not show_all and len(forms_found) > 5:
                click.echo(f"    ... and {len(forms_found) - 5} more")
            click.echo()

        # JavaScript endpoints
        if js_endpoints:
            click.echo(click.style("  JAVASCRIPT ENDPOINTS", bold=True, fg="magenta"))
            display_limit = None if show_all else 5
            for url in js_endpoints[:display_limit]:
                click.echo(f"    {url}")
            if not show_all and len(js_endpoints) > 5:
                click.echo(f"    ... and {len(js_endpoints) - 5} more")
            click.echo()

        # Unique parameters found
        if unique_params:
            click.echo(click.style("  UNIQUE PARAMETERS FOUND", bold=True))
            params_str = ", ".join(unique_params[:20])
            if len(unique_params) > 20:
                params_str += f", ... (+{len(unique_params) - 20} more)"
            click.echo(f"    {params_str}")
            click.echo()

        click.echo(click.style("=" * 70, fg="green"))
        click.echo()

    def display_error(
        self,
        job: Dict[str, Any],
        log_path: str,
        log_content: Optional[str] = None,
    ) -> None:
        """Display katana error results."""
        target = job.get("target", "Unknown")
        parse_result = job.get("parse_result", {})

        click.echo(click.style("=" * 70, fg="red"))
        click.echo(click.style("KATANA CRAWL ERROR", bold=True, fg="red"))
        click.echo(click.style("=" * 70, fg="red"))
        click.echo()
        click.echo(f"  Target: {target}")
        click.echo()

        # Try to identify common errors
        if log_content is None:
            try:
                with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                    log_content = f.read()
            except Exception:
                log_content = ""

        error_identified = False

        if (
            "no such file or directory" in log_content.lower()
            or "failed to run command" in log_content.lower()
        ):
            click.echo(click.style("  Issue: Katana not installed", fg="red"))
            click.echo("  Katana binary was not found on this system.")
            click.echo()
            click.echo("  To install:")
            click.echo("    Kali Linux: sudo apt install katana chromium")
            click.echo(
                "    Ubuntu:     go install github.com/projectdiscovery/katana/cmd/katana@latest"
            )
            click.echo()
            click.echo("  Also ensure Chromium is installed for headless mode:")
            click.echo("    sudo apt install chromium")
            error_identified = True
        elif "connection refused" in log_content.lower():
            click.echo(click.style("  Issue: Connection refused", fg="red"))
            click.echo("  The target is not responding on the specified port.")
            error_identified = True
        elif "timeout" in log_content.lower():
            click.echo(click.style("  Issue: Connection timeout", fg="red"))
            click.echo("  The target took too long to respond.")
            error_identified = True
        elif "chromium" in log_content.lower() or "headless" in log_content.lower():
            click.echo(click.style("  Issue: Headless browser error", fg="red"))
            click.echo("  Chromium may not be installed or configured correctly.")
            click.echo("  Try: sudo apt install chromium")
            click.echo('  Or run with --args "-no-headless" to skip browser mode.')
            error_identified = True
        elif "certificate" in log_content.lower() or "ssl" in log_content.lower():
            click.echo(click.style("  Issue: SSL/TLS certificate error", fg="red"))
            click.echo("  The target has an invalid or self-signed certificate.")
            error_identified = True

        if not error_identified:
            error_msg = parse_result.get("error", "Unknown error occurred")
            click.echo(f"  Error: {error_msg}")

        click.echo()
        click.echo("  Tips:")
        click.echo("    - Verify the target URL is accessible")
        click.echo("    - Check if Chromium is installed for headless mode")
        click.echo("    - Try with -no-headless flag if browser issues persist")
        click.echo()
        click.echo(click.style("=" * 70, fg="red"))
        click.echo()

    def display_no_results(
        self,
        job: Dict[str, Any],
        log_path: str,
    ) -> None:
        """Display no results message with tips."""
        target = job.get("target", "Unknown")

        click.echo(click.style("=" * 70, fg="yellow"))
        click.echo(click.style("KATANA CRAWL - NO RESULTS", bold=True, fg="yellow"))
        click.echo(click.style("=" * 70, fg="yellow"))
        click.echo()
        click.echo(f"  Target: {target}")
        click.echo()
        click.echo("  No URLs were discovered during the crawl.")
        click.echo()
        click.echo("  Tips:")
        click.echo("    - Verify the target URL is accessible and returns content")
        click.echo("    - The page may require authentication")
        click.echo("    - Try increasing crawl depth with -d 5")
        click.echo("    - Ensure headless mode is working (check Chromium install)")
        click.echo("    - The target may be blocking automated crawlers")
        click.echo()
        click.echo(click.style("=" * 70, fg="yellow"))
        click.echo()

    def display_warning(
        self,
        job: Dict[str, Any],
        log_path: str,
        log_content: Optional[str] = None,
    ) -> None:
        """Display warning status results."""
        target = job.get("target", "Unknown")
        parse_result = job.get("parse_result", {})

        click.echo(click.style("=" * 70, fg="yellow"))
        click.echo(click.style("KATANA CRAWL WARNING", bold=True, fg="yellow"))
        click.echo(click.style("=" * 70, fg="yellow"))
        click.echo()
        click.echo(f"  Target: {target}")
        click.echo()

        summary = parse_result.get("summary", "Crawl completed with warnings")
        click.echo(f"  {summary}")
        click.echo()

        # Still show any results we got
        urls_found = parse_result.get("urls_found", 0)
        urls_with_params = len(parse_result.get("urls_with_params", []))
        if urls_found > 0:
            click.echo(f"  Partial results: {urls_found} URLs discovered")
            if urls_with_params > 0:
                click.echo(f"  URLs with parameters: {urls_with_params}")

        click.echo()
        click.echo(click.style("=" * 70, fg="yellow"))
        click.echo()


# Register handler - this makes it discoverable by the registry
handler = KatanaHandler()
