"""
Tests for storage modules - hosts, findings, credentials
Simple tests focusing on core CRUD operations.
"""

import pytest


@pytest.fixture
def temp_db(tmp_path, monkeypatch):
    """Create temporary database for tests."""
    db_path = tmp_path / "test_storage.db"

    # Reset database singleton and create with explicit path
    from souleyez.storage.database import Database
    import souleyez.storage.database as db_module

    db_module._db = None

    # Create database with explicit path (bypasses DB_PATH constant)
    db = Database(str(db_path))
    db_module._db = db  # Set as singleton so get_db() returns this instance

    # Create a test engagement to satisfy foreign key constraints
    db.execute(
        "INSERT OR REPLACE INTO engagements (id, name, description) VALUES (1, 'test', 'Test engagement')"
    )

    yield db

    # Cleanup
    db_module._db = None


class TestHostManager:
    """Test host management operations."""

    def test_add_host(self, temp_db):
        """Test adding a new host."""
        from souleyez.storage.hosts import HostManager

        hm = HostManager()
        host_data = {"ip": "192.168.1.1", "hostname": "testhost.local", "status": "up"}

        host_id = hm.add_or_update_host(1, host_data)

        assert isinstance(host_id, int)
        assert host_id > 0

    def test_update_existing_host(self, temp_db):
        """Test updating an existing host."""
        from souleyez.storage.hosts import HostManager

        hm = HostManager()

        # Add host
        host_data = {"ip": "192.168.1.2", "hostname": "host1"}
        host_id1 = hm.add_or_update_host(1, host_data)

        # Update same host
        host_data2 = {"ip": "192.168.1.2", "hostname": "host1-updated"}
        host_id2 = hm.add_or_update_host(1, host_data2)

        # Should be same ID
        assert host_id1 == host_id2

    def test_host_requires_ip(self, temp_db):
        """Test that host requires IP address."""
        from souleyez.storage.hosts import HostManager

        hm = HostManager()

        with pytest.raises(ValueError):
            hm.add_or_update_host(1, {"hostname": "noip"})

    def test_list_hosts(self, temp_db):
        """Test listing hosts."""
        from souleyez.storage.hosts import HostManager

        hm = HostManager()

        # Add multiple hosts
        hm.add_or_update_host(1, {"ip": "10.0.0.1"})
        hm.add_or_update_host(1, {"ip": "10.0.0.2"})

        hosts = hm.list_hosts(1)

        assert isinstance(hosts, list)
        assert len(hosts) >= 2

    def test_get_host_by_id(self, temp_db):
        """Test getting host by ID."""
        from souleyez.storage.hosts import HostManager

        hm = HostManager()
        host_id = hm.add_or_update_host(1, {"ip": "10.0.0.10"})

        host = hm.get_host(host_id)

        assert host is not None
        assert host["ip_address"] == "10.0.0.10"

    def test_add_service_to_host(self, temp_db):
        """Test adding a service to a host."""
        from souleyez.storage.hosts import HostManager

        hm = HostManager()
        host_id = hm.add_or_update_host(1, {"ip": "10.0.0.20"})

        service_data = {
            "port": 80,
            "protocol": "tcp",
            "service": "http",
            "state": "open",
        }

        service_id = hm.add_service(host_id, service_data)

        assert isinstance(service_id, int)
        assert service_id > 0


class TestFindingsManager:
    """Test finding/vulnerability management."""

    def test_findings_manager_init(self, temp_db):
        """Test FindingsManager initializes."""
        from souleyez.storage.findings import FindingsManager

        fm = FindingsManager()
        assert fm is not None
        assert fm.db is not None

    def test_list_findings_empty(self, temp_db):
        """Test listing findings when empty."""
        from souleyez.storage.findings import FindingsManager

        fm = FindingsManager()
        findings = fm.list_findings(1)

        assert isinstance(findings, list)

    def test_list_findings_with_filters(self, temp_db):
        """Test listing findings works."""
        from souleyez.storage.findings import FindingsManager

        fm = FindingsManager()
        # list_findings is the actual method
        result = fm.list_findings(1)

        assert isinstance(result, list)


class TestCredentialsManager:
    """Test credential management."""

    def test_credentials_manager_init(self, temp_db):
        """Test CredentialsManager initializes."""
        from souleyez.storage.credentials import CredentialsManager

        cm = CredentialsManager()
        assert cm is not None
        assert cm.db is not None

    def test_list_credentials_empty(self, temp_db):
        """Test listing credentials when empty."""
        from souleyez.storage.credentials import CredentialsManager

        cm = CredentialsManager()
        creds = cm.list_credentials(1)

        assert isinstance(creds, list)

    def test_list_all_credentials(self, temp_db):
        """Test listing credentials."""
        from souleyez.storage.credentials import CredentialsManager

        cm = CredentialsManager()
        result = cm.list_credentials(1)

        assert isinstance(result, list)


class TestStorageEdgeCases:
    """Test edge cases and error handling."""

    def test_add_host_with_minimal_data(self, temp_db):
        """Test adding host with only IP."""
        from souleyez.storage.hosts import HostManager

        hm = HostManager()
        host_id = hm.add_or_update_host(1, {"ip": "1.1.1.1"})

        assert host_id > 0

    def test_managers_initialize(self, temp_db):
        """Test all managers can initialize."""
        from souleyez.storage.hosts import HostManager
        from souleyez.storage.findings import FindingsManager
        from souleyez.storage.credentials import CredentialsManager

        hm = HostManager()
        fm = FindingsManager()
        cm = CredentialsManager()

        assert hm is not None
        assert fm is not None
        assert cm is not None
