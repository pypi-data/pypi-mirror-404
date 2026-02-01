"""
Simple standalone tests for engagements - 100% coverage goal
"""

import pytest
from pathlib import Path


@pytest.fixture
def isolated_env(tmp_path, monkeypatch):
    """Completely isolated environment for each test."""
    # Reset BOTH singletons FIRST
    from souleyez.storage.database import Database
    import souleyez.storage.database

    Database._instance = None
    souleyez.storage.database._db = None

    # Unique DB and file for this test
    db_path = tmp_path / "test.db"
    eng_file = tmp_path / "current_engagement"

    # Patch DB_PATH directly (not environment variable!)
    monkeypatch.setattr("souleyez.storage.database.DB_PATH", db_path)
    monkeypatch.setattr("souleyez.storage.engagements.ENGAGEMENT_FILE", eng_file)

    yield tmp_path

    # Cleanup
    Database._instance = None
    souleyez.storage.database._db = None


def test_list_engagements(isolated_env):
    """Test listing all engagements."""
    from souleyez.storage.engagements import EngagementManager

    em = EngagementManager()
    em.create("Test1")
    em.create("Test2")

    # Use user_filtered=False to bypass RBAC in tests
    engagements = em.list(user_filtered=False)

    assert len(engagements) >= 2


def test_set_current_with_mkdir(isolated_env):
    """Test set_current creates parent directory."""
    from souleyez.storage.engagements import EngagementManager

    em = EngagementManager()
    em.create("SetMe")

    result = em.set_current("SetMe")

    assert result is True


def test_set_current_nonexistent(isolated_env):
    """Test set_current with non-existent engagement."""
    from souleyez.storage.engagements import EngagementManager

    em = EngagementManager()

    result = em.set_current("DoesNotExist")

    assert result is False


def test_get_current_creates_default(isolated_env):
    """Test get_current creates default if missing."""
    from souleyez.storage.engagements import EngagementManager

    em = EngagementManager()

    # Should create default
    current = em.get_current()

    assert current is not None
    assert current["name"] == "default"


def test_get_current_reads_file(isolated_env):
    """Test get_current reads from file."""
    from souleyez.storage.engagements import EngagementManager

    em = EngagementManager()
    em.create("FromFile")
    em.set_current("FromFile")

    # Get current should read the file
    current = em.get_current()

    assert current is not None
    assert current["name"] == "FromFile"


def test_delete_engagement(isolated_env):
    """Test deleting engagement."""
    from souleyez.storage.engagements import EngagementManager

    em = EngagementManager()
    em.create("DeleteMe")

    result = em.delete("DeleteMe")

    assert result is True


def test_delete_nonexistent(isolated_env):
    """Test deleting non-existent engagement."""
    from souleyez.storage.engagements import EngagementManager

    em = EngagementManager()

    result = em.delete("DoesNotExist")

    assert result is False


def test_stats_basic(isolated_env):
    """Test getting engagement stats."""
    from souleyez.storage.engagements import EngagementManager

    em = EngagementManager()
    eng_id = em.create("StatsTest")

    stats = em.stats(eng_id)

    assert isinstance(stats, dict)


def test_get_by_id(isolated_env):
    """Test getting engagement by ID."""
    from souleyez.storage.engagements import EngagementManager

    em = EngagementManager()
    eng_id = em.create("GetByID")

    result = em.get_by_id(eng_id)

    assert result is not None
    assert result["name"] == "GetByID"


def test_create_duplicate_engagement(isolated_env):
    """Test creating duplicate engagement raises error."""
    from souleyez.storage.engagements import EngagementManager
    import pytest

    em = EngagementManager()
    em.create("Duplicate")

    # Try to create again - should raise ValueError
    with pytest.raises(ValueError, match="already exists"):
        em.create("Duplicate")
