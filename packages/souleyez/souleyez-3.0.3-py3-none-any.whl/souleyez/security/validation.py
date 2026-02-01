#!/usr/bin/env python3
"""
Input validation and sanitization for security-critical operations.
"""

import ipaddress
import re
import shlex
from pathlib import Path
from typing import List, Optional, Union

from souleyez.log_config import get_logger

logger = get_logger(__name__)


class ValidationError(Exception):
    """Raised when input validation fails."""

    pass


# ===== IP ADDRESS VALIDATION =====


def validate_ip_address(ip: str) -> str:
    """
    Validate and normalize an IP address.

    Args:
        ip: IP address string

    Returns:
        Normalized IP address string

    Raises:
        ValidationError: If IP is invalid
    """
    try:
        # This handles both IPv4 and IPv6
        ip_obj = ipaddress.ip_address(ip)
        return str(ip_obj)
    except ValueError as e:
        logger.warning("Invalid IP address", extra={"input": ip, "error": str(e)})
        raise ValidationError(f"Invalid IP address: {ip}")


def validate_cidr(cidr: str) -> str:
    """
    Validate and normalize a CIDR notation network.

    Args:
        cidr: CIDR string (e.g., "192.168.1.0/24")

    Returns:
        Normalized CIDR string

    Raises:
        ValidationError: If CIDR is invalid
    """
    try:
        network = ipaddress.ip_network(cidr, strict=False)
        return str(network)
    except ValueError as e:
        logger.warning("Invalid CIDR notation", extra={"input": cidr, "error": str(e)})
        raise ValidationError(f"Invalid CIDR notation: {cidr}")


def validate_hostname(hostname: str) -> str:
    """
    Validate hostname format.

    Args:
        hostname: Hostname string

    Returns:
        Validated hostname

    Raises:
        ValidationError: If hostname is invalid
    """
    # RFC 1123 hostname rules
    if not hostname or len(hostname) > 253:
        raise ValidationError("Hostname must be 1-253 characters")

    # Valid hostname regex
    hostname_pattern = re.compile(
        r"^(?!-)[A-Za-z0-9-]{1,63}(?<!-)(\.[A-Za-z0-9-]{1,63})*$"
    )

    if not hostname_pattern.match(hostname):
        logger.warning("Invalid hostname format", extra={"input": hostname})
        raise ValidationError(f"Invalid hostname format: {hostname}")

    return hostname


# ===== PORT VALIDATION =====


def validate_port(port: Union[int, str]) -> int:
    """
    Validate port number.

    Args:
        port: Port number (1-65535)

    Returns:
        Validated port as integer

    Raises:
        ValidationError: If port is invalid
    """
    try:
        port_num = int(port)
        if not (1 <= port_num <= 65535):
            raise ValidationError(f"Port must be between 1-65535, got: {port}")
        return port_num
    except (ValueError, TypeError):
        raise ValidationError(f"Invalid port number: {port}")


def validate_port_list(ports: str) -> str:
    """
    Validate and sanitize port list for nmap.

    Args:
        ports: Port specification (e.g., "80,443", "1-1000", "80,443,8000-9000")

    Returns:
        Validated port string

    Raises:
        ValidationError: If port specification is invalid
    """
    # Allow comma-separated ports and ranges
    port_pattern = re.compile(r"^[0-9,\-]+$")

    if not port_pattern.match(ports):
        raise ValidationError(f"Invalid port specification: {ports}")

    # Validate each component
    for part in ports.split(","):
        if "-" in part:
            # Range
            try:
                start, end = part.split("-")
                start_port = validate_port(start)
                end_port = validate_port(end)
                if start_port > end_port:
                    raise ValidationError(f"Invalid port range: {part}")
            except ValueError:
                raise ValidationError(f"Invalid port range format: {part}")
        else:
            # Single port
            validate_port(part)

    return ports


# ===== PATH VALIDATION =====


def validate_file_path(
    path: Union[str, Path],
    must_exist: bool = False,
    allowed_dirs: Optional[List[Path]] = None,
) -> Path:
    """
    Validate and sanitize file path to prevent directory traversal.

    Args:
        path: File path to validate
        must_exist: If True, path must exist
        allowed_dirs: List of allowed parent directories (None = user's .souleyez dir only)

    Returns:
        Resolved absolute Path object

    Raises:
        ValidationError: If path is invalid or unsafe
    """
    try:
        path_obj = Path(path).expanduser().resolve()
    except Exception as e:
        raise ValidationError(f"Invalid path: {path} - {e}")

    # Default to only allowing .souleyez directory
    if allowed_dirs is None:
        allowed_dirs = [Path.home() / ".souleyez"]

    # Ensure resolved path is within allowed directories
    is_allowed = False
    for allowed_dir in allowed_dirs:
        allowed_resolved = allowed_dir.expanduser().resolve()
        try:
            path_obj.relative_to(allowed_resolved)
            is_allowed = True
            break
        except ValueError:
            continue

    if not is_allowed:
        logger.warning(
            "Path traversal attempt blocked",
            extra={
                "requested_path": str(path),
                "resolved_path": str(path_obj),
                "allowed_dirs": [str(d) for d in allowed_dirs],
            },
        )
        raise ValidationError(f"Path outside allowed directories: {path}")

    if must_exist and not path_obj.exists():
        raise ValidationError(f"Path does not exist: {path}")

    return path_obj


