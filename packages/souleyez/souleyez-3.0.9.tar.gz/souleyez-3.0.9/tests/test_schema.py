#!/usr/bin/env python3
"""
Schema validation tests - verify database structure and integrity
"""
import pytest
import sqlite3


def test_schema_has_all_tables(isolated_db):
    """Verify all required tables exist."""
    conn = isolated_db.get_connection()

    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()

    table_names = [t[0] for t in tables]

    # Check all required tables exist (schema_migrations is only created when migrations run)
    required_tables = [
        "engagements",
        "hosts",
        "services",
        "findings",
        "web_paths",
        "osint_data",
        "smb_shares",
        "smb_files",
    ]

    for table in required_tables:
        assert table in table_names, f"Missing table: {table}"

    conn.close()


def test_schema_has_foreign_keys(isolated_db):
    """Verify all foreign keys are defined."""
    conn = isolated_db.get_connection()

    # Enable foreign key checking
    conn.execute("PRAGMA foreign_keys = ON")

    # Check hosts table
    fks = conn.execute("PRAGMA foreign_key_list(hosts)").fetchall()
    assert len(fks) == 1, "hosts should have 1 FK (engagement_id)"
    assert (
        fks[0][2] == "engagements"
    ), "hosts.engagement_id should reference engagements"
    assert fks[0][3] == "engagement_id", "FK should be on engagement_id"

    # Check services table
    fks = conn.execute("PRAGMA foreign_key_list(services)").fetchall()
    assert len(fks) == 1, "services should have 1 FK (host_id)"
    assert fks[0][2] == "hosts", "services.host_id should reference hosts"

    # Check findings table
    fks = conn.execute("PRAGMA foreign_key_list(findings)").fetchall()
    assert (
        len(fks) == 3
    ), "findings should have 3 FKs (engagement_id, host_id, service_id)"

    # Check web_paths table
    fks = conn.execute("PRAGMA foreign_key_list(web_paths)").fetchall()
    assert len(fks) == 1, "web_paths should have 1 FK (host_id)"

    # Check osint_data table
    fks = conn.execute("PRAGMA foreign_key_list(osint_data)").fetchall()
    assert len(fks) == 1, "osint_data should have 1 FK (engagement_id)"

    # Check smb_shares table
    fks = conn.execute("PRAGMA foreign_key_list(smb_shares)").fetchall()
    assert len(fks) == 1, "smb_shares should have 1 FK (host_id)"

    # Check smb_files table
    fks = conn.execute("PRAGMA foreign_key_list(smb_files)").fetchall()
    assert len(fks) == 1, "smb_files should have 1 FK (share_id)"

    conn.close()


def test_schema_has_indexes(isolated_db):
    """Verify performance indexes exist."""
    conn = isolated_db.get_connection()

    indexes = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%' ORDER BY name"
    ).fetchall()

    index_names = [idx[0] for idx in indexes]

    # Check required indexes exist (14 total)
    required_indexes = [
        "idx_hosts_engagement",
        "idx_hosts_ip",
        "idx_services_host",
        "idx_services_port",
        "idx_services_name",
        "idx_findings_engagement",
        "idx_findings_host",
        "idx_findings_severity",
        "idx_web_paths_host",
        "idx_web_paths_url",
        "idx_osint_engagement",
        "idx_osint_type",
        "idx_smb_shares_host",
        "idx_smb_files_share",
    ]

    for index in required_indexes:
        assert index in index_names, f"Missing index: {index}"

    assert len(index_names) >= len(
        required_indexes
    ), f"Expected at least {len(required_indexes)} indexes, found {len(index_names)}"

    conn.close()


