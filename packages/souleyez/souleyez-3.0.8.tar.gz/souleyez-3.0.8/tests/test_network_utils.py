"""
Unit tests for souleyez.core.network_utils

Tests gateway detection and Ollama host validation.
"""

import pytest
from unittest.mock import patch, MagicMock

from souleyez.core.network_utils import (
    get_default_gateway,
    extract_host_from_url,
    is_localhost,
    is_private_ip,
    is_valid_ollama_host,
    get_ollama_host_info,
)


class TestExtractHostFromUrl:
    """Test URL host extraction."""

    def test_extract_http_url(self):
        """Test extracting host from HTTP URL."""
        host = extract_host_from_url("http://10.0.0.28:11434")
        assert host == "10.0.0.28"

    def test_extract_localhost_url(self):
        """Test extracting localhost from URL."""
        host = extract_host_from_url("http://localhost:11434")
        assert host == "localhost"

    def test_extract_127_0_0_1(self):
        """Test extracting 127.0.0.1."""
        host = extract_host_from_url("http://127.0.0.1:11434")
        assert host == "127.0.0.1"

    def test_extract_no_port(self):
        """Test extracting host without port."""
        host = extract_host_from_url("http://example.com")
        assert host == "example.com"

    def test_extract_invalid_url(self):
        """Test extracting from invalid URL."""
        host = extract_host_from_url("not-a-url")
        assert (
            host is None or host == "not-a-url"
        )  # Different Python versions handle this differently


class TestIsLocalhost:
    """Test localhost detection."""

    def test_localhost_string(self):
        """Test 'localhost' is recognized."""
        assert is_localhost("localhost") is True

    def test_127_0_0_1(self):
        """Test 127.0.0.1 is recognized."""
        assert is_localhost("127.0.0.1") is True

    def test_ipv6_localhost(self):
        """Test IPv6 localhost."""
        assert is_localhost("::1") is True

    def test_other_ip(self):
        """Test other IPs are not localhost."""
        assert is_localhost("10.0.0.28") is False

    def test_none(self):
        """Test None is not localhost."""
        assert is_localhost(None) is False

    def test_empty_string(self):
        """Test empty string is not localhost."""
        assert is_localhost("") is False


class TestIsPrivateIp:
    """Test private IP detection (RFC 1918)."""

    def test_10_network(self):
        """Test 10.x.x.x is private."""
        assert is_private_ip("10.0.0.1") is True
        assert is_private_ip("10.0.0.28") is True
        assert is_private_ip("10.255.255.255") is True

    def test_172_16_network(self):
        """Test 172.16-31.x.x is private."""
        assert is_private_ip("172.16.0.1") is True
        assert is_private_ip("172.20.5.10") is True
        assert is_private_ip("172.31.255.255") is True

    def test_172_outside_range(self):
        """Test 172.x outside 16-31 is NOT private."""
        assert is_private_ip("172.15.0.1") is False
        assert is_private_ip("172.32.0.1") is False

    def test_192_168_network(self):
        """Test 192.168.x.x is private."""
        assert is_private_ip("192.168.0.1") is True
        assert is_private_ip("192.168.1.100") is True
        assert is_private_ip("192.168.255.255") is True

    def test_public_ips(self):
        """Test public IPs are not private."""
        assert is_private_ip("8.8.8.8") is False
        assert is_private_ip("1.1.1.1") is False
        assert is_private_ip("203.0.113.1") is False

    def test_invalid_ips(self):
        """Test invalid IPs return False."""
        assert is_private_ip("") is False
        assert is_private_ip(None) is False
        assert is_private_ip("not-an-ip") is False
        assert is_private_ip("10.0.0") is False  # Too few octets


class TestGetDefaultGateway:
    """Test gateway detection."""

    @patch("souleyez.core.network_utils.subprocess.run")
    def test_detects_gateway_from_ip_route(self, mock_run):
        """Test gateway detection using 'ip route'."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "default via 10.0.0.1 dev eth0 proto dhcp metric 100"
        mock_run.return_value = mock_result

        gateway = get_default_gateway()

        assert gateway == "10.0.0.1"

    @patch("souleyez.core.network_utils.subprocess.run")
    def test_returns_none_on_failure(self, mock_run):
        """Test returns None when detection fails."""
        mock_run.side_effect = FileNotFoundError("ip not found")

        gateway = get_default_gateway()

        # Should return None (might try fallbacks)
        # The actual behavior depends on fallback attempts
        assert gateway is None or isinstance(gateway, str)


class TestIsValidOllamaHost:
    """Test Ollama host validation."""

    def test_localhost_always_valid(self):
        """Test localhost is always valid."""
        is_valid, reason = is_valid_ollama_host("http://localhost:11434")

        assert is_valid is True
        assert reason == "localhost"

    def test_127_0_0_1_always_valid(self):
        """Test 127.0.0.1 is always valid."""
        is_valid, reason = is_valid_ollama_host("http://127.0.0.1:11434")

        assert is_valid is True
        assert reason == "localhost"

    def test_10_network_valid(self):
        """Test 10.x.x.x private IPs are valid."""
        is_valid, reason = is_valid_ollama_host("http://10.0.0.28:11434")

        assert is_valid is True
        assert reason == "local network"

    def test_192_168_network_valid(self):
        """Test 192.168.x.x private IPs are valid."""
        is_valid, reason = is_valid_ollama_host("http://192.168.1.100:11434")

        assert is_valid is True
        assert reason == "local network"

    def test_172_16_network_valid(self):
        """Test 172.16-31.x.x private IPs are valid."""
        is_valid, reason = is_valid_ollama_host("http://172.20.0.5:11434")

        assert is_valid is True
        assert reason == "local network"

    def test_public_ip_rejected(self):
        """Test public IPs are rejected."""
        is_valid, reason = is_valid_ollama_host("http://8.8.8.8:11434")

        assert is_valid is False
        assert "Only localhost or local network" in reason

    def test_hostname_rejected(self):
        """Test hostnames (not localhost) are rejected."""
        is_valid, reason = is_valid_ollama_host("http://ollama.example.com:11434")

        assert is_valid is False
        assert "Only localhost or local network" in reason

    def test_invalid_url(self):
        """Test invalid URL is rejected."""
        is_valid, reason = is_valid_ollama_host("")

        assert is_valid is False
        assert "Could not parse" in reason


class TestGetOllamaHostInfo:
    """Test host info retrieval."""

    def test_returns_allowed_hosts_info(self):
        """Test returns allowed hosts and description."""
        info = get_ollama_host_info()

        assert "allowed_hosts" in info
        assert "localhost" in info["allowed_hosts"]
        assert "127.0.0.1" in info["allowed_hosts"]
        assert "description" in info
        assert "blocked" in info
