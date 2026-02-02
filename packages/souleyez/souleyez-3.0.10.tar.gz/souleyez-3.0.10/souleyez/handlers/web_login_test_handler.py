#!/usr/bin/env python3
"""
Web Login Test handler.

Parses and displays results from web login credential tests.
"""

import json
import logging
import os
import re
from typing import Any, Dict, Optional

import click

from souleyez.engine.job_status import STATUS_DONE, STATUS_ERROR, STATUS_NO_RESULTS
from souleyez.handlers.base import BaseToolHandler

logger = logging.getLogger(__name__)


class WebLoginTestHandler(BaseToolHandler):
    """Handler for web login credential test jobs."""

    tool_name = "web_login_test"
    display_name = "Web Login Test"

    has_error_handler = True
    has_warning_handler = False
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
        Parse web login test results.

        Returns parsed result including:
        - login_success: bool
        - username: str
        - http_code: int
        - reason: str
        """
        try:
            if not log_path or not os.path.exists(log_path):
                return {
                    "tool": self.tool_name,
                    "status": STATUS_ERROR,
                    "error": "Log file not found",
                }

            with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                log_content = f.read()

            # Try to parse JSON result
            json_match = re.search(
                r"=== JSON_RESULT ===\s*(.*?)\s*=== END_JSON_RESULT ===",
                log_content,
                re.DOTALL,
            )

            result = {
                "tool": self.tool_name,
                "status": STATUS_NO_RESULTS,
                "login_success": False,
                "username": None,
                "http_code": None,
                "reason": None,
                "response": None,
            }

            # Extract username from log
            username_match = re.search(r"Username: (\S+)", log_content)
            if username_match:
                result["username"] = username_match.group(1)

            if json_match:
                try:
                    json_data = json.loads(json_match.group(1))

                    if json_data.get("error"):
                        result["status"] = STATUS_ERROR
                        result["error"] = json_data["error"]
                        result["summary"] = f"Error: {json_data['error'][:50]}"
                        return result

                    result["login_success"] = json_data.get("success", False)
                    result["http_code"] = json_data.get("http_code")
                    result["reason"] = json_data.get("reason")
                    result["response"] = json_data.get("response", "")[:100]

                except json.JSONDecodeError:
                    pass

            # Fallback: parse from log text
            if "[+] LOGIN SUCCESS" in log_content:
                result["login_success"] = True
                result["status"] = STATUS_DONE
            elif "[-] LOGIN FAILED" in log_content:
                result["login_success"] = False
                result["status"] = STATUS_NO_RESULTS

            # Extract HTTP code if not already found
            if not result["http_code"]:
                http_match = re.search(r"HTTP Code: (\d+)", log_content)
                if http_match:
                    result["http_code"] = int(http_match.group(1))

            # Extract reason if not already found
            if not result["reason"]:
                reason_match = re.search(r"Reason: (.+?)(?:\n|$)", log_content)
                if reason_match:
                    result["reason"] = reason_match.group(1).strip()

            # Build summary
            if result["login_success"]:
                result["status"] = STATUS_DONE
                result["summary"] = f"Login successful: {result['username']}"
                # Store validated credential
                if credentials_manager and result["username"]:
                    target = job.get("target", "")
                    # Extract password from args
                    password = self._extract_password_from_args(job.get("args", []))
                    if password:
                        try:
                            credentials_manager.add_credential(
                                engagement_id=engagement_id,
                                host_id=None,
                                username=result["username"],
                                password=password,
                                service="web",
                                credential_type="password",
                                tool="web_login_test",
                                status="validated",
                                notes=f"Validated against {target}",
                            )
                            result["credentials_validated"] = 1
                            logger.info(
                                f"Web login test: Validated credential {result['username']}"
                            )
                        except Exception as e:
                            logger.debug(f"Error storing validated credential: {e}")
            else:
                result["status"] = STATUS_NO_RESULTS
                # Build informative failure summary
                if result["reason"]:
                    # Truncate long reasons
                    reason = result["reason"]
                    if len(reason) > 50:
                        reason = reason[:47] + "..."
                    result["summary"] = f"Login failed: {reason}"
                elif result["http_code"]:
                    result["summary"] = f"Login failed (HTTP {result['http_code']})"
                else:
                    result["summary"] = "Login failed"

            return result

        except Exception as e:
            logger.error(f"Error parsing web_login_test job: {e}")
            return {"tool": self.tool_name, "status": STATUS_ERROR, "error": str(e)}

    def _extract_password_from_args(self, args: list) -> Optional[str]:
        """Extract password from job args."""
        for i, arg in enumerate(args):
            if arg == "--password" and i + 1 < len(args):
                return args[i + 1]
        return None

    def display_done(
        self,
        job: Dict[str, Any],
        log_path: str,
        show_all: bool = False,
        show_passwords: bool = False,
    ) -> None:
        """Display successful login test results."""
        result = self._parse_log(log_path)

        click.echo()
        click.echo(click.style("=" * 60, fg="green"))
        click.echo(click.style("WEB LOGIN TEST - SUCCESS", bold=True, fg="green"))
        click.echo(click.style("=" * 60, fg="green"))
        click.echo()

        target = job.get("target", "unknown")
        click.echo(f"  Target: {target}")

        username = result.get("username", "unknown")
        if show_passwords:
            password = self._extract_password_from_args(job.get("args", []))
            click.echo(click.style(f"  Credential: {username}:{password}", fg="green"))
        else:
            click.echo(click.style(f"  Credential: {username}:***", fg="green"))

        if result.get("http_code"):
            click.echo(f"  HTTP Code: {result['http_code']}")

        if result.get("reason"):
            click.echo(f"  Reason: {result['reason']}")

        click.echo()
        click.echo(click.style("=" * 60, fg="green"))
        click.echo()

    def display_no_results(
        self,
        job: Dict[str, Any],
        log_path: str,
    ) -> None:
        """Display failed login test results."""
        result = self._parse_log(log_path)

        click.echo()
        click.echo(click.style("=" * 60, fg="yellow"))
        click.echo(click.style("WEB LOGIN TEST - FAILED", bold=True, fg="yellow"))
        click.echo(click.style("=" * 60, fg="yellow"))
        click.echo()

        target = job.get("target", "unknown")
        click.echo(f"  Target: {target}")

        username = result.get("username", "unknown")
        click.echo(f"  Credential: {username}:***")

        if result.get("http_code"):
            click.echo(f"  HTTP Code: {result['http_code']}")

        if result.get("reason"):
            click.echo(f"  Reason: {result['reason']}")

        click.echo()
        click.echo(click.style("  Result: Invalid credentials", fg="yellow"))
        click.echo()
        click.echo(click.style("=" * 60, fg="yellow"))
        click.echo()

    def display_error(
        self,
        job: Dict[str, Any],
        log_path: str,
        log_content: Optional[str] = None,
    ) -> None:
        """Display error status."""
        click.echo()
        click.echo(click.style("=" * 60, fg="red"))
        click.echo(click.style("[ERROR] WEB LOGIN TEST FAILED", bold=True, fg="red"))
        click.echo(click.style("=" * 60, fg="red"))
        click.echo()

        target = job.get("target", "unknown")
        click.echo(f"  Target: {target}")

        # Try to get error details
        if log_path and os.path.exists(log_path):
            try:
                with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
                error_match = re.search(r"ERROR: (.+?)(?:\n|$)", content)
                if error_match:
                    click.echo(f"  Error: {error_match.group(1)}")
            except Exception:
                pass

        click.echo()
        click.echo("  Check raw logs for details (press 'r').")
        click.echo()
        click.echo(click.style("=" * 60, fg="red"))
        click.echo()

    def _parse_log(self, log_path: str) -> Dict[str, Any]:
        """Parse log file and return result dict."""
        result = {
            "username": None,
            "http_code": None,
            "reason": None,
            "response": None,
        }

        if not log_path or not os.path.exists(log_path):
            return result

        try:
            with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                log_content = f.read()

            # Extract username
            username_match = re.search(r"Username: (\S+)", log_content)
            if username_match:
                result["username"] = username_match.group(1)

            # Try JSON result
            json_match = re.search(
                r"=== JSON_RESULT ===\s*(.*?)\s*=== END_JSON_RESULT ===",
                log_content,
                re.DOTALL,
            )
            if json_match:
                try:
                    json_data = json.loads(json_match.group(1))
                    result["http_code"] = json_data.get("http_code")
                    result["reason"] = json_data.get("reason")
                    result["response"] = json_data.get("response", "")[:100]
                except json.JSONDecodeError:
                    pass

            # Fallback parsing
            if not result["http_code"]:
                http_match = re.search(r"HTTP Code: (\d+)", log_content)
                if http_match:
                    result["http_code"] = int(http_match.group(1))

            if not result["reason"]:
                reason_match = re.search(r"Reason: (.+?)(?:\n|$)", log_content)
                if reason_match:
                    result["reason"] = reason_match.group(1).strip()

        except Exception:
            pass

        return result