def test_cascade_delete_engagement_removes_hosts(isolated_db):
    """Verify CASCADE delete from engagement removes hosts."""
    conn = isolated_db.get_connection()
    conn.execute("PRAGMA foreign_keys = ON")

    # Create engagement
    eng_id = isolated_db.insert(
        "engagements", {"name": "test_cascade", "description": "test"}
    )

    # Create host
    host_id = isolated_db.insert(
        "hosts", {"engagement_id": eng_id, "ip_address": "1.2.3.4"}
    )

    # Verify host exists
    hosts = isolated_db.execute("SELECT * FROM hosts WHERE id = ?", (host_id,))
    assert len(hosts) == 1, "Host should exist"

    # Delete engagement
    isolated_db.execute("DELETE FROM engagements WHERE id = ?", (eng_id,))

    # Verify host was deleted (CASCADE)
    hosts = isolated_db.execute("SELECT * FROM hosts WHERE id = ?", (host_id,))
    assert len(hosts) == 0, "Host should be deleted via CASCADE"

    conn.close()


def test_cascade_delete_host_removes_services(isolated_db):
    """Verify CASCADE delete from host removes services."""
    conn = isolated_db.get_connection()
    conn.execute("PRAGMA foreign_keys = ON")

    # Create engagement and host
    eng_id = isolated_db.insert(
        "engagements", {"name": "test_cascade2", "description": "test"}
    )
    host_id = isolated_db.insert(
        "hosts", {"engagement_id": eng_id, "ip_address": "1.2.3.5"}
    )

    # Create service
    svc_id = isolated_db.insert(
        "services",
        {"host_id": host_id, "port": 80, "protocol": "tcp", "service_name": "http"},
    )

    # Verify service exists
    services = isolated_db.execute("SELECT * FROM services WHERE id = ?", (svc_id,))
    assert len(services) == 1, "Service should exist"

    # Delete host
    isolated_db.execute("DELETE FROM hosts WHERE id = ?", (host_id,))

    # Verify service was deleted (CASCADE)
    services = isolated_db.execute("SELECT * FROM services WHERE id = ?", (svc_id,))
    assert len(services) == 0, "Service should be deleted via CASCADE"

    conn.close()


def test_set_null_on_finding_when_host_deleted(isolated_db):
    """Verify findings.host_id set to NULL when host deleted."""
    conn = isolated_db.get_connection()
    conn.execute("PRAGMA foreign_keys = ON")

    # Create engagement, host, and finding
    eng_id = isolated_db.insert(
        "engagements", {"name": "test_set_null", "description": "test"}
    )
    host_id = isolated_db.insert(
        "hosts", {"engagement_id": eng_id, "ip_address": "1.2.3.6"}
    )
    finding_id = isolated_db.insert(
        "findings",
        {
            "engagement_id": eng_id,
            "host_id": host_id,
            "finding_type": "vulnerability",
            "title": "Test Finding",
        },
    )

    # Verify finding has host_id
    findings = isolated_db.execute(
        "SELECT host_id FROM findings WHERE id = ?", (finding_id,)
    )
    assert findings[0]["host_id"] == host_id, "Finding should have host_id"

    # Delete host
    isolated_db.execute("DELETE FROM hosts WHERE id = ?", (host_id,))

    # Verify finding still exists but host_id is NULL
    findings = isolated_db.execute("SELECT * FROM findings WHERE id = ?", (finding_id,))
    assert len(findings) == 1, "Finding should still exist"
    assert findings[0]["host_id"] is None, "host_id should be NULL after host deletion"

    conn.close()


def test_unique_constraint_host_ip_per_engagement(isolated_db):
    """Verify hosts have unique IPs per engagement."""
    conn = isolated_db.get_connection()

    # Create engagement
    eng_id = isolated_db.insert(
        "engagements", {"name": "test_unique", "description": "test"}
    )

    # Create first host
    isolated_db.insert("hosts", {"engagement_id": eng_id, "ip_address": "1.2.3.7"})

    # Try to create duplicate IP in same engagement
    with pytest.raises(sqlite3.IntegrityError) as exc:
        isolated_db.insert("hosts", {"engagement_id": eng_id, "ip_address": "1.2.3.7"})

    assert "UNIQUE constraint failed" in str(
        exc.value
    ), "Should fail with UNIQUE constraint error"

    conn.close()


