#!/usr/bin/env python3
"""
souleyez.parsers.searchsploit_parser - Parse SearchSploit JSON output
"""

import csv
import json
import re
from pathlib import Path
from typing import Any, Dict, Optional


def _load_exploitdb_csv() -> Dict[str, Dict[str, str]]:
    """
    Load the local exploitdb CSV database and return a dict keyed by EDB-ID.

    Returns:
        Dict mapping EDB-ID to exploit metadata (platform, type, date_published)
    """
    csv_paths = [
        "/usr/share/exploitdb/files_exploits.csv",
        "/usr/share/exploitdb/files.csv",
    ]

    for csv_path in csv_paths:
        if Path(csv_path).exists():
            try:
                exploits_db = {}
                with open(csv_path, "r", encoding="utf-8", errors="replace") as f:
                    reader = csv.reader(f)
                    next(reader)  # Skip header

                    for row in reader:
                        if len(row) < 7:
                            continue

                        edb_id = row[0]
                        exploits_db[edb_id] = {
                            "platform": row[6] if len(row) > 6 else "",
                            "type": row[5] if len(row) > 5 else "",
                            "date_published": row[3] if len(row) > 3 else "",
                        }

                return exploits_db
            except Exception:
                # If CSV parsing fails, return empty dict
                pass

    return {}


def _extract_edb_id(url: str) -> Optional[str]:
    """
    Extract EDB-ID from Exploit-DB URL.

    Args:
        url: Exploit-DB URL (e.g., https://www.exploit-db.com/exploits/49757)

    Returns:
        EDB-ID as string, or None if not found
    """
    if not url:
        return None

    match = re.search(r"/exploits/(\d+)/?$", url)
    if match:
        return match.group(1)

    match = re.search(r"/shellcodes/(\d+)/?$", url)
    if match:
        return match.group(1)

    return None


def parse_searchsploit(log_path: str, target: str) -> Dict[str, Any]:
    """
    Parse SearchSploit JSON output.

    Args:
        log_path: Path to searchsploit output file
        target: Search term that was used

    Returns:
        Dict containing parsed exploits
    """
    exploits = []

    try:
        # Load exploitdb CSV database once for all exploits
        exploits_db = _load_exploitdb_csv()

        with open(log_path, "r", encoding="utf-8") as f:
            content = f.read()

            # Find JSON content (skip metadata header)
            json_start = content.find("{")
            if json_start == -1:
                return {
                    "tool": "searchsploit",
                    "target": target,
                    "exploit_count": 0,
                    "exploits": [],
                    "error": "No JSON output found",
                }

            json_content = content[json_start:]

            # Handle potential error messages after JSON
            try:
                # Try to find where JSON ends
                bracket_count = 0
                json_end = 0
                for i, char in enumerate(json_content):
                    if char == "{":
                        bracket_count += 1
                    elif char == "}":
                        bracket_count -= 1
                        if bracket_count == 0:
                            json_end = i + 1
                            break

                if json_end > 0:
                    json_content = json_content[:json_end]

                data = json.loads(json_content)
            except json.JSONDecodeError:
                # Fallback: try loading entire content
                data = json.loads(json_content)

        # Parse results
        for result in data.get("RESULTS_EXPLOIT", []):
            # searchsploit --json provides these fields directly
            edb_id = result.get("EDB-ID", "")

            # URL may be provided or we construct it from EDB-ID
            url = result.get("URL", "")
            if not url and edb_id:
                url = f"https://www.exploit-db.com/exploits/{edb_id}"

            # If EDB-ID not in result, try extracting from URL
            if not edb_id:
                edb_id = _extract_edb_id(url) or ""

            # Get metadata directly from result (newer searchsploit format)
            # Fall back to CSV lookup if not present
            date = result.get("Date_Published", result.get("Date_Added", ""))
            platform = result.get("Platform", "")
            exploit_type = result.get("Type", "")

            # If metadata not in result, look up from CSV database
            if not (date or platform or exploit_type):
                metadata = exploits_db.get(str(edb_id), {}) if edb_id else {}
                date = date or metadata.get("date_published", "")
                platform = platform or metadata.get("platform", "")
                exploit_type = exploit_type or metadata.get("type", "")

            exploit = {
                "title": result.get("Title", ""),
                "path": result.get("Path", ""),
                "edb_id": str(edb_id),
                "date": date,
                "platform": platform,
                "type": exploit_type,
                "url": url,
                "verified": result.get("Verified", "0") == "1",
                "codes": result.get("Codes", ""),  # CVE codes
            }
            exploits.append(exploit)

        # Also check for shellcode results
        for result in data.get("RESULTS_SHELLCODE", []):
            edb_id = result.get("EDB-ID", "")
            url = result.get("URL", "")
            if not url and edb_id:
                url = f"https://www.exploit-db.com/shellcodes/{edb_id}"

            if not edb_id:
                edb_id = _extract_edb_id(url) or ""

            date = result.get("Date_Published", result.get("Date_Added", ""))
            platform = result.get("Platform", "")

            # Look up metadata from CSV database if not in result
            if not (date or platform):
                metadata = exploits_db.get(str(edb_id), {}) if edb_id else {}
                date = date or metadata.get("date_published", "")
                platform = platform or metadata.get("platform", "")

            exploit = {
                "title": result.get("Title", ""),
                "path": result.get("Path", ""),
                "edb_id": str(edb_id),
                "date": date,
                "platform": platform,
                "type": "shellcode",
                "url": url,
                "verified": result.get("Verified", "0") == "1",
                "codes": result.get("Codes", ""),
            }
            exploits.append(exploit)

    except FileNotFoundError:
        return {
            "tool": "searchsploit",
            "target": target,
            "error": "Log file not found",
            "exploit_count": 0,
            "exploits": [],
        }
    except json.JSONDecodeError as e:
        return {
            "tool": "searchsploit",
            "target": target,
            "error": f"JSON parse error: {e}",
            "exploit_count": 0,
            "exploits": [],
        }
    except Exception as e:
        return {
            "tool": "searchsploit",
            "target": target,
            "error": f"Parse error: {e}",
            "exploit_count": 0,
            "exploits": [],
        }

    return {
        "tool": "searchsploit",
        "target": target,
        "exploit_count": len(exploits),
        "exploits": exploits,
    }
