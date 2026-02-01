#!/usr/bin/env python3
"""
Log formatting utilities for human-readable display.
"""

import json
import re
from datetime import datetime
from typing import List, Optional


def format_json_log_line(line: str) -> Optional[str]:
    """
    Format a JSON log line into human-readable format.

    Args:
        line: Raw JSON log line

    Returns:
        Formatted string or None if not JSON
    """
    try:
        data = json.loads(line.strip())

        # JSON can parse primitives (numbers, strings, booleans) - we only want objects
        if not isinstance(data, dict):
            return None

        # Extract common fields
        timestamp = data.get("timestamp", "")
        level = data.get("levelname", "INFO")
        name = data.get("name", "")
        message = data.get("message", "")

        # Parse timestamp
        if timestamp:
            try:
                dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                time_str = dt.strftime("%H:%M:%S")
            except:
                time_str = timestamp[:8] if len(timestamp) > 8 else timestamp
        else:
            time_str = "??:??:??"

        # Color codes for log levels
        level_colors = {
            "DEBUG": "\033[36m",  # Cyan
            "INFO": "\033[32m",  # Green
            "WARNING": "\033[33m",  # Yellow
            "ERROR": "\033[31m",  # Red
            "CRITICAL": "\033[35m",  # Magenta
        }
        reset = "\033[0m"

        level_color = level_colors.get(level, "")
        level_short = level[0]  # D, I, W, E, C

        # Build formatted line
        formatted = f"{time_str} {level_color}[{level_short}]{reset} "

        # Add module name if not too long
        if name and len(name) < 30:
            module = name.split(".")[-1]  # Last part only
            formatted += f"{module}: "

        formatted += message

        # Add interesting extra fields
        extras = []
        skip_fields = {
            "timestamp",
            "levelname",
            "name",
            "message",
            "log_file",
            "log_level",
            "log_format",
        }
        for key, value in data.items():
            if key not in skip_fields and value:
                if isinstance(value, (str, int, float, bool)):
                    extras.append(f"{key}={value}")

        if extras:
            formatted += f" ({', '.join(extras[:3])})"  # Limit to 3 extras

        return formatted

    except (json.JSONDecodeError, KeyError):
        # Not JSON or malformed
        return None


def format_log_stream(lines: List[str], max_lines: int = 50) -> List[str]:
    """
    Format a stream of log lines (mix of JSON and plain text).

    Args:
        lines: List of raw log lines
        max_lines: Maximum lines to return

    Returns:
        List of formatted lines
    """
    formatted = []

    for line in lines[-max_lines:]:
        if not line.strip():
            continue

        # Try JSON formatting first
        json_formatted = format_json_log_line(line)
        if json_formatted:
            formatted.append(json_formatted)
        else:
            # Keep plain text as-is (tool output, etc.)
            formatted.append(line.rstrip())

    return formatted


def tail_and_format_log(log_path: str, num_lines: int = 50) -> List[str]:
    """
    Read last N lines from log file and format them.

    Args:
        log_path: Path to log file
        num_lines: Number of lines to read

    Returns:
        List of formatted lines
    """
    try:
        with open(log_path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()

        return format_log_stream(lines, max_lines=num_lines)
    except Exception as e:
        return [f"Error reading log: {e}"]