@pytest.mark.skip(
    reason="Flaky in CI - SQLite database locking race condition (CPM-134). Passes locally, fails intermittently in CI. Will fix in follow-up ticket."
)
def test_unique_constraint_service_port_per_host(isolated_db):
    """Verify services have unique port/protocol per host."""
    conn = isolated_db.get_connection()

    # Create engagement and host
    eng_id = isolated_db.insert(
        "engagements", {"name": "test_service_unique", "description": "test"}
    )
    host_id = isolated_db.insert(
        "hosts", {"engagement_id": eng_id, "ip_address": "1.2.3.8"}
    )

    # Create first service
    isolated_db.insert("services", {"host_id": host_id, "port": 443, "protocol": "tcp"})

    # Try to create duplicate service on same port/protocol
    with pytest.raises(sqlite3.IntegrityError) as exc:
        isolated_db.insert(
            "services", {"host_id": host_id, "port": 443, "protocol": "tcp"}
        )

    assert "UNIQUE constraint failed" in str(
        exc.value
    ), "Should fail with UNIQUE constraint error"

    # But should allow same port on different protocol
    udp_id = isolated_db.insert(
        "services", {"host_id": host_id, "port": 443, "protocol": "udp"}
    )
    assert udp_id > 0, "Should allow same port with different protocol"

    conn.close()


def test_unique_constraint_smb_share_per_host(isolated_db):
    """Verify SMB shares have unique names per host."""
    conn = isolated_db.get_connection()

    # Create engagement and host
    eng_id = isolated_db.insert(
        "engagements", {"name": "test_smb_unique", "description": "test"}
    )
    host_id = isolated_db.insert(
        "hosts", {"engagement_id": eng_id, "ip_address": "1.2.3.9"}
    )

    # Create first share
    isolated_db.insert("smb_shares", {"host_id": host_id, "share_name": "C$"})

    # Try to create duplicate share name
    with pytest.raises(sqlite3.IntegrityError) as exc:
        isolated_db.insert("smb_shares", {"host_id": host_id, "share_name": "C$"})

    assert "UNIQUE constraint failed" in str(
        exc.value
    ), "Should fail with UNIQUE constraint error"

    conn.close()


def test_foreign_keys_enabled_by_default(isolated_db):
    """Verify foreign key constraints are enabled."""
    conn = isolated_db.get_connection()

    result = conn.execute("PRAGMA foreign_keys").fetchone()
    assert result[0] == 1, "Foreign keys should be enabled (PRAGMA foreign_keys = 1)"

    conn.close()


def test_schema_integrity_check(isolated_db):
    """Verify database integrity."""
    conn = isolated_db.get_connection()

    result = conn.execute("PRAGMA integrity_check").fetchone()
    assert result[0] == "ok", f"Database integrity check failed: {result[0]}"

    conn.close()


def test_index_improves_query_performance(isolated_db):
    """Verify indexes are actually used by queries."""
    conn = isolated_db.get_connection()

    # Create test data
    eng_id = isolated_db.insert(
        "engagements", {"name": "perf_test", "description": "test"}
    )

    for i in range(10):
        isolated_db.insert(
            "hosts", {"engagement_id": eng_id, "ip_address": f"192.168.1.{i}"}
        )

    # Check query plan for engagement lookup
    plan = conn.execute(
        "EXPLAIN QUERY PLAN SELECT * FROM hosts WHERE engagement_id = ?", (eng_id,)
    ).fetchall()

    # Convert Row objects to strings
    plan_str = " ".join([" ".join([str(col) for col in row]) for row in plan]).lower()

    # Should mention index usage
    assert (
        "idx_hosts_engagement" in plan_str
        or "using index" in plan_str
        or "search" in plan_str
    ), f"Query should use index. Plan: {plan_str}"

    conn.close()
