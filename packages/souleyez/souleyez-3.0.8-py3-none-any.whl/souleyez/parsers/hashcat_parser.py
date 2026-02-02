#!/usr/bin/env python3
"""
souleyez.parsers.hashcat_parser

Parse hashcat output and extract cracked passwords.
"""

import re
from typing import Any, Dict, List


def parse_hashcat_output(output: str, hash_file: str = "") -> Dict[str, Any]:
    """
    Parse hashcat output and extract cracked passwords.

    Hashcat output format:
        <hash>:<password>

    Args:
        output: Raw hashcat output text
        hash_file: Path to hash file (for reference, also used to map hashes to usernames)

    Returns:
        Dict with structure:
        {
            'hash_file': str,
            'cracked': [
                {
                    'hash': str,
                    'password': str,
                    'hash_type': str,  # if identifiable
                    'username': str    # if available from hash file
                }
            ],
            'stats': {
                'cracked_count': int,
                'status': str  # 'cracked', 'exhausted', 'running'
            }
        }
    """
    result = {
        "hash_file": hash_file,
        "cracked": [],
        "stats": {
            "cracked_count": 0,
            "total_count": 0,
            "potfile_hits": 0,  # Hashes already cracked in potfile
            "status": "unknown",
        },
    }

    # Build hash → username mapping from the original hash file
    # This handles --username format where input is username:hash
    hash_to_username = {}
    if hash_file:
        try:
            import os

            if os.path.exists(hash_file):
                with open(hash_file, "r", encoding="utf-8", errors="replace") as f:
                    for line in f:
                        line = line.strip()
                        if ":" in line and not line.startswith("#"):
                            parts = line.split(":")
                            if len(parts) >= 2:
                                # Format: username:hash or username:hash:... (for complex hashes)
                                potential_user = parts[0].strip()
                                potential_hash = parts[1].strip()
                                # Hash should be hex (MD5, SHA, etc.) or start with $
                                if re.match(
                                    r"^[a-fA-F0-9]+$", potential_hash
                                ) or potential_hash.startswith("$"):
                                    hash_to_username[potential_hash.lower()] = (
                                        potential_user
                                    )
        except Exception:
            pass  # Continue without username mapping

    lines = output.split("\n")

    # Check for potfile hits (already cracked)
    for line in lines:
        if "Removed hash found as potfile entry" in line:
            result["stats"]["potfile_hits"] += 1
        # Also parse "INFO: Removed 3 hashes found as potfile entries"
        potfile_match = re.search(
            r"Removed (\d+) hash(?:es)? found as potfile entr", line
        )
        if potfile_match:
            result["stats"]["potfile_hits"] = int(potfile_match.group(1))

    for line in lines:
        line_stripped = line.strip()

        # Skip empty lines and comments
        if not line_stripped or line_stripped.startswith("#"):
            continue

        # === PRIORITY 1: Check for cracked Kerberos hashes ===
        # Format: $krb5tgs$23$*user$realm$spn*$...:password
        # Format: $krb5asrep$23$user@realm:hash:password
        if "$krb5" in line_stripped:
            krb_start = line_stripped.find("$krb5")
            if krb_start >= 0:
                krb_portion = line_stripped[krb_start:]
                # Password is after the last colon
                last_colon = krb_portion.rfind(":")
                if last_colon > 0:
                    hash_value = krb_portion[:last_colon]
                    password = krb_portion[last_colon + 1 :]
                    # Validate: hash must be long, password must exist and not look like hash data
                    if (
                        password
                        and len(hash_value) > 50
                        and not password.startswith("$")
                    ):
                        # Extract username from TGS hash: $krb5tgs$23$*user$realm$spn*$...
                        username = None
                        user_match = re.search(
                            r"\$krb5(?:tgs|asrep)\$\d+\$\*([^$*]+)", hash_value
                        )
                        if user_match:
                            username = user_match.group(1)
                        result["cracked"].append(
                            {
                                "hash": hash_value,
                                "password": password,
                                "hash_type": "kerberos",
                                "username": username,
                            }
                        )
                        continue

        # === PRIORITY 2: Parse status line ===
        # Multiple formats: "Status...........: Cracked" or "Status........: Cracked"
        # Use flexible pattern that handles varying dots/spaces
        status_match = re.search(
            r"Status[.\s]+:\s*(Cracked|Exhausted|Running|Quit)", line_stripped
        )
        if status_match:
            status_value = status_match.group(1).lower()
            result["stats"]["status"] = status_value
            continue

        # === PRIORITY 3: Parse recovered count ===
        # Format: "Recovered........: 1/1 (100.00%)" or "Recovered: 1/1"
        recovered_match = re.search(r"Recovered[.\s]*:\s*(\d+)/(\d+)", line_stripped)
        if recovered_match:
            cracked_count = int(recovered_match.group(1))
            total_count = int(recovered_match.group(2))
            result["stats"]["cracked_count"] = cracked_count
            result["stats"]["total_count"] = total_count
            # If recovered > 0, mark as cracked
            if cracked_count > 0 and result["stats"]["status"] == "unknown":
                result["stats"]["status"] = "cracked"
            continue

        # === Skip known status/progress lines ===
        line_lower = line_stripped.lower()
        if any(
            x in line_lower
            for x in [
                "progress",
                "speed",
                "session",
                "time.",
                "[s]tatus",
                "hash.mode",
                "hash.target",
                "kernel",
                "guess",
                "restore",
                "candidate",
                "hardware",
                "started",
                "stopped",
                "watchdog",
                "attention",
                "pure kernels",
                "optimizers",
                "bitmaps",
                "hashes:",
                "initializ",
                "dictionary cache",
                "approaching",
                "workload",
                "keyspace",
                "rejected",
                "accel",
                "loops",
                "thr",
                "vec",
            ]
        ):
            continue

        # === PRIORITY 4: Check for NTLM/other hashes ===
        # Format: hash:password (simple colon-separated)
        # Format with --username: username:hash:password
        if ":" in line_stripped:
            parts = line_stripped.split(":")
            username = None
            hash_value = None
            password = None

            if len(parts) == 2:
                # Simple hash:password format
                hash_value = parts[0].strip()
                password = parts[1].strip()
            elif len(parts) == 3:
                # username:hash:password format (--username flag)
                username = parts[0].strip()
                hash_value = parts[1].strip()
                password = parts[2].strip()
            elif len(parts) > 3:
                # Could be username:hash:password where password contains ':'
                # Try: first part is username, second is hash, rest is password
                username = parts[0].strip()
                hash_value = parts[1].strip()
                password = ":".join(parts[2:]).strip()

            # Validate: hash looks like hex, password exists
            if hash_value and password and len(hash_value) >= 16:
                if re.match(r"^[a-fA-F0-9]+$", hash_value) or hash_value.startswith(
                    "$"
                ):
                    cracked_entry = {
                        "hash": hash_value,
                        "password": password,
                        "hash_type": "unknown",
                    }
                    # Get username from parsing or from hash file mapping
                    if username:
                        cracked_entry["username"] = username
                    elif hash_to_username:
                        # Look up username from hash file mapping
                        mapped_user = hash_to_username.get(hash_value.lower())
                        if mapped_user:
                            cracked_entry["username"] = mapped_user
                    result["cracked"].append(cracked_entry)

    # === Post-processing ===
    # Update count from cracked list if not found in stats
    if result["stats"]["cracked_count"] == 0 and result["cracked"]:
        result["stats"]["cracked_count"] = len(result["cracked"])

    # If we found cracked hashes, ensure status reflects that
    if result["cracked"] and result["stats"]["status"] == "unknown":
        result["stats"]["status"] = "cracked"

    # If no new cracks but potfile hits, retrieve from potfile using --show
    if not result["cracked"] and result["stats"]["potfile_hits"] > 0:
        if result["stats"]["status"] in ["unknown", "exhausted"]:
            result["stats"]["status"] = "already_cracked"

        # Try to retrieve already cracked passwords using hashcat --show
        if hash_file:
            potfile_cracked = _get_potfile_cracked(hash_file, hash_to_username)
            if potfile_cracked:
                result["cracked"] = potfile_cracked
                result["stats"]["cracked_count"] = len(potfile_cracked)

    return result


