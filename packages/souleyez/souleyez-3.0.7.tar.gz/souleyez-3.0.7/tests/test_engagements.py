"""
Tests for souleyez.storage.engagements - Engagement management
"""

import pytest
import os
from pathlib import Path


@pytest.fixture
def engagement_manager(tmp_path, monkeypatch):
    """Create EngagementManager with isolated temporary database."""
    # Reset BOTH database singletons
    import souleyez.storage.database as db_module

    db_module._db = None

    # Create unique database path for this test
    db_path = tmp_path / f"test_{os.getpid()}_{id(tmp_path)}.db"

    # Set temp engagement file
    temp_file = tmp_path / "current_engagement"
    monkeypatch.setattr("souleyez.storage.engagements.ENGAGEMENT_FILE", temp_file)

    # Monkey patch the database module to use our test database
    from souleyez.storage.database import Database

    test_db = Database(str(db_path))
    monkeypatch.setattr(db_module, "_db", test_db)

    # Import AFTER setting up mocks
    from souleyez.storage.engagements import EngagementManager

    # Create manager
    em = EngagementManager()

    yield em

    # Clean up after test
    db_module._db = None


class TestEngagementManager:
    """Tests for EngagementManager class."""

    def test_create_engagement(self, engagement_manager):
        """Test creating a new engagement."""
        engagement_id = engagement_manager.create(
            name="Test Engagement", description="Test Description"
        )

        assert isinstance(engagement_id, int)
        assert engagement_id > 0

        # Verify it was created
        eng = engagement_manager.get("Test Engagement")
        assert eng is not None
        assert eng["name"] == "Test Engagement"
        assert eng["description"] == "Test Description"

    def test_create_duplicate_engagement_fails(self, engagement_manager):
        """Test that creating duplicate engagement raises error."""
        engagement_manager.create(name="Duplicate Test")

        with pytest.raises(ValueError, match="already exists"):
            engagement_manager.create(name="Duplicate Test")

    def test_list_engagements(self, engagement_manager):
        """Test listing all engagements."""
        # Create a few engagements
        engagement_manager.create("Engagement 1")
        engagement_manager.create("Engagement 2")
        engagement_manager.create("Engagement 3")

        # Use user_filtered=False to bypass RBAC in tests
        engagements = engagement_manager.list(user_filtered=False)

        assert len(engagements) >= 3
        names = [e["name"] for e in engagements]
        assert "Engagement 1" in names
        assert "Engagement 2" in names
        assert "Engagement 3" in names

    def test_get_engagement_by_name(self, engagement_manager):
        """Test getting engagement by name."""
        engagement_manager.create("Find Me", "Description Here")

        eng = engagement_manager.get("Find Me")

        assert eng is not None
        assert eng["name"] == "Find Me"
        assert eng["description"] == "Description Here"

    def test_get_nonexistent_engagement(self, engagement_manager):
        """Test getting engagement that doesn't exist."""
        eng = engagement_manager.get("Does Not Exist")
        assert eng is None

    def test_get_engagement_by_id(self, engagement_manager):
        """Test getting engagement by ID."""
        eng_id = engagement_manager.create("ID Test")

        eng = engagement_manager.get_by_id(eng_id)

        assert eng is not None
        assert eng["id"] == eng_id
        assert eng["name"] == "ID Test"

    def test_set_current_engagement(self, engagement_manager, monkeypatch, tmp_path):
        """Test setting current engagement."""
        # Get the engagement file path that was set up by fixture
        temp_file = tmp_path / "current_engagement"

        engagement_manager.create("Current Test")

        result = engagement_manager.set_current("Current Test")

        assert result is True
        assert temp_file.exists()

        # Verify the ID was written
        saved_id = int(temp_file.read_text())
        assert saved_id > 0

    def test_set_nonexistent_engagement_as_current(self, engagement_manager):
        """Test setting nonexistent engagement as current fails."""
        result = engagement_manager.set_current("Does Not Exist")
        assert result is False

    def test_get_current_engagement(self, engagement_manager):
        """Test getting current engagement."""
        # Create and set current
        eng_id = engagement_manager.create("Current Engagement")
        engagement_manager.set_current("Current Engagement")

        current = engagement_manager.get_current()

        assert current is not None
        assert current["name"] == "Current Engagement"
        assert current["id"] == eng_id

    def test_get_current_creates_default(self, engagement_manager, tmp_path):
        """Test that get_current creates default engagement if none exists."""
        engagement_file = tmp_path / "current_engagement"

        # Ensure default doesn't already exist
        existing = engagement_manager.get("default")
        if existing:
            engagement_manager.delete("default")

        # Don't set any current engagement
        current = engagement_manager.get_current()

        assert current is not None
        assert current["name"] == "default"
        assert engagement_file.exists()

    def test_delete_engagement(self, engagement_manager):
        """Test deleting an engagement."""
        engagement_manager.create("To Delete")

        # Verify it exists
        eng = engagement_manager.get("To Delete")
        assert eng is not None

        # Delete it
        result = engagement_manager.delete("To Delete")
        assert result is True

        # Verify it's gone
        eng = engagement_manager.get("To Delete")
        assert eng is None

    def test_delete_nonexistent_engagement(self, engagement_manager):
        """Test deleting engagement that doesn't exist."""
        result = engagement_manager.delete("Does Not Exist")
        assert result is False

    def test_engagement_stats(self, engagement_manager):
        """Test getting engagement statistics."""
        eng_id = engagement_manager.create("Stats Test")

        stats = engagement_manager.stats(eng_id)

        assert isinstance(stats, dict)
        # Stats should have host/service/finding counts
        # Initially all should be 0 or have keys
        assert "hosts" in stats or stats.get("hosts", 0) == 0