# ===== COMMAND INJECTION PREVENTION =====


def sanitize_command_arg(arg: str) -> str:
    """
    Sanitize a single command argument using shlex.

    Args:
        arg: Command argument to sanitize

    Returns:
        Safely quoted argument
    """
    return shlex.quote(str(arg))


def validate_nmap_args(args: List[str]) -> List[str]:
    """
    Validate nmap arguments to prevent command injection.

    Args:
        args: List of nmap arguments

    Returns:
        Validated argument list

    Raises:
        ValidationError: If dangerous arguments detected
    """
    # Dangerous patterns that could lead to command injection
    # These patterns should only match within script arguments
    dangerous_patterns = [
        r"--script[=\s].*&&",  # Command chaining in scripts
        r"--script[=\s].*;",  # Command separator in scripts
        r"--script[=\s].*\|",  # Pipe in scripts
        r"--script[=\s].*`",  # Command substitution in scripts
        r"--script[=\s].*\$",  # Variable expansion in scripts
    ]

    # Blocked arguments that could be abused
    blocked_args = [
        "--interactive",  # Interactive mode
        "--iflist",  # Could reveal sensitive info
    ]

    validated_args = []
    for arg in args:
        # Check for dangerous patterns
        for pattern in dangerous_patterns:
            if re.search(pattern, arg):
                logger.warning(
                    "Blocked dangerous nmap argument",
                    extra={"argument": arg, "pattern": pattern},
                )
                raise ValidationError(f"Dangerous nmap argument blocked: {arg}")

        # Check for blocked arguments
        arg_lower = arg.lower()
        for blocked in blocked_args:
            if arg_lower.startswith(blocked):
                logger.warning("Blocked nmap argument", extra={"argument": arg})
                raise ValidationError(f"Blocked nmap argument: {arg}")

        validated_args.append(arg)

    return validated_args


# ===== SQL INJECTION PREVENTION =====


def validate_table_name(table: str) -> str:
    """
    Validate table name to prevent SQL injection.
    Only alphanumeric and underscore allowed.

    Args:
        table: Table name

    Returns:
        Validated table name

    Raises:
        ValidationError: If table name is invalid
    """
    if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", table):
        raise ValidationError(f"Invalid table name: {table}")
    return table


def validate_column_name(column: str) -> str:
    """
    Validate column name to prevent SQL injection.
    Only alphanumeric and underscore allowed.

    Args:
        column: Column name

    Returns:
        Validated column name

    Raises:
        ValidationError: If column name is invalid
    """
    if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", column):
        raise ValidationError(f"Invalid column name: {column}")
    return column


def validate_severity(severity: str) -> str:
    """
    Validate finding severity level.

    Args:
        severity: Severity string

    Returns:
        Validated severity (lowercase)

    Raises:
        ValidationError: If severity is invalid
    """
    valid_severities = ["critical", "high", "medium", "low", "info"]
    severity_lower = severity.lower()

    if severity_lower not in valid_severities:
        raise ValidationError(
            f"Invalid severity: {severity}. Must be one of: {valid_severities}"
        )

    return severity_lower


# ===== HTML/XSS PREVENTION =====


def escape_html(text: str) -> str:
    """
    Escape HTML special characters to prevent XSS.

    Args:
        text: Text to escape

    Returns:
        HTML-escaped text
    """
    if text is None:
        return ""

    escape_dict = {
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#x27;",
        "/": "&#x2F;",
    }

    return "".join(escape_dict.get(c, c) for c in str(text))


def sanitize_for_json(text: str) -> str:
    """
    Sanitize text for safe inclusion in JSON.

    Args:
        text: Text to sanitize

    Returns:
        Sanitized text
    """
    if text is None:
        return ""

    # Remove control characters
    text = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", str(text))
    return text


# ===== ENGAGEMENT NAME VALIDATION =====


def validate_engagement_name(name: str) -> str:
    """
    Validate engagement name.

    Args:
        name: Engagement name

    Returns:
        Validated name

    Raises:
        ValidationError: If name is invalid
    """
    if not name or len(name) < 1:
        raise ValidationError("Engagement name cannot be empty")

    if len(name) > 255:
        raise ValidationError("Engagement name too long (max 255 characters)")

    # Prevent path traversal in names
    if "/" in name or "\\" in name or ".." in name:
        raise ValidationError("Engagement name cannot contain path separators")

    return name.strip()


# ===== PLUGIN NAME VALIDATION =====


