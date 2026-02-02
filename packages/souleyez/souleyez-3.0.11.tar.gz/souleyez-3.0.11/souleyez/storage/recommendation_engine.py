"""
AI-powered recommendation engine for deliverables.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional

from .database import get_db
from .deliverable_evidence import EvidenceManager
from .deliverables import DeliverableManager
from .timeline_tracker import TimelineTracker


class RecommendationEngine:
    """Generate smart recommendations for next actions and coverage gaps."""

    def __init__(self):
        self.db = get_db()
        self.dm = DeliverableManager()
        self.em = EvidenceManager()
        self.tt = TimelineTracker()

    def get_recommendations(self, engagement_id: int) -> Dict:
        """
        Generate comprehensive recommendations for an engagement.

        Returns:
            Dict with recommendation categories
        """
        return {
            "next_actions": self._get_next_actions(engagement_id),
            "blockers": self._get_blocker_recommendations(engagement_id),
            "quick_wins": self._get_quick_wins(engagement_id),
            "coverage_gaps": self._get_coverage_gaps(engagement_id),
            "at_risk": self._get_at_risk_deliverables(engagement_id),
            "priority_boost": self._get_priority_boost_suggestions(engagement_id),
        }

    def _get_next_actions(self, engagement_id: int) -> List[Dict]:
        """
        Recommend next deliverables to work on based on:
        - Dependencies (phase order)
        - Priority (critical first)
        - Evidence availability (easier to complete)
        - Time estimates
        """
        deliverables = self.dm.list_deliverables(engagement_id)

        # Filter to pending/in_progress only
        actionable = [
            d for d in deliverables if d["status"] in ["pending", "in_progress"]
        ]

        recommendations = []

        for d in actionable:
            score = 0
            reasons = []

            # Priority scoring (critical = 100, high = 75, medium = 50, low = 25)
            priority_scores = {"critical": 100, "high": 75, "medium": 50, "low": 25}
            priority_score = priority_scores.get(d.get("priority", "medium"), 50)
            score += priority_score

            if d.get("priority") == "critical":
                reasons.append("Critical priority")

            # Phase scoring (earlier phases = higher score)
            phase_scores = {
                "reconnaissance": 90,
                "enumeration": 80,
                "exploitation": 70,
                "post_exploitation": 60,
                "techniques": 50,
            }
            phase_score = phase_scores.get(d["category"], 50)
            score += phase_score

            # Evidence availability (if we already have related evidence, easier to complete)
            evidence_count = self.em.get_evidence_count(d["id"])
            if evidence_count > 0:
                score += 20
                reasons.append(f"{evidence_count} evidence items available")

            # In-progress items get boost (finish what we started)
            if d["status"] == "in_progress":
                score += 30
                reasons.append("Already in progress")

                # Add time pressure if started long ago
                if d.get("started_at"):
                    try:
                        started = datetime.fromisoformat(
                            d["started_at"].replace("Z", "+00:00")
                        )
                        hours_since = (datetime.now() - started).total_seconds() / 3600
                        if hours_since > 24:
                            score += 15
                            reasons.append(f"Started {int(hours_since)}h ago")
                    except:
                        pass

            # Blocker penalty
            if d.get("blocker"):
                score -= 50
                reasons.append("⚠️ BLOCKED")

            # Auto-validate items (quick wins)
            if d.get("auto_validate"):
                score += 10
                reasons.append("Auto-validates")

            recommendations.append(
                {
                    "deliverable": d,
                    "score": score,
                    "reasons": reasons,
                    "confidence": min(100, int(score / 3)),  # Scale to 0-100
                }
            )

        # Sort by score descending
        recommendations.sort(key=lambda x: x["score"], reverse=True)

        return recommendations[:10]  # Top 10

    def _get_blocker_recommendations(self, engagement_id: int) -> List[Dict]:
        """
        Recommend actions to unblock deliverables.
        """
        blockers = self.tt.get_blockers(engagement_id)

        recommendations = []

        for blocker in blockers:
            suggestions = []
            blocker_text = blocker.get("blocker", "").lower()

            # Pattern matching for common blockers
            if (
                "credential" in blocker_text
                or "password" in blocker_text
                or "login" in blocker_text
            ):
                suggestions.append("Run credential enumeration tools (hydra, medusa)")
                suggestions.append("Check for default credentials")
                suggestions.append("Review already discovered credentials")

            if "access" in blocker_text or "permission" in blocker_text:
                suggestions.append("Verify network connectivity")
                suggestions.append("Check firewall rules")
                suggestions.append("Request VPN access from client")

            if "client" in blocker_text or "waiting" in blocker_text:
                suggestions.append("Send follow-up email to client")
                suggestions.append("Schedule status call")
                suggestions.append("Document waiting time for billing")

            if (
                "tool" in blocker_text
                or "error" in blocker_text
                or "fail" in blocker_text
            ):
                suggestions.append("Check tool installation")
                suggestions.append("Review error logs")
                suggestions.append("Try alternative tool")

            if "scope" in blocker_text or "clarification" in blocker_text:
                suggestions.append("Review engagement SOW")
                suggestions.append("Email client for clarification")
                suggestions.append("Document scope questions")

            # Generic suggestions if no patterns matched
            if not suggestions:
                suggestions.append("Review blocker details")
                suggestions.append("Consult with team lead")
                suggestions.append("Document resolution steps")

            recommendations.append(
                {
                    "deliverable": blocker,
                    "blocker": blocker.get("blocker"),
                    "suggestions": suggestions,
                    "priority": blocker.get("priority", "medium"),
                }
            )

        return recommendations

    def _get_quick_wins(self, engagement_id: int) -> List[Dict]:
        """
        Identify deliverables that can be completed quickly.

        Criteria:
        - Auto-validate enabled
        - Low estimated hours
        - Evidence already available
        - Low priority (save critical for focused time)
        """
        deliverables = self.dm.list_deliverables(engagement_id)

        quick_wins = []

        for d in deliverables:
            if d["status"] != "pending":
                continue

            score = 0
            reasons = []

            # Auto-validate = quick
            if d.get("auto_validate"):
                score += 40
                reasons.append("Auto-validates")

            # Low estimated hours
            est_hours = d.get("estimated_hours", 0)
            if est_hours > 0 and est_hours <= 2:
                score += 30
                reasons.append(f"Quick ({est_hours}h estimated)")
            elif est_hours == 0:
                score += 20  # No estimate, assume might be quick

            # Evidence available
            evidence_count = self.em.get_evidence_count(d["id"])
            if evidence_count > 0:
                score += 20
                reasons.append(f"{evidence_count} evidence ready")

            # Boolean target type (simple yes/no)
            if d.get("target_type") == "boolean":
                score += 15
                reasons.append("Simple yes/no target")

            # Not critical (save those for focused time)
            if d.get("priority") in ["low", "medium"]:
                score += 10

            if score >= 40:  # Threshold for "quick win"
                quick_wins.append(
                    {
                        "deliverable": d,
                        "score": score,
                        "reasons": reasons,
                        "estimated_minutes": (
                            int(est_hours * 60) if est_hours > 0 else 30
                        ),
                    }
                )

        # Sort by score
        quick_wins.sort(key=lambda x: x["score"], reverse=True)

        return quick_wins[:5]  # Top 5

    def _get_coverage_gaps(self, engagement_id: int) -> List[Dict]:
        """
        Identify phases or categories with low completion rates.
        """
        phase_breakdown = self.tt.get_phase_breakdown(engagement_id)

        gaps = []

        for phase, stats in phase_breakdown.items():
            if stats["total"] == 0:
                continue

            completion_rate = stats["completion_rate"]

            # Flag phases below 50% completion
            if completion_rate < 50:
                severity = "critical" if completion_rate < 25 else "high"

                gaps.append(
                    {
                        "phase": phase,
                        "completion_rate": completion_rate,
                        "completed": stats["completed"],
                        "total": stats["total"],
                        "remaining": stats["total"] - stats["completed"],
                        "severity": severity,
                        "recommendation": self._get_phase_recommendation(phase, stats),
                    }
                )

        # Sort by completion rate (lowest first)
        gaps.sort(key=lambda x: x["completion_rate"])

        return gaps

    def _get_phase_recommendation(self, phase: str, stats: Dict) -> str:
        """Generate phase-specific recommendation."""
        remaining = stats["total"] - stats["completed"]

        recommendations = {
            "reconnaissance": f"Run OSINT tools to complete {remaining} recon deliverables",
            "enumeration": f"Enumerate services and users ({remaining} items remaining)",
            "exploitation": f"Test for vulnerabilities - {remaining} exploit deliverables pending",
            "post_exploitation": f"Complete post-exploitation activities ({remaining} remaining)",
            "techniques": f"Document techniques and methodologies ({remaining} items left)",
        }

        return recommendations.get(phase, f"Complete {remaining} {phase} deliverables")

    def _get_at_risk_deliverables(self, engagement_id: int) -> List[Dict]:
        """
        Identify deliverables at risk of delay.

        At risk if:
        - In progress for > 24 hours
        - Critical priority but not started
        - Has blocker
        - High estimated hours but no progress
        """
        deliverables = self.dm.list_deliverables(engagement_id)

        at_risk = []

        for d in deliverables:
            if d["status"] == "completed":
                continue

            risk_factors = []
            risk_score = 0

            # In progress too long
            if d["status"] == "in_progress" and d.get("started_at"):
                try:
                    started = datetime.fromisoformat(
                        d["started_at"].replace("Z", "+00:00")
                    )
                    hours_since = (datetime.now() - started).total_seconds() / 3600

                    if hours_since > 48:
                        risk_score += 40
                        risk_factors.append(f"In progress {int(hours_since)}h")
                    elif hours_since > 24:
                        risk_score += 20
                        risk_factors.append(f"In progress {int(hours_since)}h")
                except:
                    pass

            # Critical but not started
            if d.get("priority") == "critical" and d["status"] == "pending":
                risk_score += 30
                risk_factors.append("Critical priority not started")

            # Has blocker
            if d.get("blocker"):
                risk_score += 50
                risk_factors.append("Blocked")

            # High estimated hours but pending
            est_hours = d.get("estimated_hours", 0)
            if est_hours > 8 and d["status"] == "pending":
                risk_score += 15
                risk_factors.append(f"{est_hours}h estimated, not started")

            if risk_score >= 20:  # Risk threshold
                severity = (
                    "critical"
                    if risk_score >= 50
                    else ("high" if risk_score >= 35 else "medium")
                )

                at_risk.append(
                    {
                        "deliverable": d,
                        "risk_score": risk_score,
                        "risk_factors": risk_factors,
                        "severity": severity,
                    }
                )

        # Sort by risk score
        at_risk.sort(key=lambda x: x["risk_score"], reverse=True)

        return at_risk[:5]  # Top 5

    def _get_priority_boost_suggestions(self, engagement_id: int) -> List[Dict]:
        """
        Suggest deliverables that should be higher priority.

        Based on:
        - Lots of evidence collected (we found something interesting)
        - Related to critical findings
        - Dependency for other deliverables
        """
        deliverables = self.dm.list_deliverables(engagement_id)

        suggestions = []

        for d in deliverables:
            if d["status"] == "completed":
                continue

            current_priority = d.get("priority", "medium")

            # Skip if already critical
            if current_priority == "critical":
                continue

            boost_score = 0
            reasons = []

            # High evidence count (we found something interesting)
            evidence = self.em.get_evidence(d["id"])

            critical_findings = len(
                [f for f in evidence["findings"] if f.get("severity") == "critical"]
            )
            high_findings = len(
                [f for f in evidence["findings"] if f.get("severity") == "high"]
            )

            if critical_findings > 0:
                boost_score += 50
                reasons.append(f"{critical_findings} critical findings linked")

            if high_findings > 0:
                boost_score += 25
                reasons.append(f"{high_findings} high findings linked")

            # Lots of evidence in general
            total_evidence = sum(
                [
                    len(evidence["findings"]),
                    len(evidence["credentials"]),
                    len(evidence["screenshots"]),
                    len(evidence["jobs"]),
                ]
            )

            if total_evidence > 10:
                boost_score += 20
                reasons.append(f"{total_evidence} evidence items")

            if boost_score >= 25:  # Threshold
                suggested_priority = "critical" if boost_score >= 50 else "high"

                suggestions.append(
                    {
                        "deliverable": d,
                        "current_priority": current_priority,
                        "suggested_priority": suggested_priority,
                        "boost_score": boost_score,
                        "reasons": reasons,
                    }
                )

        # Sort by boost score
        suggestions.sort(key=lambda x: x["boost_score"], reverse=True)

        return suggestions[:5]  # Top 5
