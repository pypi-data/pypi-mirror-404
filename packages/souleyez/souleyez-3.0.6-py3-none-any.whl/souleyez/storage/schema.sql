CREATE TABLE IF NOT EXISTS engagements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    engagement_type TEXT DEFAULT 'custom',
    owner_id INTEGER,
    estimated_hours FLOAT DEFAULT 0,
    actual_hours FLOAT DEFAULT 0,
    scope_enforcement TEXT DEFAULT 'off',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS hosts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    engagement_id INTEGER NOT NULL,
    ip_address TEXT NOT NULL,
    hostname TEXT,
    domain TEXT,
    os_name TEXT,
    os_accuracy INTEGER,
    mac_address TEXT,
    status TEXT DEFAULT 'up',
    access_level TEXT DEFAULT 'none',
    scope_status TEXT DEFAULT 'unknown',
    notes TEXT,
    tags TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (engagement_id) REFERENCES engagements(id) ON DELETE CASCADE,
    UNIQUE(engagement_id, ip_address)
);

CREATE TABLE IF NOT EXISTS services (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    host_id INTEGER NOT NULL,
    port INTEGER NOT NULL,
    protocol TEXT DEFAULT 'tcp',
    state TEXT DEFAULT 'open',
    service_name TEXT,
    service_version TEXT,
    service_product TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (host_id) REFERENCES hosts(id) ON DELETE CASCADE,
    UNIQUE(host_id, port, protocol)
);

