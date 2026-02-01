#!/usr/bin/env python3
"""
souleyez.parsers.hydra_parser

Parses Hydra brute-force attack output and extracts successful credentials.
"""

import re
from typing import Any, Dict, List, Optional


def parse_hydra_output(output: str, target: str = "") -> Dict[str, Any]:
    """
    Parse Hydra output and extract successful login credentials.

    Hydra output format:
    Hydra v9.5 (c) 2023 by van Hauser/THC
    [DATA] max 16 tasks per 1 server, overall 16 tasks
    [DATA] attacking ssh://192.168.1.10:22/
    [22][ssh] host: 192.168.1.10   login: admin   password: password123
    [22][ssh] host: 192.168.1.10   login: root   password: toor
    [STATUS] attack finished for 192.168.1.10 (valid pair found)

    For WordPress http-post-form attacks:
    - If redirect to /wp-admin/ is found, credentials are fully valid
    - If no redirect, only the username is validated (password was wrong)

    Args:
        output: Raw hydra output text
        target: Target host from job

    Returns:
        Dict with structure:
        {
            'target_host': str,
            'service': str,  # ssh, ftp, smb, etc.
            'port': int,
            'credentials': [
                {
                    'username': str,
                    'password': str,
                    'service': str,
                    'port': int,
                    'username_only': bool  # True if only username validated
                }
            ],
            'usernames': [str],  # Validated usernames (password unknown)
            'attempts': int,  # Total attempts if available
            'status': str  # 'success', 'failed', 'partial'
        }
    """
    result = {
        "target_host": target,
        "service": None,
        "port": None,
        "credentials": [],
        "usernames": [],  # For username-only enumeration results
        "attempts": 0,
        "status": "failed",
    }

    lines = output.split("\n")

    # Check for WordPress admin redirect (indicates successful login)
    has_wp_admin_redirect = bool(
        re.search(r"redirected to.*[:/]wp-admin", output, re.IGNORECASE)
    )

    # Detect if this is a WordPress/http-post-form attack
    is_wordpress_attack = "http-post-form" in output.lower() and (
        "wp-login" in output.lower() or "wordpress" in output.lower()
    )

    # Track attempted credentials from [ATTEMPT] lines (for when Hydra doesn't report match lines)
    last_attempt = None

    for line in lines:
        line_stripped = line.strip()

        # Parse [ATTEMPT] lines to capture what credentials were tried
        # Format: [ATTEMPT] target HOST - login "USER" - pass "PASS" - N of M [child X] (Y/Z)
        attempt_match = re.search(
            r'\[ATTEMPT\]\s+target\s+(\S+)\s+-\s+login\s+"([^"]+)"\s+-\s+pass\s+"([^"]+)"',
            line_stripped,
        )
        if attempt_match:
            last_attempt = {
                "host": attempt_match.group(1),
                "username": attempt_match.group(2),
                "password": attempt_match.group(3),
            }

        # Parse successful login lines with multiple format support
        # Format 1: [PORT][SERVICE] host: HOST   login: USER   password: PASS
        # Format 2: [PORT][SERVICE] host: HOST  login: USER  password: PASS (single space)
        # Format 3: [SERVICE][PORT] host: HOST login: USER password: PASS (swapped)
        # Format 4: [PORT][SERVICE] HOST login: USER password: PASS (no "host:")

        login_match = None
        port = None
        service = None
        host = None
        username = None
        password = None

        # Try standard format: [PORT][SERVICE] host: HOST login: USER password: PASS
        login_match = re.search(
            r"\[(\d+)\]\[([\w-]+)\]\s+host:\s*(\S+)\s+login:\s*(\S+)\s+password:\s*(.+)",
            line_stripped,
            re.IGNORECASE,
        )
        if login_match:
            port = int(login_match.group(1))
            service = login_match.group(2).lower()
            host = login_match.group(3)
            username = login_match.group(4)
            password = login_match.group(5).strip()

        # Try swapped format: [SERVICE][PORT]
        if not login_match:
            login_match = re.search(
                r"\[([\w-]+)\]\[(\d+)\]\s+host:\s*(\S+)\s+login:\s*(\S+)\s+password:\s*(.+)",
                line_stripped,
                re.IGNORECASE,
            )
            if login_match:
                service = login_match.group(1).lower()
                port = int(login_match.group(2))
                host = login_match.group(3)
                username = login_match.group(4)
                password = login_match.group(5).strip()

        # Try format without "host:" label
        if not login_match:
            login_match = re.search(
                r"\[(\d+)\]\[([\w-]+)\]\s+(\d+\.\d+\.\d+\.\d+|\S+)\s+login:\s*(\S+)\s+password:\s*(.+)",
                line_stripped,
                re.IGNORECASE,
            )
            if login_match:
                port = int(login_match.group(1))
                service = login_match.group(2).lower()
                host = login_match.group(3)
                username = login_match.group(4)
                password = login_match.group(5).strip()

        # Try flexible format with any whitespace between fields
        # Note: Use \s+login: to require whitespace before "login:" and require the colon
        # This prevents matching "login" inside paths like "wp-login.php"
        if not login_match:
            login_match = re.search(
                r"\[(\d+)\]\[([\w-]+)\].*?(?:host:?\s*)?(\d+\.\d+\.\d+\.\d+|\S+\.\S+).*?\s+login:\s*(\S+).*?password:\s*(.+)",
                line_stripped,
                re.IGNORECASE,
            )
            if login_match:
                port = int(login_match.group(1))
                service = login_match.group(2).lower()
                host = login_match.group(3)
                username = login_match.group(4)
                password = login_match.group(5).strip()

        if login_match and port and service and username:
            # Store service info if not already set
            if not result["service"]:
                result["service"] = service
            if not result["port"]:
                result["port"] = port
            if not result["target_host"] or result["target_host"] == "":
                result["target_host"] = host

            # For WordPress attacks, check if this is a full credential or just username enumeration
            if is_wordpress_attack and not has_wp_admin_redirect:
                # No redirect to wp-admin means only username was validated
                # (password was wrong but username exists)
                if username not in result["usernames"]:
                    result["usernames"].append(username)
                result["status"] = "partial"  # Partial success - username found
            else:
                # Full credential validation (redirect found or non-WordPress service)
                credential = {
                    "username": username,
                    "password": password,
                    "service": service,
                    "port": port,
                    "host": host,
                    "username_only": False,
                }

                result["credentials"].append(credential)
                result["status"] = "success"

        # Extract attacking target info
        attacking_match = re.search(
            r"attacking\s+([\w-]+)://([^:]+):(\d+)", line_stripped
        )
        if attacking_match:
            result["service"] = attacking_match.group(1).lower()
            if not result["target_host"] or result["target_host"] == "":
                result["target_host"] = attacking_match.group(2)
            result["port"] = int(attacking_match.group(3))

        # Extract attempt count
        attempts_match = re.search(r"(\d+)\s+tasks", line_stripped)
        if attempts_match:
            result["attempts"] = int(attempts_match.group(1))

    # For WordPress attacks: If we see wp-admin redirect but no match lines were found,
    # extract credentials from the last ATTEMPT line (handles F=loginform case where
    # Hydra doesn't produce match lines even for valid credentials)
    if (
        is_wordpress_attack
        and has_wp_admin_redirect
        and not result["credentials"]
        and last_attempt
    ):
        credential = {
            "username": last_attempt["username"],
            "password": last_attempt["password"],
            "service": result.get("service", "http-post-form"),
            "port": result.get("port", 80),
            "host": last_attempt["host"],
            "username_only": False,
        }
        result["credentials"].append(credential)
        result["status"] = "success"

    # Determine final status
    if result["credentials"]:
        result["status"] = "success"
    elif result["usernames"]:
        result["status"] = "partial"
    elif "attack finished" in output.lower():
        result["status"] = "failed"
    else:
        result["status"] = "partial"

    return result


