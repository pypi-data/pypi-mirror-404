# Migration system for souleyez database
# Registry pattern - all migrations are imported here so they're compiled into the binary

# Import all migrations - they register themselves
from . import (
    _001_add_credential_enhancements,  # 001-010; 011-020; 021-030
    _002_add_status_tracking,
    _003_add_execution_log,
    _005_screenshots,
    _006_deliverables,
    _007_deliverable_templates,
    _008_add_nuclei_table,
    _009_add_cme_tables,
    _010_evidence_linking,
    _011_timeline_tracking,
    _012_team_collaboration,
    _013_add_host_tags,
    _014_exploit_attempts,
    _015_add_mac_os_fields,
    _016_add_domain_field,
    _017_msf_sessions,
    _018_add_osint_target,
    _019_add_engagement_type,
    _020_add_rbac,
    _021_wazuh_integration,
    _022_wazuh_indexer_columns,
    _023_fix_detection_results_fk,
    _024_wazuh_vulnerabilities,
    _025_multi_siem_support,
    _026_add_engagement_scope,
    _027_multi_siem_persistence,
)

# Migration registry - maps version to module
MIGRATIONS_REGISTRY = {
    "001": _001_add_credential_enhancements,
    "002": _002_add_status_tracking,
    "003": _003_add_execution_log,
    "005": _005_screenshots,
    "006": _006_deliverables,
    "007": _007_deliverable_templates,
    "008": _008_add_nuclei_table,
    "009": _009_add_cme_tables,
    "010": _010_evidence_linking,
    "011": _011_timeline_tracking,
    "012": _012_team_collaboration,
    "013": _013_add_host_tags,
    "014": _014_exploit_attempts,
    "015": _015_add_mac_os_fields,
    "016": _016_add_domain_field,
    "017": _017_msf_sessions,
    "018": _018_add_osint_target,
    "019": _019_add_engagement_type,
    "020": _020_add_rbac,
    "021": _021_wazuh_integration,
    "022": _022_wazuh_indexer_columns,
    "023": _023_fix_detection_results_fk,
    "024": _024_wazuh_vulnerabilities,
    "025": _025_multi_siem_support,
    "026": _026_add_engagement_scope,
    "027": _027_multi_siem_persistence,
}


def get_migration(version: str):
    """Get migration module by version."""
    return MIGRATIONS_REGISTRY.get(version)


def get_all_versions():
    """Get all registered migration versions in order."""
    return sorted(MIGRATIONS_REGISTRY.keys())
