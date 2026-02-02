"""
SIEM Abstraction Layer - Base Classes.

Provides abstract base class and normalized data structures for
multi-SIEM support (Wazuh, Splunk, Elastic SIEM, Microsoft Sentinel).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class SIEMAlert:
    """Normalized alert structure across all SIEMs.

    This provides a consistent interface for alerts regardless of
    whether they come from Wazuh, Splunk, Elastic, or Sentinel.
    """

    id: str
    timestamp: datetime
    rule_id: str
    rule_name: str
    severity: str  # critical, high, medium, low, info
    source_ip: Optional[str]
    dest_ip: Optional[str]
    description: str
    raw_data: Dict[str, Any]
    mitre_tactics: List[str] = field(default_factory=list)
    mitre_techniques: List[str] = field(default_factory=list)

    def matches_attack(
        self,
        attack_type: str,
        source_ip: Optional[str] = None,
        dest_ip: Optional[str] = None,
    ) -> bool:
        """Check if this alert matches an attack pattern.

        Args:
            attack_type: Type of attack (e.g., 'nmap', 'hydra')
            source_ip: Optional source IP to match
            dest_ip: Optional destination IP to match

        Returns:
            True if alert matches the attack pattern
        """
        # IP matching
        if source_ip and self.source_ip != source_ip:
            return False
        if dest_ip and self.dest_ip != dest_ip:
            return False

        # Attack type is typically checked against rule patterns
        # This is a base implementation - subclasses may override
        attack_keywords = attack_type.lower().split("_")
        rule_text = f"{self.rule_name} {self.description}".lower()

        return any(kw in rule_text for kw in attack_keywords)


@dataclass
class SIEMRule:
    """Normalized rule/detection structure across all SIEMs."""

    id: str
    name: str
    description: str
    severity: str  # critical, high, medium, low, info
    enabled: bool
    mitre_tactics: List[str] = field(default_factory=list)
    mitre_techniques: List[str] = field(default_factory=list)
    raw_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SIEMConnectionStatus:
    """Connection status for a SIEM."""

    connected: bool
    version: str = ""
    error: str = ""
    siem_type: str = ""
    details: Dict[str, Any] = field(default_factory=dict)


class SIEMClient(ABC):
    """Abstract base class for SIEM integrations.

    All SIEM clients (Wazuh, Splunk, Elastic, Sentinel) must implement
    this interface to provide consistent detection validation.
    """

    @property
    @abstractmethod
    def siem_type(self) -> str:
        """Return the SIEM type identifier.

        Returns:
            One of: 'wazuh', 'splunk', 'elastic', 'sentinel'
        """
        pass

    @abstractmethod
    def test_connection(self) -> SIEMConnectionStatus:
        """Test connection to the SIEM.

        Returns:
            SIEMConnectionStatus with connection details
        """
        pass

    @abstractmethod
    def get_alerts(
        self,
        start_time: datetime,
        end_time: datetime,
        source_ip: Optional[str] = None,
        dest_ip: Optional[str] = None,
        rule_ids: Optional[List[str]] = None,
        search_text: Optional[str] = None,
        limit: int = 100,
    ) -> List[SIEMAlert]:
        """Query alerts from the SIEM.

        Args:
            start_time: Start of time range
            end_time: End of time range
            source_ip: Filter by source IP
            dest_ip: Filter by destination IP
            rule_ids: Filter by specific rule IDs
            search_text: Free text search
            limit: Maximum number of results

        Returns:
            List of normalized SIEMAlert objects
        """
        pass

    @abstractmethod
    def get_rules(
        self, rule_ids: Optional[List[str]] = None, enabled_only: bool = True
    ) -> List[SIEMRule]:
        """Get detection rules from the SIEM.

        Args:
            rule_ids: Optional list of specific rule IDs to fetch
            enabled_only: Only return enabled rules

        Returns:
            List of normalized SIEMRule objects
        """
        pass

    @abstractmethod
    def get_recommended_rules(self, attack_type: str) -> List[Dict[str, Any]]:
        """Get recommended rules for detecting a specific attack type.

        Args:
            attack_type: Tool/attack name (e.g., 'nmap', 'hydra', 'sqlmap')

        Returns:
            List of rule recommendations with:
            - rule_id: SIEM-specific rule identifier
            - rule_name: Human-readable name
            - description: What the rule detects
            - severity: Rule severity
            - enabled: Whether rule is currently enabled
        """
        pass

    def search_alerts_for_attack(
        self,
        attack_type: str,
        attack_time: datetime,
        source_ip: Optional[str] = None,
        target_ip: Optional[str] = None,
        time_window_minutes: int = 5,
    ) -> List[SIEMAlert]:
        """Search for alerts related to a specific attack.

        Convenience method that wraps get_alerts with attack-specific
        time window and filtering.

        Args:
            attack_type: Type of attack (e.g., 'nmap', 'hydra')
            attack_time: When the attack was executed
            source_ip: Source IP of the attack
            target_ip: Target IP of the attack
            time_window_minutes: Search window around attack time

        Returns:
            List of matching alerts
        """
        from datetime import timedelta

        # Calculate time window
        start_time = attack_time - timedelta(minutes=time_window_minutes)
        end_time = attack_time + timedelta(minutes=time_window_minutes)

        # Get alerts in time window
        alerts = self.get_alerts(
            start_time=start_time,
            end_time=end_time,
            source_ip=source_ip,
            dest_ip=target_ip,
        )

        # Filter by attack type patterns
        matching_alerts = [
            alert
            for alert in alerts
            if alert.matches_attack(attack_type, source_ip, target_ip)
        ]

        return matching_alerts

    def check_detection(
        self,
        attack_type: str,
        attack_time: datetime,
        source_ip: Optional[str] = None,
        target_ip: Optional[str] = None,
        expected_rule_ids: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Check if an attack was detected by the SIEM.

        Args:
            attack_type: Type of attack
            attack_time: When the attack occurred
            source_ip: Source IP of attack
            target_ip: Target IP of attack
            expected_rule_ids: Expected rule IDs that should fire

        Returns:
            Dict with:
            - detected: bool
            - alerts: List of matching alerts
            - matched_rules: List of rule IDs that fired
            - expected_rules_matched: List of expected rules that fired
            - expected_rules_missed: List of expected rules that didn't fire
        """
        alerts = self.search_alerts_for_attack(
            attack_type=attack_type,
            attack_time=attack_time,
            source_ip=source_ip,
            target_ip=target_ip,
        )

        matched_rules = list(set(alert.rule_id for alert in alerts))

        result = {
            "detected": len(alerts) > 0,
            "alerts": alerts,
            "alert_count": len(alerts),
            "matched_rules": matched_rules,
            "matched_rule_count": len(matched_rules),
        }

        if expected_rule_ids:
            expected_set = set(str(r) for r in expected_rule_ids)
            matched_set = set(str(r) for r in matched_rules)
            result["expected_rules_matched"] = list(expected_set & matched_set)
            result["expected_rules_missed"] = list(expected_set - matched_set)

        return result
