"""
SIEM Rule Mappings.

Maps attack types to SIEM-specific detection rules.
"""

from souleyez.integrations.siem.rule_mappings.wazuh_rules import WAZUH_ATTACK_RULES

__all__ = [
    "WAZUH_ATTACK_RULES",
]
