#!/usr/bin/env python3
"""
souleyez.parsers.john_parser

Parser for John the Ripper output.
"""

import os
import re
from typing import Dict, List, Tuple


def parse_john_output(output: str, hash_file: str = None) -> Dict:
    """
    Parse John the Ripper output and extract cracked passwords.

    Args:
        output: John's stdout/stderr output
        hash_file: Path to the hash file (to run --show if needed)

    Returns:
        Dictionary with cracked credentials
    """
    results = {
        "cracked": [],
        "total_loaded": 0,
        "total_cracked": 0,
        "session_status": "unknown",
    }

    # Parse loaded hashes
    loaded_match = re.search(r"Loaded (\d+) password hash", output)
    if loaded_match:
        results["total_loaded"] = int(loaded_match.group(1))

    # Parse cracked passwords from live output with multiple format support
    # Format 1: "password         (username)"
    # Format 2: "password (username)"
    # Format 3: "username:password"
    # Format 4: "password          (username) [hash_type]"
    for line in output.split("\n"):
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("["):
            continue

        # Try format: password (username) with optional hash type
        match = re.match(r"^(\S+)\s+\(([^)]+)\)(?:\s+\[.+\])?\s*$", line)
        if match:
            password = match.group(1)
            username = match.group(2)
            results["cracked"].append(
                {"username": username, "password": password, "source": "john_live"}
            )
            continue

        # Try format: username:password (from --show output)
        if ":" in line and not line.startswith("Loaded"):
            parts = line.split(":")
            if len(parts) >= 2 and len(parts[0]) > 0 and len(parts[-1]) > 0:
                # Skip if it looks like a hash (32+ hex chars)
                if not re.match(r"^[0-9a-fA-F]{32,}$", parts[-1]):
                    username = parts[0]
                    password = parts[-1]
                    results["cracked"].append(
                        {
                            "username": username,
                            "password": password,
                            "source": "john_live",
                        }
                    )

    # Check session status with multiple format support
    if any(
        x in output
        for x in ["Session completed", "session completed", "Proceeding with next"]
    ):
        results["session_status"] = "completed"
    elif any(
        x in output for x in ["Session aborted", "session aborted", "Interrupted"]
    ):
        results["session_status"] = "aborted"
    elif "No password hashes left to crack" in output:
        results["session_status"] = "completed"

    # Parse summary line with multiple formats
    # Format 1: "2g 0:00:00:01 DONE..."
    # Format 2: "2g 0:00:00:01 100% DONE..."
    # Format 3: "Session completed, 2g"
    summary_patterns = [
        r"(\d+)g\s+[\d:]+\s+(?:\d+%\s+)?(DONE|Session)",
        r"Session completed[,\s]+(\d+)g",
        r"(\d+)\s+password hashes? cracked",
    ]
    for pattern in summary_patterns:
        summary_match = re.search(pattern, output, re.IGNORECASE)
        if summary_match:
            results["total_cracked"] = int(summary_match.group(1))
            break

    # If hash_file provided, also parse john.pot or run --show
    if hash_file and os.path.isfile(hash_file):
        pot_results = parse_john_pot(hash_file)
        # Merge with live results (pot is authoritative)
        if pot_results:
            results["cracked"].extend(pot_results)
            # Deduplicate by username
            seen = set()
            unique_creds = []
            for cred in results["cracked"]:
                if cred["username"] not in seen:
                    seen.add(cred["username"])
                    unique_creds.append(cred)
            results["cracked"] = unique_creds
            results["total_cracked"] = len(unique_creds)

    return results


def parse_john_pot(hash_file: str = None) -> List[Dict]:
    """
    Parse John's potfile for cracked passwords.

    Args:
        hash_file: If provided, run 'john --show hashfile' to get results

    Returns:
        List of cracked credentials
    """
    cracked = []

    # Try running john --show on the hash file
    if hash_file and os.path.isfile(hash_file):
        try:
            import subprocess

            result = subprocess.run(
                ["john", "--show", hash_file],
                capture_output=True,
                text=True,
                timeout=10,
            )

            # Parse --show output
            # Format: "username:password" or "username:hash:password"
            for line in result.stdout.split("\n"):
                line = line.strip()
                if ":" in line and not line.startswith("#"):
                    parts = line.split(":")
                    if len(parts) >= 2:
                        username = parts[0]
                        # Password is the last part
                        password = parts[-1]
                        if username and password:
                            cracked.append(
                                {
                                    "username": username,
                                    "password": password,
                                    "source": "john_pot",
                                }
                            )
        except Exception:
            pass

    # Also try reading ~/.john/john.pot directly
    pot_file = os.path.expanduser("~/.john/john.pot")
    if os.path.isfile(pot_file):
        try:
            with open(pot_file, "r") as f:
                for line in f:
                    line = line.strip()
                    if ":" in line:
                        # Potfile format: hash:password
                        parts = line.split(":")
                        if len(parts) >= 2:
                            # Extract password (last part)
                            password = parts[-1]
                            # Try to find username from hash if available
                            # This is basic - john.pot doesn't always have username
                            cracked.append(
                                {
                                    "username": "unknown",
                                    "password": password,
                                    "hash": parts[0],
                                    "source": "john_pot_file",
                                }
                            )
        except Exception:
            pass

    return cracked


def extract_credentials_to_db(
    output: str, hash_file: str = None, engagement_id: int = None
):
    """
    Extract cracked credentials and store them in the database.

    Args:
        output: John's output
        hash_file: Path to hash file
        engagement_id: Current engagement ID
    """
    from souleyez.storage.credentials import CredentialsManager

    results = parse_john_output(output, hash_file)

    if not results["cracked"]:
        return 0

    cred_mgr = CredentialsManager()
    added = 0

    for cred in results["cracked"]:
        username = cred.get("username")
        password = cred.get("password")

        if username and password and username != "unknown":
            try:
                # Add to credentials database
                cred_mgr.add_credential(
                    username=username,
                    password=password,
                    service="cracked",  # Mark as cracked hash
                    host="",  # No specific host
                    engagement_id=engagement_id,
                )
                added += 1
            except Exception:
                pass  # Credential might already exist

    return added
