"""
Wazuh SIEM Client.

Wraps the existing WazuhClient to implement the SIEMClient interface
for unified multi-SIEM detection validation.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from souleyez.integrations.siem.base import (
    SIEMAlert,
    SIEMClient,
    SIEMConnectionStatus,
    SIEMRule,
)
from souleyez.integrations.siem.rule_mappings.wazuh_rules import (
    WAZUH_ATTACK_RULES,
    get_wazuh_rules_for_attack,
)


class WazuhSIEMClient(SIEMClient):
    """Wazuh implementation of the SIEMClient interface.

    Wraps the existing WazuhClient to provide a unified interface
    that can be used interchangeably with other SIEM clients.
    """

    def __init__(
        self,
        api_url: str,
        username: str,
        password: str,
        verify_ssl: bool = False,
        indexer_url: Optional[str] = None,
        indexer_user: Optional[str] = None,
        indexer_password: Optional[str] = None,
    ):
        """Initialize Wazuh SIEM client.

        Args:
            api_url: Wazuh Manager API URL (e.g., https://10.0.0.111:55000)
            username: Wazuh Manager API username
            password: Wazuh Manager API password
            verify_ssl: Verify SSL certificates
            indexer_url: Wazuh Indexer URL (auto-derived if not set)
            indexer_user: Indexer username (defaults to 'admin')
            indexer_password: Indexer password (defaults to manager password)
        """
        from souleyez.integrations.wazuh.client import WazuhClient

        self._client = WazuhClient(
            api_url=api_url,
            username=username,
            password=password,
            verify_ssl=verify_ssl,
            indexer_url=indexer_url,
            indexer_user=indexer_user,
            indexer_password=indexer_password,
        )

    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> "WazuhSIEMClient":
        """Create client from configuration dictionary.

        Args:
            config: Dict with keys: api_url, username, password, etc.

        Returns:
            WazuhSIEMClient instance
        """
        return cls(
            api_url=config.get("api_url", ""),
            username=config.get("username", ""),
            password=config.get("password", ""),
            verify_ssl=config.get("verify_ssl", False),
            indexer_url=config.get("indexer_url"),
            indexer_user=config.get("indexer_user"),
            indexer_password=config.get("indexer_password"),
        )

    @property
    def siem_type(self) -> str:
        """Return the SIEM type identifier."""
        return "wazuh"

    def test_connection(self) -> SIEMConnectionStatus:
        """Test connection to Wazuh Manager.

        Returns:
            SIEMConnectionStatus with connection details
        """
        result = self._client.test_connection()

        return SIEMConnectionStatus(
            connected=result.get("connected", False),
            version=result.get("version", ""),
            error=result.get("error", ""),
            siem_type="wazuh",
            details={
                "hostname": result.get("hostname", ""),
                "cluster": result.get("cluster", False),
            },
        )

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
        """Query alerts from Wazuh Indexer.

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
        # Convert rule_ids to integers for Wazuh
        int_rule_ids = None
        if rule_ids:
            int_rule_ids = [int(r) for r in rule_ids if r.isdigit()]

        # Wazuh uses agent_ip for IP filtering
        # We prioritize source_ip for attacker-based detection
        filter_ip = source_ip or dest_ip

        raw_alerts = self._client.get_alerts(
            start_time=start_time,
            end_time=end_time,
            agent_ip=filter_ip,
            rule_ids=int_rule_ids,
            search_text=search_text,
            limit=limit,
        )

        return [self._normalize_alert(alert) for alert in raw_alerts]

    def _normalize_alert(self, raw_alert: Dict[str, Any]) -> SIEMAlert:
        """Convert Wazuh alert to normalized SIEMAlert.

        Args:
            raw_alert: Raw alert from Wazuh Indexer

        Returns:
            Normalized SIEMAlert
        """
        # Extract timestamp
        timestamp_str = raw_alert.get("timestamp", "")
        try:
            timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            timestamp = datetime.now()

        # Extract rule info
        rule = raw_alert.get("rule", {})
        rule_id = str(rule.get("id", ""))
        rule_name = rule.get("description", "")
        severity = self._map_level_to_severity(rule.get("level", 0))

        # Extract IPs from various fields
        data = raw_alert.get("data", {})
        source_ip = (
            data.get("srcip")
            or data.get("src_ip")
            or raw_alert.get("agent", {}).get("ip")
        )
        dest_ip = data.get("dstip") or data.get("dst_ip") or data.get("dstIp")

        # Extract MITRE info
        mitre = rule.get("mitre", {})
        mitre_tactics = mitre.get("tactic", [])
        mitre_techniques = mitre.get("id", [])

        # Ensure lists
        if isinstance(mitre_tactics, str):
            mitre_tactics = [mitre_tactics]
        if isinstance(mitre_techniques, str):
            mitre_techniques = [mitre_techniques]

        return SIEMAlert(
            id=raw_alert.get("_id", raw_alert.get("id", "")),
            timestamp=timestamp,
            rule_id=rule_id,
            rule_name=rule_name,
            severity=severity,
            source_ip=source_ip,
            dest_ip=dest_ip,
            description=rule.get("description", ""),
            raw_data=raw_alert,
            mitre_tactics=mitre_tactics,
            mitre_techniques=mitre_techniques,
        )

    def _map_level_to_severity(self, level: int) -> str:
        """Map Wazuh rule level to normalized severity.

        Wazuh levels: 0-15
        - 0-3: Low/Info
        - 4-7: Medium
        - 8-11: High
        - 12-15: Critical
        """
        if level >= 12:
            return "critical"
        elif level >= 8:
            return "high"
        elif level >= 4:
            return "medium"
        else:
            return "low"

    def get_rules(
        self, rule_ids: Optional[List[str]] = None, enabled_only: bool = True
    ) -> List[SIEMRule]:
        """Get detection rules from Wazuh Manager.

        Args:
            rule_ids: Optional list of specific rule IDs to fetch
            enabled_only: Only return enabled rules

        Returns:
            List of normalized SIEMRule objects
        """
        # Convert rule_ids to integers for Wazuh
        int_rule_ids = None
        if rule_ids:
            int_rule_ids = [int(r) for r in rule_ids if r.isdigit()]

        raw_rules = self._client.get_rules(rule_ids=int_rule_ids)

        rules = []
        for raw_rule in raw_rules:
            # Skip disabled rules if requested
            status = raw_rule.get("status", "enabled")
            if enabled_only and status != "enabled":
                continue

            # Extract MITRE info
            mitre = raw_rule.get("mitre", {})
            mitre_tactics = mitre.get("tactic", [])
            mitre_techniques = mitre.get("id", [])

            if isinstance(mitre_tactics, str):
                mitre_tactics = [mitre_tactics]
            if isinstance(mitre_techniques, str):
                mitre_techniques = [mitre_techniques]

            rule = SIEMRule(
                id=str(raw_rule.get("id", "")),
                name=raw_rule.get("description", ""),
                description=raw_rule.get("description", ""),
                severity=self._map_level_to_severity(raw_rule.get("level", 0)),
                enabled=(status == "enabled"),
                mitre_tactics=mitre_tactics,
                mitre_techniques=mitre_techniques,
                raw_data=raw_rule,
            )
            rules.append(rule)

        return rules

    def get_recommended_rules(self, attack_type: str) -> List[Dict[str, Any]]:
        """Get recommended Wazuh rules for detecting an attack type.

        Args:
            attack_type: Tool/attack name (e.g., 'nmap', 'hydra')

        Returns:
            List of rule recommendations
        """
        rules_info = get_wazuh_rules_for_attack(attack_type)
        recommendations = []

        rule_ids = rules_info.get("rule_ids", [])
        rule_names = rules_info.get("rule_names", {})

        for rule_id in rule_ids:
            recommendations.append(
                {
                    "rule_id": str(rule_id),
                    "rule_name": rule_names.get(rule_id, f"Rule {rule_id}"),
                    "description": f"Wazuh rule for detecting {attack_type} attacks",
                    "severity": "high",
                    "enabled": True,  # Assume enabled by default
                    "siem_type": "wazuh",
                }
            )

        return recommendations

    def get_detection_guidance(self, attack_type: str) -> str:
        """Get detection guidance for an attack type.

        Args:
            attack_type: Tool/attack name

        Returns:
            Human-readable detection guidance
        """
        rules_info = get_wazuh_rules_for_attack(attack_type)
        return rules_info.get(
            "detection_guidance",
            "Review SIEM rule configuration for this attack category.",
        )
