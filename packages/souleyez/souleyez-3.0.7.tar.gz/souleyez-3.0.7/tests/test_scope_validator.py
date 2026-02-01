#!/usr/bin/env python3
"""
Tests for engagement scope validation.
"""
import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from souleyez.security.scope_validator import (
    ScopeValidator,
    ScopeValidationResult,
    ScopeViolationError,
    ScopeManager,
)


# ===== FIXTURES =====


@pytest.fixture
def mock_db():
    """Create a mock database for testing."""
    with patch("souleyez.security.scope_validator.get_db") as mock:
        db = MagicMock()
        mock.return_value = db
        yield db


@pytest.fixture
def validator_no_scope(mock_db):
    """Create a validator with no scope defined."""
    mock_db.execute.return_value = []  # No scope entries
    mock_db.execute_one.return_value = {"scope_enforcement": "warn"}
    return ScopeValidator(engagement_id=1)


@pytest.fixture
def validator_cidr_scope(mock_db):
    """Create a validator with CIDR scope."""
    mock_db.execute.return_value = [
        {
            "id": 1,
            "scope_type": "cidr",
            "value": "192.168.1.0/24",
            "is_excluded": False,
            "description": "Internal network",
        }
    ]
    mock_db.execute_one.return_value = {"scope_enforcement": "block"}
    return ScopeValidator(engagement_id=1)


@pytest.fixture
def validator_domain_scope(mock_db):
    """Create a validator with domain scope."""
    mock_db.execute.return_value = [
        {
            "id": 1,
            "scope_type": "domain",
            "value": "*.example.com",
            "is_excluded": False,
            "description": "Example domain",
        },
        {
            "id": 2,
            "scope_type": "domain",
            "value": "test.org",
            "is_excluded": False,
            "description": "Test domain",
        },
    ]
    mock_db.execute_one.return_value = {"scope_enforcement": "warn"}
    return ScopeValidator(engagement_id=1)


@pytest.fixture
def validator_mixed_scope(mock_db):
    """Create a validator with mixed scope (inclusions and exclusions)."""
    mock_db.execute.return_value = [
        # Inclusions first (sorted by is_excluded ASC)
        {
            "id": 1,
            "scope_type": "cidr",
            "value": "10.0.0.0/8",
            "is_excluded": False,
            "description": "Private network",
        },
        {
            "id": 2,
            "scope_type": "domain",
            "value": "*.target.com",
            "is_excluded": False,
            "description": "Target domain",
        },
        # Exclusions
        {
            "id": 3,
            "scope_type": "cidr",
            "value": "10.0.1.0/24",
            "is_excluded": True,
            "description": "Excluded subnet",
        },
        {
            "id": 4,
            "scope_type": "hostname",
            "value": "10.0.0.1",
            "is_excluded": True,
            "description": "Excluded gateway",
        },
    ]
    mock_db.execute_one.return_value = {"scope_enforcement": "block"}
    return ScopeValidator(engagement_id=1)


# ===== NO SCOPE TESTS =====


def test_no_scope_defined_is_permissive(validator_no_scope):
    """When no scope is defined, all targets should be in scope."""
    result = validator_no_scope.validate_target("192.168.1.100")
    assert result.is_in_scope is True
    assert result.reason == "No scope defined (permissive)"


def test_has_scope_defined_false_when_empty(validator_no_scope):
    """has_scope_defined returns False when no scope entries."""
    assert validator_no_scope.has_scope_defined() is False


# ===== IP/CIDR VALIDATION TESTS =====


def test_ip_in_cidr_range(validator_cidr_scope):
    """IP within CIDR range is in scope."""
    result = validator_cidr_scope.validate_target("192.168.1.100")
    assert result.is_in_scope is True
    assert result.scope_type == "cidr"
    assert "192.168.1.0/24" in result.reason


def test_ip_outside_cidr_range(validator_cidr_scope):
    """IP outside CIDR range is out of scope."""
    result = validator_cidr_scope.validate_target("192.168.2.100")
    assert result.is_in_scope is False
    assert "does not match" in result.reason


def test_ip_at_cidr_boundary(validator_cidr_scope):
    """Test IPs at CIDR boundaries."""
    # First IP in range
    result = validator_cidr_scope.validate_target("192.168.1.0")
    assert result.is_in_scope is True

    # Last IP in range
    result = validator_cidr_scope.validate_target("192.168.1.255")
    assert result.is_in_scope is True


def test_validate_ip_method(validator_cidr_scope):
    """Test the validate_ip convenience method."""
    result = validator_cidr_scope.validate_ip("192.168.1.50")
    assert result.is_in_scope is True


