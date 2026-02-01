#!/usr/bin/env python3
"""
Integration tests for engagement scope validation.

These tests verify that scope validation is properly integrated with:
- enqueue_job() in background.py
- Tool chaining in tool_chaining.py
- Host import in hosts.py
- Audit log population
"""
import pytest
import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from souleyez.storage.database import Database
from souleyez.storage.engagements import EngagementManager
from souleyez.storage.hosts import HostManager
from souleyez.security.scope_validator import (
    ScopeValidator,
    ScopeManager,
    ScopeViolationError,
)


# ===== FIXTURES =====


@pytest.fixture
def scope_db(tmp_path, monkeypatch):
    """Create isolated test database with scope tables."""
    # Reset database singleton
    import souleyez.storage.database as db_module

    db_module._db = None

    db_path = tmp_path / f"scope_test_{os.getpid()}.db"
    db = Database(str(db_path))

    # Set the global db to our test db
    monkeypatch.setattr(db_module, "_db", db)

    # Run the scope migration
    db.execute(
        """
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
        )
    """
    )

    db.execute(
        """
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
        )
    """
    )

    # Add scope_enforcement column to engagements if not exists
    try:
        db.execute(
            "ALTER TABLE engagements ADD COLUMN scope_enforcement TEXT DEFAULT 'off'"
        )
    except Exception:
        pass

    # Add scope_status column to hosts if not exists
    try:
        db.execute("ALTER TABLE hosts ADD COLUMN scope_status TEXT DEFAULT 'unknown'")
    except Exception:
        pass

    yield db

    # Cleanup
    db_module._db = None


@pytest.fixture
def scope_engagement(scope_db, monkeypatch):
    """Create a test engagement with scope support."""
    # Mock auth to avoid user requirement
    monkeypatch.setattr("souleyez.auth.get_current_user", lambda: None)

    em = EngagementManager()
    eng_id = em.create(
        name="scope_test_engagement", description="Test engagement for scope validation"
    )
    return eng_id, scope_db


@pytest.fixture
def engagement_with_cidr_scope(scope_engagement):
    """Create engagement with CIDR scope defined."""
    eng_id, db = scope_engagement

    # Add CIDR scope entry
    db.insert(
        "engagement_scope",
        {
            "engagement_id": eng_id,
            "scope_type": "cidr",
            "value": "192.168.1.0/24",
            "is_excluded": False,
            "description": "Test network",
        },
    )

    # Set enforcement to block
    db.execute(
        "UPDATE engagements SET scope_enforcement = ? WHERE id = ?", ("block", eng_id)
    )

    return eng_id, db


@pytest.fixture
def engagement_with_domain_scope(scope_engagement):
    """Create engagement with domain scope defined."""
    eng_id, db = scope_engagement

    # Add domain scope entries
    db.insert(
        "engagement_scope",
        {
            "engagement_id": eng_id,
            "scope_type": "domain",
            "value": "*.example.com",
            "is_excluded": False,
            "description": "Example domain",
        },
    )
    db.insert(
        "engagement_scope",
        {
            "engagement_id": eng_id,
            "scope_type": "domain",
            "value": "target.org",
            "is_excluded": False,
            "description": "Target org",
        },
    )

    # Set enforcement to warn
    db.execute(
        "UPDATE engagements SET scope_enforcement = ? WHERE id = ?", ("warn", eng_id)
    )

    return eng_id, db


@pytest.fixture
def engagement_with_mixed_scope(scope_engagement):
    """Create engagement with inclusions and exclusions."""
    eng_id, db = scope_engagement

    # Inclusion: entire 10.0.0.0/8 network
    db.insert(
        "engagement_scope",
        {
            "engagement_id": eng_id,
            "scope_type": "cidr",
            "value": "10.0.0.0/8",
            "is_excluded": False,
            "description": "Internal network",
        },
    )

    # Exclusion: specific subnet
    db.insert(
        "engagement_scope",
        {
            "engagement_id": eng_id,
            "scope_type": "cidr",
            "value": "10.0.1.0/24",
            "is_excluded": True,
            "description": "Excluded production subnet",
        },
    )

    # Exclusion: specific gateway
    db.insert(
        "engagement_scope",
        {
            "engagement_id": eng_id,
            "scope_type": "hostname",
            "value": "10.0.0.1",
            "is_excluded": True,
            "description": "Gateway - do not scan",
        },
    )

    # Set enforcement to block
    db.execute(
        "UPDATE engagements SET scope_enforcement = ? WHERE id = ?", ("block", eng_id)
    )

    return eng_id, db


