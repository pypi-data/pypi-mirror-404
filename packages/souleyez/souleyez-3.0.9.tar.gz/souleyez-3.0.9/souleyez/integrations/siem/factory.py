"""
SIEM Factory.

Creates SIEM clients based on configuration, providing a unified
interface for working with multiple SIEM platforms.
"""

from typing import Any, Dict, List, Optional

from souleyez.integrations.siem.base import SIEMClient, SIEMConnectionStatus

# Registry of available SIEM types
# Ordered: Open Source first, then Commercial
SIEM_TYPES = ["wazuh", "elastic", "splunk", "sentinel", "google_secops"]


class SIEMFactory:
    """Factory for creating SIEM client instances.

    Usage:
        # Create from explicit type
        client = SIEMFactory.create('wazuh', config)

        # Create from engagement config
        client = SIEMFactory.from_engagement(engagement_id)

        # Get available types
        types = SIEMFactory.get_available_types()
    """

    @staticmethod
    def create(siem_type: str, config: Dict[str, Any]) -> SIEMClient:
        """Create a SIEM client instance.

        Args:
            siem_type: Type of SIEM ('wazuh', 'splunk', 'elastic', 'sentinel')
            config: SIEM-specific configuration dictionary

        Returns:
            SIEMClient instance

        Raises:
            ValueError: If siem_type is not supported
        """
        siem_type_lower = siem_type.lower()

        if siem_type_lower == "wazuh":
            from souleyez.integrations.siem.wazuh import WazuhSIEMClient

            return WazuhSIEMClient.from_config(config)

        elif siem_type_lower == "splunk":
            from souleyez.integrations.siem.splunk import SplunkSIEMClient

            return SplunkSIEMClient.from_config(config)

        elif siem_type_lower == "elastic":
            from souleyez.integrations.siem.elastic import ElasticSIEMClient

            return ElasticSIEMClient.from_config(config)

        elif siem_type_lower == "sentinel":
            from souleyez.integrations.siem.sentinel import SentinelSIEMClient

            return SentinelSIEMClient.from_config(config)

        elif siem_type_lower == "google_secops":
            from souleyez.integrations.siem.googlesecops import GoogleSecOpsSIEMClient

            return GoogleSecOpsSIEMClient.from_config(config)

        else:
            raise ValueError(
                f"Unsupported SIEM type: {siem_type}. "
                f"Supported types: {', '.join(SIEM_TYPES)}"
            )

    @staticmethod
    def from_engagement(engagement_id: int) -> Optional[SIEMClient]:
        """Create a SIEM client from engagement configuration.

        Looks up the SIEM configuration stored for the engagement
        and creates the appropriate client.

        Args:
            engagement_id: Engagement ID to get config from

        Returns:
            SIEMClient instance or None if not configured
        """
        from souleyez.integrations.wazuh.config import WazuhConfig

        # Get SIEM config (currently stored as Wazuh config)
        config = WazuhConfig.get_config(engagement_id)

        if not config or not config.get("enabled"):
            return None

        # Determine SIEM type from config
        siem_type = config.get("siem_type", "wazuh")

        return SIEMFactory.create(siem_type, config)

    @staticmethod
    def get_available_types() -> List[str]:
        """Get list of available SIEM types.

        Returns:
            List of SIEM type identifiers
        """
        return SIEM_TYPES.copy()

    @staticmethod
    def get_type_info(siem_type: str) -> Dict[str, Any]:
        """Get information about a SIEM type.

        Args:
            siem_type: SIEM type identifier

        Returns:
            Dict with name, description, config_fields
        """
        info_map = {
            "wazuh": {
                "name": "Wazuh",
                "description": "[Open Source] Security monitoring platform (OSSEC fork)",
                "config_fields": [
                    {
                        "name": "api_url",
                        "label": "Manager API URL",
                        "required": True,
                        "placeholder": "https://wazuh.example.com:55000",
                    },
                    {"name": "username", "label": "Username", "required": True},
                    {
                        "name": "password",
                        "label": "Password",
                        "required": True,
                        "secret": True,
                    },
                    {
                        "name": "indexer_url",
                        "label": "Indexer URL",
                        "required": False,
                        "placeholder": "https://wazuh.example.com:9200",
                    },
                    {
                        "name": "indexer_user",
                        "label": "Indexer Username",
                        "required": False,
                        "placeholder": "admin",
                    },
                    {
                        "name": "indexer_password",
                        "label": "Indexer Password",
                        "required": False,
                        "secret": True,
                    },
                    {
                        "name": "verify_ssl",
                        "label": "Verify SSL",
                        "required": False,
                        "type": "boolean",
                    },
                ],
            },
            "splunk": {
                "name": "Splunk",
                "description": "[Commercial] Enterprise SIEM and log management",
                "config_fields": [
                    {
                        "name": "api_url",
                        "label": "REST API URL",
                        "required": True,
                        "placeholder": "https://splunk.example.com:8089",
                    },
                    {"name": "username", "label": "Username", "required": True},
                    {
                        "name": "password",
                        "label": "Password",
                        "required": True,
                        "secret": True,
                    },
                    {
                        "name": "token",
                        "label": "Auth Token (alternative)",
                        "required": False,
                        "secret": True,
                    },
                    {
                        "name": "default_index",
                        "label": "Default Index",
                        "required": False,
                        "placeholder": "main",
                    },
                    {
                        "name": "verify_ssl",
                        "label": "Verify SSL",
                        "required": False,
                        "type": "boolean",
                    },
                ],
            },
            "elastic": {
                "name": "Elastic Security",
                "description": "[Open Source] Elastic Stack security solution (ELK SIEM)",
                "config_fields": [
                    {
                        "name": "elasticsearch_url",
                        "label": "Elasticsearch URL",
                        "required": True,
                        "placeholder": "https://elastic.example.com:9200",
                    },
                    {
                        "name": "kibana_url",
                        "label": "Kibana URL",
                        "required": False,
                        "placeholder": "https://kibana.example.com:5601",
                    },
                    {
                        "name": "api_key",
                        "label": "API Key",
                        "required": False,
                        "secret": True,
                    },
                    {"name": "username", "label": "Username", "required": False},
                    {
                        "name": "password",
                        "label": "Password",
                        "required": False,
                        "secret": True,
                    },
                    {
                        "name": "space",
                        "label": "Kibana Space",
                        "required": False,
                        "placeholder": "default",
                    },
                    {
                        "name": "verify_ssl",
                        "label": "Verify SSL",
                        "required": False,
                        "type": "boolean",
                    },
                ],
            },
            "sentinel": {
                "name": "Microsoft Sentinel",
                "description": "[Commercial] Azure cloud-native SIEM",
                "config_fields": [
                    {"name": "tenant_id", "label": "Azure Tenant ID", "required": True},
                    {"name": "client_id", "label": "App Client ID", "required": True},
                    {
                        "name": "client_secret",
                        "label": "App Client Secret",
                        "required": True,
                        "secret": True,
                    },
                    {
                        "name": "subscription_id",
                        "label": "Subscription ID",
                        "required": True,
                    },
                    {
                        "name": "resource_group",
                        "label": "Resource Group",
                        "required": True,
                    },
                    {
                        "name": "workspace_name",
                        "label": "Workspace Name",
                        "required": True,
                    },
                    {
                        "name": "workspace_id",
                        "label": "Workspace ID (GUID)",
                        "required": True,
                    },
                ],
            },
            "google_secops": {
                "name": "Google SecOps",
                "description": "[Commercial] Google Cloud security operations (Chronicle)",
                "config_fields": [
                    {
                        "name": "customer_id",
                        "label": "Chronicle Customer ID",
                        "required": True,
                        "placeholder": "Your Chronicle customer ID",
                    },
                    {
                        "name": "region",
                        "label": "Chronicle Region",
                        "required": True,
                        "placeholder": "us, europe, asia-southeast1",
                    },
                    {
                        "name": "project_id",
                        "label": "Google Cloud Project ID",
                        "required": False,
                        "placeholder": "Optional if in service account JSON",
                    },
                    {
                        "name": "credentials_json",
                        "label": "Service Account JSON",
                        "required": True,
                        "secret": True,
                        "type": "textarea",
                        "placeholder": "Paste service account JSON key",
                    },
                    {
                        "name": "verify_ssl",
                        "label": "Verify SSL",
                        "required": False,
                        "type": "boolean",
                    },
                ],
            },
        }

        return info_map.get(
            siem_type.lower(),
            {
                "name": siem_type,
                "description": "Unknown SIEM type",
                "config_fields": [],
            },
        )

    @staticmethod
    def test_config(siem_type: str, config: Dict[str, Any]) -> SIEMConnectionStatus:
        """Test a SIEM configuration without storing it.

        Args:
            siem_type: SIEM type identifier
            config: Configuration to test

        Returns:
            SIEMConnectionStatus with test results
        """
        try:
            client = SIEMFactory.create(siem_type, config)
            return client.test_connection()
        except Exception as e:
            return SIEMConnectionStatus(
                connected=False, error=str(e), siem_type=siem_type
            )
