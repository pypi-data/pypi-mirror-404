#!/usr/bin/env python3
"""
Tests for souleyez.core.version_utils

Tests semantic version parsing, comparison, and condition matching
for version-aware tool chaining.
"""
import pytest
from souleyez.core.version_utils import (
    SemanticVersion,
    VersionOperator,
    VersionCondition,
    parse_version,
    parse_condition,
    parse_version_conditions,
    parse_version_spec,
    matches_version,
    normalize_product_name,
    check_version_condition,
)


class TestSemanticVersion:
    """Tests for SemanticVersion class."""

    def test_basic_comparison(self):
        """Test basic version comparison."""
        v1 = SemanticVersion(1, 0, 0)
        v2 = SemanticVersion(2, 0, 0)
        assert v1 < v2
        assert v2 > v1
        assert v1 != v2

    def test_minor_comparison(self):
        """Test minor version comparison."""
        v1 = SemanticVersion(1, 18, 0)
        v2 = SemanticVersion(1, 19, 0)
        assert v1 < v2
        assert v1 <= v2
        assert v2 > v1
        assert v2 >= v1

    def test_patch_comparison(self):
        """Test patch version comparison."""
        v1 = SemanticVersion(2, 4, 49)
        v2 = SemanticVersion(2, 4, 50)
        assert v1 < v2
        assert v1 <= v2

    def test_equality(self):
        """Test version equality."""
        v1 = SemanticVersion(1, 19, 0)
        v2 = SemanticVersion(1, 19, 0)
        assert v1 == v2
        assert v1 <= v2
        assert v1 >= v2

    def test_prerelease_comparison(self):
        """Test prerelease versions are less than release."""
        v1 = SemanticVersion(1, 0, 0, prerelease="alpha")
        v2 = SemanticVersion(1, 0, 0)
        assert v1 < v2

    def test_prerelease_alphabetical(self):
        """Test prerelease alphabetical comparison."""
        v1 = SemanticVersion(1, 0, 0, prerelease="alpha")
        v2 = SemanticVersion(1, 0, 0, prerelease="beta")
        assert v1 < v2

    def test_extra_version_part(self):
        """Test versions with 4 parts (1.0.0.1)."""
        v1 = SemanticVersion(1, 0, 0, extra=1)
        v2 = SemanticVersion(1, 0, 0, extra=2)
        assert v1 < v2

    def test_str_representation(self):
        """Test string representation."""
        v = SemanticVersion(1, 19, 0)
        assert str(v) == "1.19.0"

        v_pre = SemanticVersion(1, 0, 0, prerelease="alpine")
        assert str(v_pre) == "1.0.0-alpine"


class TestParseVersion:
    """Tests for parse_version function."""

    def test_simple_version(self):
        """Test parsing simple version."""
        v = parse_version("1.19.0")
        assert v is not None
        assert v.major == 1
        assert v.minor == 19
        assert v.patch == 0

    def test_two_part_version(self):
        """Test parsing two-part version."""
        v = parse_version("1.19")
        assert v is not None
        assert v.major == 1
        assert v.minor == 19
        assert v.patch == 0

    def test_major_only(self):
        """Test parsing major-only version."""
        v = parse_version("5")
        assert v is not None
        assert v.major == 5
        assert v.minor == 0

    def test_with_prerelease_dash(self):
        """Test parsing version with dash prerelease."""
        v = parse_version("1.19.0-alpine")
        assert v is not None
        assert v.major == 1
        assert v.minor == 19
        assert v.patch == 0
        assert v.prerelease == "alpine"

    def test_with_prerelease_p(self):
        """Test parsing version with p prerelease (OpenSSH style)."""
        v = parse_version("8.2p1")
        assert v is not None
        assert v.major == 8
        assert v.minor == 2
        assert v.patch == 0
        assert "p1" in v.prerelease or v.prerelease == "1"

    def test_four_part_version(self):
        """Test parsing four-part version."""
        v = parse_version("1.0.0.1")
        assert v is not None
        assert v.major == 1
        assert v.minor == 0
        assert v.patch == 0
        assert v.extra == 1

    def test_extract_from_product_string(self):
        """Test extracting version from product string."""
        v = parse_version("OpenSSH 8.2p1")
        assert v is not None
        assert v.major == 8
        assert v.minor == 2

    def test_empty_string(self):
        """Test parsing empty string returns None."""
        assert parse_version("") is None
        assert parse_version(None) is None

    def test_invalid_string(self):
        """Test parsing invalid string returns None."""
        assert parse_version("not-a-version") is None


