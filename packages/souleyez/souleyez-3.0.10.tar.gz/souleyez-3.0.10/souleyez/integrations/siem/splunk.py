"""
Splunk SIEM Client.

Implements the SIEMClient interface for Splunk Enterprise/Cloud.
Uses the Splunk REST API for querying alerts and search results.
"""

import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests
from requests.auth import HTTPBasicAuth

from souleyez.integrations.siem.base import (
    SIEMAlert,
    SIEMClient,
    SIEMConnectionStatus,
    SIEMRule,
)


class SplunkSIEMClient(SIEMClient):
    """Splunk implementation of the SIEMClient interface.

    Uses Splunk REST API:
    - Authentication: POST /services/auth/login
    - Search: POST /services/search/jobs
    - Results: GET /services/search/jobs/{sid}/results
    """

    def __init__(
        self,
        api_url: str,
        username: str,
        password: str,
        verify_ssl: bool = False,
        token: Optional[str] = None,
        default_index: str = "main",
        sourcetypes: Optional[List[str]] = None,
    ):
        """Initialize Splunk SIEM client.

        Args:
            api_url: Splunk REST API URL (e.g., https://splunk.example.com:8089)
            username: Splunk username (not needed if using token)
            password: Splunk password (not needed if using token)
            verify_ssl: Verify SSL certificates
            token: Optional Splunk auth token (alternative to user/pass)
            default_index: Default index to search
            sourcetypes: List of sourcetypes to include in searches
        """
        self.api_url = api_url.rstrip("/")
        self.username = username
        self.password = password
        self.verify_ssl = verify_ssl
        self.token = token
        self.default_index = default_index
        self.sourcetypes = sourcetypes or []
        self._session_key: Optional[str] = None

    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> "SplunkSIEMClient":
        """Create client from configuration dictionary.

        Args:
            config: Dict with keys: api_url, username, password, etc.

        Returns:
            SplunkSIEMClient instance
        """
        return cls(
            api_url=config.get("api_url", ""),
            username=config.get("username", ""),
            password=config.get("password", ""),
            verify_ssl=config.get("verify_ssl", False),
            token=config.get("token"),
            default_index=config.get("default_index", "main"),
            sourcetypes=config.get("sourcetypes", []),
        )

    @property
    def siem_type(self) -> str:
        """Return the SIEM type identifier."""
        return "splunk"

    def _get_session_key(self) -> str:
        """Get Splunk session key for authentication.

        Returns:
            Session key string
        """
        if self.token:
            return self.token

        if self._session_key:
            return self._session_key

        # Authenticate to get session key
        url = f"{self.api_url}/services/auth/login"
        response = requests.post(
            url,
            data={"username": self.username, "password": self.password},
            verify=self.verify_ssl,
            timeout=30,
        )
        response.raise_for_status()

        # Parse XML response to get session key
        # XML is from authenticated Splunk API response, not untrusted input
        import xml.etree.ElementTree as ET

        root = ET.fromstring(response.text)  # nosec B314
        session_key = root.find(".//sessionKey")
        if session_key is not None:
            self._session_key = session_key.text
            return self._session_key

        raise ValueError("Failed to get session key from Splunk")

    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
    ) -> requests.Response:
        """Make authenticated API request.

        Args:
            method: HTTP method
            endpoint: API endpoint
            params: Query parameters
            data: Request body data

        Returns:
            Response object
        """
        session_key = self._get_session_key()
        url = f"{self.api_url}{endpoint}"

        headers = {
            "Authorization": f"Splunk {session_key}",
        }

        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            params=params,
            data=data,
            verify=self.verify_ssl,
            timeout=60,
        )
        return response

    def test_connection(self) -> SIEMConnectionStatus:
        """Test connection to Splunk.

        Returns:
            SIEMConnectionStatus with connection details
        """
        try:
            # Get server info
            response = self._request(
                "GET", "/services/server/info", params={"output_mode": "json"}
            )
            response.raise_for_status()
            data = response.json()

            entry = data.get("entry", [{}])[0]
            content = entry.get("content", {})

            return SIEMConnectionStatus(
                connected=True,
                version=content.get("version", "unknown"),
                siem_type="splunk",
                details={
                    "server_name": content.get("serverName", ""),
                    "build": content.get("build", ""),
                    "os": content.get("os_name", ""),
                    "license": content.get("licenseState", ""),
                },
            )
        except requests.exceptions.ConnectionError as e:
            return SIEMConnectionStatus(
                connected=False,
                error=f"Connection failed: {str(e)}",
                siem_type="splunk",
            )
        except Exception as e:
            return SIEMConnectionStatus(
                connected=False, error=str(e), siem_type="splunk"
            )

    def _run_search(
        self,
        spl_query: str,
        earliest_time: str = "-1h",
        latest_time: str = "now",
        max_results: int = 100,
    ) -> List[Dict[str, Any]]:
        """Run a SPL search and return results.

        Args:
            spl_query: SPL search query
            earliest_time: Earliest time for search
            latest_time: Latest time for search
            max_results: Maximum results to return

        Returns:
            List of result dictionaries
        """
        # Create search job
        response = self._request(
            "POST",
            "/services/search/jobs",
            data={
                "search": f"search {spl_query}",
                "earliest_time": earliest_time,
                "latest_time": latest_time,
                "output_mode": "json",
            },
        )
        response.raise_for_status()
        data = response.json()
        sid = data.get("sid")

        if not sid:
            return []

        # Wait for job to complete (with timeout)
        max_wait = 60
        waited = 0
        while waited < max_wait:
            status_resp = self._request(
                "GET", f"/services/search/jobs/{sid}", params={"output_mode": "json"}
            )
            status_data = status_resp.json()
            entry = status_data.get("entry", [{}])[0]
            content = entry.get("content", {})

            if content.get("isDone"):
                break

            time.sleep(1)
            waited += 1

        # Get results
        results_resp = self._request(
            "GET",
            f"/services/search/jobs/{sid}/results",
            params={"output_mode": "json", "count": max_results},
        )

        if results_resp.status_code == 200:
            results_data = results_resp.json()
            return results_data.get("results", [])

        return []

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
        """Query alerts from Splunk.

        Args:
            start_time: Start of time range
            end_time: End of time range
            source_ip: Filter by source IP
            dest_ip: Filter by destination IP
            rule_ids: Filter by specific rule/search IDs
            search_text: Free text search
            limit: Maximum number of results

        Returns:
            List of normalized SIEMAlert objects
        """
        # Build SPL query
        query_parts = [f"index={self.default_index}"]

        # Add sourcetype filter
        if self.sourcetypes:
            st_filter = " OR ".join(f'sourcetype="{st}"' for st in self.sourcetypes)
            query_parts.append(f"({st_filter})")

        # IP filters - search common field names and raw text
        if source_ip:
            query_parts.append(
                f'(src_ip="{source_ip}" OR src="{source_ip}" OR '
                f'source_ip="{source_ip}" OR host="{source_ip}" OR '
                f'source="{source_ip}" OR "{source_ip}")'
            )
        if dest_ip:
            query_parts.append(
                f'(dest_ip="{dest_ip}" OR dest="{dest_ip}" OR '
                f'destination_ip="{dest_ip}" OR host="{dest_ip}" OR '
                f'"{dest_ip}")'
            )

        # Search text
        if search_text:
            query_parts.append(f'"{search_text}"')

        # Rule IDs (saved search names or correlation rule IDs)
        if rule_ids:
            rule_filter = " OR ".join(f'savedsearch_name="{r}"' for r in rule_ids)
            query_parts.append(f"({rule_filter})")

        spl = " ".join(query_parts)

        # Time range formatting
        earliest = start_time.strftime("%Y-%m-%dT%H:%M:%S")
        latest = end_time.strftime("%Y-%m-%dT%H:%M:%S")

        results = self._run_search(spl, earliest, latest, limit)
        return [self._normalize_alert(r) for r in results]

    def _normalize_alert(self, raw_result: Dict[str, Any]) -> SIEMAlert:
        """Convert Splunk result to normalized SIEMAlert.

        Args:
            raw_result: Raw result from Splunk search

        Returns:
            Normalized SIEMAlert
        """
        import json as json_lib

        # Try to parse _raw if it's JSON (HEC events store data here)
        event_data = {}
        raw_str = raw_result.get("_raw", "")
        if raw_str and isinstance(raw_str, str):
            try:
                parsed = json_lib.loads(raw_str)
                # HEC wraps in 'event' key, or data might be at top level
                event_data = (
                    parsed.get("event", parsed) if isinstance(parsed, dict) else {}
                )
            except (json_lib.JSONDecodeError, TypeError):
                # Try to extract embedded JSON from syslog lines
                # Format: "Jan  7 14:23:38 host program {json...}"
                import re

                json_match = re.search(r"\{.*\}", raw_str)
                if json_match:
                    try:
                        event_data = json_lib.loads(json_match.group())
                    except (json_lib.JSONDecodeError, TypeError):
                        pass

        # Helper to get field from event_data first, then raw_result
        def get_field(*keys, default=""):
            for key in keys:
                if event_data.get(key):
                    return event_data[key]
                if raw_result.get(key):
                    return raw_result[key]
            return default

        # Parse timestamp
        timestamp_str = raw_result.get("_time", "")
        try:
            timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            timestamp = datetime.now()

        # Extract rule/alert info - check event_data first
        rule_id = get_field("rule_id", "rule_name", "savedsearch_name", "alert")
        rule_name = get_field("rule_name", "search_name") or rule_id

        # For plain log events (no alert fields), use event_type or sourcetype
        if not rule_id:
            # Prefer Suricata event_type over generic sourcetype
            event_type = get_field("event_type")
            sourcetype = raw_result.get("sourcetype", "")
            if event_type:
                rule_id = event_type
                rule_name = f"Suricata: {event_type}"
            elif sourcetype:
                rule_id = sourcetype
                rule_name = f"Log: {sourcetype}"

        # Map severity - check event_data first
        severity_raw = get_field("severity", default="info")
        severity = self._map_severity(severity_raw)

        # Extract IPs - check event_data first
        source_ip = get_field("src_ip", "src", "source_ip")
        dest_ip = get_field("dest_ip", "dest", "destination_ip")

        # For plain log events, use 'host' as source
        if not source_ip:
            source_ip = raw_result.get("host", "")

        # Extract description - try multiple sources
        description = get_field("description", "signature", "message")

        # Suricata-specific: check nested alert object
        if not description and event_data.get("alert"):
            alert_obj = event_data["alert"]
            if isinstance(alert_obj, dict):
                description = alert_obj.get("signature", alert_obj.get("category", ""))

        # Suricata event_type with context
        if not description:
            event_type = get_field("event_type", "category")
            if event_type:
                # Add context based on event type
                if event_type == "dns" and event_data.get("dns"):
                    dns = event_data["dns"]
                    rrname = dns.get("rrname", "") if isinstance(dns, dict) else ""
                    description = f"DNS: {rrname}" if rrname else f"DNS query"
                elif event_type == "http" and event_data.get("http"):
                    http = event_data["http"]
                    hostname = (
                        http.get("hostname", "") if isinstance(http, dict) else ""
                    )
                    description = f"HTTP: {hostname}" if hostname else "HTTP request"
                elif event_type == "flow":
                    app_proto = get_field("app_proto", default="")
                    description = f"Flow: {app_proto}" if app_proto else "Network flow"
                elif event_type == "alert":
                    description = "Suricata alert"
                else:
                    description = (
                        f"{event_type}: {get_field('action', default='detected')}"
                    )

        # For plain log events, try to extract something useful from _raw
        if not description and raw_str:
            # Skip syslog header to get actual message
            # Format: "Mon DD HH:MM:SS hostname program: message"
            import re

            # Try to extract message after "program:" or "program["
            msg_match = re.search(
                r"^\w+\s+\d+\s+[\d:]+\s+\S+\s+\S+[:\[]\s*(.+)", raw_str
            )
            if msg_match:
                description = msg_match.group(1).strip()[:150]
            else:
                # Fallback: clean up raw log
                clean_raw = raw_str.replace("\n", " ").strip()
                # Skip if it's just timestamps/IPs with no real content
                if len(clean_raw) > 50:
                    description = clean_raw[:150] + (
                        "..." if len(clean_raw) > 150 else ""
                    )
                else:
                    description = clean_raw if clean_raw else "No details available"

        # Extract MITRE info - check event_data first
        mitre_tactics = []
        mitre_techniques = []
        mitre_tactic = get_field("mitre_tactic", "mitre_attack_tactic")
        mitre_tech = get_field("mitre_technique", "mitre_attack_technique_id")
        if mitre_tactic:
            mitre_tactics = (
                [mitre_tactic] if isinstance(mitre_tactic, str) else mitre_tactic
            )
        if mitre_tech:
            mitre_techniques = (
                [mitre_tech] if isinstance(mitre_tech, str) else mitre_tech
            )

        # Store both raw_result and parsed event_data
        full_raw = raw_result.copy()
        if event_data:
            full_raw["_parsed_event"] = event_data

        return SIEMAlert(
            id=raw_result.get(
                "_cd", raw_result.get("_serial", str(hash(raw_str))[:12])
            ),
            timestamp=timestamp,
            rule_id=str(rule_id) if rule_id else "",
            rule_name=str(rule_name) if rule_name else "",
            severity=severity,
            source_ip=source_ip if source_ip else None,
            dest_ip=dest_ip if dest_ip else None,
            description=str(description)[:200] if description else "",
            raw_data=full_raw,
            mitre_tactics=mitre_tactics,
            mitre_techniques=mitre_techniques,
        )

    def _map_severity(self, severity: str) -> str:
        """Map Splunk severity to normalized severity."""
        severity_lower = str(severity).lower()
        if severity_lower in ("critical", "crit", "1"):
            return "critical"
        elif severity_lower in ("high", "2"):
            return "high"
        elif severity_lower in ("medium", "med", "3"):
            return "medium"
        elif severity_lower in ("low", "4"):
            return "low"
        return "info"

    def get_rules(
        self, rule_ids: Optional[List[str]] = None, enabled_only: bool = True
    ) -> List[SIEMRule]:
        """Get saved searches/correlation rules from Splunk.

        Args:
            rule_ids: Optional list of specific rule names
            enabled_only: Only return enabled rules

        Returns:
            List of normalized SIEMRule objects
        """
        # Get saved searches
        response = self._request(
            "GET",
            "/servicesNS/-/-/saved/searches",
            params={"output_mode": "json", "count": 500},
        )

        if response.status_code != 200:
            return []

        data = response.json()
        entries = data.get("entry", [])

        rules = []
        for entry in entries:
            name = entry.get("name", "")
            content = entry.get("content", {})

            # Filter by rule_ids if provided
            if rule_ids and name not in rule_ids:
                continue

            # Filter disabled if requested
            if enabled_only and content.get("disabled", False):
                continue

            rule = SIEMRule(
                id=name,
                name=name,
                description=content.get("description", ""),
                severity=self._map_severity(content.get("alert.severity", "")),
                enabled=not content.get("disabled", False),
                mitre_tactics=[],
                mitre_techniques=[],
                raw_data=content,
            )
            rules.append(rule)

        return rules

    def get_hosts(
        self, time_range: str = "-24h", limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Query hosts that have sent data to Splunk.

        Similar to Wazuh agents view - shows which hosts are reporting.

        Args:
            time_range: Time range to search (e.g., "-24h", "-7d")
            limit: Maximum number of hosts to return

        Returns:
            List of host dictionaries with name, last_seen, event_count, sourcetypes
        """
        # Query to get unique hosts with stats
        spl = (
            f"index={self.default_index} "
            f"| stats count as event_count, latest(_time) as last_seen, "
            f"values(sourcetype) as sourcetypes by host "
            f"| sort -last_seen "
            f"| head {limit}"
        )

        results = self._run_search(
            spl, earliest_time=time_range, latest_time="now", max_results=limit
        )

        hosts = []
        for r in results:
            # Parse sourcetypes (may be multivalue)
            sourcetypes_raw = r.get("sourcetypes", "")
            if isinstance(sourcetypes_raw, list):
                sourcetypes = sourcetypes_raw
            elif isinstance(sourcetypes_raw, str):
                sourcetypes = [
                    s.strip() for s in sourcetypes_raw.split(",") if s.strip()
                ]
            else:
                sourcetypes = []

            # Infer OS from sourcetypes and hostname
            os_name = self._infer_os(sourcetypes, r.get("host", ""))

            hosts.append(
                {
                    "name": r.get("host", "unknown"),
                    "last_seen": r.get("last_seen", ""),
                    "event_count": int(r.get("event_count", 0)),
                    "sourcetypes": sourcetypes,
                    "os": os_name,
                }
            )

        return hosts

    def _infer_os(self, sourcetypes: List[str], hostname: str) -> str:
        """Infer operating system from sourcetypes and hostname patterns.

        Args:
            sourcetypes: List of sourcetypes for this host
            hostname: The hostname

        Returns:
            Inferred OS name or 'Unknown'
        """
        sourcetypes_lower = [st.lower() for st in sourcetypes]
        hostname_lower = hostname.lower()

        # Check sourcetype patterns
        for st in sourcetypes_lower:
            # macOS patterns
            if "macos" in st or "osx" in st or "darwin" in st:
                return "macOS"
            # Windows patterns
            if "winevent" in st or "windows" in st or "win:" in st:
                return "Windows"
            # Linux patterns
            if "linux" in st:
                return "Linux"

        # Check hostname patterns
        if (
            "mac" in hostname_lower
            or "macbook" in hostname_lower
            or "imac" in hostname_lower
        ):
            return "macOS"
        if "win" in hostname_lower or "desktop-" in hostname_lower:
            return "Windows"

        # Infer from common sourcetypes
        for st in sourcetypes_lower:
            if st in ("linux_secure", "linux_audit", "linux_messages", "linux_syslog"):
                return "Linux"
            if st in ("syslog",):
                # Generic syslog - could be Linux, BSD, or network device
                # Check hostname for clues
                if any(
                    x in hostname_lower
                    for x in ["ubuntu", "debian", "centos", "rhel", "fedora"]
                ):
                    return "Linux"
                if "metasploitable" in hostname_lower:
                    return "Linux"
                # Default syslog to Linux (most common)
                return "Linux"
            if "apache" in st or "nginx" in st:
                return "Linux"  # Most common, though not guaranteed

        return "Unknown"

    def get_vulnerabilities(
        self,
        index: str = "wazuh_vulns",
        sourcetype: str = "wazuh:vulnerabilities",
        severity: Optional[str] = None,
        agent_name: Optional[str] = None,
        limit: int = 1000,
        time_range: str = "-7d",
    ) -> List[Dict[str, Any]]:
        """Query vulnerability data from Splunk.

        Queries the wazuh_vulns index populated by the vuln sync script.

        Args:
            index: Splunk index containing vulnerability data
            sourcetype: Sourcetype for vulnerability events
            severity: Filter by severity (Critical, High, Medium, Low)
            agent_name: Filter by agent/host name
            limit: Maximum results to return
            time_range: Time range to search (e.g., "-7d", "-30d")

        Returns:
            List of vulnerability dictionaries
        """
        # Build SPL query
        query_parts = [f"index={index} sourcetype={sourcetype}"]

        if severity:
            query_parts.append(f'severity="{severity}"')
        if agent_name:
            query_parts.append(f'agent_name="*{agent_name}*"')

        # Dedup by CVE and agent, get latest
        spl = " ".join(query_parts) + (
            f" | dedup cve, agent_name"
            f" | table cve, severity, cvss_score, package_name, package_version, "
            f"os_name, agent_name, agent_id, detected_at, description"
            f" | sort -cvss_score"
            f" | head {limit}"
        )

        results = self._run_search(
            spl, earliest_time=time_range, latest_time="now", max_results=limit
        )

        vulns = []
        for r in results:
            vulns.append(
                {
                    "cve_id": r.get("cve", ""),
                    "severity": r.get("severity", "Medium"),
                    "cvss_score": (
                        float(r.get("cvss_score", 0)) if r.get("cvss_score") else None
                    ),
                    "package_name": r.get("package_name", ""),
                    "package_version": r.get("package_version", ""),
                    "os_name": r.get("os_name", ""),
                    "agent_name": r.get("agent_name", ""),
                    "agent_id": r.get("agent_id", ""),
                    "detected_at": r.get("detected_at", ""),
                    "description": r.get("description", ""),
                }
            )

        return vulns

    def get_vulnerability_summary(
        self,
        index: str = "wazuh_vulns",
        sourcetype: str = "wazuh:vulnerabilities",
        time_range: str = "-7d",
    ) -> Dict[str, Any]:
        """Get vulnerability summary statistics from Splunk.

        Args:
            index: Splunk index containing vulnerability data
            sourcetype: Sourcetype for vulnerability events
            time_range: Time range to search

        Returns:
            Summary dictionary with counts by severity, total, etc.
        """
        # Get counts by severity
        spl = (
            f"index={index} sourcetype={sourcetype}"
            f" | dedup cve, agent_name"
            f" | stats dc(cve) as unique_cves, count as total by severity"
        )

        results = self._run_search(
            spl, earliest_time=time_range, latest_time="now", max_results=10
        )

        by_severity = {}
        total = 0
        unique_cves = 0

        for r in results:
            sev = r.get("severity", "Unknown")
            count = int(r.get("total", 0))
            cve_count = int(r.get("unique_cves", 0))
            by_severity[sev] = count
            total += count
            unique_cves += cve_count

        # Get affected agents count
        spl_agents = (
            f"index={index} sourcetype={sourcetype}"
            f" | stats dc(agent_name) as agent_count"
        )
        agent_results = self._run_search(
            spl_agents, earliest_time=time_range, latest_time="now", max_results=1
        )
        agent_count = (
            int(agent_results[0].get("agent_count", 0)) if agent_results else 0
        )

        return {
            "total": total,
            "unique_cves": unique_cves,
            "by_severity": by_severity,
            "agents_affected": agent_count,
        }

    def get_recommended_rules(self, attack_type: str) -> List[Dict[str, Any]]:
        """Get recommended Splunk rules for detecting an attack type.

        Args:
            attack_type: Tool/attack name (e.g., 'nmap', 'hydra')

        Returns:
            List of rule recommendations
        """
        # Splunk-specific rule recommendations
        recommendations_map = {
            "nmap": [
                {
                    "rule_id": "Network_Port_Scan_Detection",
                    "rule_name": "Network Port Scan Detection",
                    "spl": "index=* sourcetype=firewall | stats count by src_ip dest_port | where count > 100",
                },
            ],
            "hydra": [
                {
                    "rule_id": "Brute_Force_Authentication",
                    "rule_name": "Brute Force Authentication Detection",
                    "spl": "index=* sourcetype=*auth* | stats count by src_ip user | where count > 10",
                },
            ],
            "sqlmap": [
                {
                    "rule_id": "SQL_Injection_Attempt",
                    "rule_name": "SQL Injection Attempt Detection",
                    "spl": "index=* sourcetype=*web* | search *UNION* OR *SELECT* | stats count by src_ip",
                },
            ],
        }

        attack_lower = attack_type.lower()
        recommendations = recommendations_map.get(attack_lower, [])

        return [
            {
                "rule_id": r["rule_id"],
                "rule_name": r["rule_name"],
                "description": f"Splunk saved search for detecting {attack_type}",
                "severity": "high",
                "enabled": True,
                "siem_type": "splunk",
                "spl_query": r.get("spl", ""),
            }
            for r in recommendations
        ]
