"""
Microsoft Sentinel SIEM Client.

Implements the SIEMClient interface for Microsoft Sentinel (Azure).
Uses Azure REST APIs for querying alerts and analytics rules.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import requests

from souleyez.integrations.siem.base import (
    SIEMAlert,
    SIEMClient,
    SIEMConnectionStatus,
    SIEMRule,
)


class SentinelSIEMClient(SIEMClient):
    """Microsoft Sentinel implementation of the SIEMClient interface.

    Uses Azure APIs:
    - Log Analytics: POST https://api.loganalytics.io/v1/workspaces/{id}/query
    - Sentinel Incidents: GET /providers/Microsoft.SecurityInsights/incidents
    - Analytics Rules: GET /providers/Microsoft.SecurityInsights/alertRules
    """

    def __init__(
        self,
        tenant_id: str,
        client_id: str,
        client_secret: str,
        subscription_id: str,
        resource_group: str,
        workspace_name: str,
        workspace_id: str,
    ):
        """Initialize Microsoft Sentinel client.

        Args:
            tenant_id: Azure AD tenant ID
            client_id: Azure AD app registration client ID
            client_secret: Azure AD app registration client secret
            subscription_id: Azure subscription ID
            resource_group: Resource group containing the workspace
            workspace_name: Log Analytics workspace name
            workspace_id: Log Analytics workspace ID (GUID)
        """
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.subscription_id = subscription_id
        self.resource_group = resource_group
        self.workspace_name = workspace_name
        self.workspace_id = workspace_id

        self._access_token: Optional[str] = None
        self._token_expiry: Optional[datetime] = None

        # Azure endpoints
        self.login_url = (
            f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
        )
        self.log_analytics_url = (
            f"https://api.loganalytics.io/v1/workspaces/{workspace_id}"
        )
        self.management_base = "https://management.azure.com"
        self.sentinel_base = (
            f"{self.management_base}/subscriptions/{subscription_id}"
            f"/resourceGroups/{resource_group}"
            f"/providers/Microsoft.OperationalInsights/workspaces/{workspace_name}"
            f"/providers/Microsoft.SecurityInsights"
        )

    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> "SentinelSIEMClient":
        """Create client from configuration dictionary.

        Args:
            config: Dict with Azure credentials

        Returns:
            SentinelSIEMClient instance
        """
        return cls(
            tenant_id=config.get("tenant_id", ""),
            client_id=config.get("client_id", ""),
            client_secret=config.get("client_secret", ""),
            subscription_id=config.get("subscription_id", ""),
            resource_group=config.get("resource_group", ""),
            workspace_name=config.get("workspace_name", ""),
            workspace_id=config.get("workspace_id", ""),
        )

    @property
    def siem_type(self) -> str:
        """Return the SIEM type identifier."""
        return "sentinel"

    def _get_access_token(
        self, scope: str = "https://api.loganalytics.io/.default"
    ) -> str:
        """Get Azure AD access token.

        Args:
            scope: OAuth scope

        Returns:
            Access token string
        """
        # Check cached token
        if self._access_token and self._token_expiry:
            if datetime.now() < self._token_expiry:
                return self._access_token

        # Request new token
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": scope,
        }

        response = requests.post(self.login_url, data=data, timeout=30)
        response.raise_for_status()

        token_data = response.json()
        self._access_token = token_data["access_token"]
        expires_in = token_data.get("expires_in", 3600)
        self._token_expiry = datetime.now() + timedelta(seconds=expires_in - 60)

        return self._access_token

    def _log_analytics_query(self, kql: str) -> List[Dict[str, Any]]:
        """Execute KQL query against Log Analytics.

        Args:
            kql: Kusto Query Language query

        Returns:
            List of result rows as dictionaries
        """
        token = self._get_access_token("https://api.loganalytics.io/.default")

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        response = requests.post(
            f"{self.log_analytics_url}/query",
            headers=headers,
            json={"query": kql},
            timeout=60,
        )
        response.raise_for_status()

        data = response.json()
        tables = data.get("tables", [])

        if not tables:
            return []

        # Convert first table to list of dicts
        table = tables[0]
        columns = [col["name"] for col in table.get("columns", [])]
        rows = table.get("rows", [])

        return [dict(zip(columns, row)) for row in rows]

    def _management_request(
        self,
        method: str,
        endpoint: str,
        json_data: Optional[Dict] = None,
    ) -> requests.Response:
        """Make Azure Management API request.

        Args:
            method: HTTP method
            endpoint: API endpoint (relative to sentinel_base)
            json_data: Request body

        Returns:
            Response object
        """
        token = self._get_access_token("https://management.azure.com/.default")

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        url = f"{self.sentinel_base}{endpoint}?api-version=2023-02-01"

        return requests.request(
            method=method, url=url, headers=headers, json=json_data, timeout=60
        )

    def test_connection(self) -> SIEMConnectionStatus:
        """Test connection to Microsoft Sentinel.

        Returns:
            SIEMConnectionStatus with connection details
        """
        try:
            # Test Log Analytics connection with simple query
            result = self._log_analytics_query("print test='connected'")

            if result:
                return SIEMConnectionStatus(
                    connected=True,
                    version="Azure Sentinel",
                    siem_type="sentinel",
                    details={
                        "workspace_id": self.workspace_id,
                        "workspace_name": self.workspace_name,
                        "subscription": self.subscription_id,
                    },
                )
            else:
                return SIEMConnectionStatus(
                    connected=False,
                    error="Query returned no results",
                    siem_type="sentinel",
                )

        except requests.exceptions.ConnectionError as e:
            return SIEMConnectionStatus(
                connected=False,
                error=f"Connection failed: {str(e)}",
                siem_type="sentinel",
            )
        except Exception as e:
            return SIEMConnectionStatus(
                connected=False, error=str(e), siem_type="sentinel"
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
        """Query alerts from Microsoft Sentinel.

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
        # Build KQL query
        kql_parts = [
            "SecurityAlert",
            f"| where TimeGenerated between(datetime({start_time.isoformat()}) .. datetime({end_time.isoformat()}))",
        ]

        # IP filters (check Entities JSON)
        if source_ip:
            kql_parts.append(f'| where Entities contains "{source_ip}"')
        if dest_ip:
            kql_parts.append(f'| where Entities contains "{dest_ip}"')

        # Rule ID filter
        if rule_ids:
            rule_filter = " or ".join(f'AlertName == "{r}"' for r in rule_ids)
            kql_parts.append(f"| where {rule_filter}")

        # Search text
        if search_text:
            kql_parts.append(f'| where * contains "{search_text}"')

        # Limit and project
        kql_parts.extend(
            [
                f"| take {limit}",
                "| project TimeGenerated, AlertName, AlertSeverity, Description, "
                "Tactics, Entities, ExtendedProperties, ProviderName, SystemAlertId",
            ]
        )

        kql = "\n".join(kql_parts)

        try:
            results = self._log_analytics_query(kql)
            return [self._normalize_alert(r) for r in results]
        except Exception:
            return []

    def _normalize_alert(self, raw_alert: Dict[str, Any]) -> SIEMAlert:
        """Convert Sentinel alert to normalized SIEMAlert.

        Args:
            raw_alert: Raw alert from Log Analytics

        Returns:
            Normalized SIEMAlert
        """
        import json

        # Parse timestamp
        timestamp_str = raw_alert.get("TimeGenerated", "")
        try:
            timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            timestamp = datetime.now()

        # Map severity
        severity = self._map_severity(raw_alert.get("AlertSeverity", ""))

        # Parse entities for IPs
        source_ip = None
        dest_ip = None
        entities_str = raw_alert.get("Entities", "[]")
        try:
            entities = json.loads(entities_str) if entities_str else []
            for entity in entities:
                if entity.get("Type") == "ip":
                    addr = entity.get("Address", "")
                    if not source_ip:
                        source_ip = addr
                    elif not dest_ip:
                        dest_ip = addr
        except (json.JSONDecodeError, TypeError):
            pass

        # Parse tactics
        tactics_str = raw_alert.get("Tactics", "")
        mitre_tactics = []
        if tactics_str:
            try:
                mitre_tactics = (
                    json.loads(tactics_str)
                    if tactics_str.startswith("[")
                    else [tactics_str]
                )
            except json.JSONDecodeError:
                mitre_tactics = [tactics_str] if tactics_str else []

        return SIEMAlert(
            id=raw_alert.get("SystemAlertId", ""),
            timestamp=timestamp,
            rule_id=raw_alert.get("AlertName", ""),
            rule_name=raw_alert.get("AlertName", ""),
            severity=severity,
            source_ip=source_ip,
            dest_ip=dest_ip,
            description=raw_alert.get("Description", ""),
            raw_data=raw_alert,
            mitre_tactics=mitre_tactics,
            mitre_techniques=[],
        )

    def _map_severity(self, severity: str) -> str:
        """Map Sentinel severity to normalized severity."""
        severity_lower = str(severity).lower()
        if severity_lower == "high":
            return "critical"
        elif severity_lower == "medium":
            return "high"
        elif severity_lower == "low":
            return "medium"
        return "low"

    def get_rules(
        self, rule_ids: Optional[List[str]] = None, enabled_only: bool = True
    ) -> List[SIEMRule]:
        """Get analytics rules from Microsoft Sentinel.

        Args:
            rule_ids: Optional list of specific rule IDs
            enabled_only: Only return enabled rules

        Returns:
            List of normalized SIEMRule objects
        """
        try:
            response = self._management_request("GET", "/alertRules")

            if response.status_code != 200:
                return []

            data = response.json()
            raw_rules = data.get("value", [])

            rules = []
            for raw_rule in raw_rules:
                properties = raw_rule.get("properties", {})

                # Filter by rule_ids if provided
                rule_id = raw_rule.get("name", "")
                if rule_ids and rule_id not in rule_ids:
                    continue

                # Filter disabled if requested
                enabled = properties.get("enabled", True)
                if enabled_only and not enabled:
                    continue

                # Extract MITRE tactics
                mitre_tactics = properties.get("tactics", [])

                rule = SIEMRule(
                    id=rule_id,
                    name=properties.get("displayName", ""),
                    description=properties.get("description", ""),
                    severity=self._map_severity(properties.get("severity", "")),
                    enabled=enabled,
                    mitre_tactics=mitre_tactics,
                    mitre_techniques=[],
                    raw_data=raw_rule,
                )
                rules.append(rule)

            return rules

        except Exception:
            return []

    def get_recommended_rules(self, attack_type: str) -> List[Dict[str, Any]]:
        """Get recommended Sentinel rules for detecting an attack type.

        Args:
            attack_type: Tool/attack name (e.g., 'nmap', 'hydra')

        Returns:
            List of rule recommendations
        """
        # Sentinel content hub rule templates
        recommendations_map = {
            "nmap": [
                {
                    "rule_id": "port-scan-detection",
                    "rule_name": "Potential Port Scan Detection",
                    "kql": 'AzureFirewall | where Action == "Deny" | summarize count() by SourceIP | where count_ > 100',
                },
            ],
            "hydra": [
                {
                    "rule_id": "brute-force-detection",
                    "rule_name": "Brute Force Attack Detection",
                    "kql": "SigninLogs | where ResultType != 0 | summarize count() by IPAddress | where count_ > 10",
                },
            ],
            "sqlmap": [
                {
                    "rule_id": "sql-injection-detection",
                    "rule_name": "SQL Injection Attack Detection",
                    "kql": 'AzureDiagnostics | where Category == "SQLSecurityAuditEvents" | where action_name_s == "BATCH COMPLETED"',
                },
            ],
        }

        attack_lower = attack_type.lower()
        recommendations = recommendations_map.get(attack_lower, [])

        return [
            {
                "rule_id": r["rule_id"],
                "rule_name": r["rule_name"],
                "description": f"Sentinel analytics rule for {attack_type}",
                "severity": "high",
                "enabled": True,
                "siem_type": "sentinel",
                "kql_query": r.get("kql", ""),
            }
            for r in recommendations
        ]
