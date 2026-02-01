"""
Wazuh API Client for SoulEyez Detection Validation.

Connects to Wazuh Manager API (port 55000) for management operations
and Wazuh Indexer API (port 9200) for querying alerts.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import requests
from urllib3.exceptions import InsecureRequestWarning

# Suppress SSL warnings for self-signed certs (common in Wazuh)
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)


class WazuhClient:
    """Client for Wazuh Manager REST API (v4.x) and Indexer."""

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
        """
        Initialize Wazuh API client.

        Args:
            api_url: Manager API URL (e.g., https://10.0.0.111:55000)
            username: Wazuh Manager API username
            password: Wazuh Manager API password
            verify_ssl: Verify SSL certificates (False for self-signed)
            indexer_url: Indexer URL (e.g., https://10.0.0.111:9200), auto-derived if not set
            indexer_user: Indexer username (defaults to 'admin')
            indexer_password: Indexer password (defaults to manager password)
        """
        self.api_url = api_url.rstrip("/")
        self.username = username
        self.password = password
        self.verify_ssl = verify_ssl
        self._token: Optional[str] = None
        self._token_expiry: Optional[datetime] = None

        # Derive indexer URL from manager URL if not provided
        # Manager is on :55000, Indexer is on :9200
        if indexer_url:
            self.indexer_url = indexer_url.rstrip("/")
        else:
            # Replace port 55000 with 9200
            self.indexer_url = self.api_url.replace(":55000", ":9200")

        # Indexer credentials (often different from Manager)
        self.indexer_user = indexer_user or "admin"
        self.indexer_password = indexer_password or password

    def _get_token(self) -> str:
        """Authenticate and get JWT token."""
        # Check if we have a valid cached token
        if self._token and self._token_expiry and datetime.now() < self._token_expiry:
            return self._token

        # Authenticate
        url = f"{self.api_url}/security/user/authenticate"
        response = requests.post(
            url, auth=(self.username, self.password), verify=self.verify_ssl, timeout=30
        )
        response.raise_for_status()

        data = response.json()
        self._token = data.get("data", {}).get("token")
        # Tokens typically expire in 15 minutes, refresh at 10
        self._token_expiry = datetime.now() + timedelta(minutes=10)

        if not self._token:
            raise ValueError("Failed to get authentication token from Wazuh")

        return self._token

    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        json_data: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Make authenticated API request."""
        token = self._get_token()
        url = f"{self.api_url}{endpoint}"

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
        response.raise_for_status()
        return response.json()

    def test_connection(self) -> Dict[str, Any]:
        """
        Test connection to Wazuh Manager.

        Returns:
            Dict with manager info (version, cluster status, etc.)
        """
        try:
            result = self._request("GET", "/manager/info")
            # Wazuh 4.x returns data in affected_items array
            data = result.get("data", {})
            items = data.get("affected_items", [])
            info = items[0] if items else {}

            # Get hostname from agent 000 (manager)
            hostname = "unknown"
            try:
                agent_result = self._request(
                    "GET", "/agents", params={"agents_list": "000"}
                )
                agent_items = agent_result.get("data", {}).get("affected_items", [])
                if agent_items:
                    hostname = agent_items[0].get("name", "unknown")
            except Exception:
                pass

            return {
                "connected": True,
                "version": info.get("version", "unknown"),
                "cluster": data.get("cluster", {}).get("enabled", False),
                "hostname": hostname,
            }
        except requests.exceptions.ConnectionError as e:
            return {"connected": False, "error": f"Connection failed: {str(e)}"}
        except requests.exceptions.HTTPError as e:
            return {"connected": False, "error": f"Auth failed: {str(e)}"}
        except Exception as e:
            return {"connected": False, "error": str(e)}

    def get_alerts(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        agent_ip: Optional[str] = None,
        rule_ids: Optional[List[int]] = None,
        limit: int = 100,
        search_text: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Query alerts from Wazuh Indexer (Elasticsearch-based).

        Args:
            start_time: Filter alerts after this time
            end_time: Filter alerts before this time
            agent_ip: Filter by agent IP address
            rule_ids: Filter by specific rule IDs
            limit: Max results to return
            search_text: Free text search

        Returns:
            List of alert dictionaries
        """
        # Build Elasticsearch query
        must_clauses = []

        # Time range filter
        if start_time or end_time:
            time_range = {}
            if start_time:
                time_range["gte"] = start_time.strftime("%Y-%m-%dT%H:%M:%S")
            if end_time:
                time_range["lte"] = end_time.strftime("%Y-%m-%dT%H:%M:%S")
            must_clauses.append({"range": {"timestamp": time_range}})

        # Rule ID filter
        if rule_ids:
            must_clauses.append({"terms": {"rule.id": [str(r) for r in rule_ids]}})

        # Agent IP filter (check various IP fields)
        if agent_ip:
            must_clauses.append(
                {
                    "multi_match": {
                        "query": agent_ip,
                        "fields": ["agent.ip", "data.srcip", "data.src_ip", "src_ip"],
                    }
                }
            )

        # Free text search
        if search_text:
            must_clauses.append({"query_string": {"query": f"*{search_text}*"}})

        # Build the query
        query = {
            "size": limit,
            "sort": [{"timestamp": {"order": "desc"}}],
            "query": {
                "bool": {"must": must_clauses if must_clauses else [{"match_all": {}}]}
            },
        }

        try:
            # Query the Wazuh Indexer (wazuh-alerts-* index)
            response = requests.post(
                f"{self.indexer_url}/wazuh-alerts-*/_search",
                auth=(self.indexer_user, self.indexer_password),
                json=query,
                verify=self.verify_ssl,
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()

            # Extract hits
            hits = data.get("hits", {}).get("hits", [])
            return [hit.get("_source", {}) for hit in hits]

        except requests.exceptions.ConnectionError:
            # Indexer might not be accessible, return empty
            return []
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                # No alerts index yet
                return []
            raise

    def get_alerts_by_src_ip(
        self, src_ip: str, start_time: datetime, end_time: datetime, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get alerts where source IP matches (attacker IP).

        This is the primary method for detection validation -
        we look for alerts triggered by our attack source IP.
        """
        return self.get_alerts(
            start_time=start_time, end_time=end_time, agent_ip=src_ip, limit=limit
        )

    def get_rules(self, rule_ids: Optional[List[int]] = None) -> List[Dict[str, Any]]:
        """Get rule definitions from Wazuh."""
        params = {"limit": 500}
        if rule_ids:
            params["rule_ids"] = ",".join(str(r) for r in rule_ids)

        result = self._request("GET", "/rules", params=params)
        return result.get("data", {}).get("affected_items", [])

    def get_rule_file_content(
        self, filename: str, relative_dirname: str = None
    ) -> Optional[str]:
        """
        Get the content of a rule file.

        Args:
            filename: The rule filename (e.g., '0095-sshd_rules.xml')
            relative_dirname: The relative directory (e.g., 'ruleset/rules')

        Returns:
            The XML content of the rule file, or None if not found
        """
        try:
            # Build parameters
            params = {"raw": "true"}  # Get raw file content
            if relative_dirname:
                params["relative_dirname"] = relative_dirname

            # Make request - raw=true returns plain text, not JSON
            token = self._get_token()
            url = f"{self.api_url}/rules/files/{filename}"

            headers = {
                "Authorization": f"Bearer {token}",
            }

            response = requests.get(
                url=url,
                headers=headers,
                params=params,
                verify=self.verify_ssl,
                timeout=30,
            )

            if response.status_code == 200:
                # Check if response is JSON or raw text
                content_type = response.headers.get("Content-Type", "")
                if "application/json" in content_type:
                    # JSON response - extract content from data
                    data = response.json()
                    affected_items = data.get("data", {}).get("affected_items", [])
                    if affected_items:
                        item = affected_items[0]
                        # The content might be in a 'content' field
                        if isinstance(item, dict):
                            return item.get("content") or item.get("data")
                        return item if isinstance(item, str) else None
                else:
                    # Raw text response
                    return response.text
            return None
        except Exception:
            return None

    def get_rule_xml(
        self, rule_id: int, filename: str, relative_dirname: str = None
    ) -> Optional[str]:
        """
        Extract a specific rule's XML from a rule file.

        Args:
            rule_id: The rule ID to extract
            filename: The rule filename
            relative_dirname: The relative directory

        Returns:
            The XML snippet for the specific rule, or None if not found
        """
        import re

        content = self.get_rule_file_content(filename, relative_dirname)
        if not content:
            return None

        # Parse the XML to find the specific rule
        # Rules are in format: <rule id="5700" level="0">...</rule>
        pattern = rf'<rule\s+id="{rule_id}"[^>]*>.*?</rule>'
        match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)

        if match:
            return match.group(0)
        return None

    def get_agents(self) -> List[Dict[str, Any]]:
        """Get list of registered agents."""
        result = self._request("GET", "/agents", params={"limit": 500})
        return result.get("data", {}).get("affected_items", [])

    # =========================================================================
    # Vulnerability Detection Methods
    # =========================================================================

    def get_agent_vulnerabilities(
        self, agent_id: str, severity: Optional[str] = None, limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Fetch vulnerabilities for a specific agent from Wazuh Indexer.

        Queries the wazuh-states-vulnerabilities-* index.

        Args:
            agent_id: Wazuh agent ID (e.g., "002")
            severity: Filter by severity (Critical, High, Medium, Low)
            limit: Max results to return

        Returns:
            List of vulnerability dictionaries
        """
        must_clauses = [{"term": {"agent.id": agent_id}}]

        if severity:
            must_clauses.append({"term": {"vulnerability.severity": severity}})

        query = {
            "size": limit,
            "sort": [{"vulnerability.severity": {"order": "desc"}}],
            "query": {"bool": {"must": must_clauses}},
        }

        try:
            response = requests.post(
                f"{self.indexer_url}/wazuh-states-vulnerabilities-*/_search",
                auth=(self.indexer_user, self.indexer_password),
                json=query,
                verify=self.verify_ssl,
                timeout=60,
            )
            response.raise_for_status()
            data = response.json()

            hits = data.get("hits", {}).get("hits", [])
            return [
                self._normalize_vulnerability(hit.get("_source", {})) for hit in hits
            ]

        except requests.exceptions.ConnectionError:
            return []
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return []
            raise

    def get_all_vulnerabilities(
        self,
        severity: Optional[str] = None,
        agent_ids: Optional[List[str]] = None,
        limit: int = 5000,
    ) -> List[Dict[str, Any]]:
        """
        Fetch all vulnerabilities from Wazuh Indexer.

        Args:
            severity: Filter by severity (Critical, High, Medium, Low)
            agent_ids: Filter by specific agent IDs
            limit: Max results to return

        Returns:
            List of vulnerability dictionaries
        """
        must_clauses = []

        if severity:
            must_clauses.append({"term": {"vulnerability.severity": severity}})

        if agent_ids:
            must_clauses.append({"terms": {"agent.id": agent_ids}})

        query = {
            "size": limit,
            "sort": [
                {"vulnerability.severity": {"order": "desc"}},
                {"agent.id": {"order": "asc"}},
            ],
            "query": {
                "bool": {"must": must_clauses if must_clauses else [{"match_all": {}}]}
            },
        }

        try:
            response = requests.post(
                f"{self.indexer_url}/wazuh-states-vulnerabilities-*/_search",
                auth=(self.indexer_user, self.indexer_password),
                json=query,
                verify=self.verify_ssl,
                timeout=120,
            )
            response.raise_for_status()
            data = response.json()

            hits = data.get("hits", {}).get("hits", [])
            return [
                self._normalize_vulnerability(hit.get("_source", {})) for hit in hits
            ]

        except requests.exceptions.ConnectionError:
            return []
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return []
            raise

    def get_vulnerability_summary(self) -> Dict[str, Any]:
        """
        Get aggregated vulnerability counts by severity and agent.

        Returns:
            Dict with severity counts and agent breakdown
        """
        query = {
            "size": 0,
            "aggs": {
                "by_severity": {
                    "terms": {"field": "vulnerability.severity", "size": 10}
                },
                "by_agent": {
                    "terms": {"field": "agent.id", "size": 100},
                    "aggs": {
                        "by_severity": {
                            "terms": {"field": "vulnerability.severity", "size": 10}
                        }
                    },
                },
                "total": {"value_count": {"field": "vulnerability.id"}},
            },
        }

        try:
            response = requests.post(
                f"{self.indexer_url}/wazuh-states-vulnerabilities-*/_search",
                auth=(self.indexer_user, self.indexer_password),
                json=query,
                verify=self.verify_ssl,
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()

            aggs = data.get("aggregations", {})

            # Parse severity counts
            severity_counts = {}
            for bucket in aggs.get("by_severity", {}).get("buckets", []):
                severity_counts[bucket["key"]] = bucket["doc_count"]

            # Parse agent breakdown
            agent_breakdown = {}
            for bucket in aggs.get("by_agent", {}).get("buckets", []):
                agent_id = bucket["key"]
                agent_breakdown[agent_id] = {
                    "total": bucket["doc_count"],
                    "by_severity": {},
                }
                for sev_bucket in bucket.get("by_severity", {}).get("buckets", []):
                    agent_breakdown[agent_id]["by_severity"][sev_bucket["key"]] = (
                        sev_bucket["doc_count"]
                    )

            return {
                "total": aggs.get("total", {}).get("value", 0),
                "by_severity": severity_counts,
                "by_agent": agent_breakdown,
            }

        except requests.exceptions.ConnectionError:
            return {"total": 0, "by_severity": {}, "by_agent": {}}
        except requests.exceptions.HTTPError:
            return {"total": 0, "by_severity": {}, "by_agent": {}}

    def test_vulnerability_index(self) -> Dict[str, Any]:
        """
        Test if vulnerability index exists and is accessible.

        Returns:
            Dict with status and info
        """
        try:
            response = requests.get(
                f"{self.indexer_url}/wazuh-states-vulnerabilities-*/_count",
                auth=(self.indexer_user, self.indexer_password),
                verify=self.verify_ssl,
                timeout=10,
            )

            if response.status_code == 200:
                data = response.json()
                return {"accessible": True, "count": data.get("count", 0)}
            elif response.status_code == 404:
                return {
                    "accessible": False,
                    "error": "Vulnerability index not found. Ensure vulnerability detection is enabled in Wazuh.",
                }
            else:
                return {"accessible": False, "error": f"HTTP {response.status_code}"}

        except requests.exceptions.ConnectionError as e:
            return {"accessible": False, "error": f"Connection failed: {str(e)}"}
        except Exception as e:
            return {"accessible": False, "error": str(e)}

    def _normalize_vulnerability(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize Wazuh vulnerability document to standard format.

        Args:
            doc: Raw Wazuh vulnerability document

        Returns:
            Normalized vulnerability dict
        """
        agent = doc.get("agent", {})
        vuln = doc.get("vulnerability", {})
        package = doc.get("package", {})

        # Extract CVSS score - try multiple fields
        cvss_score = None
        cvss_version = None

        if vuln.get("score", {}).get("base"):
            cvss_score = vuln["score"]["base"]
            cvss_version = vuln.get("score", {}).get("version", "unknown")
        elif vuln.get("cvss", {}).get("cvss3", {}).get("base_score"):
            cvss_score = vuln["cvss"]["cvss3"]["base_score"]
            cvss_version = "3.x"
        elif vuln.get("cvss", {}).get("cvss2", {}).get("base_score"):
            cvss_score = vuln["cvss"]["cvss2"]["base_score"]
            cvss_version = "2.0"

        return {
            # Agent info
            "agent_id": agent.get("id"),
            "agent_name": agent.get("name"),
            "agent_ip": agent.get("ip"),
            # Vulnerability info
            "cve_id": vuln.get("id"),
            "name": vuln.get("title") or vuln.get("description", "")[:100],
            "severity": vuln.get("severity"),
            "cvss_score": cvss_score,
            "cvss_version": cvss_version,
            "published_date": vuln.get("published"),
            # Package info
            "package_name": package.get("name"),
            "package_version": package.get("version"),
            "package_architecture": package.get("architecture"),
            # References
            "reference_urls": vuln.get("reference", []),
            # Detection time
            "detection_time": vuln.get("detected_at"),
            # Raw data for debugging
            "raw_data": doc,
        }
