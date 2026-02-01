"""
Tests for souleyez.config - Configuration management

Simple tests for config file operations.
"""

import pytest
import json
from pathlib import Path


@pytest.fixture
def temp_config(tmp_path, monkeypatch):
    """Use temporary config file and database."""
    config_file = tmp_path / "config.json"
    monkeypatch.setattr("souleyez.config.CONFIG_PATH", config_file)

    # Also set up temp database to avoid conflicts with production db
    db_path = tmp_path / "test.db"
    import souleyez.storage.database as db_module

    db_module._db = None  # Reset singleton

    # Monkeypatch DB_PATH to use temp path
    monkeypatch.setattr("souleyez.storage.database.DB_PATH", db_path)

    return config_file


class TestConfigBasics:
    """Test basic config operations."""

    def test_read_config_creates_default(self, temp_config):
        """Test that reading config creates default if not exists."""
        from souleyez import config

        cfg = config.read_config()

        assert cfg is not None
        assert "plugins" in cfg
        assert "settings" in cfg
        assert temp_config.exists()

    def test_default_config_structure(self, temp_config):
        """Test default config has correct structure."""
        from souleyez import config

        cfg = config.read_config()

        assert "enabled" in cfg["plugins"]
        assert "disabled" in cfg["plugins"]
        assert isinstance(cfg["plugins"]["enabled"], list)
        assert isinstance(cfg["plugins"]["disabled"], list)

    def test_write_config(self, temp_config):
        """Test writing config to file."""
        from souleyez import config

        test_config = {
            "plugins": {"enabled": ["test"], "disabled": []},
            "settings": {"threads": 5},
        }

        config.write_config(test_config)

        assert temp_config.exists()
        saved = json.loads(temp_config.read_text())
        assert "test" in saved["plugins"]["enabled"]

    def test_read_written_config(self, temp_config):
        """Test reading back written config."""
        from souleyez import config

        original = {
            "plugins": {"enabled": ["plugin1"], "disabled": ["plugin2"]},
            "settings": {"threads": 20},
        }

        config.write_config(original)
        loaded = config.read_config()

        assert "plugin1" in loaded["plugins"]["enabled"]
        assert "plugin2" in loaded["plugins"]["disabled"]


class TestPluginManagement:
    """Test plugin enable/disable functionality."""

    def test_enable_plugin(self, temp_config):
        """Test enabling a plugin."""
        from souleyez import config

        config.enable_plugin("testplugin")

        enabled, disabled = config.list_plugins_config()
        assert "testplugin" in enabled
        assert "testplugin" not in disabled

    def test_disable_plugin(self, temp_config):
        """Test disabling a plugin."""
        from souleyez import config

        config.disable_plugin("testplugin")

        enabled, disabled = config.list_plugins_config()
        assert "testplugin" not in enabled
        assert "testplugin" in disabled

    def test_enable_then_disable(self, temp_config):
        """Test enabling then disabling a plugin."""
        from souleyez import config

        config.enable_plugin("myplugin")
        enabled, _ = config.list_plugins_config()
        assert "myplugin" in enabled

        config.disable_plugin("myplugin")
        enabled, disabled = config.list_plugins_config()
        assert "myplugin" not in enabled
        assert "myplugin" in disabled

    def test_enable_already_enabled(self, temp_config):
        """Test enabling an already enabled plugin."""
        from souleyez import config

        config.enable_plugin("plugin1")
        config.enable_plugin("plugin1")  # Enable again

        enabled, _ = config.list_plugins_config()
        # Should only appear once
        assert enabled.count("plugin1") == 1

    def test_disable_already_disabled(self, temp_config):
        """Test disabling an already disabled plugin."""
        from souleyez import config

        config.disable_plugin("plugin1")
        config.disable_plugin("plugin1")  # Disable again

        _, disabled = config.list_plugins_config()
        # Should only appear once
        assert disabled.count("plugin1") == 1

    def test_plugin_names_lowercase(self, temp_config):
        """Test that plugin names are converted to lowercase."""
        from souleyez import config

        config.enable_plugin("MyPlugin")
        enabled, _ = config.list_plugins_config()

        assert "myplugin" in enabled
        assert "MyPlugin" not in enabled

    def test_list_plugins_empty(self, temp_config):
        """Test listing plugins when none configured."""
        from souleyez import config

        enabled, disabled = config.list_plugins_config()

        assert isinstance(enabled, list)
        assert isinstance(disabled, list)

    def test_reset_plugins(self, temp_config):
        """Test resetting all plugins."""
        from souleyez import config

        # Add some plugins
        config.enable_plugin("plugin1")
        config.disable_plugin("plugin2")

        # Reset
        config.reset_plugins()

        enabled, disabled = config.list_plugins_config()
        assert len(enabled) == 0
        assert len(disabled) == 0


