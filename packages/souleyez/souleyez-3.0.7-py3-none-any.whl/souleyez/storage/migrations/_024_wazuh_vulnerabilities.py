"""
Migration 024: Add Wazuh Vulnerabilities table

Adds table for storing vulnerabilities discovered by Wazuh agents,
enabling gap analysis between passive (agent-based) and active (scan-based)
vulnerability detection.
"""

MIGRATION_ID = 24
DESCRIPTION = "Add Wazuh vulnerabilities table for gap analysis"


def upgrade(conn):
    """Apply migration"""
    cursor = conn.cursor()

    # Wazuh vulnerabilities table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS wazuh_vulnerabilities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            engagement_id INTEGER NOT NULL,
            host_id INTEGER,

            -- Agent info
            agent_id TEXT NOT NULL,
            agent_name TEXT,
            agent_ip TEXT,

            -- Vulnerability details
            cve_id TEXT NOT NULL,
            name TEXT,
            severity TEXT,
            cvss_score REAL,
            cvss_version TEXT,

            -- Affected package
            package_name TEXT,
            package_version TEXT,
            package_architecture TEXT,

            -- Detection info
            detection_time TIMESTAMP,
            published_date TEXT,

            -- Status tracking
            status TEXT DEFAULT 'open',
            verified_by_scan BOOLEAN DEFAULT 0,
            matched_finding_id INTEGER,

            -- Metadata
            reference_urls TEXT,
            raw_data TEXT,
            synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (engagement_id) REFERENCES engagements(id) ON DELETE CASCADE,
            FOREIGN KEY (host_id) REFERENCES hosts(id) ON DELETE SET NULL,
            FOREIGN KEY (matched_finding_id) REFERENCES findings(id) ON DELETE SET NULL,

            UNIQUE(engagement_id, agent_id, cve_id, package_name)
        )
    """)

    # Sync metadata table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS wazuh_vuln_sync (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            engagement_id INTEGER NOT NULL UNIQUE,
            last_sync_at TIMESTAMP,
            last_sync_count INTEGER DEFAULT 0,
            last_sync_status TEXT,
            last_sync_errors TEXT,
            FOREIGN KEY (engagement_id) REFERENCES engagements(id) ON DELETE CASCADE
        )
    """)

    # Indexes for performance
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_wazuh_vulns_engagement ON wazuh_vulnerabilities(engagement_id)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_wazuh_vulns_host ON wazuh_vulnerabilities(host_id)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_wazuh_vulns_cve ON wazuh_vulnerabilities(cve_id)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_wazuh_vulns_severity ON wazuh_vulnerabilities(severity)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_wazuh_vulns_agent_ip ON wazuh_vulnerabilities(agent_ip)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_wazuh_vulns_status ON wazuh_vulnerabilities(status)"
    )

    conn.commit()


def downgrade(conn):
    """Revert migration"""
    cursor = conn.cursor()

    cursor.execute("DROP INDEX IF EXISTS idx_wazuh_vulns_status")
    cursor.execute("DROP INDEX IF EXISTS idx_wazuh_vulns_agent_ip")
    cursor.execute("DROP INDEX IF EXISTS idx_wazuh_vulns_severity")
    cursor.execute("DROP INDEX IF EXISTS idx_wazuh_vulns_cve")
    cursor.execute("DROP INDEX IF EXISTS idx_wazuh_vulns_host")
    cursor.execute("DROP INDEX IF EXISTS idx_wazuh_vulns_engagement")
    cursor.execute("DROP TABLE IF EXISTS wazuh_vuln_sync")
    cursor.execute("DROP TABLE IF EXISTS wazuh_vulnerabilities")

    conn.commit()