# ===== SCOPE VALIDATOR INTEGRATION TESTS =====


class TestScopeValidatorIntegration:
    """Test ScopeValidator with real database."""

    def test_validator_loads_scope_from_db(self, engagement_with_cidr_scope):
        """Validator correctly loads scope entries from database."""
        eng_id, db = engagement_with_cidr_scope

        validator = ScopeValidator(eng_id)

        assert validator.has_scope_defined() is True
        entries = validator.get_scope_entries()
        assert len(entries) == 1
        assert entries[0]["scope_type"] == "cidr"
        assert entries[0]["value"] == "192.168.1.0/24"

    def test_validator_loads_enforcement_from_db(self, engagement_with_cidr_scope):
        """Validator loads enforcement mode from database."""
        eng_id, db = engagement_with_cidr_scope

        validator = ScopeValidator(eng_id)

        assert validator.get_enforcement_mode() == "block"

    def test_validation_in_scope_cidr(self, engagement_with_cidr_scope):
        """Target within CIDR is validated as in-scope."""
        eng_id, db = engagement_with_cidr_scope

        validator = ScopeValidator(eng_id)
        result = validator.validate_target("192.168.1.100")

        assert result.is_in_scope is True
        assert result.scope_type == "cidr"

    def test_validation_out_of_scope_cidr(self, engagement_with_cidr_scope):
        """Target outside CIDR is validated as out-of-scope."""
        eng_id, db = engagement_with_cidr_scope

        validator = ScopeValidator(eng_id)
        result = validator.validate_target("10.0.0.50")

        assert result.is_in_scope is False

    def test_validation_wildcard_domain(self, engagement_with_domain_scope):
        """Wildcard domain matching works correctly."""
        eng_id, db = engagement_with_domain_scope

        validator = ScopeValidator(eng_id)

        # Matches *.example.com
        result = validator.validate_target("app.example.com")
        assert result.is_in_scope is True

        # Matches target.org exactly
        result = validator.validate_target("target.org")
        assert result.is_in_scope is True

        # Does not match
        result = validator.validate_target("other.com")
        assert result.is_in_scope is False

    def test_exclusions_override_inclusions(self, engagement_with_mixed_scope):
        """Exclusions take precedence over inclusions."""
        eng_id, db = engagement_with_mixed_scope

        validator = ScopeValidator(eng_id)

        # In 10.0.0.0/8 but not excluded
        result = validator.validate_target("10.0.2.50")
        assert result.is_in_scope is True

        # In 10.0.0.0/8 but excluded via 10.0.1.0/24
        result = validator.validate_target("10.0.1.50")
        assert result.is_in_scope is False
        assert "Explicitly excluded" in result.reason

        # Explicitly excluded gateway
        result = validator.validate_target("10.0.0.1")
        assert result.is_in_scope is False


# ===== AUDIT LOG TESTS =====