# ===== DOMAIN VALIDATION TESTS =====


def test_wildcard_domain_match(validator_domain_scope):
    """Wildcard domain pattern matches subdomains."""
    # Direct subdomain
    result = validator_domain_scope.validate_target("app.example.com")
    assert result.is_in_scope is True
    assert result.scope_type == "domain"

    # Deep subdomain
    result = validator_domain_scope.validate_target("deep.sub.example.com")
    assert result.is_in_scope is True


def test_wildcard_domain_base_match(validator_domain_scope):
    """Wildcard *.example.com also matches example.com."""
    result = validator_domain_scope.validate_target("example.com")
    assert result.is_in_scope is True


def test_exact_domain_match(validator_domain_scope):
    """Exact domain match works."""
    result = validator_domain_scope.validate_target("test.org")
    assert result.is_in_scope is True


def test_domain_case_insensitive(validator_domain_scope):
    """Domain matching is case insensitive."""
    result = validator_domain_scope.validate_target("APP.EXAMPLE.COM")
    assert result.is_in_scope is True


def test_domain_not_matching(validator_domain_scope):
    """Non-matching domain is out of scope."""
    result = validator_domain_scope.validate_target("other.org")
    assert result.is_in_scope is False


def test_validate_domain_method(validator_domain_scope):
    """Test the validate_domain convenience method."""
    result = validator_domain_scope.validate_domain("sub.example.com")
    assert result.is_in_scope is True


# ===== URL VALIDATION TESTS =====


def test_url_extracts_host(validator_domain_scope):
    """URL validation extracts host for matching."""
    result = validator_domain_scope.validate_target(
        "https://app.example.com/path/to/resource"
    )
    assert result.is_in_scope is True


def test_url_with_port(validator_domain_scope):
    """URL with port is handled correctly."""
    result = validator_domain_scope.validate_target("http://app.example.com:8080/api")
    assert result.is_in_scope is True


def test_url_with_ip_in_cidr(validator_cidr_scope):
    """URL with IP address matches CIDR scope."""
    result = validator_cidr_scope.validate_target("http://192.168.1.50/admin")
    assert result.is_in_scope is True


def test_url_out_of_scope(validator_domain_scope):
    """URL for non-matching domain is out of scope."""
    result = validator_domain_scope.validate_target("https://other-site.com/page")
    assert result.is_in_scope is False


def test_validate_url_method(validator_domain_scope):
    """Test the validate_url convenience method."""
    result = validator_domain_scope.validate_url("https://test.org/api")
    assert result.is_in_scope is True


# ===== EXCLUSION TESTS =====


def test_exclusion_overrides_inclusion(validator_mixed_scope):
    """Explicit exclusion takes precedence over inclusion."""
    # 10.0.1.50 is in 10.0.0.0/8 but explicitly excluded via 10.0.1.0/24
    result = validator_mixed_scope.validate_target("10.0.1.50")
    assert result.is_in_scope is False
    assert "Explicitly excluded" in result.reason


def test_exact_ip_exclusion(validator_mixed_scope):
    """Exact IP exclusion works."""
    result = validator_mixed_scope.validate_target("10.0.0.1")
    assert result.is_in_scope is False
    assert "Explicitly excluded" in result.reason


def test_inclusion_when_not_excluded(validator_mixed_scope):
    """Target in inclusion but not in exclusion is in scope."""
    # 10.0.2.50 is in 10.0.0.0/8 and NOT in excluded 10.0.1.0/24
    result = validator_mixed_scope.validate_target("10.0.2.50")
    assert result.is_in_scope is True


# ===== EDGE CASES =====


def test_empty_target():
    """Empty target returns out of scope."""
    with patch("souleyez.security.scope_validator.get_db"):
        validator = ScopeValidator(engagement_id=1)
        result = validator.validate_target("")
        assert result.is_in_scope is False
        assert "Empty target" in result.reason


def test_whitespace_target():
    """Whitespace-only target returns out of scope."""
    with patch("souleyez.security.scope_validator.get_db"):
        validator = ScopeValidator(engagement_id=1)
        result = validator.validate_target("   ")
        assert result.is_in_scope is False


# ===== ENFORCEMENT MODE TESTS =====


def test_get_enforcement_mode(validator_cidr_scope):
    """Get enforcement mode from engagement."""
    assert validator_cidr_scope.get_enforcement_mode() == "block"


def test_enforcement_default_to_off(mock_db):
    """Default enforcement is 'off' when not set."""
    mock_db.execute.return_value = []
    mock_db.execute_one.return_value = {"scope_enforcement": None}
    validator = ScopeValidator(engagement_id=1)
    assert validator.get_enforcement_mode() == "off"


