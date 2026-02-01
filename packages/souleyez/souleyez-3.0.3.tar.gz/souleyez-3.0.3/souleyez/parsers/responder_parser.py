#!/usr/bin/env python3
"""
Responder result parser - extracts captured credentials.
"""

import re
from pathlib import Path
from typing import Dict, List


def parse_responder(log_path: str, interface: str) -> Dict:
    """
    Parse Responder logs and extract captured credentials.

    Args:
        log_path: Path to Responder job log
        interface: Network interface used

    Returns:
        Dict with captured credentials
    """
    log_dir = Path.home() / ".souleyez" / "responder_logs"

    credentials = []
    hash_files = list(log_dir.glob("*NTLMv2*.txt"))

    for hash_file in hash_files:
        with open(hash_file, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                cred = _parse_ntlmv2_hash(line, hash_file.name)
                if cred:
                    credentials.append(cred)

    return {
        "tool": "responder",
        "interface": interface,
        "credentials_captured": len(credentials),
        "credentials": credentials,
        "hash_files": [str(f) for f in hash_files],
        "summary": f"Captured {len(credentials)} NTLMv2 hash(es) from {len(hash_files)} file(s)",
    }


def _parse_ntlmv2_hash(hash_line: str, filename: str) -> Dict:
    """Parse NTLMv2 hash line."""
    protocol_match = re.match(r"([A-Z]+)-NTLMv2", filename)
    protocol = protocol_match.group(1) if protocol_match else "Unknown"

    parts = hash_line.split(":")

    if len(parts) >= 5:
        username = parts[0]
        domain = parts[2]
        challenge = parts[3]
        response = parts[4]
    elif "\\" in hash_line:
        user_part, hash_part = hash_line.split(":", 1)
        domain, username = user_part.split("\\")
        response = hash_part
        challenge = ""
    else:
        return None

    return {
        "username": username,
        "domain": domain,
        "protocol": protocol,
        "hash_type": "NTLMv2",
        "hash": hash_line,
        "challenge": challenge,
        "response": response,
        "source": "responder",
    }


def store_responder_results(result: Dict, engagement_id: int, job_id: int):
    """
    Store Responder results in database.

    Args:
        result: Parsed Responder results
        engagement_id: Engagement ID
        job_id: Job ID
    """
    from souleyez.storage.credentials import CredentialsManager

    cm = CredentialsManager(engagement_id)

    for cred in result.get("credentials", []):
        cm.add_credential(
            username=f"{cred['domain']}\\{cred['username']}",
            password=cred["hash"],
            service=cred["protocol"].lower(),
            host=None,
            status="captured",
            source=f'responder_{cred["protocol"]}',
            notes=f"NTLMv2 hash captured via {cred['protocol']} poisoning",
        )

    if result["credentials_captured"] > 0:
        from souleyez.storage.findings import FindingsManager

        fm = FindingsManager()
        fm.add_finding(
            engagement_id=engagement_id,
            title=f"LLMNR/NBT-NS Poisoning - {result['credentials_captured']} Credential(s) Captured",
            description=f"Responder successfully captured {result['credentials_captured']} NTLMv2 hash(es) "
            f"via LLMNR/NBT-NS poisoning. These hashes can be cracked offline.",
            severity="high",
            tool="responder",
            evidence=result["summary"],
        )
