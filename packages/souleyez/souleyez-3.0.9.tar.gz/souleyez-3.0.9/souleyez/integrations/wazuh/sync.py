#!/usr/bin/env python3
"""
souleyez.integrations.wazuh.sync - Wazuh vulnerability sync

Syncs vulnerabilities from Wazuh to SoulEyez database.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from souleyez.log_config import get_logger
from souleyez.storage.wazuh_vulns import WazuhVulnsManager

from .client import WazuhClient
from .config import WazuhConfig
from .host_mapper import WazuhHostMapper

logger = get_logger(__name__)


@dataclass
class SyncResult:
    """Result of a vulnerability sync operation."""

    success: bool = True
    total_fetched: int = 0
    new_vulns: int = 0
    updated_vulns: int = 0
    mapped_hosts: int = 0
    unmapped_agents: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    duration_seconds: float = 0.0


class WazuhVulnSync:
    """Syncs Wazuh vulnerabilities to SoulEyez database."""

    def __init__(self, engagement_id: int):
        """
        Initialize sync for an engagement.

        Args:
            engagement_id: Engagement ID
        """
        self.engagement_id = engagement_id
        self.vulns_manager = WazuhVulnsManager()
        self.host_mapper = WazuhHostMapper()
        self._client: Optional[WazuhClient] = None

    def _get_client(self) -> Optional[WazuhClient]:
        """Get or create Wazuh client."""
        if self._client:
            return self._client

        config = WazuhConfig.get_config(self.engagement_id)
        if not config or not config.get("enabled"):
            logger.warning(f"Wazuh not configured for engagement {self.engagement_id}")
            return None

        try:
            self._client = WazuhClient(
                api_url=config["api_url"],
                username=config["api_user"],
                password=config["api_password"],
                verify_ssl=config.get("verify_ssl", False),
                indexer_url=config.get("indexer_url"),
                indexer_user=config.get("indexer_user"),
                indexer_password=config.get("indexer_password"),
            )
            return self._client
        except Exception as e:
            logger.error(f"Failed to create Wazuh client: {e}")
            return None

    def sync_full(self) -> SyncResult:
        """
        Full sync - fetch all vulnerabilities from Wazuh and upsert to DB.

        Returns:
            SyncResult with sync statistics
        """
        start_time = datetime.now()
        result = SyncResult()

        client = self._get_client()
        if not client:
            result.success = False
            result.errors.append("Wazuh not configured or client creation failed")
            return result

        try:
            # Test vulnerability index access
            index_status = client.test_vulnerability_index()
            if not index_status.get("accessible"):
                result.success = False
                result.errors.append(
                    index_status.get("error", "Vulnerability index not accessible")
                )
                return result

            # Build agent ID -> IP lookup table
            # (vulnerability index often lacks agent IP, but agents endpoint has it)
            agent_ip_lookup = {}
            try:
                agents = client.get_agents()
                for agent in agents:
                    agent_id = agent.get("id")
                    agent_ip = agent.get("ip")
                    if agent_id and agent_ip:
                        agent_ip_lookup[agent_id] = agent_ip
                logger.info(
                    f"Built agent IP lookup with {len(agent_ip_lookup)} entries"
                )
            except Exception as e:
                logger.warning(f"Could not fetch agent IPs: {e}")

            # Fetch all vulnerabilities
            logger.info(
                f"Fetching vulnerabilities from Wazuh for engagement {self.engagement_id}"
            )
            vulns = client.get_all_vulnerabilities()
            result.total_fetched = len(vulns)

            if not vulns:
                logger.info("No vulnerabilities found in Wazuh")
                self.vulns_manager.update_sync_status(
                    self.engagement_id, count=0, status="success"
                )
                result.duration_seconds = (datetime.now() - start_time).total_seconds()
                return result

            # Process each vulnerability
            new_count = 0
            updated_count = 0

            for vuln in vulns:
                try:
                    # Get agent_ip from vuln, or look it up by agent_id
                    agent_id = vuln.get("agent_id")
                    agent_ip = vuln.get("agent_ip")
                    if not agent_ip and agent_id and agent_id in agent_ip_lookup:
                        agent_ip = agent_ip_lookup[agent_id]

                    vuln_id = self.vulns_manager.upsert_vulnerability(
                        engagement_id=self.engagement_id,
                        agent_id=agent_id,
                        cve_id=vuln.get("cve_id"),
                        package_name=vuln.get("package_name"),
                        agent_name=vuln.get("agent_name"),
                        agent_ip=agent_ip,
                        name=vuln.get("name"),
                        severity=vuln.get("severity"),
                        cvss_score=vuln.get("cvss_score"),
                        cvss_version=vuln.get("cvss_version"),
                        package_version=vuln.get("package_version"),
                        package_architecture=vuln.get("package_architecture"),
                        detection_time=vuln.get("detection_time"),
                        published_date=vuln.get("published_date"),
                        reference_urls=vuln.get("reference_urls"),
                        raw_data=vuln.get("raw_data"),
                    )

                    if vuln_id:
                        new_count += 1
                    else:
                        updated_count += 1

                except Exception as e:
                    logger.error(
                        f"Error processing vulnerability {vuln.get('cve_id')}: {e}"
                    )
                    result.errors.append(f"CVE {vuln.get('cve_id')}: {str(e)}")

            result.new_vulns = new_count
            result.updated_vulns = updated_count

            # Auto-map hosts
            logger.info("Auto-mapping agents to hosts")
            mapping = self.host_mapper.auto_map_all(self.engagement_id)

            mapped_count = sum(1 for host_id in mapping.values() if host_id is not None)
            result.mapped_hosts = mapped_count

            # Get unmapped agents
            unmapped = self.host_mapper.get_unmapped_agents(self.engagement_id)
            result.unmapped_agents = [
                a.get("agent_ip") for a in unmapped if a.get("agent_ip")
            ]

            # Update sync status
            self.vulns_manager.update_sync_status(
                self.engagement_id,
                count=result.total_fetched,
                status="success" if not result.errors else "partial",
                errors=result.errors if result.errors else None,
            )

            result.duration_seconds = (datetime.now() - start_time).total_seconds()
            logger.info(
                f"Sync complete: {result.total_fetched} vulns fetched, "
                f"{result.new_vulns} new, {result.updated_vulns} updated, "
                f"{result.mapped_hosts} mapped hosts, "
                f"{len(result.unmapped_agents)} unmapped agents"
            )

            return result

        except Exception as e:
            logger.error(f"Sync failed: {e}")
            result.success = False
            result.errors.append(str(e))

            self.vulns_manager.update_sync_status(
                self.engagement_id, count=0, status="error", errors=[str(e)]
            )

            result.duration_seconds = (datetime.now() - start_time).total_seconds()
            return result

    def sync_agent(self, agent_id: str) -> SyncResult:
        """
        Sync vulnerabilities for a specific agent.

        Args:
            agent_id: Wazuh agent ID

        Returns:
            SyncResult with sync statistics
        """
        start_time = datetime.now()
        result = SyncResult()

        client = self._get_client()
        if not client:
            result.success = False
            result.errors.append("Wazuh not configured")
            return result

        try:
            # Fetch vulnerabilities for this agent
            vulns = client.get_agent_vulnerabilities(agent_id)
            result.total_fetched = len(vulns)

            for vuln in vulns:
                try:
                    self.vulns_manager.upsert_vulnerability(
                        engagement_id=self.engagement_id,
                        agent_id=vuln.get("agent_id"),
                        cve_id=vuln.get("cve_id"),
                        package_name=vuln.get("package_name"),
                        agent_name=vuln.get("agent_name"),
                        agent_ip=vuln.get("agent_ip"),
                        name=vuln.get("name"),
                        severity=vuln.get("severity"),
                        cvss_score=vuln.get("cvss_score"),
                        cvss_version=vuln.get("cvss_version"),
                        package_version=vuln.get("package_version"),
                        package_architecture=vuln.get("package_architecture"),
                        detection_time=vuln.get("detection_time"),
                        published_date=vuln.get("published_date"),
                        reference_urls=vuln.get("reference_urls"),
                        raw_data=vuln.get("raw_data"),
                    )
                    result.new_vulns += 1
                except Exception as e:
                    result.errors.append(f"CVE {vuln.get('cve_id')}: {str(e)}")

            # Auto-map this agent's IP
            if vulns and vulns[0].get("agent_ip"):
                agent_ip = vulns[0]["agent_ip"]
                host_id = self.host_mapper.map_agent_to_host(
                    self.engagement_id, agent_ip
                )
                if host_id:
                    self.host_mapper._update_vuln_host_mapping(
                        self.engagement_id, agent_ip, host_id
                    )
                    result.mapped_hosts = 1
                else:
                    result.unmapped_agents = [agent_ip]

            result.duration_seconds = (datetime.now() - start_time).total_seconds()
            return result

        except Exception as e:
            result.success = False
            result.errors.append(str(e))
            result.duration_seconds = (datetime.now() - start_time).total_seconds()
            return result

    def is_stale(self, max_age_hours: int = 1) -> bool:
        """
        Check if sync data is stale and needs refresh.

        Args:
            max_age_hours: Maximum age in hours

        Returns:
            True if stale or never synced
        """
        return self.vulns_manager.is_stale(self.engagement_id, max_age_hours)

    def sync_if_stale(self, max_age_hours: int = 1) -> Optional[SyncResult]:
        """
        Sync only if data is stale.

        Args:
            max_age_hours: Maximum age before sync

        Returns:
            SyncResult if sync was performed, None otherwise
        """
        if self.is_stale(max_age_hours):
            return self.sync_full()
        return None

    def get_sync_status(self) -> dict:
        """
        Get current sync status.

        Returns:
            Dict with last sync info
        """
        status = self.vulns_manager.get_sync_status(self.engagement_id)
        if not status:
            return {
                "synced": False,
                "last_sync_at": None,
                "last_sync_count": 0,
                "is_stale": True,
            }

        return {
            "synced": True,
            "last_sync_at": status.get("last_sync_at"),
            "last_sync_count": status.get("last_sync_count", 0),
            "last_sync_status": status.get("last_sync_status"),
            "is_stale": self.is_stale(),
        }
