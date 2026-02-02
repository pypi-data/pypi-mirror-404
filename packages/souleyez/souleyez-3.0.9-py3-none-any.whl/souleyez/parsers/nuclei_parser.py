#!/usr/bin/env python3
"""
souleyez.parsers.nuclei_parser - Parse Nuclei JSONL output
"""

import json
import os
import tempfile
from typing import Any, Dict


def parse_nuclei(log_path: str, target: str) -> Dict[str, Any]:
    """
    Parse Nuclei JSONL output (one JSON object per line).

    Args:
        log_path: Path to nuclei output file
        target: Target URL that was scanned

    Returns:
        Dict containing parsed findings with severity breakdown
    """
    findings = []
    severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}

    try:
        with open(log_path, "r", encoding="utf-8") as f:
            for line in f:
                # Skip comment lines (metadata)
                if line.startswith("#"):
                    continue

                line = line.strip()
                if not line:
                    continue

                try:
                    result = json.loads(line)

                    # Extract finding information
                    info = result.get("info", {})
                    severity = info.get("severity", "info").lower()

                    finding = {
                        "template_id": result.get(
                            "template-id", result.get("templateID")
                        ),
                        "name": info.get("name"),
                        "severity": severity,
                        "description": info.get("description"),
                        "tags": info.get("tags", []),
                        "matched_at": result.get("matched-at", result.get("matched")),
                        "matcher_name": result.get("matcher-name"),
                        "extracted_results": result.get("extracted-results", []),
                        "curl_command": result.get("curl-command"),
                        "type": result.get("type"),
                        "host": result.get("host"),
                        "metadata": info.get("metadata", {}),
                    }

                    # Extract CVE ID if present
                    classification = info.get("classification", {})
                    if classification:
                        finding["cve_id"] = classification.get("cve-id")
                        finding["cvss_score"] = classification.get("cvss-score")
                        finding["cwe_id"] = classification.get("cwe-id")

                    # Extract reference links
                    finding["references"] = info.get("reference", [])

                    findings.append(finding)
                    severity_counts[severity] = severity_counts.get(severity, 0) + 1

                except json.JSONDecodeError:
                    # Skip non-JSON lines
                    continue

    except FileNotFoundError:
        return {
            "tool": "nuclei",
            "target": target,
            "error": "Log file not found",
            "findings_count": 0,
            "findings": [],
        }

    return {
        "tool": "nuclei",
        "target": target,
        "findings_count": len(findings),
        "critical": severity_counts["critical"],
        "high": severity_counts["high"],
        "medium": severity_counts["medium"],
        "low": severity_counts["low"],
        "info": severity_counts["info"],
        "findings": findings,
        "severity_breakdown": severity_counts,
    }


def parse_nuclei_output(content: str, target: str) -> Dict[str, Any]:
    """
    Wrapper that parses from string content instead of file path.

    Args:
        content: Raw nuclei output text
        target: Target URL

    Returns:
        Parsed nuclei data structure
    """
    # Write content to temp file and call existing parse_nuclei
    with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
        f.write(content)
        temp_path = f.name

    try:
        result = parse_nuclei(temp_path, target)
        return result
    finally:
        os.unlink(temp_path)