class TestScopeAuditLog:
    """Test scope validation audit logging."""

    def test_log_validation_creates_entry(
        self, engagement_with_cidr_scope, monkeypatch
    ):
        """Logging creates audit trail entry in database."""
        eng_id, db = engagement_with_cidr_scope
        monkeypatch.setattr("souleyez.auth.get_current_user", lambda: None)

        validator = ScopeValidator(eng_id)
        result = validator.validate_target("192.168.1.100")

        validator.log_validation(
            target="192.168.1.100", result=result, action="allowed", job_id=42
        )

        # Verify log entry was created
        log_entries = db.execute(
            "SELECT * FROM scope_validation_log WHERE engagement_id = ?", (eng_id,)
        )

        assert len(log_entries) == 1
        assert log_entries[0]["target"] == "192.168.1.100"
        assert log_entries[0]["validation_result"] == "in_scope"
        assert log_entries[0]["action_taken"] == "allowed"
        assert log_entries[0]["job_id"] == 42

    def test_log_out_of_scope_blocked(self, engagement_with_cidr_scope, monkeypatch):
        """Blocked out-of-scope targets are logged correctly."""
        eng_id, db = engagement_with_cidr_scope
        monkeypatch.setattr("souleyez.auth.get_current_user", lambda: None)

        validator = ScopeValidator(eng_id)
        result = validator.validate_target("10.0.0.50")

        validator.log_validation(
            target="10.0.0.50", result=result, action="blocked", job_id=99
        )

        log_entries = db.execute(
            "SELECT * FROM scope_validation_log WHERE job_id = ?", (99,)
        )

        assert len(log_entries) == 1
        assert log_entries[0]["validation_result"] == "out_of_scope"
        assert log_entries[0]["action_taken"] == "blocked"

    def test_log_warned_action(self, engagement_with_domain_scope, monkeypatch):
        """Warned actions are logged correctly."""
        eng_id, db = engagement_with_domain_scope
        monkeypatch.setattr("souleyez.auth.get_current_user", lambda: None)

        validator = ScopeValidator(eng_id)
        result = validator.validate_target("other.com")

        validator.log_validation(
            target="other.com", result=result, action="warned", job_id=55
        )

        log_entries = db.execute(
            "SELECT * FROM scope_validation_log WHERE job_id = ?", (55,)
        )

        assert len(log_entries) == 1
        assert log_entries[0]["action_taken"] == "warned"


# ===== SCOPE MANAGER INTEGRATION TESTS =====


class TestScopeManagerIntegration:
    """Test ScopeManager with real database."""

    def test_add_scope_persists_to_db(self, scope_engagement, monkeypatch):
        """Adding scope persists to database."""
        eng_id, db = scope_engagement
        monkeypatch.setattr("souleyez.auth.get_current_user", lambda: None)

        manager = ScopeManager()

        scope_id = manager.add_scope(
            engagement_id=eng_id,
            scope_type="cidr",
            value="172.16.0.0/16",
            description="Private network",
        )

        assert scope_id is not None

        # Verify in database
        entries = db.execute("SELECT * FROM engagement_scope WHERE id = ?", (scope_id,))

        assert len(entries) == 1
        assert entries[0]["value"] == "172.16.0.0/16"
        assert entries[0]["scope_type"] == "cidr"

    def test_add_exclusion_persists(self, scope_engagement, monkeypatch):
        """Adding exclusion with is_excluded=True persists correctly."""
        eng_id, db = scope_engagement
        monkeypatch.setattr("souleyez.auth.get_current_user", lambda: None)

        manager = ScopeManager()

        scope_id = manager.add_scope(
            engagement_id=eng_id,
            scope_type="hostname",
            value="10.0.0.1",
            is_excluded=True,
            description="Excluded gateway",
        )

        entries = db.execute("SELECT * FROM engagement_scope WHERE id = ?", (scope_id,))

        assert entries[0]["is_excluded"] == 1

    def test_remove_scope(self, engagement_with_cidr_scope):
        """Removing scope entry deletes from database."""
        eng_id, db = engagement_with_cidr_scope

        # Get the scope entry id
        entries = db.execute(
            "SELECT id FROM engagement_scope WHERE engagement_id = ?", (eng_id,)
        )
        scope_id = entries[0]["id"]

        manager = ScopeManager()
        result = manager.remove_scope(scope_id)

        assert result is True

        # Verify deleted
        entries = db.execute("SELECT * FROM engagement_scope WHERE id = ?", (scope_id,))
        assert len(entries) == 0

    def test_list_scope(self, engagement_with_domain_scope):
        """Listing scope entries returns all entries."""
        eng_id, db = engagement_with_domain_scope

        manager = ScopeManager()
        entries = manager.list_scope(eng_id)

        assert len(entries) == 2
        values = [e["value"] for e in entries]
        assert "*.example.com" in values
        assert "target.org" in values

    def test_set_enforcement_updates_db(self, scope_engagement):
        """Setting enforcement mode updates database."""
        eng_id, db = scope_engagement

        manager = ScopeManager()

        result = manager.set_enforcement(eng_id, "block")
        assert result is True

        # Verify in database
        eng = db.execute_one(
            "SELECT scope_enforcement FROM engagements WHERE id = ?", (eng_id,)
        )
        assert eng["scope_enforcement"] == "block"

    def test_get_validation_log(self, engagement_with_cidr_scope):
        """Retrieving validation log returns entries."""
        eng_id, db = engagement_with_cidr_scope

        # Create some log entries
        db.insert(
            "scope_validation_log",
            {
                "engagement_id": eng_id,
                "job_id": 1,
                "target": "192.168.1.100",
                "validation_result": "in_scope",
                "action_taken": "allowed",
            },
        )
        db.insert(
            "scope_validation_log",
            {
                "engagement_id": eng_id,
                "job_id": 2,
                "target": "10.0.0.50",
                "validation_result": "out_of_scope",
                "action_taken": "blocked",
            },
        )

        manager = ScopeManager()
        log = manager.get_validation_log(eng_id)

        assert len(log) == 2


