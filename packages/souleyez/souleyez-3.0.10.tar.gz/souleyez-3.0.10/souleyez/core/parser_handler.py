#!/usr/bin/env python3
"""
souleyez.core.parser_handler

Centralized parser handling with error recovery and logging.
"""

import logging
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class ParserError(Exception):
    """Base exception for parser errors."""


class ParserHandler:
    """
    Handles parser execution with error recovery and logging.

    Features:
    - Graceful error handling
    - Logging of parser errors
    - Fallback to raw output
    - Parser retry logic
    """

    def __init__(self):
        self.parsers = {}
        self._register_parsers()

    def _register_parsers(self):
        """Register all available parsers."""
        parser_modules = {
            "nmap": "souleyez.parsers.nmap_parser",
            "enum4linux": "souleyez.parsers.enum4linux_parser",
            "gobuster": "souleyez.parsers.gobuster_parser",
            "sqlmap": "souleyez.parsers.sqlmap_parser",
            "smbmap": "souleyez.parsers.smbmap_parser",
            "theharvester": "souleyez.parsers.theharvester_parser",
            "msf": "souleyez.parsers.msf_parser",
            "whois": "souleyez.parsers.whois_parser",
            "wpscan": "souleyez.parsers.wpscan_parser",
            "hydra": "souleyez.parsers.hydra_parser",
            "dnsrecon": "souleyez.parsers.dnsrecon_parser",
            "nikto": "souleyez.parsers.nikto_parser",
            "dalfox": "souleyez.parsers.dalfox_parser",
        }

        for tool, module_path in parser_modules.items():
            try:
                module = __import__(module_path, fromlist=[""])
                parse_func_name = f"parse_{tool}_output"
                if hasattr(module, parse_func_name):
                    self.parsers[tool] = getattr(module, parse_func_name)
                    logger.debug(f"Registered parser for {tool}")
                else:
                    logger.warning(
                        f"Parser module {module_path} missing {parse_func_name}"
                    )
            except ImportError as e:
                logger.warning(f"Could not import parser for {tool}: {e}")
            except Exception as e:
                logger.error(f"Error registering parser for {tool}: {e}")

    def parse(
        self, tool: str, output: str, target: str = "", **kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        Parse tool output with error handling.

        Args:
            tool: Tool name (e.g., 'nmap', 'sqlmap')
            output: Raw tool output
            target: Target host/URL
            **kwargs: Additional parser-specific arguments

        Returns:
            Parsed data dict or None if parsing failed
        """
        if tool not in self.parsers:
            logger.warning(f"No parser available for {tool}")
            return None

        parser_func = self.parsers[tool]

        try:
            logger.debug(f"Parsing {tool} output ({len(output)} bytes)")
            result = parser_func(output, target, **kwargs)
            logger.info(f"Successfully parsed {tool} output")
            return result

        except Exception as e:
            logger.error(f"Parser error for {tool}: {e}", exc_info=True)
            # Return basic structure with error information
            return {
                "error": str(e),
                "tool": tool,
                "target": target,
                "raw_output": output[:500],  # First 500 chars for debugging
            }

    def parse_file(
        self, tool: str, log_path: str, target: str = "", **kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        Parse tool output from file with error handling.

        Args:
            tool: Tool name
            log_path: Path to log file
            target: Target host/URL
            **kwargs: Additional parser arguments

        Returns:
            Parsed data dict or None
        """
        try:
            path = Path(log_path)
            if not path.exists():
                logger.error(f"Log file does not exist: {log_path}")
                return None

            with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                output = f.read()

            return self.parse(tool, output, target, **kwargs)

        except Exception as e:
            logger.error(f"Error reading log file {log_path}: {e}")
            return None

    def has_parser(self, tool: str) -> bool:
        """Check if a parser is available for the tool."""
        return tool in self.parsers

    def list_parsers(self) -> list:
        """List all available parsers."""
        return list(self.parsers.keys())


# Global parser handler instance
_parser_handler = None


def get_parser_handler() -> ParserHandler:
    """Get or create the global parser handler instance."""
    global _parser_handler
    if _parser_handler is None:
        _parser_handler = ParserHandler()
    return _parser_handler


# Convenience functions
def parse_output(
    tool: str, output: str, target: str = "", **kwargs
) -> Optional[Dict[str, Any]]:
    """Parse tool output using the global parser handler."""
    handler = get_parser_handler()
    return handler.parse(tool, output, target, **kwargs)


def parse_file(
    tool: str, log_path: str, target: str = "", **kwargs
) -> Optional[Dict[str, Any]]:
    """Parse tool output file using the global parser handler."""
    handler = get_parser_handler()
    return handler.parse_file(tool, log_path, target, **kwargs)


def has_parser(tool: str) -> bool:
    """Check if parser is available."""
    handler = get_parser_handler()
    return handler.has_parser(tool)