def validate_plugin_name(plugin: str) -> str:
    """
    Validate plugin name to prevent code injection.

    Args:
        plugin: Plugin name

    Returns:
        Validated plugin name

    Raises:
        ValidationError: If plugin name is invalid
    """
    # Only lowercase letters, numbers, underscores
    if not re.match(r"^[a-z][a-z0-9_]*$", plugin):
        raise ValidationError(f"Invalid plugin name: {plugin}")

    if len(plugin) > 50:
        raise ValidationError("Plugin name too long")

    return plugin


# ===== PROTOCOL VALIDATION =====


def validate_protocol(protocol: str) -> str:
    """
    Validate network protocol.

    Args:
        protocol: Protocol string (tcp, udp, etc.)

    Returns:
        Validated protocol (lowercase)

    Raises:
        ValidationError: If protocol is invalid
    """
    valid_protocols = ["tcp", "udp", "icmp", "sctp"]
    protocol_lower = protocol.lower()

    if protocol_lower not in valid_protocols:
        raise ValidationError(
            f"Invalid protocol: {protocol}. Must be one of: {valid_protocols}"
        )

    return protocol_lower


# ===== UNIVERSAL TARGET VALIDATION =====


def validate_target(target: str) -> str:
    """
    Validate a target which can be IP, CIDR, or hostname.
    Tries each format in order and returns the first match.

    Args:
        target: Target string (IP, CIDR, or hostname)

    Returns:
        Validated target string

    Raises:
        ValidationError: If target is not valid in any format
    """
    if not target or not target.strip():
        raise ValidationError("Target cannot be empty")

    target = target.strip()

    # Try IP address
    try:
        return validate_ip_address(target)
    except ValidationError:
        pass

    # Try CIDR notation
    try:
        return validate_cidr(target)
    except ValidationError:
        pass

    # Try hostname
    try:
        return validate_hostname(target)
    except ValidationError:
        pass

    # Nothing matched
    raise ValidationError(
        f"Invalid target: '{target}'. Must be IP address, CIDR notation, or valid hostname"
    )


# ===== URL VALIDATION =====


def validate_url(url: str) -> str:
    """
    Validate URL format for web-based tools.

    Args:
        url: URL string

    Returns:
        Validated URL

    Raises:
        ValidationError: If URL is invalid
    """
    if not url or not url.strip():
        raise ValidationError("URL cannot be empty")

    url = url.strip()

    # Basic URL pattern (http/https only)
    import re

    url_pattern = re.compile(
        r"^https?://"  # http:// or https://
        r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"  # domain
        r"localhost|"  # localhost
        r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # or IP
        r"(?::\d+)?"  # optional port
        r"(?:/?|[/?]\S+)$",
        re.IGNORECASE,  # optional path
    )

    if not url_pattern.match(url):
        raise ValidationError(
            f"Invalid URL format: {url}. Must start with http:// or https://"
        )

    # Block dangerous protocols
    if url.lower().startswith(("file://", "ftp://", "javascript:", "data:")):
        raise ValidationError(f"Dangerous URL protocol blocked: {url}")

    return url


def validate_target_or_url(target: str) -> str:
    """
    Validate a target which can be IP, CIDR, hostname, or URL.
    Tries each format in order and returns the first match.

    Args:
        target: Target string (IP, CIDR, hostname, or URL)

    Returns:
        Validated target string

    Raises:
        ValidationError: If target is not valid in any format
    """
    if not target or not target.strip():
        raise ValidationError("Target cannot be empty")

    target = target.strip()

    # Try URL first (if it has a scheme)
    if target.startswith(("http://", "https://")):
        try:
            return validate_url(target)
        except ValidationError:
            pass

    # Try IP address
    try:
        return validate_ip_address(target)
    except ValidationError:
        pass

    # Try CIDR notation
    try:
        return validate_cidr(target)
    except ValidationError:
        pass

    # Check if input looks like an IP address attempt
    # Patterns: dot-separated numbers, or starts with numbers and dots
    # If so, don't allow fallthrough to hostname - it's an invalid IP
    ip_like_pattern = re.compile(r"^-?\d+(\.\d+)+$")  # All numeric octets
    mixed_ip_pattern = re.compile(
        r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.[a-zA-Z]"
    )  # 3 numeric octets + letters
    if ip_like_pattern.match(target) or mixed_ip_pattern.match(target):
        # Looks like an IP but failed IP validation - reject it
        raise ValidationError(
            f"Invalid IP address: '{target}'. "
            "Each octet must be 0-255 (e.g., 192.168.1.1)"
        )

    # Try hostname (more lenient pattern for domains)
    # Allow single-part hostnames and domains
    hostname_pattern = re.compile(
        r"^(?!-)[A-Za-z0-9-]{1,63}(?<!-)(\.[A-Za-z0-9-]{1,63})*\.?$"
    )
    if hostname_pattern.match(target) and len(target) <= 253:
        return target

    # Nothing matched
    raise ValidationError(
        f"Invalid target: '{target}'. Must be IP address, CIDR notation, hostname, or URL"
    )