class TestParseCondition:
    """Tests for parse_condition function."""

    def test_less_than(self):
        """Test parsing less than condition."""
        cond = parse_condition("<1.19")
        assert cond is not None
        assert cond.operator == VersionOperator.LT
        assert cond.version.major == 1
        assert cond.version.minor == 19

    def test_less_equal(self):
        """Test parsing less than or equal condition."""
        cond = parse_condition("<=2.4.50")
        assert cond is not None
        assert cond.operator == VersionOperator.LE
        assert cond.version.major == 2
        assert cond.version.minor == 4
        assert cond.version.patch == 50

    def test_greater_than(self):
        """Test parsing greater than condition."""
        cond = parse_condition(">1.0")
        assert cond is not None
        assert cond.operator == VersionOperator.GT

    def test_greater_equal(self):
        """Test parsing greater than or equal condition."""
        cond = parse_condition(">=2.4.49")
        assert cond is not None
        assert cond.operator == VersionOperator.GE

    def test_equal_explicit(self):
        """Test parsing explicit equal condition."""
        cond = parse_condition("=1.0.0")
        assert cond is not None
        assert cond.operator == VersionOperator.EQ

    def test_equal_implicit(self):
        """Test parsing implicit equal (no operator)."""
        cond = parse_condition("1.0.0")
        assert cond is not None
        assert cond.operator == VersionOperator.EQ

    def test_not_equal(self):
        """Test parsing not equal condition."""
        cond = parse_condition("!=2.0")
        assert cond is not None
        assert cond.operator == VersionOperator.NE


class TestParseVersionConditions:
    """Tests for parse_version_conditions function."""

    def test_single_condition(self):
        """Test parsing single condition."""
        conditions = parse_version_conditions("<1.19")
        assert len(conditions) == 1
        assert conditions[0].operator == VersionOperator.LT

    def test_multiple_conditions(self):
        """Test parsing multiple comma-separated conditions."""
        conditions = parse_version_conditions(">=2.4.49,<=2.4.50")
        assert len(conditions) == 2
        assert conditions[0].operator == VersionOperator.GE
        assert conditions[1].operator == VersionOperator.LE

    def test_empty_string(self):
        """Test parsing empty string returns empty list."""
        assert parse_version_conditions("") == []


class TestParseVersionSpec:
    """Tests for parse_version_spec function."""

    def test_simple_spec(self):
        """Test parsing simple version spec."""
        product, conditions = parse_version_spec("nginx:<1.19")
        assert product == "nginx"
        assert len(conditions) == 1

    def test_range_spec(self):
        """Test parsing range version spec."""
        product, conditions = parse_version_spec("apache:>=2.4.49,<=2.4.50")
        assert product == "apache"
        assert len(conditions) == 2

    def test_no_colon(self):
        """Test parsing spec without colon returns empty."""
        product, conditions = parse_version_spec("nginx")
        assert product == ""
        assert conditions == []


class TestMatchesVersion:
    """Tests for matches_version function."""

    def test_less_than_matches(self):
        """Test less than condition matches."""
        conditions = parse_version_conditions("<1.19")
        assert matches_version("1.18.0", conditions) is True
        assert matches_version("1.19.0", conditions) is False
        assert matches_version("1.20.0", conditions) is False

    def test_range_matches(self):
        """Test range condition matches."""
        conditions = parse_version_conditions(">=2.4.49,<=2.4.50")
        assert matches_version("2.4.48", conditions) is False
        assert matches_version("2.4.49", conditions) is True
        assert matches_version("2.4.50", conditions) is True
        assert matches_version("2.4.51", conditions) is False

    def test_empty_conditions(self):
        """Test empty conditions returns False."""
        assert matches_version("1.0.0", []) is False

    def test_invalid_version(self):
        """Test invalid version returns False."""
        conditions = parse_version_conditions("<1.19")
        assert matches_version("", conditions) is False
        assert matches_version("invalid", conditions) is False


