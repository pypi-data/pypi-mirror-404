"""
Elastic SIEM Client.

Implements the SIEMClient interface for Elastic Security (SIEM).
Uses the Elasticsearch and Kibana APIs for querying alerts and rules.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

import requests

from souleyez.integrations.siem.base import (
    SIEMAlert,
    SIEMClient,
    SIEMConnectionStatus,
    SIEMRule,
)


class ElasticSIEMClient(SIEMClient):
    """Elastic SIEM implementation of the SIEMClient interface.

    Uses Elasticsearch APIs:
    - Alerts: POST /.siem-signals-<space>/_search
    - Rules: GET /api/detection_engine/rules/_find

    Note: Requires Elastic Security (formerly SIEM) license.
    """

    def __init__(
        self,
        elasticsearch_url: str,
        kibana_url: Optional[str] = None,
        api_key: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        verify_ssl: bool = False,
        space: str = "default",
    ):
        """Initialize Elastic SIEM client.

        Args:
            elasticsearch_url: Elasticsearch URL (e.g., https://elastic:9200)
            kibana_url: Kibana URL (e.g., https://kibana:5601)
            api_key: Elasticsearch API key (alternative to user/pass)
            username: Elasticsearch username
            password: Elasticsearch password
            verify_ssl: Verify SSL certificates
            space: Kibana space (default: "default")
        """
        self.elasticsearch_url = elasticsearch_url.rstrip("/")
        self.kibana_url = (kibana_url or elasticsearch_url).rstrip("/")
        self.api_key = api_key
        self.username = username
        self.password = password
        self.verify_ssl = verify_ssl
        self.space = space

    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> "ElasticSIEMClient":
        """Create client from configuration dictionary.

        Args:
            config: Dict with connection parameters

        Returns:
            ElasticSIEMClient instance
        """
        return cls(
            elasticsearch_url=config.get("elasticsearch_url", ""),
            kibana_url=config.get("kibana_url"),
            api_key=config.get("api_key"),
            username=config.get("username"),
            password=config.get("password"),
            verify_ssl=config.get("verify_ssl", False),
            space=config.get("space", "default"),
        )

    @property
    def siem_type(self) -> str:
        """Return the SIEM type identifier."""
        return "elastic"

    def _get_auth(self):
        """Get authentication for requests."""
        if self.api_key:
            return None  # API key goes in headers
        elif self.username and self.password:
            return (self.username, self.password)
        return None

    def _get_headers(self) -> Dict[str, str]:
        """Get headers for requests."""
        headers = {
            "Content-Type": "application/json",
            "kbn-xsrf": "true",  # Required for Kibana API
        }
        if self.api_key:
            headers["Authorization"] = f"ApiKey {self.api_key}"
        return headers

    def _es_request(
        self,
        method: str,
        endpoint: str,
        json_data: Optional[Dict] = None,
    ) -> requests.Response:
        """Make Elasticsearch request.

        Args:
            method: HTTP method
            endpoint: API endpoint
            json_data: Request body

        Returns:
            Response object
        """
        url = f"{self.elasticsearch_url}{endpoint}"
        return requests.request(
            method=method,
            url=url,
            headers=self._get_headers(),
            auth=self._get_auth(),
            json=json_data,
            verify=self.verify_ssl,
            timeout=60,
        )

    def _kibana_request(
        self,
        method: str,
        endpoint: str,
        json_data: Optional[Dict] = None,
    ) -> requests.Response:
        """Make Kibana request.

        Args:
            method: HTTP method
            endpoint: API endpoint
            json_data: Request body

        Returns:
            Response object
        """
        # Handle space in URL
        if self.space != "default":
            url = f"{self.kibana_url}/s/{self.space}{endpoint}"
        else:
            url = f"{self.kibana_url}{endpoint}"

        return requests.request(
            method=method,
            url=url,
            headers=self._get_headers(),
            auth=self._get_auth(),
            json=json_data,
            verify=self.verify_ssl,
            timeout=60,
        )

    def test_connection(self) -> SIEMConnectionStatus:
        """Test connection to Elastic.

        Returns:
            SIEMConnectionStatus with connection details
        """
        try:
            # Test Elasticsearch connection
            response = self._es_request("GET", "/")
            response.raise_for_status()
            data = response.json()

            version = data.get("version", {}).get("number", "unknown")
            cluster_name = data.get("cluster_name", "unknown")

            return SIEMConnectionStatus(
                connected=True,
                version=version,
                siem_type="elastic",
                details={
                    "cluster_name": cluster_name,
                    "cluster_uuid": data.get("cluster_uuid", ""),
                    "tagline": data.get("tagline", ""),
                },
            )
        except requests.exceptions.ConnectionError as e:
            return SIEMConnectionStatus(
                connected=False,
                error=f"Connection failed: {str(e)}",
                siem_type="elastic",
            )
        except Exception as e:
            return SIEMConnectionStatus(
                connected=False, error=str(e), siem_type="elastic"
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
        """Query alerts from Elastic Security.

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
        # Build Elasticsearch query
        must_clauses = [
            {
                "range": {
                    "@timestamp": {
                        "gte": start_time.isoformat(),
                        "lte": end_time.isoformat(),
                    }
                }
            }
        ]

        # IP filters
        if source_ip:
            must_clauses.append(
                {
                    "multi_match": {
                        "query": source_ip,
                        "fields": ["source.ip", "client.ip", "host.ip"],
                    }
                }
            )
        if dest_ip:
            must_clauses.append(
                {
                    "multi_match": {
                        "query": dest_ip,
                        "fields": ["destination.ip", "server.ip"],
                    }
                }
            )

        # Rule ID filter
        if rule_ids:
            must_clauses.append({"terms": {"signal.rule.id": rule_ids}})

        # Search text
        if search_text:
            must_clauses.append({"query_string": {"query": f"*{search_text}*"}})

        query = {
            "size": limit,
            "sort": [{"@timestamp": {"order": "desc"}}],
            "query": {"bool": {"must": must_clauses}},
        }

        # Query the signals index
        index_pattern = f".siem-signals-{self.space}"
        try:
            response = self._es_request(
                "POST", f"/{index_pattern}/_search", json_data=query
            )

            if response.status_code == 404:
                # No signals index yet
                return []

            response.raise_for_status()
            data = response.json()
            hits = data.get("hits", {}).get("hits", [])
            return [self._normalize_alert(hit) for hit in hits]

        except requests.exceptions.HTTPError:
            return []

    def _normalize_alert(self, hit: Dict[str, Any]) -> SIEMAlert:
        """Convert Elasticsearch hit to normalized SIEMAlert.

        Args:
            hit: Raw hit from Elasticsearch

        Returns:
            Normalized SIEMAlert
        """
        source = hit.get("_source", {})
        signal = source.get("signal", {})
        rule = signal.get("rule", {})

        # Parse timestamp
        timestamp_str = source.get("@timestamp", "")
        try:
            timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            timestamp = datetime.now()

        # Extract rule info
        rule_id = rule.get("id", "")
        rule_name = rule.get("name", "")
        severity = rule.get("severity", "low")

        # Extract IPs
        source_data = source.get("source", {})
        dest_data = source.get("destination", {})
        source_ip = source_data.get("ip")
        dest_ip = dest_data.get("ip")

        # Extract MITRE info
        threats = rule.get("threat", [])
        mitre_tactics = []
        mitre_techniques = []
        for threat in threats:
            if threat.get("framework") == "MITRE ATT&CK":
                tactic = threat.get("tactic", {})
                if tactic.get("name"):
                    mitre_tactics.append(tactic.get("name"))
                for technique in threat.get("technique", []):
                    if technique.get("id"):
                        mitre_techniques.append(technique.get("id"))

        return SIEMAlert(
            id=hit.get("_id", ""),
            timestamp=timestamp,
            rule_id=rule_id,
            rule_name=rule_name,
            severity=severity,
            source_ip=source_ip,
            dest_ip=dest_ip,
            description=rule.get("description", ""),
            raw_data=source,
            mitre_tactics=mitre_tactics,
            mitre_techniques=mitre_techniques,
        )

    def get_rules(
        self, rule_ids: Optional[List[str]] = None, enabled_only: bool = True
    ) -> List[SIEMRule]:
        """Get detection rules from Elastic Security.

        Args:
            rule_ids: Optional list of specific rule IDs
            enabled_only: Only return enabled rules

        Returns:
            List of normalized SIEMRule objects
        """
        # Use Kibana Detection Engine API
        params = {
            "page": 1,
            "per_page": 500,
        }

        try:
            response = self._kibana_request(
                "GET", "/api/detection_engine/rules/_find", json_data=params
            )

            if response.status_code != 200:
                return []

            data = response.json()
            raw_rules = data.get("data", [])

            rules = []
            for raw_rule in raw_rules:
                # Filter by rule_ids if provided
                if rule_ids and raw_rule.get("id") not in rule_ids:
                    continue

                # Filter disabled if requested
                if enabled_only and not raw_rule.get("enabled", True):
                    continue

                # Extract MITRE info
                threats = raw_rule.get("threat", [])
                mitre_tactics = []
                mitre_techniques = []
                for threat in threats:
                    if threat.get("framework") == "MITRE ATT&CK":
                        tactic = threat.get("tactic", {})
                        if tactic.get("name"):
                            mitre_tactics.append(tactic.get("name"))
                        for technique in threat.get("technique", []):
                            if technique.get("id"):
                                mitre_techniques.append(technique.get("id"))

                rule = SIEMRule(
                    id=raw_rule.get("id", ""),
                    name=raw_rule.get("name", ""),
                    description=raw_rule.get("description", ""),
                    severity=raw_rule.get("severity", "low"),
                    enabled=raw_rule.get("enabled", True),
                    mitre_tactics=mitre_tactics,
                    mitre_techniques=mitre_techniques,
                    raw_data=raw_rule,
                )
                rules.append(rule)

            return rules

        except Exception:
            return []

    def get_recommended_rules(self, attack_type: str) -> List[Dict[str, Any]]:
        """Get recommended Elastic rules for detecting an attack type.

        Args:
            attack_type: Tool/attack name (e.g., 'nmap', 'hydra')

        Returns:
            List of rule recommendations
        """
        # Elastic Security prebuilt rule recommendations
        recommendations_map = {
            "nmap": [
                {
                    "rule_id": "port-scan-activity",
                    "rule_name": "Network Port Scan Activity",
                    "index": "filebeat-*,packetbeat-*",
                },
            ],
            "hydra": [
                {
                    "rule_id": "brute-force-ssh",
                    "rule_name": "SSH Brute Force Attempt",
                    "index": "auditbeat-*,filebeat-*",
                },
            ],
            "sqlmap": [
                {
                    "rule_id": "sql-injection-attack",
                    "rule_name": "SQL Injection Attempt",
                    "index": "filebeat-*",
                },
            ],
        }

        attack_lower = attack_type.lower()
        recommendations = recommendations_map.get(attack_lower, [])

        return [
            {
                "rule_id": r["rule_id"],
                "rule_name": r["rule_name"],
                "description": f"Elastic detection rule for {attack_type}",
                "severity": "high",
                "enabled": True,
                "siem_type": "elastic",
                "index_pattern": r.get("index", ""),
            }
            for r in recommendations
        ]
