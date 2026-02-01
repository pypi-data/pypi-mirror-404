"""
SIEM Integration Layer.

Provides a unified interface for multiple SIEM platforms:
- Wazuh (open source)
- Splunk (enterprise)
- Elastic SIEM (open source / cloud)
- Microsoft Sentinel (Azure)

Usage:
    from souleyez.integrations.siem import SIEMFactory, SIEMClient, SIEMAlert

    # Create a SIEM client
    client = SIEMFactory.create('wazuh', config)

    # Query alerts
    alerts = client.get_alerts(start_time, end_time, source_ip='10.0.0.1')

    # Check detection
    result = client.check_detection('nmap', attack_time, target_ip='10.0.0.50')
"""

from souleyez.integrations.siem.base import (
    SIEMAlert,
    SIEMClient,
    SIEMConnectionStatus,
    SIEMRule,
)
from souleyez.integrations.siem.elastic import ElasticSIEMClient
from souleyez.integrations.siem.factory import SIEMFactory
from souleyez.integrations.siem.googlesecops import GoogleSecOpsSIEMClient
from souleyez.integrations.siem.sentinel import SentinelSIEMClient
from souleyez.integrations.siem.splunk import SplunkSIEMClient
from souleyez.integrations.siem.wazuh import WazuhSIEMClient

__all__ = [
    # Base classes
    "SIEMClient",
    "SIEMAlert",
    "SIEMRule",
    "SIEMConnectionStatus",
    # Factory
    "SIEMFactory",
    # Implementations
    "WazuhSIEMClient",
    "SplunkSIEMClient",
    "ElasticSIEMClient",
    "SentinelSIEMClient",
    "GoogleSecOpsSIEMClient",
]
