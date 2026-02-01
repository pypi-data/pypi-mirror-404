#!/usr/bin/env python3
"""
Bloodhound result parser - analyze AD enumeration data.
"""

import json
from pathlib import Path
from typing import Dict


def parse_bloodhound(log_path: str, target: str) -> Dict:
    """
    Parse Bloodhound enumeration results.

    Args:
        log_path: Path to Bloodhound job log
        target: Domain controller IP

    Returns:
        Dict with AD statistics
    """
    output_dir = Path.home() / ".souleyez" / "bloodhound_data"

    collections = sorted(
        output_dir.glob("*"), key=lambda p: p.stat().st_mtime, reverse=True
    )

    if not collections:
        return {
            "tool": "bloodhound",
            "target": target,
            "error": "No Bloodhound data found",
        }

    latest_collection = collections[0]

    stats = {
        "users": 0,
        "groups": 0,
        "computers": 0,
        "domains": 0,
        "gpos": 0,
        "sessions": 0,
    }

    for json_file in latest_collection.glob("*.json"):
        try:
            with open(json_file, "r") as f:
                data = json.load(f)

                if "users" in data:
                    stats["users"] += len(data["users"])
                if "groups" in data:
                    stats["groups"] += len(data["groups"])
                if "computers" in data:
                    stats["computers"] += len(data["computers"])
                if "domains" in data:
                    stats["domains"] += len(data["domains"])
                if "gpos" in data:
                    stats["gpos"] += len(data["gpos"])
                if "sessions" in data:
                    stats["sessions"] += len(data["sessions"])
        except Exception:
            continue

    return {
        "tool": "bloodhound",
        "target": target,
        "collection_path": str(latest_collection),
        "statistics": stats,
        "summary": f"Enumerated {stats['users']} users, {stats['groups']} groups, "
        f"{stats['computers']} computers in AD domain",
    }


def store_bloodhound_results(result: Dict, engagement_id: int, job_id: int):
    """
    Store Bloodhound results in database.

    Args:
        result: Parsed Bloodhound results
        engagement_id: Engagement ID
        job_id: Job ID
    """
    from souleyez.storage.findings import FindingsManager

    fm = FindingsManager()

    stats = result.get("statistics", {})

    fm.add_finding(
        engagement_id=engagement_id,
        title=f"Active Directory Enumerated - {stats.get('users', 0)} Users Discovered",
        description=f"Bloodhound successfully enumerated Active Directory:\n"
        f"- Users: {stats.get('users', 0)}\n"
        f"- Groups: {stats.get('groups', 0)}\n"
        f"- Computers: {stats.get('computers', 0)}\n"
        f"- GPOs: {stats.get('gpos', 0)}\n\n"
        f"Data saved to: {result.get('collection_path', 'Unknown')}\n"
        f"Import into Bloodhound GUI to visualize attack paths.",
        severity="info",
        tool="bloodhound",
        evidence=result.get("summary", "AD enumeration complete"),
    )