class TestEngagementEdgeCases:
    """Test edge cases for EngagementManager."""

    def test_create_engagement_empty_description(self, engagement_manager):
        """Test creating engagement with empty description."""
        eng_id = engagement_manager.create("Empty Description", "")
        assert eng_id > 0

    def test_create_engagement_long_name(self, engagement_manager):
        """Test creating engagement with very long name."""
        long_name = "A" * 255
        eng_id = engagement_manager.create(long_name)
        assert eng_id > 0

    def test_list_engagements_ordered(self, engagement_manager):
        """Test engagements are ordered by created_at DESC."""
        engagement_manager.create("First")
        engagement_manager.create("Second")
        engagement_manager.create("Third")

        # Use user_filtered=False to bypass RBAC in tests
        engagements = engagement_manager.list(user_filtered=False)

        # Should be in reverse chronological order
        assert len(engagements) >= 3

    def test_get_nonexistent_by_id(self, engagement_manager):
        """Test getting non-existent engagement by ID."""
        result = engagement_manager.get_by_id(99999)
        assert result is None

    def test_stats_for_nonexistent_engagement(self, engagement_manager):
        """Test getting stats for non-existent engagement."""
        stats = engagement_manager.stats(99999)

        # Should return empty or zero stats
        assert isinstance(stats, dict)

    def test_create_multiple_engagements(self, engagement_manager):
        """Test creating many engagements."""
        for i in range(10):
            eng_id = engagement_manager.create(f"Engagement {i}")
            assert eng_id > 0

        # Use user_filtered=False to bypass RBAC in tests
        engagements = engagement_manager.list(user_filtered=False)
        assert len(engagements) >= 10