def _get_potfile_cracked(
    hash_file: str, hash_to_username: Dict[str, str] = None
) -> List[Dict[str, Any]]:
    """
    Retrieve already cracked passwords from hashcat potfile using --show.

    Args:
        hash_file: Path to the hash file
        hash_to_username: Mapping of hash -> username from the hash file

    Returns:
        List of cracked password dicts with username, hash, password
    """
    import os
    import subprocess

    cracked = []

    if not hash_file or not os.path.exists(hash_file):
        return cracked

    try:
        # Run hashcat --show to get cracked passwords from potfile
        # Use -m 0 for MD5 (most common from SQLi dumps)
        # --username flag tells hashcat the input format is username:hash
        cmd = ["hashcat", "--show", "-m", "0", "--username", hash_file]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        # Parse output: username:hash:password
        for line in proc.stdout.strip().split("\n"):
            line = line.strip()
            if not line:
                continue

            parts = line.split(":")
            if len(parts) >= 3:
                username = parts[0].strip()
                hash_value = parts[1].strip()
                password = ":".join(parts[2:]).strip()  # Password may contain ':'

                if username and password:
                    cracked.append(
                        {
                            "hash": hash_value,
                            "password": password,
                            "hash_type": "md5",
                            "username": username,
                        }
                    )
            elif len(parts) == 2:
                # hash:password format (no username in output)
                hash_value = parts[0].strip()
                password = parts[1].strip()

                # Try to get username from mapping
                username = None
                if hash_to_username:
                    username = hash_to_username.get(hash_value.lower())

                if password:
                    cracked.append(
                        {
                            "hash": hash_value,
                            "password": password,
                            "hash_type": "md5",
                            "username": username,
                        }
                    )
    except subprocess.TimeoutExpired:
        pass
    except Exception:
        pass

    return cracked