class TestConfigNormalization:
    """Test config normalization and backward compatibility."""

    def test_normalize_new_format(self, temp_config):
        """Test normalizing new format config."""
        from souleyez.config import _normalize

        new_format = {
            "plugins": {"enabled": ["p1"], "disabled": ["p2"]},
            "settings": {"threads": 10},
        }

        normalized = _normalize(new_format)

        assert "plugins" in normalized
        assert "settings" in normalized

    def test_normalize_old_format(self, temp_config):
        """Test normalizing old flat format."""
        from souleyez.config import _normalize

        old_format = {"enabled": ["p1"], "disabled": ["p2"]}

        normalized = _normalize(old_format)

        assert "plugins" in normalized
        assert "p1" in normalized["plugins"]["enabled"]
        assert "p2" in normalized["plugins"]["disabled"]

    def test_normalize_empty_dict(self, temp_config):
        """Test normalizing empty dict."""
        from souleyez.config import _normalize

        normalized = _normalize({})

        assert "plugins" in normalized
        assert "settings" in normalized

    def test_normalize_invalid_type(self, temp_config):
        """Test normalizing invalid type returns default."""
        from souleyez.config import _normalize

        normalized = _normalize("invalid")

        assert isinstance(normalized, dict)
        assert "plugins" in normalized

    def test_normalize_adds_missing_keys(self, temp_config):
        """Test that normalize adds missing keys."""
        from souleyez.config import _normalize

        incomplete = {"plugins": {}}

        normalized = _normalize(incomplete)

        assert "enabled" in normalized["plugins"]
        assert "disabled" in normalized["plugins"]


class TestConfigCorruption:
    """Test handling of corrupted config files."""

    def test_corrupted_json_auto_repairs(self, temp_config):
        """Test that corrupted JSON is auto-repaired."""
        from souleyez import config

        # Write corrupted JSON
        temp_config.parent.mkdir(parents=True, exist_ok=True)
        temp_config.write_text("{ invalid json }")

        # Should auto-repair
        cfg = config.read_config()

        assert cfg is not None
        assert "plugins" in cfg

    def test_missing_file_creates_default(self, temp_config):
        """Test that missing file creates default."""
        from souleyez import config

        # Ensure file doesn't exist
        if temp_config.exists():
            temp_config.unlink()

        cfg = config.read_config()

        assert cfg is not None
        assert temp_config.exists()


class TestConfigEdgeCases:
    """Test edge cases."""

    def test_multiple_plugins(self, temp_config):
        """Test enabling multiple plugins."""
        from souleyez import config

        plugins = ["plugin1", "plugin2", "plugin3"]

        for p in plugins:
            config.enable_plugin(p)

        enabled, _ = config.list_plugins_config()

        for p in plugins:
            assert p in enabled

    def test_move_plugin_from_disabled_to_enabled(self, temp_config):
        """Test moving plugin from disabled to enabled list."""
        from souleyez import config

        # First disable
        config.disable_plugin("mover")
        _, disabled = config.list_plugins_config()
        assert "mover" in disabled

        # Then enable (should remove from disabled)
        config.enable_plugin("mover")
        enabled, disabled = config.list_plugins_config()

        assert "mover" in enabled
        assert "mover" not in disabled


