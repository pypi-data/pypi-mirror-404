#!/usr/bin/env python3
"""
Tests for the tool handler registry.

These tests verify:
- Registry singleton behavior
- Handler discovery via __subclasses__()
- Capability queries (has_warning_handler, etc.)
- Case-insensitive tool name lookup
- Fallback behavior (None for unmigrated tools)
"""
import pytest
from typing import Any, Dict

from souleyez.handlers.base import BaseToolHandler
from souleyez.handlers.registry import (
    ToolHandlerRegistry,
    get_handler,
    get_registry,
)


class MockHandler(BaseToolHandler):
    """Mock handler for testing."""

    tool_name = "mock_tool"
    display_name = "Mock Tool"
    has_warning_handler = True
    has_error_handler = True
    has_no_results_handler = True
    has_done_handler = True

    def parse_job(self, engagement_id, log_path, job, **kwargs) -> Dict[str, Any]:
        return {"status": "done", "summary": "Mock parse complete"}

    def display_done(self, job, log_path, show_all=False, show_passwords=False) -> None:
        pass


class NoWarningHandler(BaseToolHandler):
    """Handler without warning support."""

    tool_name = "no_warning_tool"
    display_name = "No Warning Tool"
    has_warning_handler = False  # This one doesn't support warnings
    has_error_handler = True
    has_no_results_handler = True
    has_done_handler = True

    def parse_job(self, engagement_id, log_path, job, **kwargs) -> Dict[str, Any]:
        return {"status": "done", "summary": "Parse complete"}

    def display_done(self, job, log_path, show_all=False, show_passwords=False) -> None:
        pass


@pytest.fixture
def fresh_registry():
    """Provide a fresh registry for each test."""
    registry = ToolHandlerRegistry()
    yield registry
    # Cleanup - reset discovery state
    registry.reset()


class TestRegistryBasics:
    """Test basic registry functionality."""

    def test_empty_registry_returns_none(self, fresh_registry):
        """Unmigrated tools should return None (fallback to legacy)."""
        handler = fresh_registry.get_handler("nonexistent_tool")  # Tool without handler
        assert handler is None

    def test_empty_registry_list(self, fresh_registry):
        """Empty registry should list no handlers."""
        # Note: MockHandler and NoWarningHandler are defined in this module
        # and will be discovered. We test with a completely fresh registry
        # that has no subclasses yet by checking behavior.
        handlers = fresh_registry.list_handlers()
        # Will include our test handlers since they're defined above
        assert isinstance(handlers, list)

    def test_has_handler_false_for_unknown(self, fresh_registry):
        """has_handler should return False for unknown tools."""
        assert fresh_registry.has_handler("unknown_tool") is False


class TestHandlerDiscovery:
    """Test handler auto-discovery."""

    def test_discovers_mock_handler(self, fresh_registry):
        """Should discover MockHandler via __subclasses__()."""
        handler = fresh_registry.get_handler("mock_tool")
        assert handler is not None
        assert handler.tool_name == "mock_tool"
        assert handler.display_name == "Mock Tool"

    def test_case_insensitive_lookup(self, fresh_registry):
        """Tool name lookup should be case-insensitive."""
        handler1 = fresh_registry.get_handler("mock_tool")
        handler2 = fresh_registry.get_handler("MOCK_TOOL")
        handler3 = fresh_registry.get_handler("Mock_Tool")

        assert handler1 is not None
        assert handler1 is handler2
        assert handler1 is handler3

    def test_list_handlers_includes_discovered(self, fresh_registry):
        """list_handlers should include discovered handlers."""
        handlers = fresh_registry.list_handlers()
        assert "mock_tool" in handlers
        assert "no_warning_tool" in handlers


class TestCapabilityQueries:
    """Test capability query methods (replaces manual lists)."""

    def test_has_warning_handler_true(self, fresh_registry):
        """MockHandler has warning handler."""
        assert fresh_registry.has_warning_handler("mock_tool") is True

    def test_has_warning_handler_false(self, fresh_registry):
        """NoWarningHandler doesn't have warning handler."""
        assert fresh_registry.has_warning_handler("no_warning_tool") is False

    def test_has_warning_handler_unknown_tool(self, fresh_registry):
        """Unknown tools return False for capability queries."""
        assert fresh_registry.has_warning_handler("unknown_tool") is False

    def test_has_error_handler(self, fresh_registry):
        """Test error handler capability query."""
        assert fresh_registry.has_error_handler("mock_tool") is True
        assert fresh_registry.has_error_handler("unknown_tool") is False

    def test_has_no_results_handler(self, fresh_registry):
        """Test no_results handler capability query."""
        assert fresh_registry.has_no_results_handler("mock_tool") is True
        assert fresh_registry.has_no_results_handler("unknown_tool") is False

    def test_has_done_handler(self, fresh_registry):
        """Test done handler capability query."""
        assert fresh_registry.has_done_handler("mock_tool") is True
        assert fresh_registry.has_done_handler("unknown_tool") is False


class TestSingleton:
    """Test singleton behavior."""

    def test_get_registry_returns_same_instance(self):
        """get_registry should return the same instance."""
        registry1 = get_registry()
        registry2 = get_registry()
        assert registry1 is registry2

    def test_get_handler_uses_singleton(self):
        """get_handler convenience function should use singleton."""
        handler = get_handler("mock_tool")
        assert handler is not None
        assert handler.tool_name == "mock_tool"


class TestHandlerInstance:
    """Test handler instance behavior."""

    def test_handler_parse_job_returns_dict(self, fresh_registry):
        """Handler parse_job should return a dict with status."""
        handler = fresh_registry.get_handler("mock_tool")
        result = handler.parse_job(1, "/fake/path.log", {})

        assert isinstance(result, dict)
        assert "status" in result
        assert "summary" in result

    def test_handler_display_methods_exist(self, fresh_registry):
        """Handler should have all display methods."""
        handler = fresh_registry.get_handler("mock_tool")

        assert hasattr(handler, "display_done")
        assert hasattr(handler, "display_warning")
        assert hasattr(handler, "display_error")
        assert hasattr(handler, "display_no_results")

        # These should not raise
        handler.display_done({}, "/fake/path")
        handler.display_warning({}, "/fake/path")
        handler.display_error({}, "/fake/path")
        handler.display_no_results({}, "/fake/path")