def parse_hashcat_potfile(potfile_path: str) -> List[Dict[str, str]]:
    """
    Parse hashcat potfile (hashcat.potfile) for cracked passwords.

    The potfile contains all previously cracked hashes in format:
        hash:password

    Args:
        potfile_path: Path to hashcat.potfile

    Returns:
        List of dicts with hash and password
    """
    cracked = []

    try:
        with open(potfile_path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if ":" in line:
                    parts = line.split(":", 1)
                    if len(parts) == 2:
                        cracked.append({"hash": parts[0], "password": parts[1]})
    except Exception:
        pass

    return cracked


def map_to_credentials(
    parsed_data: Dict[str, Any], engagement_id: int, host_id: int = None
) -> List[Dict[str, Any]]:
    """
    Convert parsed hashcat data into credential records for database storage.

    Args:
        parsed_data: Output from parse_hashcat_output()
        engagement_id: Current engagement ID
        host_id: Optional host ID if known

    Returns:
        List of credential dicts ready for CredentialManager.add()
    """
    credentials = []

    for cracked in parsed_data.get("cracked", []):
        credential = {
            "password": cracked["password"],
            "credential_type": "password",
            "source": "hashcat",
            "validation_status": "cracked",
            "notes": f"Cracked from hash: {cracked['hash'][:32]}...",
            "hash_original": cracked["hash"],
        }

        if host_id:
            credential["host_id"] = host_id

        credentials.append(credential)

    return credentials


__all__ = ["parse_hashcat_output", "parse_hashcat_potfile", "map_to_credentials"]
