"""
Google SecOps (Chronicle) SIEM Client.

Implements the SIEMClient interface for Google SecOps (formerly Chronicle SIEM).
Uses Chronicle REST APIs for querying detections, events, and rules.
"""

import base64
import json
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import requests

from souleyez.integrations.siem.base import (
    SIEMAlert,
    SIEMClient,
    SIEMConnectionStatus,
    SIEMRule,
)


class GoogleSecOpsSIEMClient(SIEMClient):
    """Google SecOps (Chronicle) implementation of the SIEMClient interface.

    Uses Chronicle APIs:
    - Auth: OAuth 2.0 with service account JWT
    - Search: POST /v1alpha/events:udmSearch
    - Detections: GET /v1alpha/detections
    - Rules: GET /v1alpha/rules
    """

    # Chronicle API regions
    REGIONS = {
        "us": "https://backstory.googleapis.com",
        "europe": "https://europe-backstory.googleapis.com",
        "asia-southeast1": "https://asia-southeast1-backstory.googleapis.com",
    }

    def __init__(
        self,
        credentials_json: str,
        customer_id: str,
        region: str = "us",
        project_id: Optional[str] = None,
        verify_ssl: bool = True,
    ):
        """Initialize Google SecOps client.

        Args:
            credentials_json: Service account JSON key (as string)
            customer_id: Chronicle customer ID
            region: Chronicle region ('us', 'europe', 'asia-southeast1')
            project_id: Google Cloud project ID (optional, extracted from creds if not provided)
            verify_ssl: Verify SSL certificates
        """
        self.customer_id = customer_id
        self.region = region.lower()
        self.verify_ssl = verify_ssl
        self._access_token: Optional[str] = None
        self._token_expiry: Optional[datetime] = None

        # Parse service account credentials
        try:
            if isinstance(credentials_json, str):
                self._credentials = json.loads(credentials_json)
            else:
                self._credentials = credentials_json
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid service account JSON: {e}")

        self.project_id = project_id or self._credentials.get("project_id", "")

        # Set API base URL
        self.api_base = self.REGIONS.get(self.region, self.REGIONS["us"])

    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> "GoogleSecOpsSIEMClient":
        """Create client from configuration dictionary.

        Args:
            config: Dict with credentials_json, customer_id, region, etc.

        Returns:
            GoogleSecOpsSIEMClient instance
        """
        return cls(
            credentials_json=config.get("credentials_json", "{}"),
            customer_id=config.get("customer_id", ""),
            region=config.get("region", "us"),
            project_id=config.get("project_id"),
            verify_ssl=config.get("verify_ssl", True),
        )

    @property
    def siem_type(self) -> str:
        """Return the SIEM type identifier."""
        return "google_secops"

    def _create_jwt(self) -> str:
        """Create a signed JWT for service account authentication.

        Returns:
            Signed JWT string
        """
        from cryptography.hazmat.backends import default_backend
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import padding

        now = int(time.time())
        expiry = now + 3600  # 1 hour

        # JWT header
        header = {
            "alg": "RS256",
            "typ": "JWT",
            "kid": self._credentials.get("private_key_id", ""),
        }

        # JWT claims
        claims = {
            "iss": self._credentials.get("client_email", ""),
            "sub": self._credentials.get("client_email", ""),
            "aud": "https://oauth2.googleapis.com/token",
            "iat": now,
            "exp": expiry,
            "scope": "https://www.googleapis.com/auth/chronicle-backstory",
        }

        # Encode header and claims
        def b64_encode(data: dict) -> str:
            return (
                base64.urlsafe_b64encode(
                    json.dumps(data, separators=(",", ":")).encode()
                )
                .rstrip(b"=")
                .decode()
            )

        header_b64 = b64_encode(header)
        claims_b64 = b64_encode(claims)
        message = f"{header_b64}.{claims_b64}".encode()

        # Sign with private key
        private_key_pem = self._credentials.get("private_key", "")
        private_key = serialization.load_pem_private_key(
            private_key_pem.encode(), password=None, backend=default_backend()
        )

        signature = private_key.sign(message, padding.PKCS1v15(), hashes.SHA256())
        signature_b64 = base64.urlsafe_b64encode(signature).rstrip(b"=").decode()

        return f"{header_b64}.{claims_b64}.{signature_b64}"

    def _get_access_token(self) -> str:
        """Get Google OAuth access token using service account.

        Returns:
            Access token string
        """
        # Check cached token
        if self._access_token and self._token_expiry:
            if datetime.now() < self._token_expiry:
                return self._access_token

        # Create signed JWT
        jwt = self._create_jwt()

        # Exchange JWT for access token
        response = requests.post(
            "https://oauth2.googleapis.com/token",
            data={
                "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
                "assertion": jwt,
            },
            timeout=30,
            verify=self.verify_ssl,
        )
        response.raise_for_status()

        token_data = response.json()
        self._access_token = token_data["access_token"]
        expires_in = token_data.get("expires_in", 3600)
        self._token_expiry = datetime.now() + timedelta(seconds=expires_in - 60)

        return self._access_token

    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        json_data: Optional[Dict] = None,
    ) -> requests.Response:
        """Make authenticated API request.

        Args:
            method: HTTP method
            endpoint: API endpoint (relative to api_base)
            params: Query parameters
            json_data: JSON request body

        Returns:
            Response object
        """
        token = self._get_access_token()
        url = f"{self.api_base}{endpoint}"

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            params=params,
            json=json_data,
            verify=self.verify_ssl,
            timeout=60,
        )
        return response

    def test_connection(self) -> SIEMConnectionStatus:
        """Test connection to Google SecOps.

        Returns:
            SIEMConnectionStatus with connection details
        """
        try:
            # Try to get access token first (validates credentials)
            self._get_access_token()

            # Query for a small time window to verify API access
            response = self._request(
                "GET", "/v1alpha/detect/rules", params={"page_size": 1}
            )

            if response.status_code == 200:
                return SIEMConnectionStatus(
                    connected=True,
                    version="Chronicle API v1alpha",
                    siem_type="google_secops",
                    details={
                        "region": self.region,
                        "customer_id": self.customer_id,
                        "project_id": self.project_id,
                    },
                )
            elif response.status_code == 403:
                return SIEMConnectionStatus(
                    connected=False,
                    error="Permission denied. Check service account permissions.",
                    siem_type="google_secops",
                )
            else:
                return SIEMConnectionStatus(
                    connected=False,
                    error=f"API error: {response.status_code} - {response.text[:200]}",
                    siem_type="google_secops",
                )

        except requests.exceptions.ConnectionError as e:
            return SIEMConnectionStatus(
                connected=False,
                error=f"Connection failed: {str(e)}",
                siem_type="google_secops",
            )
        except ValueError as e:
            return SIEMConnectionStatus(
                connected=False,
                error=f"Configuration error: {str(e)}",
                siem_type="google_secops",
            )
        except Exception as e:
            return SIEMConnectionStatus(
                connected=False, error=str(e), siem_type="google_secops"
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
        """Query detections/alerts from Google SecOps.

        Args:
            start_time: Start of time range
            end_time: End of time range
            source_ip: Filter by source IP
            dest_ip: Filter by destination IP
            rule_ids: Filter by rule IDs
            search_text: Free text search
            limit: Maximum number of results

        Returns:
            List of normalized SIEMAlert objects
        """
        # Format times for Chronicle API (RFC 3339)
        start_str = start_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        end_str = end_time.strftime("%Y-%m-%dT%H:%M:%SZ")

        # Query detections endpoint
        params = {
            "start_time": start_str,
            "end_time": end_str,
            "page_size": min(limit, 1000),
        }

        response = self._request("GET", "/v1alpha/detect/detections", params=params)

        if response.status_code != 200:
            return []

        data = response.json()
        detections = data.get("detections", [])

        # Filter and normalize results
        alerts = []
        for detection in detections:
            alert = self._normalize_alert(detection)

            # Apply filters
            if source_ip and alert.source_ip != source_ip:
                continue
            if dest_ip and alert.dest_ip != dest_ip:
                continue
            if rule_ids and alert.rule_id not in rule_ids:
                continue
            if search_text:
                search_lower = search_text.lower()
                if (
                    search_lower not in alert.rule_name.lower()
                    and search_lower not in alert.description.lower()
                ):
                    continue

            alerts.append(alert)

            if len(alerts) >= limit:
                break

        return alerts

    def _normalize_alert(self, detection: Dict[str, Any]) -> SIEMAlert:
        """Convert Chronicle detection to normalized SIEMAlert.

        Args:
            detection: Raw detection from Chronicle API

        Returns:
            Normalized SIEMAlert
        """
        # Parse timestamp
        timestamp_str = detection.get("detectionTime", "")
        try:
            timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            timestamp = datetime.now()

        # Extract rule info
        rule_info = (
            detection.get("detection", [{}])[0] if detection.get("detection") else {}
        )
        rule_id = rule_info.get("ruleId", detection.get("ruleId", ""))
        rule_name = rule_info.get("ruleName", detection.get("ruleName", rule_id))

        # Map severity
        severity_raw = detection.get(
            "severity", rule_info.get("severity", "INFORMATIONAL")
        )
        severity = self._map_severity(severity_raw)

        # Extract IPs from UDM events
        source_ip = None
        dest_ip = None
        events = detection.get("collectionElements", [])
        for element in events:
            references = element.get("references", [])
            for ref in references:
                event = ref.get("event", {})
                principal = event.get("principal", {})
                target = event.get("target", {})

                if not source_ip and principal.get("ip"):
                    ips = principal.get("ip", [])
                    source_ip = ips[0] if ips else None

                if not dest_ip and target.get("ip"):
                    ips = target.get("ip", [])
                    dest_ip = ips[0] if ips else None

        # Extract description
        description = detection.get("description", rule_info.get("ruleText", ""))
        if not description:
            description = f"Chronicle detection: {rule_name}"

        return SIEMAlert(
            id=detection.get("id", str(hash(str(detection)))[:12]),
            timestamp=timestamp,
            rule_id=str(rule_id),
            rule_name=str(rule_name),
            severity=severity,
            source_ip=source_ip,
            dest_ip=dest_ip,
            description=str(description)[:200],
            raw_data=detection,
            mitre_tactics=[],
            mitre_techniques=[],
        )

    def _map_severity(self, severity: str) -> str:
        """Map Chronicle severity to normalized severity."""
        severity_upper = str(severity).upper()
        severity_map = {
            "CRITICAL": "critical",
            "HIGH": "high",
            "MEDIUM": "medium",
            "LOW": "low",
            "INFORMATIONAL": "info",
            "INFO": "info",
        }
        return severity_map.get(severity_upper, "info")

    def get_rules(
        self, rule_ids: Optional[List[str]] = None, enabled_only: bool = True
    ) -> List[SIEMRule]:
        """Get YARA-L detection rules from Google SecOps.

        Args:
            rule_ids: Optional list of specific rule IDs
            enabled_only: Only return enabled rules

        Returns:
            List of normalized SIEMRule objects
        """
        response = self._request(
            "GET", "/v1alpha/detect/rules", params={"page_size": 1000}
        )

        if response.status_code != 200:
            return []

        data = response.json()
        raw_rules = data.get("rules", [])

        rules = []
        for raw_rule in raw_rules:
            rule_id = raw_rule.get("ruleId", "")

            # Filter by rule_ids if provided
            if rule_ids and rule_id not in rule_ids:
                continue

            # Check if enabled
            is_enabled = raw_rule.get("liveRuleEnabled", True)
            if enabled_only and not is_enabled:
                continue

            rule = SIEMRule(
                id=rule_id,
                name=raw_rule.get("ruleName", rule_id),
                description=raw_rule.get("metadata", {}).get("description", ""),
                severity=self._map_severity(
                    raw_rule.get("metadata", {}).get("severity", "")
                ),
                enabled=is_enabled,
                mitre_tactics=raw_rule.get("metadata", {}).get("mitreTactics", []),
                mitre_techniques=raw_rule.get("metadata", {}).get(
                    "mitreTechniques", []
                ),
                raw_data=raw_rule,
            )
            rules.append(rule)

        return rules

    def get_recommended_rules(self, attack_type: str) -> List[Dict[str, Any]]:
        """Get recommended rules for detecting an attack type.

        Args:
            attack_type: Tool/attack name (e.g., 'nmap', 'hydra')

        Returns:
            List of rule recommendations
        """
        # Chronicle/Google SecOps rule recommendations
        recommendations_map = {
            "nmap": [
                {
                    "rule_id": "network_port_scan",
                    "rule_name": "Network Port Scan Detection",
                    "yaral": """
rule network_port_scan {
  meta:
    description = "Detects potential port scanning activity"
    severity = "MEDIUM"
  events:
    $e.metadata.event_type = "NETWORK_CONNECTION"
    $e.principal.ip = $src_ip
  match:
    $src_ip over 5m
  condition:
    #e > 100
}""",
                },
            ],
            "hydra": [
                {
                    "rule_id": "brute_force_auth",
                    "rule_name": "Brute Force Authentication",
                    "yaral": """
rule brute_force_authentication {
  meta:
    description = "Detects brute force login attempts"
    severity = "HIGH"
  events:
    $e.metadata.event_type = "USER_LOGIN"
    $e.security_result.action = "BLOCK"
    $e.principal.ip = $src_ip
  match:
    $src_ip over 5m
  condition:
    #e > 10
}""",
                },
            ],
            "sqlmap": [
                {
                    "rule_id": "sql_injection",
                    "rule_name": "SQL Injection Attempt",
                    "yaral": """
rule sql_injection_attempt {
  meta:
    description = "Detects SQL injection patterns in requests"
    severity = "HIGH"
  events:
    $e.metadata.event_type = "NETWORK_HTTP"
    re.regex($e.target.url, `(?i)(union|select|insert|update|delete|drop).*`)
  condition:
    $e
}""",
                },
            ],
        }

        attack_lower = attack_type.lower()
        recommendations = recommendations_map.get(attack_lower, [])

        return [
            {
                "rule_id": r["rule_id"],
                "rule_name": r["rule_name"],
                "description": f"YARA-L rule for detecting {attack_type}",
                "severity": "high",
                "enabled": False,  # These are recommendations, not deployed
                "siem_type": "google_secops",
                "yaral_rule": r.get("yaral", ""),
            }
            for r in recommendations
        ]

    def search_udm_events(
        self, query: str, start_time: datetime, end_time: datetime, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Search UDM events with a custom query.

        This is a Chronicle-specific method for advanced queries.

        Args:
            query: UDM search query
            start_time: Start of time range
            end_time: End of time range
            limit: Maximum results

        Returns:
            List of UDM events
        """
        start_str = start_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        end_str = end_time.strftime("%Y-%m-%dT%H:%M:%SZ")

        response = self._request(
            "POST",
            "/v1alpha/events:udmSearch",
            json_data={
                "query": query,
                "time_range": {
                    "start_time": start_str,
                    "end_time": end_str,
                },
                "limit": limit,
            },
        )

        if response.status_code != 200:
            return []

        data = response.json()
        return data.get("events", {}).get("events", [])
