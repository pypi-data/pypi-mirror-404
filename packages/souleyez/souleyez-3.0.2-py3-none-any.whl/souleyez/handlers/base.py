#!/usr/bin/env python3
"""
Base handler class for tool result parsing and display.

All tool handlers inherit from BaseToolHandler and implement
the required methods for their specific tool.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

import click

logger = logging.getLogger(__name__)


class BaseToolHandler(ABC):
    """
    Abstract base class for tool handlers.

    Each handler consolidates:
    - Parsing logic (parse_job)
    - Display logic (display_done, display_warning, etc.)
    - Capability flags (has_warning_handler, etc.)

    Subclasses MUST define:
    - tool_name: The tool identifier (e.g., 'msf_exploit')
    - display_name: Human-readable name (e.g., 'Metasploit Exploit')
    - parse_job(): Parse job output and write to database
    - display_done(): Show successful results
    """

    # Tool identifier - MUST be overridden
    tool_name: str = "base"
    display_name: str = "Unknown Tool"

    # Capability flags - registry checks these instead of manual lists
    # Override in subclass if the handler doesn't support a status
    has_error_handler: bool = True
    has_warning_handler: bool = True
    has_no_results_handler: bool = True
    has_done_handler: bool = True

    @abstractmethod
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
        Parse job output and write findings/credentials to database.

        This replaces parse_*_job() functions in result_handler.py.
        Called ONCE when job completes.

        Args:
            engagement_id: The engagement ID
            log_path: Path to the job's log file
            job: The job dict from background system
            host_manager: Optional HostManager for DB operations
            findings_manager: Optional FindingsManager for DB operations
            credentials_manager: Optional CredentialsManager for DB operations

        Returns:
            parse_result dict with at minimum:
            - 'status': 'done' | 'warning' | 'no_results' | 'error'
            - 'summary': Human-readable summary
        """
        pass

    @abstractmethod
    def display_done(
        self,
        job: Dict[str, Any],
        log_path: str,
        show_all: bool = False,
        show_passwords: bool = False,
    ) -> None:
        """
        Display successful job results.

        Called when job status is 'done' and handler.has_done_handler is True.

        Args:
            job: The job dict (includes parse_result)
            log_path: Path to the job's log file
            show_all: Whether to show all results (not just top N)
            show_passwords: Whether to reveal passwords
        """
        pass

    def display_warning(
        self,
        job: Dict[str, Any],
        log_path: str,
        log_content: Optional[str] = None,
    ) -> None:
        """
        Display warning status results.

        Default implementation shows a generic warning block.
        Override for tool-specific warning display.

        Args:
            job: The job dict (includes parse_result)
            log_path: Path to the job's log file
            log_content: Optional pre-read log content
        """
        parse_result = job.get("parse_result", {})
        summary = "Warning"
        if isinstance(parse_result, dict):
            summary = parse_result.get("summary", "Warning")

        click.echo(click.style("=" * 70, fg="yellow"))
        click.echo(
            click.style(
                f"[WARNING] {self.display_name.upper()}", bold=True, fg="yellow"
            )
        )
        click.echo(click.style("=" * 70, fg="yellow"))
        click.echo()
        click.echo(f"  {summary}")
        click.echo()
        click.echo(click.style("=" * 70, fg="yellow"))
        click.echo()

    def display_error(
        self,
        job: Dict[str, Any],
        log_path: str,
        log_content: Optional[str] = None,
    ) -> None:
        """
        Display error status results.

        Default implementation shows a generic error block.
        Override for tool-specific error display.

        Args:
            job: The job dict (includes parse_result)
            log_path: Path to the job's log file
            log_content: Optional pre-read log content
        """
        parse_result = job.get("parse_result", {})
        summary = "An error occurred"
        if isinstance(parse_result, dict):
            summary = parse_result.get("summary", "An error occurred")

        click.echo(click.style("=" * 70, fg="red"))
        click.echo(
            click.style(f"[ERROR] {self.display_name.upper()}", bold=True, fg="red")
        )
        click.echo(click.style("=" * 70, fg="red"))
        click.echo()
        click.echo(f"  {summary}")
        click.echo()
        click.echo(click.style("=" * 70, fg="red"))
        click.echo()

    def display_no_results(
        self,
        job: Dict[str, Any],
        log_path: str,
    ) -> None:
        """
        Display no_results status.

        Default implementation shows a generic no results block.
        Override for tool-specific no results display.

        Args:
            job: The job dict (includes parse_result)
            log_path: Path to the job's log file
        """
        click.echo(click.style("=" * 70, fg="yellow"))
        click.echo(
            click.style(f"{self.display_name.upper()} RESULTS", bold=True, fg="yellow")
        )
        click.echo(click.style("=" * 70, fg="yellow"))
        click.echo()
        click.echo("  No results found.")
        click.echo()
        click.echo(click.style("=" * 70, fg="yellow"))
        click.echo()
