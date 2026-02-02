"""
Network utilities for security validation.

Provides functions for detecting VM host (gateway) and validating
that Ollama connections only go to trusted destinations.
"""

import re
import socket
import subprocess
from typing import Optional, Tuple
from urllib.parse import urlparse


def get_default_gateway() -> Optional[str]:
    """
    Get the default gateway IP address.

    On a VM, the default gateway is typically the host machine.

    Returns:
        Gateway IP address or None if detection fails
    """
    try:
        # Try using 'ip route' (Linux)
        result = subprocess.run(
            ["ip", "route", "show", "default"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            # Parse: "default via 10.0.0.1 dev eth0 ..."
            match = re.search(r"default via (\d+\.\d+\.\d+\.\d+)", result.stdout)
            if match:
                return match.group(1)
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    try:
        # Fallback: 'route -n' (older Linux)
        result = subprocess.run(
            ["route", "-n"], capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            for line in result.stdout.split("\n"):
                if line.startswith(
                    "0.0.0.0"
                ):  # nosec B104 - parsing route output, not binding
                    parts = line.split()
                    if len(parts) >= 2:
                        return parts[1]
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    try:
        # Fallback: netifaces if available
        import netifaces

        gateways = netifaces.gateways()
        default = gateways.get("default", {})
        if netifaces.AF_INET in default:
            return default[netifaces.AF_INET][0]
    except ImportError:
        pass

    return None


def extract_host_from_url(url: str) -> Optional[str]:
    """
    Extract the host/IP from a URL.

    Args:
        url: URL like 'http://10.0.0.28:11434'

    Returns:
        Host/IP portion or None
    """
    try:
        parsed = urlparse(url)
        return parsed.hostname
    except Exception:
        return None


def is_localhost(host: str) -> bool:
    """Check if host is localhost."""
    if not host:
        return False
    return host in ("localhost", "127.0.0.1", "::1")


def is_private_ip(ip: str) -> bool:
    """
    Check if an IP address is in a private RFC 1918 range.

    Private ranges:
    - 10.0.0.0/8 (10.x.x.x)
    - 172.16.0.0/12 (172.16.x.x - 172.31.x.x)
    - 192.168.0.0/16 (192.168.x.x)

    Args:
        ip: IP address string

    Returns:
        True if private network IP
    """
    if not ip:
        return False

    try:
        parts = ip.split(".")
        if len(parts) != 4:
            return False

        octets = [int(p) for p in parts]

        # 10.0.0.0/8
        if octets[0] == 10:
            return True

        # 172.16.0.0/12
        if octets[0] == 172 and 16 <= octets[1] <= 31:
            return True

        # 192.168.0.0/16
        if octets[0] == 192 and octets[1] == 168:
            return True

        return False
    except (ValueError, IndexError):
        return False


def is_valid_ollama_host(url: str) -> Tuple[bool, str]:
    """
    Validate that an Ollama URL points to a trusted destination.

    Only allows:
    - localhost (127.0.0.1, localhost)
    - Private network IPs (RFC 1918: 10.x, 172.16-31.x, 192.168.x)

    Blocks public internet IPs to prevent accidental data exfiltration.

    Args:
        url: Ollama URL to validate

    Returns:
        Tuple of (is_valid, reason)
    """
    host = extract_host_from_url(url)

    if not host:
        return False, "Could not parse URL"

    # Localhost is always allowed
    if is_localhost(host):
        return True, "localhost"

    # Private network IPs are allowed (local network machines)
    if is_private_ip(host):
        return True, "local network"

    # Block public IPs and hostnames
    return False, f"Only localhost or local network IPs allowed. Got: {host}"


def get_ollama_host_info() -> dict:
    """
    Get information about allowed Ollama hosts.

    Returns:
        Dict with allowed host info
    """
    return {
        "allowed_hosts": [
            "localhost",
            "127.0.0.1",
            "10.x.x.x",
            "172.16-31.x.x",
            "192.168.x.x",
        ],
        "description": "Localhost and private network IPs (RFC 1918)",
        "blocked": "Public internet IPs and hostnames",
    }
