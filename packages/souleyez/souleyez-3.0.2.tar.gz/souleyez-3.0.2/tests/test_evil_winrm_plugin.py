#!/usr/bin/env python3
"""Tests for Evil-WinRM plugin."""
import pytest


class TestEvilWinRMPlugin:
    """Test Evil-WinRM plugin functionality."""

    @pytest.fixture
    def plugin(self):
        """Get Evil-WinRM plugin instance."""
        from souleyez.plugins.evil_winrm import plugin

        return plugin

    def test_plugin_name(self, plugin):
        """Plugin should have correct name."""
        assert plugin.name == "Evil-WinRM"

    def test_plugin_tool(self, plugin):
        """Plugin should have correct tool identifier."""
        assert plugin.tool == "evil_winrm"

    def test_plugin_category(self, plugin):
        """Plugin should be in lateral_movement category."""
        assert plugin.category == "lateral_movement"

    def test_help_has_required_fields(self, plugin):
        """HELP dict should have required fields."""
        required_fields = [
            "name",
            "description",
            "usage",
            "examples",
            "flags",
            "presets",
        ]
        for field in required_fields:
            assert field in plugin.HELP, f"Missing required field: {field}"

    def test_build_command_basic(self, plugin):
        """build_command should create valid command."""
        result = plugin.build_command("192.168.1.10", ["-u", "admin", "-p", "pass"])
        assert result is not None
        assert "cmd" in result
        assert "timeout" in result
        assert result["cmd"][0] == "evil-winrm"
        assert "-i" in result["cmd"]
        assert "192.168.1.10" in result["cmd"]

    def test_build_command_with_hash(self, plugin):
        """build_command should handle pass-the-hash."""
        result = plugin.build_command(
            "192.168.1.10", ["-u", "admin", "-H", "aad3b435:31d6cfe0"]
        )
        assert "-H" in result["cmd"]
        assert "aad3b435:31d6cfe0" in result["cmd"]

    def test_build_command_with_ssl(self, plugin):
        """build_command should handle SSL flag."""
        result = plugin.build_command(
            "192.168.1.10", ["-u", "admin", "-p", "pass", "-s"]
        )
        assert "-s" in result["cmd"]

    def test_build_command_with_command(self, plugin):
        """build_command should handle command execution."""
        result = plugin.build_command(
            "192.168.1.10", ["-u", "admin", "-p", "pass", "-c", "whoami"]
        )
        assert "-c" in result["cmd"]
        assert "whoami" in result["cmd"]

    def test_presets_exist(self, plugin):
        """Plugin should have presets defined."""
        assert len(plugin.HELP["presets"]) > 0

    def test_preset_categories_exist(self, plugin):
        """Plugin should have preset categories."""
        assert "preset_categories" in plugin.HELP
        assert "authentication" in plugin.HELP["preset_categories"]
        assert "command_execution" in plugin.HELP["preset_categories"]


class TestEvilWinRMPresets:
    """Test Evil-WinRM preset configurations."""

    @pytest.fixture
    def presets(self):
        """Get presets from plugin."""
        from souleyez.plugins.evil_winrm import HELP

        return HELP["presets"]

    def test_password_auth_preset(self, presets):
        """Password Auth preset should exist."""
        preset = next((p for p in presets if p["name"] == "Password Auth"), None)
        assert preset is not None
        assert "-u" in preset["args"]
        assert "-p" in preset["args"]

    def test_pass_the_hash_preset(self, presets):
        """Pass-the-Hash preset should exist."""
        preset = next((p for p in presets if p["name"] == "Pass-the-Hash"), None)
        assert preset is not None
        assert "-H" in preset["args"]

    def test_whoami_preset(self, presets):
        """Whoami preset should exist."""
        preset = next((p for p in presets if p["name"] == "Whoami"), None)
        assert preset is not None
        assert "-c" in preset["args"]
        assert "whoami" in " ".join(preset["args"])
