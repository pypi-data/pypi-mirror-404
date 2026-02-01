#!/usr/bin/env python3
"""
Tool handler registry with auto-discovery.

Provides a central registry for tool handlers that:
- Auto-discovers handlers via __subclasses__()
- Provides capability queries (has_warning_handler, etc.)
- Returns None for unmigrated tools (fallback to legacy code)
"""

import logging
from typing import Dict, List, Optional

from souleyez.handlers.base import BaseToolHandler

logger = logging.getLogger(__name__)

# Singleton registry instance
_registry: Optional["ToolHandlerRegistry"] = None


class ToolHandlerRegistry:
    """
    Registry for tool handlers.

    Handlers are discovered automatically when their modules are imported.
    The registry uses __subclasses__() to find all BaseToolHandler subclasses.
    """

    def __init__(self):
        self._handlers: Dict[str, BaseToolHandler] = {}
        self._discovered = False

    def _discover_handlers(self) -> None:
        """
        Auto-discover all BaseToolHandler subclasses.

        This imports handler modules to trigger class definition,
        then finds all subclasses of BaseToolHandler.
        """
        if self._discovered:
            return

        # Import handler modules here to trigger class registration
        # As we add handlers, add imports here:
        try:
            from souleyez.handlers import msf_exploit_handler  # noqa: F401
        except ImportError as e:
            logger.warning(f"Failed to import msf_exploit_handler: {e}")
        try:
            from souleyez.handlers import msf_auxiliary_handler  # noqa: F401
        except ImportError as e:
            logger.warning(f"Failed to import msf_auxiliary_handler: {e}")
        try:
            from souleyez.handlers import hydra_handler  # noqa: F401
        except ImportError as e:
            logger.warning(f"Failed to import hydra_handler: {e}")
        try:
            from souleyez.handlers import gobuster_handler  # noqa: F401
        except ImportError as e:
            logger.warning(f"Failed to import gobuster_handler: {e}")
        try:
            from souleyez.handlers import ffuf_handler  # noqa: F401
        except ImportError as e:
            logger.warning(f"Failed to import ffuf_handler: {e}")
        try:
            from souleyez.handlers import nmap_handler  # noqa: F401
        except ImportError as e:
            logger.warning(f"Failed to import nmap_handler: {e}")
        try:
            from souleyez.handlers import nuclei_handler  # noqa: F401
        except ImportError as e:
            logger.warning(f"Failed to import nuclei_handler: {e}")
        try:
            from souleyez.handlers import theharvester_handler  # noqa: F401
        except ImportError as e:
            logger.warning(f"Failed to import theharvester_handler: {e}")
        try:
            from souleyez.handlers import nikto_handler  # noqa: F401
        except ImportError as e:
            logger.warning(f"Failed to import nikto_handler: {e}")
        try:
            from souleyez.handlers import wpscan_handler  # noqa: F401
        except ImportError as e:
            logger.warning(f"Failed to import wpscan_handler: {e}")
        try:
            from souleyez.handlers import dnsrecon_handler  # noqa: F401
        except ImportError as e:
            logger.warning(f"Failed to import dnsrecon_handler: {e}")
        try:
            from souleyez.handlers import sqlmap_handler  # noqa: F401
        except ImportError as e:
            logger.warning(f"Failed to import sqlmap_handler: {e}")
        try:
            from souleyez.handlers import smbmap_handler  # noqa: F401
        except ImportError as e:
            logger.warning(f"Failed to import smbmap_handler: {e}")
        try:
            from souleyez.handlers import gpp_extract_handler  # noqa: F401
        except ImportError as e:
            logger.warning(f"Failed to import gpp_extract_handler: {e}")
        try:
            from souleyez.handlers import enum4linux_handler  # noqa: F401
        except ImportError as e:
            logger.warning(f"Failed to import enum4linux_handler: {e}")
        try:
            from souleyez.handlers import crackmapexec_handler  # noqa: F401
        except ImportError as e:
            logger.warning(f"Failed to import crackmapexec_handler: {e}")
        try:
            from souleyez.handlers import john_handler  # noqa: F401
        except ImportError as e:
            logger.warning(f"Failed to import john_handler: {e}")
        try:
            from souleyez.handlers import hashcat_handler  # noqa: F401
        except ImportError as e:
            logger.warning(f"Failed to import hashcat_handler: {e}")
        try:
            from souleyez.handlers import responder_handler  # noqa: F401
        except ImportError as e:
            logger.warning(f"Failed to import responder_handler: {e}")
        try:
            from souleyez.handlers import whois_handler  # noqa: F401
        except ImportError as e:
            logger.warning(f"Failed to import whois_handler: {e}")
        try:
            from souleyez.handlers import impacket_secretsdump_handler  # noqa: F401
        except ImportError as e:
            logger.warning(f"Failed to import impacket_secretsdump_handler: {e}")
        try:
            from souleyez.handlers import impacket_psexec_handler  # noqa: F401
        except ImportError as e:
            logger.warning(f"Failed to import impacket_psexec_handler: {e}")
        try:
            from souleyez.handlers import impacket_getuserspns_handler  # noqa: F401
        except ImportError as e:
            logger.warning(f"Failed to import impacket_getuserspns_handler: {e}")
        try:
            from souleyez.handlers import katana_handler  # noqa: F401
        except ImportError as e:
            logger.warning(f"Failed to import katana_handler: {e}")
        try:
            from souleyez.handlers import lfi_extract_handler  # noqa: F401
        except ImportError as e:
            logger.warning(f"Failed to import lfi_extract_handler: {e}")
        try:
            from souleyez.handlers import evil_winrm_handler  # noqa: F401
        except ImportError as e:
            logger.warning(f"Failed to import evil_winrm_handler: {e}")
        try:
            from souleyez.handlers import ldapsearch_handler  # noqa: F401
        except ImportError as e:
            logger.warning(f"Failed to import ldapsearch_handler: {e}")
        try:
            from souleyez.handlers import service_explorer_handler  # noqa: F401
        except ImportError as e:
            logger.warning(f"Failed to import service_explorer_handler: {e}")
        try:
            from souleyez.handlers import kerbrute_handler  # noqa: F401
        except ImportError as e:
            logger.warning(f"Failed to import kerbrute_handler: {e}")
        try:
            from souleyez.handlers import rdp_sec_check_handler  # noqa: F401
        except ImportError as e:
            logger.warning(f"Failed to import rdp_sec_check_handler: {e}")
        try:
            from souleyez.handlers import nxc_handler  # noqa: F401
        except ImportError as e:
            logger.warning(f"Failed to import nxc_handler: {e}")
        try:
            from souleyez.handlers import certipy_handler  # noqa: F401
        except ImportError as e:
            logger.warning(f"Failed to import certipy_handler: {e}")
        try:
            from souleyez.handlers import bloodhound_handler  # noqa: F401
        except ImportError as e:
            logger.warning(f"Failed to import bloodhound_handler: {e}")
        try:
            from souleyez.handlers import smbclient_handler  # noqa: F401
        except ImportError as e:
            logger.warning(f"Failed to import smbclient_handler: {e}")
        try:
            from souleyez.handlers import smbpasswd_handler  # noqa: F401
        except ImportError as e:
            logger.warning(f"Failed to import smbpasswd_handler: {e}")
        try:
            from souleyez.handlers import bash_handler  # noqa: F401
        except ImportError as e:
            logger.warning(f"Failed to import bash_handler: {e}")
        try:
            from souleyez.handlers import web_login_test_handler  # noqa: F401
        except ImportError as e:
            logger.warning(f"Failed to import web_login_test_handler: {e}")

        # Find all subclasses of BaseToolHandler
        for handler_class in BaseToolHandler.__subclasses__():
            try:
                # Skip the base class itself
                if handler_class.tool_name == "base":
                    continue

                instance = handler_class()
                tool_key = instance.tool_name.lower()

                if tool_key in self._handlers:
                    logger.warning(
                        f"Duplicate handler for tool '{tool_key}': "
                        f"{handler_class.__name__} (using first registered)"
                    )
                    continue

                self._handlers[tool_key] = instance
                logger.debug(
                    f"Registered handler: {tool_key} -> {handler_class.__name__}"
                )

            except Exception as e:
                logger.warning(
                    f"Failed to register handler {handler_class.__name__}: {e}"
                )

        self._discovered = True
        logger.debug(
            f"Handler discovery complete. Registered: {list(self._handlers.keys())}"
        )

    def get_handler(self, tool_name: str) -> Optional[BaseToolHandler]:
        """
        Get handler for a tool.

        Args:
            tool_name: The tool identifier (case-insensitive)

        Returns:
            The handler instance, or None if no handler registered
        """
        self._discover_handlers()
        return self._handlers.get(tool_name.lower())

    def has_handler(self, tool_name: str) -> bool:
        """Check if a handler exists for this tool."""
        return self.get_handler(tool_name) is not None

    def has_warning_handler(self, tool_name: str) -> bool:
        """Check if tool has a warning handler (replaces manual list)."""
        handler = self.get_handler(tool_name)
        return handler is not None and handler.has_warning_handler

    def has_error_handler(self, tool_name: str) -> bool:
        """Check if tool has an error handler (replaces manual list)."""
        handler = self.get_handler(tool_name)
        return handler is not None and handler.has_error_handler

    def has_no_results_handler(self, tool_name: str) -> bool:
        """Check if tool has a no_results handler (replaces manual list)."""
        handler = self.get_handler(tool_name)
        return handler is not None and handler.has_no_results_handler

    def has_done_handler(self, tool_name: str) -> bool:
        """Check if tool has a done handler."""
        handler = self.get_handler(tool_name)
        return handler is not None and handler.has_done_handler

    def list_handlers(self) -> List[str]:
        """List all registered handler tool names."""
        self._discover_handlers()
        return list(self._handlers.keys())

    def reset(self) -> None:
        """Reset registry (for testing)."""
        self._handlers.clear()
        self._discovered = False


def get_registry() -> ToolHandlerRegistry:
    """Get the singleton registry instance."""
    global _registry
    if _registry is None:
        _registry = ToolHandlerRegistry()
    return _registry


def get_handler(tool_name: str) -> Optional[BaseToolHandler]:
    """
    Convenience function to get a handler.

    Args:
        tool_name: The tool identifier (case-insensitive)

    Returns:
        The handler instance, or None if no handler registered
    """
    return get_registry().get_handler(tool_name)