class TestNormalizeProductName:
    """Tests for normalize_product_name function."""

    def test_apache_variants(self):
        """Test Apache product name normalization."""
        assert normalize_product_name("Apache httpd") == "apache"
        assert normalize_product_name("Apache HTTP Server") == "apache"
        assert normalize_product_name("apache/2.4.49") == "apache"
        assert normalize_product_name("httpd") == "apache"

    def test_nginx_variants(self):
        """Test nginx product name normalization."""
        assert normalize_product_name("nginx") == "nginx"
        assert normalize_product_name("nginx/1.19.0") == "nginx"

    def test_openssh_variants(self):
        """Test OpenSSH product name normalization."""
        assert normalize_product_name("OpenSSH") == "ssh"
        assert normalize_product_name("openssh") == "ssh"

    def test_php_variants(self):
        """Test PHP product name normalization."""
        assert normalize_product_name("PHP") == "php"
        assert normalize_product_name("php-fpm") == "php"
        assert normalize_product_name("PHP/7.4") == "php"

    def test_mysql_variants(self):
        """Test MySQL/MariaDB product name normalization."""
        assert normalize_product_name("MySQL") == "mysql"
        assert normalize_product_name("MariaDB") == "mysql"

    def test_unknown_product(self):
        """Test unknown product returns lowercase."""
        assert normalize_product_name("CustomServer") == "customserver"
        assert normalize_product_name("my-app/1.0") == "my-app"

    def test_empty_product(self):
        """Test empty product returns empty string."""
        assert normalize_product_name("") == ""
        assert normalize_product_name(None) == ""


class TestCheckVersionCondition:
    """Tests for check_version_condition main entry point."""

    def test_apache_cve_2021_41773(self):
        """Test Apache CVE-2021-41773 version range."""
        spec = "apache:>=2.4.49,<=2.4.50"

        # Vulnerable versions
        assert check_version_condition("Apache httpd", "2.4.49", spec) is True
        assert check_version_condition("Apache httpd", "2.4.50", spec) is True
        assert check_version_condition("apache", "2.4.49", spec) is True

        # Not vulnerable
        assert check_version_condition("Apache httpd", "2.4.48", spec) is False
        assert check_version_condition("Apache httpd", "2.4.51", spec) is False

    def test_nginx_old_version(self):
        """Test nginx old version detection."""
        spec = "nginx:<1.19"

        assert check_version_condition("nginx", "1.18.0", spec) is True
        assert check_version_condition("nginx/1.18.0", "1.18.0", spec) is True
        assert check_version_condition("nginx", "1.19.0", spec) is False
        assert check_version_condition("nginx", "1.20.0", spec) is False

    def test_php_range(self):
        """Test PHP version range."""
        spec = "php:>=7.0,<8.0"

        assert check_version_condition("PHP", "7.0", spec) is True
        assert check_version_condition("PHP", "7.4.3", spec) is True
        assert check_version_condition("PHP", "6.9", spec) is False
        assert check_version_condition("PHP", "8.0", spec) is False
        assert check_version_condition("PHP", "8.1", spec) is False

    def test_product_mismatch(self):
        """Test product mismatch returns False."""
        spec = "apache:>=2.4.49"
        assert check_version_condition("nginx", "2.4.49", spec) is False

    def test_empty_inputs(self):
        """Test empty inputs return False."""
        assert check_version_condition("", "1.0", "apache:>=1.0") is False
        assert check_version_condition("apache", "", "apache:>=1.0") is False
        assert check_version_condition("apache", "1.0", "") is False


class TestRealWorldVersions:
    """Tests with real-world version strings from nmap scans."""

    def test_openssh_version(self):
        """Test OpenSSH version parsing from scan output."""
        # Real nmap output: "OpenSSH 8.2p1 Ubuntu 4ubuntu0.1"
        v = parse_version("8.2p1")
        assert v is not None
        assert v.major == 8
        assert v.minor == 2

        spec = "ssh:>=7.0,<8.3"
        assert check_version_condition("OpenSSH", "8.2p1", spec) is True

    def test_nginx_alpine(self):
        """Test nginx alpine version parsing."""
        v = parse_version("1.19.0-alpine")
        assert v is not None
        assert v.major == 1
        assert v.minor == 19
        assert "alpine" in v.prerelease

    def test_mysql_version(self):
        """Test MySQL version parsing."""
        v = parse_version("5.7.32-0ubuntu0.18.04.1")
        assert v is not None
        assert v.major == 5
        assert v.minor == 7
        assert v.patch == 32

    def test_vsftpd_backdoor_version(self):
        """Test vsftpd backdoor version (CVE-2011-2523)."""
        spec = "vsftpd:=2.3.4"
        assert check_version_condition("vsftpd", "2.3.4", spec) is True
        assert check_version_condition("vsftpd", "2.3.5", spec) is False
        assert check_version_condition("vsftpd", "3.0.0", spec) is False