# ===== HOST SCOPE STATUS TESTS =====


class TestHostScopeStatus:
    """Test host scope_status tracking."""

    def test_new_host_gets_scope_status(self, engagement_with_cidr_scope):
        """New host is assigned correct scope_status on creation."""
        eng_id, db = engagement_with_cidr_scope

        manager = HostManager()

        # In-scope host
        host_id = manager.add_or_update_host(
            engagement_id=eng_id, host_data={"ip": "192.168.1.100", "status": "up"}
        )

        host = db.execute_one("SELECT * FROM hosts WHERE id = ?", (host_id,))
        assert host["scope_status"] == "in_scope"

    def test_out_of_scope_host_marked(self, engagement_with_cidr_scope):
        """Out-of-scope host is marked correctly."""
        eng_id, db = engagement_with_cidr_scope

        manager = HostManager()

        # Out-of-scope host
        host_id = manager.add_or_update_host(
            engagement_id=eng_id, host_data={"ip": "10.0.0.50", "status": "up"}
        )

        host = db.execute_one("SELECT * FROM hosts WHERE id = ?", (host_id,))
        assert host["scope_status"] == "out_of_scope"

    def test_host_unknown_when_no_scope(self, scope_engagement):
        """Host gets 'unknown' status when no scope is defined."""
        eng_id, db = scope_engagement

        manager = HostManager()

        host_id = manager.add_or_update_host(
            engagement_id=eng_id, host_data={"ip": "192.168.1.100", "status": "up"}
        )

        host = db.execute_one("SELECT * FROM hosts WHERE id = ?", (host_id,))
        assert host["scope_status"] == "unknown"

    def test_revalidate_scope_status(self, scope_engagement):
        """Revalidating scope updates all host statuses."""
        eng_id, db = scope_engagement

        manager = HostManager()

        # Create hosts first (no scope defined, so all will be 'unknown')
        host1_id = manager.add_or_update_host(
            eng_id, {"ip": "192.168.1.10", "status": "up"}
        )
        host2_id = manager.add_or_update_host(
            eng_id, {"ip": "192.168.1.20", "status": "up"}
        )
        host3_id = manager.add_or_update_host(
            eng_id, {"ip": "10.0.0.50", "status": "up"}
        )

        # Verify all are 'unknown'
        hosts = db.execute("SELECT * FROM hosts WHERE engagement_id = ?", (eng_id,))
        for h in hosts:
            assert h["scope_status"] == "unknown"

        # Now add scope
        db.insert(
            "engagement_scope",
            {
                "engagement_id": eng_id,
                "scope_type": "cidr",
                "value": "192.168.1.0/24",
                "is_excluded": False,
            },
        )

        # Revalidate
        result = manager.revalidate_scope_status(eng_id)

        assert result["updated"] == 3
        assert result["in_scope"] == 2
        assert result["out_of_scope"] == 1

        # Verify updated statuses
        host1 = db.execute_one("SELECT * FROM hosts WHERE id = ?", (host1_id,))
        assert host1["scope_status"] == "in_scope"

        host3 = db.execute_one("SELECT * FROM hosts WHERE id = ?", (host3_id,))
        assert host3["scope_status"] == "out_of_scope"


# ===== ENQUEUE_JOB INTEGRATION TESTS =====


