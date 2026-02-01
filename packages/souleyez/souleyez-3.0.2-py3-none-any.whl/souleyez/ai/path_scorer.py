#!/usr/bin/env python3
"""
souleyez.ai.path_scorer - Score and rank attack paths
"""

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class PathScorer:
    """
    Scores and ranks attack paths based on multiple factors.

    Scoring algorithm:
    Path Score = (Success * 0.4) + (Impact * 0.3) + (Stealth * 0.2) - (Complexity * 0.1)
    """

    # Scoring weights (configurable)
    WEIGHTS = {
        "success": 0.4,
        "impact": 0.3,
        "stealth": 0.2,
        "complexity": 0.1,  # Negative weight
    }

    # Success probability scoring
    SUCCESS_SCORES = {
        "has_valid_creds": 30,
        "known_vulnerability": 25,
        "common_service": 15,  # SSH, RDP, HTTP
        "uncommon_service": 5,
    }

    # Impact scoring
    IMPACT_SCORES = {
        "domain_controller": 40,
        "database": 30,
        "file_server": 20,
        "workstation": 10,
        "unknown": 5,
    }

    # Stealth scoring
    STEALTH_SCORES = {
        "credential_reuse": 30,  # No exploits
        "quiet_exploit": 20,
        "noisy_exploit": 10,
        "unknown": 15,  # Default to middle ground
    }

    # Complexity penalty
    COMPLEXITY_PENALTIES = {1: 0, 2: 5, 3: 5, 4: 10, 5: 10, 6: 20}

    def __init__(self):
        """Initialize path scorer."""
        pass

    def score_path(
        self, path: Dict[str, Any], engagement_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Score a single attack path.

        Args:
            path: Attack path with action, target, rationale
            engagement_data: Current engagement context (hosts, creds, etc.)

        Returns:
            Dict with:
                - path: Original path data
                - scores: Breakdown of scores
                - total_score: Final weighted score
        """
        # Calculate individual scores
        success_score = self._score_success(path, engagement_data)
        impact_score = self._score_impact(path, engagement_data)
        stealth_score = self._score_stealth(path)
        complexity_penalty = self._score_complexity(path)

        # Calculate weighted total
        total_score = (
            (success_score * self.WEIGHTS["success"])
            + (impact_score * self.WEIGHTS["impact"])
            + (stealth_score * self.WEIGHTS["stealth"])
            - (complexity_penalty * self.WEIGHTS["complexity"])
        )

        return {
            "path": path,
            "scores": {
                "success": success_score,
                "impact": impact_score,
                "stealth": stealth_score,
                "complexity": complexity_penalty,
            },
            "total_score": round(total_score, 2),
            "rank": None,  # Set by rank_paths()
        }

    def _score_success(
        self, path: Dict[str, Any], engagement_data: Dict[str, Any]
    ) -> float:
        """Score success probability based on available resources."""
        score = 0
        action = path.get("action", "").lower()
        target = path.get("target", "").lower()

        # Check for valid credentials
        creds = engagement_data.get("credentials", [])
        valid_creds = [c for c in creds if c.get("status") == "valid"]
        if valid_creds and (
            "credential" in action or "login" in action or "auth" in action
        ):
            score += self.SUCCESS_SCORES["has_valid_creds"]

        # Check for known vulnerabilities
        findings = engagement_data.get("findings", [])
        critical_vulns = [
            f for f in findings if f.get("severity") in ["critical", "high"]
        ]
        if critical_vulns and ("exploit" in action or "vulnerability" in action):
            score += self.SUCCESS_SCORES["known_vulnerability"]

        # Check service type
        common_services = ["ssh", "rdp", "http", "https", "mysql", "smb"]
        if any(svc in target or svc in action for svc in common_services):
            score += self.SUCCESS_SCORES["common_service"]
        else:
            score += self.SUCCESS_SCORES["uncommon_service"]

        return min(score, 100)  # Cap at 100

    def _score_impact(
        self, path: Dict[str, Any], engagement_data: Dict[str, Any]
    ) -> float:
        """Score potential impact of successful path."""
        target = path.get("target", "").lower()
        action = path.get("action", "").lower()

        # Check target type
        if "domain controller" in target or "dc" in target or "ad" in target:
            return self.IMPACT_SCORES["domain_controller"]

        if (
            "database" in target
            or "mysql" in target
            or "postgres" in target
            or "sql" in target
        ):
            return self.IMPACT_SCORES["database"]

        if "file server" in target or "smb" in target or "share" in target:
            return self.IMPACT_SCORES["file_server"]

        # Check for privilege escalation (high impact)
        if (
            "privilege" in action
            or "escalat" in action
            or "root" in action
            or "admin" in action
        ):
            return self.IMPACT_SCORES["database"]  # High impact

        # Default to workstation
        return self.IMPACT_SCORES["workstation"]

    def _score_stealth(self, path: Dict[str, Any]) -> float:
        """Score stealth/detection likelihood."""
        action = path.get("action", "").lower()

        # Credential reuse is stealthiest
        if "credential" in action and "exploit" not in action and "brute" not in action:
            return self.STEALTH_SCORES["credential_reuse"]

        # Known quiet exploits
        quiet_keywords = ["pass-the-hash", "token", "kerberos", "golden ticket"]
        if any(keyword in action for keyword in quiet_keywords):
            return self.STEALTH_SCORES["quiet_exploit"]

        # Noisy exploits
        noisy_keywords = ["brute", "scan", "spray", "exploit", "buffer overflow"]
        if any(keyword in action for keyword in noisy_keywords):
            return self.STEALTH_SCORES["noisy_exploit"]

        # Default
        return self.STEALTH_SCORES["unknown"]

    def _score_complexity(self, path: Dict[str, Any]) -> float:
        """Score complexity (simpler = better, so this is a penalty)."""
        # Single-step paths have no penalty
        # Multi-step paths get penalties based on length

        # Check if this is a multi-step path
        steps = path.get("steps", [])
        if steps:
            num_steps = len(steps)
        else:
            num_steps = 1  # Single-step path

        # Look up penalty
        if num_steps <= 5:
            return self.COMPLEXITY_PENALTIES.get(num_steps, 0)
        else:
            return self.COMPLEXITY_PENALTIES[6]

    def rank_paths(
        self, paths: List[Dict[str, Any]], engagement_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Score and rank multiple paths.

        Args:
            paths: List of attack path recommendations
            engagement_data: Current engagement context

        Returns:
            List of scored paths, sorted by total_score (highest first)
        """
        # Score each path
        scored_paths = []
        for path in paths:
            scored_path = self.score_path(path, engagement_data)
            scored_paths.append(scored_path)

        # Sort by total score (descending)
        scored_paths.sort(key=lambda x: x["total_score"], reverse=True)

        # Assign ranks
        for i, scored_path in enumerate(scored_paths, 1):
            scored_path["rank"] = i

        return scored_paths