def map_to_credentials(
    parsed_data: Dict[str, Any], engagement_id: int, host_id: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Convert parsed Hydra data into credential records for database storage.

    Args:
        parsed_data: Output from parse_hydra_output()
        engagement_id: Current engagement ID
        host_id: Optional host ID if known

    Returns:
        List of credential dicts ready for CredentialManager.add()
    """
    credentials = []

    for cred in parsed_data.get("credentials", []):
        credential = {
            "username": cred["username"],
            "password": cred["password"],
            "credential_type": _service_to_credential_type(cred["service"]),
            "source": "hydra",
            "validation_status": "confirmed",  # Hydra only reports successful logins
            "notes": f"Brute-forced via Hydra on {cred['service']}:{cred['port']}",
            "target": f"{parsed_data.get('target_host')}:{cred['port']}",
            "service": cred["service"],
            "port": cred["port"],
        }

        if host_id:
            credential["host_id"] = host_id

        credentials.append(credential)

    return credentials


def _service_to_credential_type(service: str) -> str:
    """
    Map service name to credential type.

    Args:
        service: Service name (ssh, ftp, smb, etc.)

    Returns:
        Credential type string
    """
    service_lower = service.lower()

    type_map = {
        "ssh": "ssh",
        "ftp": "ftp",
        "smb": "windows",
        "rdp": "windows",
        "mysql": "database",
        "postgres": "database",
        "postgresql": "database",
        "mssql": "database",
        "oracle": "database",
        "http": "web",
        "https": "web",
        "http-get": "web",
        "http-post": "web",
        "http-get-form": "web",
        "http-post-form": "web",
        "https-get-form": "web",
        "https-post-form": "web",
        "telnet": "telnet",
        "vnc": "vnc",
        "ldap": "ldap",
    }

    return type_map.get(service_lower, "other")


def generate_summary(parsed_data: Dict[str, Any]) -> str:
    """
    Generate a human-readable summary of the Hydra attack results.

    Args:
        parsed_data: Output from parse_hydra_output()

    Returns:
        Formatted summary string
    """
    target = parsed_data.get("target_host", "unknown")
    service = parsed_data.get("service", "unknown")
    port = parsed_data.get("port", "unknown")
    creds = parsed_data.get("credentials", [])
    usernames = parsed_data.get("usernames", [])
    status = parsed_data.get("status", "unknown")

    summary = "Hydra Attack Summary\n"
    summary += f"{'=' * 50}\n"
    summary += f"Target: {target}:{port}\n"
    summary += f"Service: {service}\n"
    summary += f"Status: {status}\n"
    summary += f"Credentials Found: {len(creds)}\n"
    summary += f"Valid Usernames Found: {len(usernames)}\n"

    if creds:
        summary += "\nSuccessful Logins:\n"
        summary += f"{'-' * 50}\n"
        for i, cred in enumerate(creds, 1):
            summary += f"{i}. {cred['username']}:{cred['password']} ({cred['service']}:{cred['port']})\n"

    if usernames:
        summary += "\nValid Usernames (password unknown):\n"
        summary += f"{'-' * 50}\n"
        for i, username in enumerate(usernames, 1):
            summary += f"{i}. {username}\n"

    if not creds and not usernames:
        summary += "\nNo valid credentials or usernames found.\n"

    return summary


def extract_failed_attempts(output: str) -> Dict[str, int]:
    """
    Extract statistics about failed login attempts.

    Useful for understanding brute-force effectiveness.

    Args:
        output: Raw hydra output text

    Returns:
        Dict with failure statistics
    """
    stats = {"total_attempts": 0, "successful": 0, "failed": 0}

    # Count login attempts (successful ones)
    successful_count = len(re.findall(r"\[\d+\]\[\w+\]\s+host:", output))
    stats["successful"] = successful_count

    # Try to extract total from status messages
    status_match = re.search(r"(\d+)\s+valid passwords? found", output, re.IGNORECASE)
    if status_match:
        stats["successful"] = int(status_match.group(1))

    return stats


# Export the main functions
__all__ = [
    "parse_hydra_output",
    "map_to_credentials",
    "generate_summary",
    "extract_failed_attempts",
]