class TestDatabaseOperations:
    """Test database operations from database.py."""

    def test_database_initialization(self, temp_config):
        """Test database initializes correctly."""
        from souleyez.storage.database import Database

        db = Database()
        assert db is not None
        assert db.db_path is not None

    def test_database_insert(self, temp_config):
        """Test database insert operation."""
        from souleyez.storage.database import get_db
        import time

        db = get_db()

        # Insert into engagements table
        eng_id = db.insert(
            "engagements",
            {"name": f"test_engagement_{time.time()}", "description": "test"},
        )

        assert isinstance(eng_id, int)
        assert eng_id > 0

    def test_database_execute_one(self, temp_config):
        """Test execute_one returns single row."""
        from souleyez.storage.database import get_db
        import time

        db = get_db()
        name = f"find_me_{time.time()}"
        db.insert("engagements", {"name": name})

        result = db.execute_one("SELECT * FROM engagements WHERE name = ?", (name,))

        assert result is not None
        assert result["name"] == name

    def test_database_execute_returns_list(self, temp_config):
        """Test execute returns list of rows."""
        from souleyez.storage.database import get_db
        import time

        db = get_db()
        t = time.time()
        db.insert("engagements", {"name": f"eng1_{t}"})
        db.insert("engagements", {"name": f"eng2_{t}"})

        results = db.execute("SELECT * FROM engagements")

        assert isinstance(results, list)
        assert len(results) >= 2

    def test_database_execute_with_params(self, temp_config):
        """Test execute with parameters."""
        from souleyez.storage.database import get_db
        import time

        db = get_db()
        name = f"param_test_{time.time()}"
        db.insert("engagements", {"name": name})

        results = db.execute("SELECT * FROM engagements WHERE name = ?", (name,))

        assert len(results) >= 1

    def test_database_update(self, temp_config):
        """Test database update operation."""
        from souleyez.storage.database import get_db
        import time

        db = get_db()
        eng_id = db.insert("engagements", {"name": f"original_{time.time()}"})

        updated_name = f"updated_{time.time()}"
        db.execute(
            "UPDATE engagements SET name = ? WHERE id = ?", (updated_name, eng_id)
        )

        result = db.execute_one("SELECT * FROM engagements WHERE id = ?", (eng_id,))

        assert result["name"] == updated_name

    def test_database_delete(self, temp_config):
        """Test database delete operation."""
        from souleyez.storage.database import get_db
        import time

        db = get_db()
        eng_id = db.insert("engagements", {"name": f"to_delete_{time.time()}"})

        db.execute("DELETE FROM engagements WHERE id = ?", (eng_id,))

        result = db.execute_one("SELECT * FROM engagements WHERE id = ?", (eng_id,))

        assert result is None

    def test_database_transaction(self, temp_config):
        """Test database handles transactions."""
        from souleyez.storage.database import get_db
        import time

        db = get_db()

        t = time.time()
        # Multiple inserts should all succeed
        for i in range(5):
            db.insert("engagements", {"name": f"trans_{t}_{i}"})

        results = db.execute(f"SELECT * FROM engagements WHERE name LIKE 'trans_{t}_%'")

        assert len(results) == 5

    def test_database_get_singleton(self, temp_config):
        """Test database singleton pattern."""
        from souleyez.storage.database import get_db

        db1 = get_db()
        db2 = get_db()

        # Should be same instance
        assert db1 is db2

    def test_database_execute_none_result(self, temp_config):
        """Test execute_one with no results."""
        from souleyez.storage.database import get_db

        db = get_db()

        result = db.execute_one("SELECT * FROM engagements WHERE id = ?", (99999,))

        assert result is None

    def test_database_creates_tables_on_init(self, temp_config):
        """Test that database creates tables on initialization."""
        from souleyez.storage.database import Database
        import os

        db_path = temp_config.parent / "new_test.db"

        # Create database - should create tables
        db = Database(str(db_path))

        # Should be able to query tables
        result = db.execute("SELECT name FROM sqlite_master WHERE type='table'")

        tables = [r["name"] for r in result]
        assert "engagements" in tables

    def test_database_with_invalid_path(self, temp_config):
        """Test database handles invalid path gracefully."""
        from souleyez.storage.database import Database

        # Database should create missing directories
        db_path = temp_config.parent / "deep" / "nested" / "path" / "test.db"

        db = Database(str(db_path))
        assert db is not None
        assert db.db_path == str(db_path)

    def test_database_execute_with_no_params(self, temp_config):
        """Test execute without parameters."""
        from souleyez.storage.database import get_db

        db = get_db()

        # Query without parameters
        results = db.execute("SELECT * FROM engagements")

        assert isinstance(results, list)
