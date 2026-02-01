"""Tests for the PluginBase class - pushing to 100% coverage."""

import pytest
from souleyez.plugins.plugin_base import PluginBase, Plugin


class TestPluginBase:
    """Test the PluginBase class."""

    def test_default_initialization(self):
        """Test plugin initializes with default values."""
        plugin = PluginBase()
        # Without custom name, uses "unnamed" from class attribute
        assert plugin.name == "unnamed"
        assert plugin.tool == "unnamed"
        assert plugin.category == "misc"

    def test_custom_class_attributes(self):
        """Test plugin with custom class attributes."""

        class CustomPlugin(PluginBase):
            name = "MyPlugin"
            tool = "MyTool"
            category = "recon"

        plugin = CustomPlugin()
        assert plugin.name == "MyPlugin"
        assert plugin.tool == "mytool"  # tool is lowercased
        assert plugin.category == "recon"

    def test_run_not_implemented(self):
        """Test that run() raises NotImplementedError."""
        plugin = PluginBase()
        with pytest.raises(NotImplementedError) as exc_info:
            plugin.run("target")
        assert "PluginBase.run() not implemented" in str(exc_info.value)

    def test_enqueue_without_args(self, monkeypatch):
        """Test enqueue with minimal parameters."""
        plugin = PluginBase()
        plugin.tool = "test_tool"

        # Mock ImportError to test the exception path
        def mock_import(*args, **kwargs):
            raise ImportError("No module named engine.background")

        monkeypatch.setattr("builtins.__import__", mock_import)

        with pytest.raises(NotImplementedError) as exc_info:
            plugin.enqueue("192.168.1.1")
        assert "enqueue() requires background job system" in str(exc_info.value)

    def test_enqueue_with_all_params(self, monkeypatch):
        """Test enqueue with all parameters - happy path."""
        import sys

        plugin = PluginBase()
        plugin.tool = "test_tool"

        # Create a mock module with enqueue_job that returns 42
        class MockBackground:
            @staticmethod
            def enqueue_job(tool, target, args, label=""):
                return 42

        # Ensure the mock is used
        monkeypatch.setitem(sys.modules, "souleyez.engine.background", MockBackground())

        job_id = plugin.enqueue(
            target="192.168.1.1", args=["-v", "-o", "output.txt"], label="test_scan"
        )
        assert job_id == 42

    def test_plugin_alias_exists(self):
        """Test that Plugin alias works."""
        assert Plugin is PluginBase

    def test_help_attribute(self):
        """Test HELP attribute defaults to None."""
        plugin = PluginBase()
        assert plugin.HELP is None

    def test_custom_help_attribute(self):
        """Test plugin with custom HELP."""

        class HelpfulPlugin(PluginBase):
            HELP = {"description": "Does stuff", "usage": "helpfulplugin <target>"}

        plugin = HelpfulPlugin()
        assert plugin.HELP is not None
        assert plugin.HELP["description"] == "Does stuff"


class TestPluginBaseEdgeCases:
    """Test edge cases and error paths."""

    def test_empty_target(self):
        """Test run with empty target string."""
        plugin = PluginBase()
        with pytest.raises(NotImplementedError):
            plugin.run("")

    def test_none_args(self):
        """Test run with None args."""
        plugin = PluginBase()
        with pytest.raises(NotImplementedError):
            plugin.run("target", args=None)

    def test_empty_label(self, monkeypatch):
        """Test enqueue with empty label - should work fine."""
        import sys

        plugin = PluginBase()

        # Create a mock module with enqueue_job that returns 99
        class MockBackground:
            @staticmethod
            def enqueue_job(tool, target, args, label=""):
                return 99

        monkeypatch.setitem(sys.modules, "souleyez.engine.background", MockBackground())
        job_id = plugin.enqueue("target", label="")
        assert job_id == 99

    def test_tool_lowercase_conversion(self):
        """Test that tool attribute is converted to lowercase."""

        class MixedCasePlugin(PluginBase):
            tool = "MyMixedCaseTool"

        plugin = MixedCasePlugin()
        assert plugin.tool == "mymixedcasetool"