class TestEnqueueJobScopeIntegration:
    """Test enqueue_job scope validation integration."""

    def test_enqueue_job_block_mode_raises(
        self, engagement_with_cidr_scope, monkeypatch
    ):
        """enqueue_job raises ScopeViolationError in block mode."""
        eng_id, db = engagement_with_cidr_scope
        monkeypatch.setattr("souleyez.auth.get_current_user", lambda: None)

        from souleyez.engine.background import enqueue_job, _ensure_dirs

        _ensure_dirs()

        # Should raise for out-of-scope target
        with pytest.raises(ScopeViolationError) as excinfo:
            enqueue_job(
                tool="nmap",
                target="10.0.0.50",  # Out of scope
                args=["-sS"],
                engagement_id=eng_id,
                skip_scope_check=False,
            )

        assert "out of scope" in str(excinfo.value).lower()

    def test_enqueue_job_in_scope_succeeds(
        self, engagement_with_cidr_scope, monkeypatch
    ):
        """enqueue_job succeeds for in-scope targets."""
        eng_id, db = engagement_with_cidr_scope
        monkeypatch.setattr("souleyez.auth.get_current_user", lambda: None)

        from souleyez.engine.background import enqueue_job, _ensure_dirs

        _ensure_dirs()

        # Should succeed for in-scope target
        job_id = enqueue_job(
            tool="nmap",
            target="192.168.1.100",  # In scope
            args=["-sS"],
            engagement_id=eng_id,
            skip_scope_check=False,
        )

        assert job_id is not None
        assert isinstance(job_id, int)

    def test_enqueue_job_warn_mode_allows(
        self, engagement_with_domain_scope, monkeypatch
    ):
        """enqueue_job allows out-of-scope in warn mode but adds warning."""
        eng_id, db = engagement_with_domain_scope
        monkeypatch.setattr("souleyez.auth.get_current_user", lambda: None)

        from souleyez.engine.background import enqueue_job, get_job, _ensure_dirs

        _ensure_dirs()

        # Should allow but warn for out-of-scope target
        job_id = enqueue_job(
            tool="nmap",
            target="other.com",  # Out of scope
            args=["-sS"],
            engagement_id=eng_id,
            skip_scope_check=False,
        )

        assert job_id is not None

        # Check warning was added
        job = get_job(job_id)
        metadata = job.get("metadata", {})
        warnings = metadata.get("warnings", [])
        assert len(warnings) > 0
        assert any("scope" in w.lower() for w in warnings)

    def test_enqueue_job_skip_scope_check(
        self, engagement_with_cidr_scope, monkeypatch
    ):
        """enqueue_job skips validation when skip_scope_check=True."""
        eng_id, db = engagement_with_cidr_scope
        monkeypatch.setattr("souleyez.auth.get_current_user", lambda: None)

        from souleyez.engine.background import enqueue_job, _ensure_dirs

        _ensure_dirs()

        # Should succeed even for out-of-scope because skip_scope_check=True
        job_id = enqueue_job(
            tool="nmap",
            target="10.0.0.50",  # Normally out of scope
            args=["-sS"],
            engagement_id=eng_id,
            skip_scope_check=True,
        )

        assert job_id is not None

    def test_enqueue_job_no_scope_allows_all(self, scope_engagement, monkeypatch):
        """enqueue_job allows all targets when no scope defined."""
        eng_id, db = scope_engagement
        monkeypatch.setattr("souleyez.auth.get_current_user", lambda: None)

        from souleyez.engine.background import enqueue_job, _ensure_dirs

        _ensure_dirs()

        # Any target should be allowed
        job_id = enqueue_job(
            tool="nmap",
            target="any.random.target",
            args=["-sS"],
            engagement_id=eng_id,
            skip_scope_check=False,
        )

        assert job_id is not None

    def test_enqueue_job_logs_validation(self, engagement_with_cidr_scope, monkeypatch):
        """enqueue_job logs scope validation to audit trail."""
        eng_id, db = engagement_with_cidr_scope
        monkeypatch.setattr("souleyez.auth.get_current_user", lambda: None)

        from souleyez.engine.background import enqueue_job, _ensure_dirs

        _ensure_dirs()

        # Enqueue in-scope target
        job_id = enqueue_job(
            tool="nmap",
            target="192.168.1.100",
            args=["-sS"],
            engagement_id=eng_id,
            skip_scope_check=False,
        )

        # Check audit log
        log_entries = db.execute(
            "SELECT * FROM scope_validation_log WHERE job_id = ?", (job_id,)
        )

        assert len(log_entries) == 1
        assert log_entries[0]["target"] == "192.168.1.100"
        assert log_entries[0]["validation_result"] == "in_scope"
        assert log_entries[0]["action_taken"] == "allowed"