# ===== SCOPE MANAGER TESTS =====


def test_scope_manager_add_cidr(mock_db):
    """Add CIDR scope entry."""
    mock_db.insert.return_value = 1
    manager = ScopeManager()

    scope_id = manager.add_scope(
        engagement_id=1,
        scope_type="cidr",
        value="192.168.1.0/24",
        description="Test network",
    )
    assert scope_id == 1
    mock_db.insert.assert_called_once()


def test_scope_manager_add_domain_wildcard(mock_db):
    """Add wildcard domain scope entry."""
    mock_db.insert.return_value = 2
    manager = ScopeManager()

    scope_id = manager.add_scope(
        engagement_id=1, scope_type="domain", value="*.example.com"
    )
    assert scope_id == 2


def test_scope_manager_add_url(mock_db):
    """Add URL scope entry."""
    mock_db.insert.return_value = 3
    manager = ScopeManager()

    scope_id = manager.add_scope(
        engagement_id=1, scope_type="url", value="https://app.example.com"
    )
    assert scope_id == 3


def test_scope_manager_invalid_type(mock_db):
    """Invalid scope type raises ValueError."""
    manager = ScopeManager()

    with pytest.raises(ValueError, match="Invalid scope_type"):
        manager.add_scope(engagement_id=1, scope_type="invalid", value="something")


def test_scope_manager_invalid_cidr(mock_db):
    """Invalid CIDR raises ValueError."""
    manager = ScopeManager()

    with pytest.raises(ValueError, match="Invalid CIDR"):
        manager.add_scope(engagement_id=1, scope_type="cidr", value="not-a-cidr")


def test_scope_manager_invalid_url(mock_db):
    """Invalid URL raises ValueError."""
    manager = ScopeManager()

    with pytest.raises(ValueError, match="URL must start with"):
        manager.add_scope(engagement_id=1, scope_type="url", value="ftp://example.com")


def test_scope_manager_set_enforcement(mock_db):
    """Set enforcement mode."""
    mock_db.execute.return_value = []
    manager = ScopeManager()

    result = manager.set_enforcement(1, "block")
    assert result is True


def test_scope_manager_invalid_enforcement(mock_db):
    """Invalid enforcement mode raises ValueError."""
    manager = ScopeManager()

    with pytest.raises(ValueError, match="Invalid enforcement mode"):
        manager.set_enforcement(1, "invalid")


def test_scope_manager_add_exclusion(mock_db):
    """Add exclusion scope entry."""
    mock_db.insert.return_value = 4
    manager = ScopeManager()

    scope_id = manager.add_scope(
        engagement_id=1,
        scope_type="hostname",
        value="10.0.0.1",
        is_excluded=True,
        description="Gateway - excluded",
    )
    assert scope_id == 4


# ===== SCOPE VALIDATION RESULT DATACLASS =====


def test_scope_validation_result_dataclass():
    """Test ScopeValidationResult dataclass."""
    result = ScopeValidationResult(
        is_in_scope=True,
        matched_entry={"id": 1, "value": "192.168.1.0/24"},
        reason="Matched scope entry",
        scope_type="cidr",
    )
    assert result.is_in_scope is True
    assert result.matched_entry["id"] == 1
    assert result.scope_type == "cidr"


# ===== SCOPE VIOLATION ERROR =====


def test_scope_violation_error():
    """Test ScopeViolationError exception."""
    error = ScopeViolationError("Target out of scope")
    assert str(error) == "Target out of scope"


# ===== LOGGING TESTS =====


def test_log_validation(mock_db):
    """Test validation logging."""
    mock_db.execute.return_value = [
        {
            "id": 1,
            "scope_type": "cidr",
            "value": "192.168.1.0/24",
            "is_excluded": False,
            "description": None,
        }
    ]
    mock_db.execute_one.return_value = {"scope_enforcement": "warn"}
    mock_db.insert.return_value = 1

    with patch("souleyez.auth.get_current_user", return_value=None):
        validator = ScopeValidator(engagement_id=1)
        result = validator.validate_target("192.168.1.100")

        validator.log_validation(
            target="192.168.1.100", result=result, action="allowed", job_id=42
        )

        # Verify insert was called
        mock_db.insert.assert_called_once()
        call_args = mock_db.insert.call_args
        assert call_args[0][0] == "scope_validation_log"
        assert call_args[0][1]["target"] == "192.168.1.100"
        assert call_args[0][1]["job_id"] == 42
