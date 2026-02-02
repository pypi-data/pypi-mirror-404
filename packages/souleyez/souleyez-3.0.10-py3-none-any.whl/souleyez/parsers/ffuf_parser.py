#!/usr/bin/env python3
"""
souleyez.parsers.ffuf_parser - Parse ffuf JSON output
"""

import json
from typing import Any, Dict


def parse_ffuf(log_path: str, target: str) -> Dict[str, Any]:
    """Parse ffuf JSON output."""

    try:
        with open(log_path, "r", encoding="utf-8") as f:
            # ffuf writes JSON on first line, then appends text output
            # Read only the first line to get the JSON
            first_line = f.readline()
            if first_line.strip():
                data = json.loads(first_line)
            else:
                raise ValueError("Empty log file")
    except (FileNotFoundError, json.JSONDecodeError, ValueError) as e:
        return {
            "tool": "ffuf",
            "target": target,
            "error": str(e),
            "results_found": 0,
            "paths": [],
        }

    results = []

    for result in data.get("results", []):
        results.append(
            {
                "url": result.get("url"),
                "status_code": result.get("status"),  # Normalized to match gobuster
                "size": result.get("length"),  # Normalized to match gobuster
                "redirect": result.get(
                    "redirectlocation", ""
                ),  # Normalized to match gobuster
                "words": result.get("words"),
                "lines": result.get("lines"),
                "content_type": result.get("content-type", ""),
                "input": result.get("input", {}),
            }
        )

    config = data.get("config", {})

    return {
        "tool": "ffuf",
        "target": target,
        "results_found": len(results),
        "wordlist": config.get("wordlist"),
        "method": config.get("method", "GET"),
        "paths": results,
        "config": config,
    }