# ===== ENFORCEMENT MODE OFF TESTS =====


class TestEnforcementOff:
    """Test that enforcement='off' allows all targets."""

    def test_off_mode_allows_out_of_scope(
        self, engagement_with_cidr_scope, monkeypatch
    ):
        """enforcement='off' allows out-of-scope targets without warnings."""
        eng_id, db = engagement_with_cidr_scope
        monkeypatch.setattr("souleyez.auth.get_current_user", lambda: None)

        # Set enforcement to 'off'
        db.execute(
            "UPDATE engagements SET scope_enforcement = ? WHERE id = ?", ("off", eng_id)
        )

        from souleyez.engine.background import enqueue_job, get_job, _ensure_dirs

        _ensure_dirs()

        job_id = enqueue_job(
            tool="nmap",
            target="10.0.0.50",  # Out of scope but should be allowed
            args=["-sS"],
            engagement_id=eng_id,
            skip_scope_check=False,
        )

        assert job_id is not None

        # Job should have been created without being blocked
        job = get_job(job_id)
        assert job is not None


# ===== URL TARGET TESTS =====


class TestURLTargetValidation:
    """Test scope validation with URL targets."""

    def test_url_host_extraction(self, engagement_with_domain_scope):
        """URL targets have host extracted for validation."""
        eng_id, db = engagement_with_domain_scope

        validator = ScopeValidator(eng_id)

        # URL with in-scope domain
        result = validator.validate_target("https://app.example.com/path")
        assert result.is_in_scope is True

        # URL with out-of-scope domain
        result = validator.validate_target("https://other.com/path")
        assert result.is_in_scope is False

    def test_url_with_port(self, engagement_with_domain_scope):
        """URL with port is validated correctly."""
        eng_id, db = engagement_with_domain_scope

        validator = ScopeValidator(eng_id)

        result = validator.validate_target("http://app.example.com:8080/api")
        assert result.is_in_scope is True


# ===== EDGE CASES =====


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_target(self, engagement_with_cidr_scope):
        """Empty target is rejected."""
        eng_id, db = engagement_with_cidr_scope

        validator = ScopeValidator(eng_id)

        result = validator.validate_target("")
        assert result.is_in_scope is False
        assert "Empty" in result.reason

    def test_whitespace_target(self, engagement_with_cidr_scope):
        """Whitespace-only target is rejected."""
        eng_id, db = engagement_with_cidr_scope

        validator = ScopeValidator(eng_id)

        result = validator.validate_target("   ")
        assert result.is_in_scope is False

    def test_invalid_ip_as_hostname(self, engagement_with_domain_scope):
        """Invalid IP-like strings are treated as hostnames."""
        eng_id, db = engagement_with_domain_scope

        # Add a hostname scope entry
        db.insert(
            "engagement_scope",
            {
                "engagement_id": eng_id,
                "scope_type": "hostname",
                "value": "999.999.999.999",  # Invalid IP treated as hostname
                "is_excluded": False,
            },
        )

        # Create new validator to pick up the new entry
        validator = ScopeValidator(eng_id)

        # This would fail as IP but should match as hostname
        result = validator.validate_target("999.999.999.999")
        assert result.is_in_scope is True

    def test_duplicate_scope_entry_rejected(self, scope_engagement, monkeypatch):
        """Adding duplicate scope entry raises error."""
        eng_id, db = scope_engagement
        monkeypatch.setattr("souleyez.auth.get_current_user", lambda: None)

        manager = ScopeManager()

        # First entry
        manager.add_scope(
            engagement_id=eng_id, scope_type="cidr", value="192.168.1.0/24"
        )

        # Duplicate should fail (unique constraint)
        with pytest.raises(Exception):
            manager.add_scope(
                engagement_id=eng_id, scope_type="cidr", value="192.168.1.0/24"
            )


# ===== RUN TESTS =====

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
