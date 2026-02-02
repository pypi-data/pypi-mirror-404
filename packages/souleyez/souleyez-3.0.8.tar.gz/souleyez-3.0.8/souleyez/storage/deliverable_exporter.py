"""
Export deliverables in multiple formats (CSV, JSON, Markdown).
"""

import csv
import json
from datetime import datetime
from typing import Dict, List, Optional

from .database import get_db
from .deliverable_evidence import EvidenceManager
from .deliverables import DeliverableManager
from .engagements import EngagementManager


class DeliverableExporter:
    """Export deliverables with evidence in various formats."""

    def __init__(self):
        self.db = get_db()
        self.dm = DeliverableManager()
        self.em = EvidenceManager()
        self.eng_mgr = EngagementManager()

    def export_csv(
        self, engagement_id: int, output_path: str, include_evidence: bool = True
    ) -> bool:
        """
        Export deliverables to CSV format.

        Args:
            engagement_id: Target engagement
            output_path: Output file path
            include_evidence: Include evidence counts/details

        Returns:
            True if successful
        """
        deliverables = self.dm.list_deliverables(engagement_id)
        engagement = self.eng_mgr.get_by_id(engagement_id)

        if not deliverables:
            return False

        with open(output_path, "w", newline="", encoding="utf-8") as f:
            # Define CSV columns
            fieldnames = [
                "ID",
                "Category",
                "Title",
                "Description",
                "Status",
                "Priority",
                "Target Type",
                "Target Value",
                "Current Value",
                "Completion %",
                "Started At",
                "Completed At",
                "Estimated Hours",
                "Actual Hours",
                "Blocker",
            ]

            if include_evidence:
                fieldnames.extend(
                    [
                        "Findings Count",
                        "Credentials Count",
                        "Screenshots Count",
                        "Jobs Count",
                        "Total Evidence",
                    ]
                )

            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for d in deliverables:
                row = {
                    "ID": d["id"],
                    "Category": d["category"].replace("_", " ").title(),
                    "Title": d["title"],
                    "Description": d.get("description", ""),
                    "Status": d["status"].replace("_", " ").title(),
                    "Priority": d.get("priority", "medium").title(),
                    "Target Type": d.get("target_type", "manual").title(),
                    "Target Value": d.get("target_value", ""),
                    "Current Value": d.get("current_value", ""),
                    "Completion %": f"{d.get('completion_rate', 0) * 100:.0f}%",
                    "Started At": d.get("started_at", ""),
                    "Completed At": d.get("completed_at", ""),
                    "Estimated Hours": d.get("estimated_hours", 0),
                    "Actual Hours": d.get("actual_hours", 0),
                    "Blocker": d.get("blocker", ""),
                }

                if include_evidence:
                    evidence = self.em.get_evidence(d["id"])
                    row.update(
                        {
                            "Findings Count": len(evidence["findings"]),
                            "Credentials Count": len(evidence["credentials"]),
                            "Screenshots Count": len(evidence["screenshots"]),
                            "Jobs Count": len(evidence["jobs"]),
                            "Total Evidence": sum(
                                [
                                    len(evidence["findings"]),
                                    len(evidence["credentials"]),
                                    len(evidence["screenshots"]),
                                    len(evidence["jobs"]),
                                ]
                            ),
                        }
                    )

                writer.writerow(row)

        return True

    def export_json(
        self, engagement_id: int, output_path: str, include_evidence: bool = True
    ) -> bool:
        """
        Export deliverables to JSON format.

        Args:
            engagement_id: Target engagement
            output_path: Output file path
            include_evidence: Include full evidence details

        Returns:
            True if successful
        """
        deliverables = self.dm.list_deliverables(engagement_id)
        engagement = self.eng_mgr.get_by_id(engagement_id)
        summary = self.dm.get_summary(engagement_id)

        export_data = {
            "engagement": {
                "id": engagement["id"],
                "name": engagement["name"],
                "description": engagement.get("description"),
                "created_at": engagement.get("created_at"),
                "engagement_type": engagement.get("engagement_type", "network"),
                "estimated_hours": engagement.get("estimated_hours", 0),
                "actual_hours": engagement.get("actual_hours", 0),
            },
            "summary": {
                "total_deliverables": summary["total"],
                "completed": summary["completed"],
                "in_progress": summary["in_progress"],
                "pending": summary["pending"],
                "completion_rate": f"{summary['completion_rate'] * 100:.1f}%",
            },
            "deliverables": [],
            "exported_at": datetime.now().isoformat(),
        }

        for d in deliverables:
            deliverable_data = {
                "id": d["id"],
                "category": d["category"],
                "title": d["title"],
                "description": d.get("description"),
                "status": d["status"],
                "priority": d.get("priority", "medium"),
                "target_type": d.get("target_type", "manual"),
                "target_value": d.get("target_value"),
                "current_value": d.get("current_value"),
                "completion_rate": d.get("completion_rate", 0),
                "auto_validate": d.get("auto_validate", False),
                "validation_query": d.get("validation_query"),
                "started_at": d.get("started_at"),
                "completed_at": d.get("completed_at"),
                "estimated_hours": d.get("estimated_hours", 0),
                "actual_hours": d.get("actual_hours", 0),
                "blocker": d.get("blocker"),
                "assigned_to": d.get("assigned_to"),
            }

            if include_evidence:
                evidence = self.em.get_evidence(d["id"])

                deliverable_data["evidence"] = {
                    "findings": [
                        {
                            "id": f["id"],
                            "title": f.get("title"),
                            "severity": f.get("severity"),
                            "host": f.get("host"),
                            "link_notes": f.get("_link_notes"),
                            "linked_at": f.get("_linked_at"),
                        }
                        for f in evidence["findings"]
                    ],
                    "credentials": [
                        {
                            "id": c["id"],
                            "username": c.get("username"),
                            "host": c.get("host"),
                            "credential_type": c.get("credential_type"),
                            "link_notes": c.get("_link_notes"),
                            "linked_at": c.get("_linked_at"),
                        }
                        for c in evidence["credentials"]
                    ],
                    "screenshots": [
                        {
                            "id": s["id"],
                            "filename": s.get("filename"),
                            "description": s.get("description"),
                            "link_notes": s.get("_link_notes"),
                            "linked_at": s.get("_linked_at"),
                        }
                        for s in evidence["screenshots"]
                    ],
                    "jobs": [
                        {
                            "id": j["id"],
                            "tool": j.get("tool"),
                            "target": j.get("target"),
                            "status": j.get("status"),
                            "link_notes": j.get("_link_notes"),
                            "linked_at": j.get("_linked_at"),
                        }
                        for j in evidence["jobs"]
                    ],
                    "total_evidence": sum(
                        [
                            len(evidence["findings"]),
                            len(evidence["credentials"]),
                            len(evidence["screenshots"]),
                            len(evidence["jobs"]),
                        ]
                    ),
                }

            export_data["deliverables"].append(deliverable_data)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)

        return True

    def export_markdown(
        self, engagement_id: int, output_path: str, include_evidence: bool = True
    ) -> bool:
        """
        Export deliverables to Markdown format.

        Args:
            engagement_id: Target engagement
            output_path: Output file path
            include_evidence: Include evidence details

        Returns:
            True if successful
        """
        deliverables = self.dm.list_deliverables(engagement_id)
        engagement = self.eng_mgr.get_by_id(engagement_id)
        summary = self.dm.get_summary(engagement_id)

        if not deliverables:
            return False

        with open(output_path, "w", encoding="utf-8") as f:
            # Header
            f.write(f"# Deliverables Report: {engagement['name']}\n\n")
            f.write(
                f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            )

            if engagement.get("description"):
                f.write(f"**Description:** {engagement['description']}\n\n")

            # Summary section
            f.write("## Summary\n\n")
            f.write(f"- **Total Deliverables:** {summary['total']}\n")
            f.write(f"- **Completed:** {summary['completed']}\n")
            f.write(f"- **In Progress:** {summary['in_progress']}\n")
            f.write(f"- **Pending:** {summary['pending']}\n")
            f.write(
                f"- **Completion Rate:** {summary['completion_rate'] * 100:.1f}%\n\n"
            )

            if engagement.get("actual_hours"):
                f.write(f"- **Time Spent:** {engagement['actual_hours']:.1f} hours\n")
            if engagement.get("estimated_hours"):
                f.write(
                    f"- **Estimated Time:** {engagement['estimated_hours']:.1f} hours\n"
                )

            f.write("\n---\n\n")

            # Group by category
            categories = {}
            for d in deliverables:
                cat = d["category"]
                if cat not in categories:
                    categories[cat] = []
                categories[cat].append(d)

            # Write deliverables by category
            category_names = {
                "reconnaissance": "Reconnaissance",
                "enumeration": "Enumeration",
                "exploitation": "Exploitation",
                "post_exploitation": "Post-Exploitation",
                "techniques": "Techniques",
            }

            for category in [
                "reconnaissance",
                "enumeration",
                "exploitation",
                "post_exploitation",
                "techniques",
            ]:
                if category not in categories:
                    continue

                cat_deliverables = categories[category]
                cat_name = category_names.get(category, category.title())

                f.write(f"## {cat_name}\n\n")

                for d in cat_deliverables:
                    # Status emoji
                    status_emoji = {
                        "completed": "✅",
                        "in_progress": "🔄",
                        "pending": "⏳",
                        "failed": "❌",
                    }.get(d["status"], "❓")

                    # Priority badge
                    priority = d.get("priority", "medium")
                    priority_badge = {
                        "critical": "🔴 CRITICAL",
                        "high": "🟡 HIGH",
                        "medium": "🟢 MEDIUM",
                        "low": "⚪ LOW",
                    }.get(priority, "MEDIUM")

                    f.write(f"### {status_emoji} {d['title']}\n\n")
                    f.write(f"**Priority:** {priority_badge}  \n")
                    f.write(f"**Status:** {d['status'].replace('_', ' ').title()}  \n")

                    if d.get("description"):
                        f.write(f"\n{d['description']}\n\n")

                    # Progress info
                    if d.get("target_type") == "count":
                        current = d.get("current_value", 0)
                        target = d.get("target_value", 0)
                        f.write(f"**Progress:** {current}/{target}\n\n")
                    elif d.get("target_type") == "boolean":
                        status = (
                            "✓ Complete"
                            if d["status"] == "completed"
                            else "✗ Incomplete"
                        )
                        f.write(f"**Status:** {status}\n\n")

                    # Time info
                    if d.get("actual_hours"):
                        f.write(f"**Time Spent:** {d['actual_hours']:.1f}h\n\n")

                    # Blocker
                    if d.get("blocker"):
                        f.write(f"⚠️ **Blocker:** {d['blocker']}\n\n")

                    # Evidence
                    if include_evidence:
                        evidence = self.em.get_evidence(d["id"])
                        total_evidence = sum(
                            [
                                len(evidence["findings"]),
                                len(evidence["credentials"]),
                                len(evidence["screenshots"]),
                                len(evidence["jobs"]),
                            ]
                        )

                        if total_evidence > 0:
                            f.write("**Evidence:**\n\n")

                            if evidence["findings"]:
                                f.write(
                                    f"- **Findings:** {len(evidence['findings'])}\n"
                                )
                                for finding in evidence["findings"][:3]:
                                    severity = finding.get("severity", "N/A").upper()
                                    f.write(
                                        f"  - [{severity}] {finding.get('title', 'Unknown')}\n"
                                    )
                                if len(evidence["findings"]) > 3:
                                    f.write(
                                        f"  - ... and {len(evidence['findings']) - 3} more\n"
                                    )

                            if evidence["credentials"]:
                                f.write(
                                    f"- **Credentials:** {len(evidence['credentials'])}\n"
                                )
                                for cred in evidence["credentials"][:3]:
                                    f.write(
                                        f"  - {cred.get('username', 'N/A')}@{cred.get('host', 'N/A')}\n"
                                    )
                                if len(evidence["credentials"]) > 3:
                                    f.write(
                                        f"  - ... and {len(evidence['credentials']) - 3} more\n"
                                    )

                            if evidence["screenshots"]:
                                f.write(
                                    f"- **Screenshots:** {len(evidence['screenshots'])}\n"
                                )

                            if evidence["jobs"]:
                                f.write(f"- **Jobs:** {len(evidence['jobs'])}\n")

                            f.write("\n")

                    f.write("---\n\n")

        return True
