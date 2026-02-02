"""
Evidence linking for deliverables.
"""

from typing import Dict, List, Optional

from .database import get_db


class EvidenceManager:
    """Manage evidence links for deliverables."""

    def __init__(self):
        self.db = get_db()

    def link_evidence(
        self,
        deliverable_id: int,
        evidence_type: str,
        evidence_id: int,
        linked_by: str = None,
        notes: str = None,
    ) -> int:
        """
        Link evidence to deliverable.

        Args:
            deliverable_id: Target deliverable
            evidence_type: 'finding', 'screenshot', 'credential', 'job'
            evidence_id: ID of the evidence item
            linked_by: Username who created the link
            notes: Optional notes about the link

        Returns:
            Link ID
        """
        # Check for duplicate
        existing = self.db.execute_one(
            """SELECT id FROM deliverable_evidence
               WHERE deliverable_id = ? AND evidence_type = ? AND evidence_id = ?""",
            (deliverable_id, evidence_type, evidence_id),
        )

        if existing:
            return existing["id"]  # Already linked

        return self.db.insert(
            "deliverable_evidence",
            {
                "deliverable_id": deliverable_id,
                "evidence_type": evidence_type,
                "evidence_id": evidence_id,
                "linked_by": linked_by,
                "notes": notes,
            },
        )

    def get_evidence(self, deliverable_id: int) -> Dict:
        """
        Get all evidence for deliverable, grouped by type.

        Returns:
            Dict with keys: findings, screenshots, credentials, jobs
        """
        links = self.db.execute(
            "SELECT * FROM deliverable_evidence WHERE deliverable_id = ? ORDER BY linked_at DESC",
            (deliverable_id,),
        )

        evidence = {"findings": [], "screenshots": [], "credentials": [], "jobs": []}

        for link in links:
            etype = link["evidence_type"]
            eid = link["evidence_id"]

            # Fetch actual evidence data
            if etype == "finding":
                finding = self._get_finding(eid)
                if finding:
                    finding["_link_notes"] = link["notes"]
                    finding["_linked_at"] = link["linked_at"]
                    finding["_link_id"] = link["id"]
                    evidence["findings"].append(finding)

            elif etype == "screenshot":
                screenshot = self._get_screenshot(eid)
                if screenshot:
                    screenshot["_link_notes"] = link["notes"]
                    screenshot["_linked_at"] = link["linked_at"]
                    screenshot["_link_id"] = link["id"]
                    evidence["screenshots"].append(screenshot)

            elif etype == "credential":
                credential = self._get_credential(eid)
                if credential:
                    credential["_link_notes"] = link["notes"]
                    credential["_linked_at"] = link["linked_at"]
                    credential["_link_id"] = link["id"]
                    evidence["credentials"].append(credential)

            elif etype == "job":
                job = self._get_job(eid)
                if job:
                    job["_link_notes"] = link["notes"]
                    job["_linked_at"] = link["linked_at"]
                    job["_link_id"] = link["id"]
                    evidence["jobs"].append(job)

        return evidence

    def suggest_evidence(self, deliverable_id: int, engagement_id: int = None) -> Dict:
        """
        AI-suggest related evidence based on deliverable keywords.

        Args:
            deliverable_id: Target deliverable
            engagement_id: Optional engagement filter
        Returns:
            Dict with suggested evidence items and confidence scores
        """
        from .deliverables import DeliverableManager

        dm = DeliverableManager()
        deliverable = dm.get_deliverable(deliverable_id)
        if not deliverable:
            # Return empty suggestions and helpful error
            return {
                "findings": [],
                "screenshots": [],
                "credentials": [],
                "jobs": [],
                "_error": "Deliverable not found or invalid ID.",
            }
        if not engagement_id:
            engagement_id = deliverable.get("engagement_id")
        # Extract keywords from title and description safely
        title = (deliverable.get("title") or "").lower()
        description = (deliverable.get("description") or "").lower()
        combined_text = f"{title} {description}"
        keywords = self._extract_keywords(combined_text)
        suggestions = {"findings": [], "screenshots": [], "credentials": [], "jobs": []}

        # Find related findings
        for keyword in keywords[:5]:  # Top 5 keywords
            findings = self.db.execute(
                """SELECT * FROM findings 
                   WHERE engagement_id = ? AND LOWER(title) LIKE ? 
                   LIMIT 10""",
                (engagement_id, f"%{keyword}%"),
            )
            for f in findings:
                # Avoid duplicates
                if not any(
                    existing["id"] == f["id"] for existing in suggestions["findings"]
                ):
                    f["_match_keyword"] = keyword
                    f["_confidence"] = self._calculate_confidence(
                        combined_text, f.get("title", "")
                    )
                    suggestions["findings"].append(f)

        # Find related credentials (if deliverable mentions credentials/users/passwords)
        if any(
            kw in combined_text
            for kw in ["credential", "user", "password", "account", "login", "auth"]
        ):
            credentials = self.db.execute(
                "SELECT * FROM credentials WHERE engagement_id = ? LIMIT 20",
                (engagement_id,),
            )
            for c in credentials:
                c["_confidence"] = 70  # Medium confidence for keyword match
                suggestions["credentials"].extend(credentials)

        # Find related screenshots
        screenshots = self.db.execute(
            "SELECT * FROM screenshots WHERE engagement_id = ? ORDER BY created_at DESC LIMIT 10",
            (engagement_id,),
        )
        for s in screenshots:
            s["_confidence"] = 50  # Lower confidence for screenshots
        suggestions["screenshots"] = screenshots

        # Sort findings by confidence
        suggestions["findings"].sort(
            key=lambda x: x.get("_confidence", 0), reverse=True
        )

        # Limit results
        suggestions["findings"] = suggestions["findings"][:10]
        suggestions["credentials"] = suggestions["credentials"][:10]

        return suggestions

    def unlink_evidence(
        self, deliverable_id: int, evidence_type: str, evidence_id: int
    ) -> bool:
        """Remove evidence link."""
        self.db.execute(
            """DELETE FROM deliverable_evidence 
               WHERE deliverable_id = ? AND evidence_type = ? AND evidence_id = ?""",
            (deliverable_id, evidence_type, evidence_id),
        )
        return True

    def get_evidence_count(self, deliverable_id: int) -> int:
        """Get count of linked evidence items."""
        result = self.db.execute_one(
            "SELECT COUNT(*) as count FROM deliverable_evidence WHERE deliverable_id = ?",
            (deliverable_id,),
        )
        return result["count"] if result else 0

    def get_deliverables_for_evidence(
        self, evidence_type: str, evidence_id: int
    ) -> List[Dict]:
        """Get all deliverables linked to this evidence item."""
        links = self.db.execute(
            """SELECT * FROM deliverable_evidence 
               WHERE evidence_type = ? AND evidence_id = ?""",
            (evidence_type, evidence_id),
        )

        deliverables = []
        if links:
            from .deliverables import DeliverableManager

            dm = DeliverableManager()

            for link in links:
                d = dm.get_deliverable(link["deliverable_id"])
                if d:
                    d["_link_notes"] = link["notes"]
                    d["_linked_at"] = link["linked_at"]
                    deliverables.append(d)

        return deliverables

    def _get_finding(self, finding_id: int) -> Optional[Dict]:
        """Fetch finding by ID."""
        return self.db.execute_one("SELECT * FROM findings WHERE id = ?", (finding_id,))

    def _get_screenshot(self, screenshot_id: int) -> Optional[Dict]:
        """Fetch screenshot by ID."""
        return self.db.execute_one(
            "SELECT * FROM screenshots WHERE id = ?", (screenshot_id,)
        )

    def _get_credential(self, credential_id: int) -> Optional[Dict]:
        """Fetch credential by ID."""
        return self.db.execute_one(
            "SELECT * FROM credentials WHERE id = ?", (credential_id,)
        )

    def _get_job(self, job_id: int) -> Optional[Dict]:
        """Fetch job by ID."""
        from souleyez.engine.background import list_jobs

        jobs = list_jobs(limit=1000)
        for job in jobs:
            if job.get("id") == job_id:
                return job
        return None

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract meaningful keywords from text."""
        stopwords = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "from",
            "by",
            "as",
            "is",
            "are",
            "was",
            "were",
            "be",
            "this",
            "that",
            "which",
            "what",
            "when",
            "where",
            "who",
            "how",
        }
        # Clean and split text
        words = text.lower().replace("-", " ").replace("_", " ").split()
        # Filter stopwords and short words
        keywords = [w for w in words if len(w) > 3 and w not in stopwords]
        # Remove duplicates while preserving order
        seen = set()
        unique_keywords = []
        for kw in keywords:
            if kw not in seen:
                seen.add(kw)
                unique_keywords.append(kw)
        return unique_keywords

    def _calculate_confidence(self, deliverable_text: str, finding_title: str) -> int:
        """
        Calculate match confidence (0-100).

        Higher score means better match between deliverable and finding.
        """
        if not finding_title:
            return 30  # Low confidence

        d_words = set(deliverable_text.lower().split())
        f_words = set(finding_title.lower().split())

        common = d_words & f_words
        if not common:
            return 30  # Low confidence

        # Calculate Jaccard similarity
        union = d_words | f_words
        ratio = len(common) / len(union) if union else 0

        # Boost score if important security terms match
        important_terms = {
            "sql",
            "xss",
            "injection",
            "authentication",
            "authorization",
            "encryption",
            "credential",
            "vulnerability",
            "exploit",
        }
        important_matches = common & important_terms
        boost = len(important_matches) * 10

        base_score = int(ratio * 100)
        final_score = min(100, base_score + boost)

        return final_score
