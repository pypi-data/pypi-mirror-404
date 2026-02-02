#!/usr/bin/env python3
"""
Bash handler.

Handles bash script execution results, particularly for auto-generated
scripts like web login credential tests.
"""

import logging
import os
import re
from typing import Any, Dict, Optional

import click

from souleyez.engine.job_status import STATUS_DONE, STATUS_ERROR, STATUS_NO_RESULTS
from souleyez.handlers.base import BaseToolHandler

logger = logging.getLogger(__name__)


class BashHandler(BaseToolHandler):
    """Handler for bash script execution jobs."""

    tool_name = "bash"
    display_name = "Bash Script"

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
        Parse bash job results.

        Detects web login test scripts and parses their output.
        """
        try:
            if not log_path or not os.path.exists(log_path):
                return {"error": "Log file not found"}

            with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                log_content = f.read()

            # Check if this is a web login test script
            args = job.get("args", [])
            is_web_login_test = any("web_login_test" in str(arg) for arg in args)

            if is_web_login_test:
                return self._parse_web_login_test(log_content, job)

            # Generic bash script - just check exit code
            exit_code = self._extract_exit_code(log_content)
            if exit_code == 0:
                return {
                    "tool": "bash",
                    "status": STATUS_DONE,
                    "summary": "Script completed successfully",
                }
            else:
                return {
                    "tool": "bash",
                    "status": STATUS_ERROR,
                    "summary": f"Script failed (exit code {exit_code})",
                }

        except Exception as e:
            logger.error(f"Error parsing bash job: {e}")
            return {"error": str(e)}

    def _parse_web_login_test(
        self, log_content: str, job: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Parse web login credential test output."""
        result = {
            "tool": "bash",
            "status": STATUS_NO_RESULTS,
            "summary": "Credential test completed",
            "login_success": False,
            "username": None,
            "response": None,
            "http_code": None,
        }

        # Extract username from "Testing user:pass against URL"
        test_match = re.search(r"Testing (\S+):(\S+) against", log_content)
        if test_match:
            result["username"] = test_match.group(1)

        # Extract HTTP response code
        http_match = re.search(r"HTTP Code: (\d+)", log_content)
        if http_match:
            result["http_code"] = http_match.group(1)

        # Extract response message
        resp_match = re.search(
            r"Response: (.+?)(?:\n|HTTP_CODE)", log_content, re.DOTALL
        )
        if resp_match:
            result["response"] = resp_match.group(1).strip()[:100]

        # Check for success indicators
        if "[+] LOGIN SUCCESS" in log_content:
            result["status"] = STATUS_DONE
            result["login_success"] = True
            result["summary"] = f"Login successful: {result['username']}"
        elif "[+] POSSIBLE SUCCESS" in log_content:
            result["status"] = STATUS_DONE
            result["login_success"] = True
            result["summary"] = (
                f"Possible login success: {result['username']} (HTTP {result['http_code']})"
            )
        elif "[-] Login failed" in log_content:
            result["status"] = STATUS_NO_RESULTS
            # Extract failure reason from response
            if result["response"]:
                # Truncate long responses
                reason = result["response"]
                if len(reason) > 50:
                    reason = reason[:47] + "..."
                result["summary"] = f"Login failed: {reason}"
            else:
                result["summary"] = (
                    f"Login failed (HTTP {result['http_code'] or 'unknown'})"
                )
        else:
            # Unknown result
            result["summary"] = "Credential test completed (check logs)"

        return result

    def _extract_exit_code(self, log_content: str) -> int:
        """Extract exit code from log content."""
        match = re.search(r"Exit Code: (\d+)", log_content)
        if match:
            return int(match.group(1))
        return -1

    def display_done(
        self,
        job: Dict[str, Any],
        log_path: str,
        show_all: bool = False,
        show_passwords: bool = False,
    ) -> None:
        """Display successful bash results."""
        args = job.get("args", [])
        is_web_login_test = any("web_login_test" in str(arg) for arg in args)

        if is_web_login_test:
            self._display_web_login_result(job, log_path, success=True)
        else:
            click.echo(click.style("=" * 60, fg="green"))
            click.echo(click.style("BASH SCRIPT COMPLETED", bold=True, fg="green"))
            click.echo(click.style("=" * 60, fg="green"))
            click.echo()
            click.echo("  Script executed successfully.")
            click.echo()
            click.echo(click.style("=" * 60, fg="green"))
            click.echo()

    def display_no_results(
        self,
        job: Dict[str, Any],
        log_path: str,
    ) -> None:
        """Display no_results status for bash."""
        args = job.get("args", [])
        is_web_login_test = any("web_login_test" in str(arg) for arg in args)

        if is_web_login_test:
            self._display_web_login_result(job, log_path, success=False)
        else:
            click.echo(click.style("=" * 60, fg="yellow"))
            click.echo(click.style("BASH SCRIPT - NO RESULTS", bold=True, fg="yellow"))
            click.echo(click.style("=" * 60, fg="yellow"))
            click.echo()
            click.echo("  Script completed but produced no actionable results.")
            click.echo()
            click.echo(click.style("=" * 60, fg="yellow"))
            click.echo()

    def display_error(
        self,
        job: Dict[str, Any],
        log_path: str,
        log_content: Optional[str] = None,
    ) -> None:
        """Display error status for bash."""
        args = job.get("args", [])
        is_web_login_test = any("web_login_test" in str(arg) for arg in args)

        if is_web_login_test:
            self._display_web_login_result(job, log_path, success=False)
        else:
            click.echo(click.style("=" * 60, fg="red"))
            click.echo(click.style("[ERROR] BASH SCRIPT FAILED", bold=True, fg="red"))
            click.echo(click.style("=" * 60, fg="red"))
            click.echo()
            click.echo("  Script execution failed.")
            click.echo("  Check raw logs for details (press 'r').")
            click.echo()
            click.echo(click.style("=" * 60, fg="red"))
            click.echo()

    def _display_web_login_result(
        self, job: Dict[str, Any], log_path: str, success: bool
    ) -> None:
        """Display web login credential test result."""
        # Parse the log to get details
        username = None
        password = "***"
        response = None
        http_code = None

        if log_path and os.path.exists(log_path):
            try:
                with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                    log_content = f.read()

                # Extract details
                test_match = re.search(r"Testing (\S+):(\S+) against", log_content)
                if test_match:
                    username = test_match.group(1)

                http_match = re.search(r"HTTP Code: (\d+)", log_content)
                if http_match:
                    http_code = http_match.group(1)

                resp_match = re.search(
                    r"Response: (.+?)(?:\nHTTP|$)", log_content, re.DOTALL
                )
                if resp_match:
                    response = resp_match.group(1).strip()

            except Exception:
                pass

        target = job.get("target", "unknown")

        if success or "[+]" in (response or ""):
            click.echo(click.style("=" * 60, fg="green"))
            click.echo(click.style("WEB LOGIN TEST - SUCCESS", bold=True, fg="green"))
            click.echo(click.style("=" * 60, fg="green"))
            click.echo()
            click.echo(f"  Target: {target}")
            click.echo(click.style(f"  Credential: {username}:{password}", fg="green"))
            click.echo(f"  HTTP Code: {http_code or 'unknown'}")
            click.echo()
            click.echo(click.style("=" * 60, fg="green"))
        else:
            click.echo(click.style("=" * 60, fg="yellow"))
            click.echo(click.style("WEB LOGIN TEST", bold=True, fg="yellow"))
            click.echo(click.style("=" * 60, fg="yellow"))
            click.echo()
            click.echo(f"  Target: {target}")
            click.echo(f"  Credential: {username}:{password}")
            click.echo(f"  HTTP Code: {http_code or 'unknown'}")
            click.echo()
            if response:
                # Show truncated response
                if len(response) > 60:
                    response = response[:57] + "..."
                click.echo(f"  Response: {response}")
                click.echo()
            click.echo(click.style("  Result: Invalid credentials", fg="yellow"))
            click.echo()
            click.echo(click.style("=" * 60, fg="yellow"))
        click.echo()
