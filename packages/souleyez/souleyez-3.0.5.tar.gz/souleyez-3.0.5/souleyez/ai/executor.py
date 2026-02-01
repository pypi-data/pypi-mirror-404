#!/usr/bin/env python3
"""
souleyez.ai.executor - Interactive AI-driven command execution
"""

import logging
import subprocess
from typing import Any, Dict, Optional

import click

from ..storage.execution_log import ExecutionLogManager
from .action_mapper import ActionMapper
from .feedback_handler import FeedbackHandler
from .recommender import AttackRecommender
from .result_parser import ResultParser
from .safety import ApprovalMode, RiskLevel, SafetyFramework

logger = logging.getLogger(__name__)


class InteractiveExecutor:
    """
    Interactive executor for AI-driven penetration testing.

    Loop: Recommend → Map → Approve → Execute → Parse → Feedback → Repeat
    """

    def __init__(
        self,
        approval_mode: ApprovalMode = ApprovalMode.MANUAL,
        target_host_ids: Optional[list] = None,
        provider=None,
    ):
        """
        Initialize executor.

        Args:
            approval_mode: How to handle command approvals
            target_host_ids: Optional list of specific host IDs to target
            provider: Optional LLM provider instance (from LLMFactory)
        """
        self.recommender = AttackRecommender(provider=provider)
        self.mapper = ActionMapper()
        self.safety = SafetyFramework(approval_mode)
        self.parser = ResultParser()
        self.feedback = FeedbackHandler()
        self.exec_log = ExecutionLogManager()
        self.approval_mode = approval_mode
        self.target_host_ids = target_host_ids  # Store for filtering recommendations

    def execute_loop(
        self,
        engagement_id: int,
        max_iterations: Optional[int] = None,
        once: bool = False,
    ) -> Dict[str, Any]:
        """
        Run interactive execution loop.

        Args:
            engagement_id: Engagement to work on
            max_iterations: Max number of iterations (None = infinite)
            once: Run only one iteration then stop

        Returns:
            Dict with execution summary
        """
        summary = {
            "iterations": 0,
            "commands_executed": 0,
            "commands_skipped": 0,
            "successes": 0,
            "failures": 0,
            "aborted": False,
        }

        click.echo("\n" + "=" * 70)
        click.echo(click.style("AI INTERACTIVE EXECUTOR", fg="cyan", bold=True))
        click.echo("=" * 70)

        if self.approval_mode == ApprovalMode.DRY_RUN:
            click.echo(
                click.style("🔍 DRY-RUN MODE", fg="yellow", bold=True)
                + " - Commands will not be executed"
            )
        elif self.approval_mode == ApprovalMode.AUTO_LOW:
            click.echo(
                click.style("⚡ AUTO-LOW MODE", fg="green")
                + " - LOW risk commands auto-approved"
            )
        elif self.approval_mode == ApprovalMode.AUTO_MEDIUM:
            click.echo(
                click.style("⚡ AUTO-MEDIUM MODE", fg="yellow")
                + " - LOW/MEDIUM risk commands auto-approved"
            )
        else:
            click.echo(
                click.style("👤 MANUAL MODE", fg="blue")
                + " - All commands require approval"
            )

        click.echo("=" * 70 + "\n")

        iteration = 0
        while True:
            iteration += 1
            summary["iterations"] = iteration

            # Check iteration limit
            if max_iterations and iteration > max_iterations:
                click.echo(f"\n✓ Reached iteration limit ({max_iterations})")
                break

            click.echo(f"\n{'─' * 70}")
            click.echo(click.style(f"ITERATION {iteration}", fg="cyan", bold=True))
            click.echo(f"{'─' * 70}\n")

            try:
                # Step 1: Get AI recommendation
                click.echo("🤖 Getting AI recommendation...")
                recommendation = self.recommender.suggest_next_step(
                    engagement_id, target_host_ids=self.target_host_ids
                )

                if recommendation.get("error"):
                    click.echo(
                        click.style(f"✗ Error: {recommendation['error']}", fg="red")
                    )
                    break

                # Display recommendation
                self._display_recommendation(recommendation)

                # Step 2: Map to command
                click.echo("\n🔧 Mapping to command...")
                command = self.mapper.map_to_command(recommendation, engagement_id)

                if not command:
                    click.echo(
                        click.style(
                            "⚠ Could not map recommendation to command - skipping",
                            fg="yellow",
                        )
                    )
                    summary["commands_skipped"] += 1

                    if once:
                        break
                    continue

                click.echo(click.style(f"Command: {command}", fg="cyan"))

                # Step 3: Risk assessment
                action = recommendation.get("action", "")
                risk_level = self.safety.assess_risk(action, command)

                # Step 4: Get approval
                try:
                    approved = self.safety.require_approval(
                        action=action,
                        target=recommendation.get("target", ""),
                        command=command,
                        risk_level=risk_level,
                    )
                except KeyboardInterrupt:
                    summary["aborted"] = True
                    click.echo(
                        click.style("\n\n🛑 Execution aborted by user", fg="red")
                    )
                    break

                if not approved:
                    summary["commands_skipped"] += 1
                    if once:
                        break
                    continue

                # Step 5: Execute (if not dry-run)
                if self.approval_mode == ApprovalMode.DRY_RUN:
                    click.echo(
                        click.style(
                            "\n[DRY-RUN] Skipping actual execution\n", fg="yellow"
                        )
                    )
                    summary["commands_skipped"] += 1
                    if once:
                        break
                    continue

                # Log execution start
                exec_id = self.exec_log.log_execution(
                    engagement_id=engagement_id,
                    action=action,
                    command=command,
                    risk_level=risk_level.value,
                    auto_approved=(
                        risk_level == RiskLevel.LOW
                        and self.approval_mode
                        in [ApprovalMode.AUTO_LOW, ApprovalMode.AUTO_MEDIUM]
                    ),
                )

                click.echo(click.style("\n⚡ Executing...", fg="green", bold=True))

                # Execute command
                result = self._execute_command(command)
                summary["commands_executed"] += 1

                # Step 6: Parse result
                click.echo("\n📊 Parsing result...")
                parsed = self.parser.parse_result(
                    command=command,
                    stdout=result["stdout"],
                    stderr=result["stderr"],
                    exit_code=result["exit_code"],
                )

                success = parsed.get("success", False)
                if success:
                    summary["successes"] += 1
                    click.echo(
                        click.style(f"✓ {parsed.get('details', 'Success')}", fg="green")
                    )
                else:
                    summary["failures"] += 1
                    click.echo(
                        click.style(f"✗ {parsed.get('details', 'Failed')}", fg="red")
                    )

                # Step 7: Apply feedback
                click.echo("\n🔄 Applying feedback to database...")
                feedback_applied = self.feedback.apply_feedback(
                    engagement_id=engagement_id,
                    parsed_result=parsed,
                    recommendation=recommendation,
                    command=command,
                )

                # Display feedback
                self._display_feedback(feedback_applied)

                # Update execution log
                self.exec_log.update_result(
                    execution_id=exec_id,
                    exit_code=result["exit_code"],
                    stdout=result["stdout"],
                    stderr=result["stderr"],
                    success=success,
                    feedback_applied=feedback_applied,
                )

                # Stop if once flag is set
                if once:
                    click.echo(click.style("\n✓ Single iteration complete", fg="green"))
                    break

            except KeyboardInterrupt:
                summary["aborted"] = True
                click.echo(
                    click.style("\n\n🛑 Execution interrupted by user", fg="red")
                )
                break
            except Exception as e:
                logger.exception("Error during execution loop")
                click.echo(click.style(f"\n✗ Error: {e}", fg="red"))
                summary["failures"] += 1

                if once:
                    break

        # Display summary
        self._display_summary(summary)

        return summary

    def _execute_command(self, command: str) -> Dict[str, Any]:
        """Execute shell command and capture output."""
        try:
            result = subprocess.run(
                command,
                shell=True,  # nosec B602 - intentional for security tool command execution
                capture_output=True,
                text=True,
                timeout=60,
            )

            return {
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }
        except subprocess.TimeoutExpired:
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": "Command timed out after 60 seconds",
            }
        except Exception as e:
            return {"exit_code": -1, "stdout": "", "stderr": str(e)}

    def _display_recommendation(self, rec: Dict[str, Any]):
        """Display AI recommendation."""
        click.echo(click.style("\n📋 AI RECOMMENDATION:", fg="cyan", bold=True))
        click.echo(f"  Action: {rec.get('action', 'N/A')}")
        click.echo(f"  Target: {rec.get('target', 'N/A')}")
        click.echo(f"  Rationale: {rec.get('rationale', 'N/A')}")

        risk = rec.get("risk_level", "unknown").upper()
        risk_colors = {"LOW": "green", "MEDIUM": "yellow", "HIGH": "red"}
        click.echo(f"  Risk: {click.style(risk, fg=risk_colors.get(risk, 'white'))}")

    def _display_feedback(self, feedback: Dict[str, Any]):
        """Display feedback results."""
        updates = []

        if feedback.get("hosts_updated", 0) > 0:
            updates.append(f"{feedback['hosts_updated']} host(s)")
        if feedback.get("credentials_updated", 0) > 0:
            updates.append(f"{feedback['credentials_updated']} credential(s)")
        if feedback.get("services_added", 0) > 0:
            updates.append(f"{feedback['services_added']} service(s)")

        if updates:
            click.echo(click.style(f"  Updated: {', '.join(updates)}", fg="green"))

            for note in feedback.get("notes_added", []):
                click.echo(f"    • {note}")
        else:
            click.echo("  No database updates")

    def _display_summary(self, summary: Dict[str, Any]):
        """Display execution summary."""
        click.echo("\n" + "=" * 70)
        click.echo(click.style("EXECUTION SUMMARY", fg="cyan", bold=True))
        click.echo("=" * 70)
        click.echo(f"Iterations:         {summary['iterations']}")
        click.echo(f"Commands executed:  {summary['commands_executed']}")
        click.echo(f"Commands skipped:   {summary['commands_skipped']}")
        click.echo(
            f"Successes:          {click.style(str(summary['successes']), fg='green')}"
        )
        click.echo(
            f"Failures:           {click.style(str(summary['failures']), fg='red')}"
        )

        if summary["aborted"]:
            click.echo(click.style("\nStatus: Aborted by user", fg="yellow"))
        else:
            click.echo(click.style("\nStatus: Complete", fg="green"))

        click.echo("=" * 70 + "\n")