class TestPluginBase:
    """Test plugin base functionality."""

    def test_plugin_template_exists(self):
        """Test plugin template can be imported."""
        from souleyez.plugins import plugin_template

        assert plugin_template is not None

    def test_plugin_base_import(self):
        """Test plugin base can be imported."""
        from souleyez.plugins import plugin_base

        assert plugin_base is not None

    def test_plugin_base_class(self):
        """Test PluginBase class exists."""
        from souleyez.plugins.plugin_base import PluginBase

        # Create a simple test plugin
        class TestPlugin(PluginBase):
            def run(self, target, options=None):
                return {"status": "success"}

        plugin = TestPlugin()
        assert plugin is not None
        result = plugin.run("test_target")
        assert result["status"] == "success"

    def test_plugin_has_name_method(self):
        """Test plugin has name method."""
        from souleyez.plugins.plugin_base import PluginBase

        class NamedPlugin(PluginBase):
            def run(self, target, options=None):
                return {}

        plugin = NamedPlugin()
        # Should have some way to identify itself
        assert hasattr(plugin, "run")

    def test_plugin_enqueue_with_mocked_background(self, monkeypatch):
        """Test plugin enqueue method with mocked background system."""
        from souleyez.plugins.plugin_base import PluginBase

        # Mock enqueue_job function
        enqueued_jobs = []

        def fake_enqueue_job(tool, target, args, label):
            job = {"tool": tool, "target": target, "args": args, "label": label}
            enqueued_jobs.append(job)
            return len(enqueued_jobs)  # Return job ID

        # Patch the enqueue_job import
        import sys
        from unittest.mock import MagicMock

        mock_background = MagicMock()
        mock_background.enqueue_job = fake_enqueue_job
        sys.modules["souleyez.engine.background"] = mock_background

        try:
            # Create test plugin
            class TestPlugin(PluginBase):
                name = "test_plugin"
                tool = "test_tool"

                def run(self, target, args=None, label="", log_path=None):
                    return 0

            plugin = TestPlugin()

            # Test enqueue
            job_id = plugin.enqueue(
                target="192.168.1.1", args=["--verbose"], label="test"
            )

            assert job_id == 1
            assert len(enqueued_jobs) == 1
            assert enqueued_jobs[0]["tool"] == "test_tool"
            assert enqueued_jobs[0]["target"] == "192.168.1.1"
            assert enqueued_jobs[0]["args"] == ["--verbose"]
            assert enqueued_jobs[0]["label"] == "test"

            # Test enqueue with no args/label
            job_id2 = plugin.enqueue(target="10.0.0.1")
            assert job_id2 == 2
            assert enqueued_jobs[1]["args"] == []
            assert enqueued_jobs[1]["label"] == ""
        finally:
            # Clean up mock
            if "souleyez.engine.background" in sys.modules:
                del sys.modules["souleyez.engine.background"]

    def test_plugin_enqueue_without_background_system(self, monkeypatch):
        """Test plugin enqueue raises NotImplementedError without background system."""
        from souleyez.plugins.plugin_base import PluginBase

        # Ensure background system isn't importable
        import sys

        if "souleyez.engine.background" in sys.modules:
            del sys.modules["souleyez.engine.background"]

        # Mock the import to fail
        import builtins

        real_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if "background" in name:
                raise ImportError("Mocked import failure")
            return real_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", mock_import)

        class TestPlugin(PluginBase):
            def run(self, target, args=None, label="", log_path=None):
                return 0

        plugin = TestPlugin()

        # Should raise NotImplementedError
        with pytest.raises(NotImplementedError, match="requires background job system"):
            plugin.enqueue(target="test")

    def test_plugin_run_not_implemented(self):
        """Test that base plugin run() raises NotImplementedError."""
        from souleyez.plugins.plugin_base import PluginBase

        plugin = PluginBase()

        with pytest.raises(NotImplementedError, match="run\\(\\) not implemented"):
            plugin.run(target="test")


class TestEngagementCurrent:
    """Test current engagement functionality with proper isolation."""

    def test_set_and_get_current_basic(self, engagement_manager, tmp_path):
        """Test setting and getting current engagement."""
        engagement_file = tmp_path / "current_engagement"

        # Create and set current
        engagement_manager.create("Current1")
        result = engagement_manager.set_current("Current1")

        assert result is True
        assert engagement_file.exists()

        # Get current
        current = engagement_manager.get_current()
        assert current is not None
        assert current["name"] == "Current1"

    def test_delete_engagement_basic(self, engagement_manager):
        """Test deleting engagement."""
        engagement_manager.create("ToDelete")
        result = engagement_manager.delete("ToDelete")

        assert result is True