CREATE TABLE IF NOT EXISTS findings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    engagement_id INTEGER NOT NULL,
    host_id INTEGER,
    service_id INTEGER,
    finding_type TEXT NOT NULL,
    severity TEXT DEFAULT 'info',
    title TEXT NOT NULL,
    description TEXT,
    evidence TEXT,
    refs TEXT,
    port INTEGER,
    path TEXT,
    tool TEXT,
    scan_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (engagement_id) REFERENCES engagements(id) ON DELETE CASCADE,
    FOREIGN KEY (host_id) REFERENCES hosts(id) ON DELETE SET NULL,
    FOREIGN KEY (service_id) REFERENCES services(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS web_paths (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    host_id INTEGER NOT NULL,
    url TEXT NOT NULL,
    status_code INTEGER,
    content_length INTEGER,
    redirect TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (host_id) REFERENCES hosts(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS osint_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    engagement_id INTEGER NOT NULL,
    data_type TEXT NOT NULL,
    value TEXT NOT NULL,
    source TEXT,
    target TEXT,
    summary TEXT,
    content TEXT,
    metadata TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (engagement_id) REFERENCES engagements(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS smb_shares (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    host_id INTEGER NOT NULL,
    share_name TEXT NOT NULL,
    share_type TEXT,
    permissions TEXT,
    comment TEXT,
    readable INTEGER DEFAULT 0,
    writable INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (host_id) REFERENCES hosts(id) ON DELETE CASCADE,
    UNIQUE(host_id, share_name)
);

CREATE TABLE IF NOT EXISTS smb_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    share_id INTEGER NOT NULL,
    path TEXT NOT NULL,
    size INTEGER,
    timestamp TEXT,
    is_directory INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (share_id) REFERENCES smb_shares(id) ON DELETE CASCADE
);

-- SQLMap SQL Injection discoveries
CREATE TABLE IF NOT EXISTS sqli_databases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    engagement_id INTEGER NOT NULL,
    host_id INTEGER NOT NULL,
    database_name TEXT NOT NULL,
    dbms_type TEXT,
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (engagement_id) REFERENCES engagements(id) ON DELETE CASCADE,
    FOREIGN KEY (host_id) REFERENCES hosts(id) ON DELETE CASCADE,
    UNIQUE(engagement_id, host_id, database_name)
);

CREATE TABLE IF NOT EXISTS sqli_tables (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    database_id INTEGER NOT NULL,
    table_name TEXT NOT NULL,
    row_count INTEGER,
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (database_id) REFERENCES sqli_databases(id) ON DELETE CASCADE,
    UNIQUE(database_id, table_name)
);

CREATE TABLE IF NOT EXISTS sqli_columns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    table_id INTEGER NOT NULL,
    column_name TEXT NOT NULL,
    column_type TEXT,
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (table_id) REFERENCES sqli_tables(id) ON DELETE CASCADE,
    UNIQUE(table_id, column_name)
);

CREATE TABLE IF NOT EXISTS sqli_dumped_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    table_id INTEGER NOT NULL,
    data_json TEXT NOT NULL,
    csv_file_path TEXT,
    row_count INTEGER,
    is_encrypted INTEGER DEFAULT 0,
    dumped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (table_id) REFERENCES sqli_tables(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_hosts_engagement ON hosts(engagement_id);
CREATE INDEX IF NOT EXISTS idx_hosts_ip ON hosts(ip_address);
CREATE INDEX IF NOT EXISTS idx_services_host ON services(host_id);
CREATE INDEX IF NOT EXISTS idx_services_port ON services(port);
CREATE INDEX IF NOT EXISTS idx_services_name ON services(service_name);
CREATE INDEX IF NOT EXISTS idx_findings_engagement ON findings(engagement_id);
CREATE INDEX IF NOT EXISTS idx_findings_host ON findings(host_id);
CREATE INDEX IF NOT EXISTS idx_findings_severity ON findings(severity);
CREATE INDEX IF NOT EXISTS idx_web_paths_host ON web_paths(host_id);
CREATE INDEX IF NOT EXISTS idx_web_paths_url ON web_paths(url);
CREATE INDEX IF NOT EXISTS idx_osint_engagement ON osint_data(engagement_id);
CREATE INDEX IF NOT EXISTS idx_osint_type ON osint_data(data_type);
CREATE INDEX IF NOT EXISTS idx_osint_target ON osint_data(target);
CREATE INDEX IF NOT EXISTS idx_smb_shares_host ON smb_shares(host_id);
CREATE INDEX IF NOT EXISTS idx_smb_files_share ON smb_files(share_id);
CREATE INDEX IF NOT EXISTS idx_sqli_databases_engagement ON sqli_databases(engagement_id);
CREATE INDEX IF NOT EXISTS idx_sqli_databases_host ON sqli_databases(host_id);
CREATE INDEX IF NOT EXISTS idx_sqli_tables_database ON sqli_tables(database_id);
CREATE INDEX IF NOT EXISTS idx_sqli_columns_table ON sqli_columns(table_id);
CREATE INDEX IF NOT EXISTS idx_sqli_dumped_data_table ON sqli_dumped_data(table_id);

-- Credentials table for storing discovered/tested credentials
CREATE TABLE IF NOT EXISTS credentials (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    engagement_id INTEGER NOT NULL,
    host_id INTEGER,
    service TEXT,
    port INTEGER,
    protocol TEXT DEFAULT 'tcp',
    username TEXT,
    password TEXT,
    credential_type TEXT DEFAULT 'user',
    status TEXT DEFAULT 'untested',
    tool TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    notes TEXT,
    last_tested TIMESTAMP,
    FOREIGN KEY (engagement_id) REFERENCES engagements(id) ON DELETE CASCADE,
    FOREIGN KEY (host_id) REFERENCES hosts(id) ON DELETE CASCADE
);

-- Execution log for AI-driven command tracking
CREATE TABLE IF NOT EXISTS execution_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    engagement_id INTEGER NOT NULL,
    recommendation_id TEXT,
    action TEXT NOT NULL,
    command TEXT NOT NULL,
    risk_level TEXT NOT NULL,
    auto_approved BOOLEAN DEFAULT 0,
    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    exit_code INTEGER,
    stdout TEXT,
    stderr TEXT,
    success BOOLEAN,
    feedback_applied TEXT,
    FOREIGN KEY (engagement_id) REFERENCES engagements(id) ON DELETE CASCADE
);

-- Indexes for credentials
CREATE INDEX IF NOT EXISTS idx_credentials_engagement ON credentials(engagement_id);
CREATE INDEX IF NOT EXISTS idx_credentials_host ON credentials(host_id);
CREATE INDEX IF NOT EXISTS idx_credentials_status ON credentials(status);

-- Indexes for execution_log
CREATE INDEX IF NOT EXISTS idx_execution_engagement ON execution_log(engagement_id);
CREATE INDEX IF NOT EXISTS idx_execution_timestamp ON execution_log(executed_at DESC);

-- Screenshots table for storing proof-of-concept images
CREATE TABLE IF NOT EXISTS screenshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    engagement_id INTEGER NOT NULL,
    host_id INTEGER,
    finding_id INTEGER,
    filename TEXT NOT NULL,
    filepath TEXT NOT NULL,
    title TEXT,
    description TEXT,
    file_size INTEGER,
    mime_type TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (engagement_id) REFERENCES engagements(id) ON DELETE CASCADE,
    FOREIGN KEY (host_id) REFERENCES hosts(id) ON DELETE SET NULL,
    FOREIGN KEY (finding_id) REFERENCES findings(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_screenshots_engagement ON screenshots(engagement_id);
CREATE INDEX IF NOT EXISTS idx_screenshots_host ON screenshots(host_id);
CREATE INDEX IF NOT EXISTS idx_screenshots_finding ON screenshots(finding_id);

-- Exploits table for SearchSploit results
CREATE TABLE IF NOT EXISTS exploits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    engagement_id INTEGER NOT NULL,
    service_id INTEGER,
    edb_id TEXT,
    title TEXT,
    platform TEXT,
    type TEXT,
    url TEXT,
    date_published TEXT,
    search_term TEXT,
    found_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (engagement_id) REFERENCES engagements(id) ON DELETE CASCADE,
    FOREIGN KEY (service_id) REFERENCES services(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_exploits_engagement ON exploits(engagement_id);
CREATE INDEX IF NOT EXISTS idx_exploits_service ON exploits(service_id);
CREATE INDEX IF NOT EXISTS idx_exploits_edb_id ON exploits(edb_id);

-- Exploit attempts tracking table
CREATE TABLE IF NOT EXISTS exploit_attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    engagement_id INTEGER NOT NULL,
    host_id INTEGER NOT NULL,
    service_id INTEGER,
    exploit_identifier TEXT NOT NULL,
    exploit_title TEXT,
    status TEXT NOT NULL DEFAULT 'not_tried',
    attempted_at TIMESTAMP,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (engagement_id) REFERENCES engagements(id) ON DELETE CASCADE,
    FOREIGN KEY (host_id) REFERENCES hosts(id) ON DELETE CASCADE,
    FOREIGN KEY (service_id) REFERENCES services(id) ON DELETE SET NULL,
    UNIQUE(engagement_id, host_id, service_id, exploit_identifier)
);

CREATE INDEX IF NOT EXISTS idx_exploit_attempts_engagement ON exploit_attempts(engagement_id);
CREATE INDEX IF NOT EXISTS idx_exploit_attempts_host ON exploit_attempts(host_id);
CREATE INDEX IF NOT EXISTS idx_exploit_attempts_status ON exploit_attempts(status);
CREATE INDEX IF NOT EXISTS idx_exploit_attempts_identifier ON exploit_attempts(exploit_identifier);

-- RBAC (Role-Based Access Control) tables
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    salt TEXT NOT NULL,
    email TEXT,
    role TEXT NOT NULL DEFAULT 'analyst',
    tier TEXT NOT NULL DEFAULT 'FREE',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    license_key TEXT,
    license_expires_at TIMESTAMP,
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    token_hash TEXT UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address TEXT,
    user_agent TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_id TEXT,
    username TEXT,
    action TEXT NOT NULL,
    resource_type TEXT,
    resource_id TEXT,
    details TEXT,
    ip_address TEXT,
    success BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS engagement_permissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    engagement_id INTEGER NOT NULL,
    user_id TEXT NOT NULL,
    permission_level TEXT NOT NULL DEFAULT 'viewer',
    granted_by TEXT,
    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (engagement_id) REFERENCES engagements(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE(engagement_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(token_hash);
CREATE INDEX IF NOT EXISTS idx_sessions_expires ON sessions(expires_at);
CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_log(user_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_log(action, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_engagement_perms ON engagement_permissions(user_id, engagement_id);

-- Deliverables tracking table (from migration 006)
CREATE TABLE IF NOT EXISTS deliverables (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    engagement_id INTEGER NOT NULL,
    category TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    target_type TEXT NOT NULL,
    target_value INTEGER,
    current_value INTEGER DEFAULT 0,
    status TEXT DEFAULT 'pending',
    auto_validate BOOLEAN DEFAULT 0,
    validation_query TEXT,
    priority TEXT DEFAULT 'medium',
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    estimated_hours FLOAT DEFAULT 0,
    actual_hours FLOAT DEFAULT 0,
    blocker TEXT,
    assigned_to TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (engagement_id) REFERENCES engagements(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_deliverables_engagement ON deliverables(engagement_id);
CREATE INDEX IF NOT EXISTS idx_deliverables_status ON deliverables(status);
CREATE INDEX IF NOT EXISTS idx_deliverables_category ON deliverables(category);

-- Deliverable templates table (from migration 007)
CREATE TABLE IF NOT EXISTS deliverable_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    framework TEXT,
    engagement_type TEXT,
    deliverables_json TEXT NOT NULL,
    created_by TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_builtin INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_templates_framework ON deliverable_templates(framework, engagement_type);

-- Nuclei vulnerability findings table (from migration 008)
CREATE TABLE IF NOT EXISTS nuclei_findings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    engagement_id INTEGER NOT NULL,
    template_id TEXT,
    name TEXT NOT NULL,
    severity TEXT CHECK(severity IN ('critical', 'high', 'medium', 'low', 'info')),
    description TEXT,
    matched_at TEXT,
    cve_id TEXT,
    cvss_score REAL,
    cwe_id TEXT,
    curl_command TEXT,
    tags TEXT,
    reference_links TEXT,
    metadata TEXT,
    found_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(engagement_id) REFERENCES engagements(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_nuclei_engagement ON nuclei_findings(engagement_id);
CREATE INDEX IF NOT EXISTS idx_nuclei_severity ON nuclei_findings(severity);
CREATE INDEX IF NOT EXISTS idx_nuclei_cve ON nuclei_findings(cve_id);

-- Evidence linking table (from migration 010)
CREATE TABLE IF NOT EXISTS deliverable_evidence (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    deliverable_id INTEGER NOT NULL,
    evidence_type TEXT NOT NULL,
    evidence_id INTEGER NOT NULL,
    linked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    linked_by TEXT,
    notes TEXT,
    FOREIGN KEY (deliverable_id) REFERENCES deliverables(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_deliverable_evidence ON deliverable_evidence(deliverable_id, evidence_type);
CREATE INDEX IF NOT EXISTS idx_evidence_lookup ON deliverable_evidence(evidence_type, evidence_id);

-- Deliverable activity log (from migration 012)
CREATE TABLE IF NOT EXISTS deliverable_activity (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    deliverable_id INTEGER NOT NULL,
    engagement_id INTEGER NOT NULL,
    user TEXT NOT NULL,
    action TEXT NOT NULL,
    details TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (deliverable_id) REFERENCES deliverables(id) ON DELETE CASCADE,
    FOREIGN KEY (engagement_id) REFERENCES engagements(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_activity_deliverable ON deliverable_activity(deliverable_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_activity_engagement ON deliverable_activity(engagement_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_activity_user ON deliverable_activity(user, created_at DESC);

-- Deliverable comments table (from migration 012)
CREATE TABLE IF NOT EXISTS deliverable_comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    deliverable_id INTEGER NOT NULL,
    user TEXT NOT NULL,
    comment TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (deliverable_id) REFERENCES deliverables(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_comments_deliverable ON deliverable_comments(deliverable_id, created_at DESC);

-- MSF Sessions tracking table (from migration 017)
CREATE TABLE IF NOT EXISTS msf_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    engagement_id INTEGER NOT NULL,
    host_id INTEGER NOT NULL,
    msf_session_id INTEGER NOT NULL,
    session_type TEXT,
    via_exploit TEXT,
    via_payload TEXT,
    platform TEXT,
    arch TEXT,
    username TEXT,
    port INTEGER,
    tunnel_peer TEXT,
    opened_at TIMESTAMP,
    closed_at TIMESTAMP,
    close_reason TEXT,
    last_seen TIMESTAMP,
    is_active BOOLEAN DEFAULT 1,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (engagement_id) REFERENCES engagements(id) ON DELETE CASCADE,
    FOREIGN KEY (host_id) REFERENCES hosts(id) ON DELETE CASCADE,
    UNIQUE(engagement_id, msf_session_id)
);

CREATE INDEX IF NOT EXISTS idx_msf_sessions_engagement ON msf_sessions(engagement_id);
CREATE INDEX IF NOT EXISTS idx_msf_sessions_host ON msf_sessions(host_id);
CREATE INDEX IF NOT EXISTS idx_msf_sessions_active ON msf_sessions(is_active);

-- Wazuh SIEM Integration (Detection Validation)
CREATE TABLE IF NOT EXISTS wazuh_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    engagement_id INTEGER NOT NULL,
    siem_type TEXT NOT NULL DEFAULT 'wazuh',
    api_url TEXT,
    api_user TEXT,
    api_password TEXT,
    indexer_url TEXT,
    indexer_user TEXT DEFAULT 'admin',
    indexer_password TEXT,
    verify_ssl BOOLEAN DEFAULT 0,
    enabled BOOLEAN DEFAULT 1,
    config_json TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (engagement_id) REFERENCES engagements(id) ON DELETE CASCADE,
    UNIQUE(engagement_id, siem_type)
);

-- Detection validation results per job
-- Note: job_id references jobs.json (file-based), not a SQLite table
CREATE TABLE IF NOT EXISTS detection_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER NOT NULL,
    engagement_id INTEGER NOT NULL,
    attack_type TEXT,
    target_ip TEXT,
    target_port INTEGER,
    source_ip TEXT,
    attack_start TIMESTAMP,
    attack_end TIMESTAMP,
    detection_status TEXT DEFAULT 'pending',
    alerts_count INTEGER DEFAULT 0,
    wazuh_alerts_json TEXT,
    rule_ids TEXT,
    checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (engagement_id) REFERENCES engagements(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_wazuh_config_engagement ON wazuh_config(engagement_id);
CREATE INDEX IF NOT EXISTS idx_wazuh_config_siem_type ON wazuh_config(siem_type);
CREATE INDEX IF NOT EXISTS idx_detection_results_job ON detection_results(job_id);
CREATE INDEX IF NOT EXISTS idx_detection_results_engagement ON detection_results(engagement_id);
CREATE INDEX IF NOT EXISTS idx_detection_results_status ON detection_results(detection_status);

-- Engagement Scope Validation (from migration 026)
CREATE TABLE IF NOT EXISTS engagement_scope (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    engagement_id INTEGER NOT NULL,
    scope_type TEXT NOT NULL,
    value TEXT NOT NULL,
    is_excluded BOOLEAN DEFAULT 0,
    description TEXT,
    added_by TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (engagement_id) REFERENCES engagements(id) ON DELETE CASCADE,
    UNIQUE(engagement_id, scope_type, value)
);

CREATE TABLE IF NOT EXISTS scope_validation_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    engagement_id INTEGER NOT NULL,
    job_id INTEGER,
    target TEXT NOT NULL,
    validation_result TEXT NOT NULL,
    action_taken TEXT NOT NULL,
    matched_scope_id INTEGER,
    user_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (engagement_id) REFERENCES engagements(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_scope_engagement ON engagement_scope(engagement_id);
CREATE INDEX IF NOT EXISTS idx_scope_type ON engagement_scope(scope_type);
CREATE INDEX IF NOT EXISTS idx_scope_log_engagement ON scope_validation_log(engagement_id);
CREATE INDEX IF NOT EXISTS idx_scope_log_result ON scope_validation_log(validation_result);
CREATE INDEX IF NOT EXISTS idx_scope_log_timestamp ON scope_validation_log(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_hosts_scope_status ON hosts(scope_status);
