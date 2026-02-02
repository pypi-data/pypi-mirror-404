#!/usr/bin/env python3
"""
souleyez.core.version_utils

Semantic version parsing and comparison for version-aware tool chaining.
Supports conditions like: version:nginx:<1.19, version:apache:>=2.4.49,<=2.4.50
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Tuple


class VersionOperator(Enum):
    """Comparison operators for version conditions."""

    LT = "<"
    LE = "<="
    GT = ">"
    GE = ">="
    EQ = "="
    NE = "!="


@dataclass
class SemanticVersion:
    """
    Parsed semantic version (major.minor.patch).

    Handles versions like:
    - 1.0, 1.0.0, 1.0.0.1
    - 2.4.49, 8.2p1
    - 1.19.0-alpine, 7.4.3-fpm
    """

    major: int
    minor: int = 0
    patch: int = 0
    extra: int = 0
    prerelease: str = ""
    raw: str = ""

    def __lt__(self, other: "SemanticVersion") -> bool:
        return self._compare(other) < 0

    def __le__(self, other: "SemanticVersion") -> bool:
        return self._compare(other) <= 0

    def __gt__(self, other: "SemanticVersion") -> bool:
        return self._compare(other) > 0

    def __ge__(self, other: "SemanticVersion") -> bool:
        return self._compare(other) >= 0

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SemanticVersion):
            return False
        return self._compare(other) == 0

    def __ne__(self, other: object) -> bool:
        return not self.__eq__(other)

    def _compare(self, other: "SemanticVersion") -> int:
        """Compare two versions. Returns -1, 0, or 1."""
        # Compare major.minor.patch.extra
        for self_val, other_val in [
            (self.major, other.major),
            (self.minor, other.minor),
            (self.patch, other.patch),
            (self.extra, other.extra),
        ]:
            if self_val < other_val:
                return -1
            elif self_val > other_val:
                return 1

        # If all numeric parts equal, prerelease versions are less than release
        # e.g., 1.0.0-alpha < 1.0.0
        if self.prerelease and not other.prerelease:
            return -1
        elif not self.prerelease and other.prerelease:
            return 1
        elif self.prerelease and other.prerelease:
            # Alphabetical comparison for prerelease
            if self.prerelease < other.prerelease:
                return -1
            elif self.prerelease > other.prerelease:
                return 1

        return 0

    def __str__(self) -> str:
        base = f"{self.major}.{self.minor}.{self.patch}"
        if self.extra:
            base += f".{self.extra}"
        if self.prerelease:
            base += f"-{self.prerelease}"
        return base


@dataclass
class VersionCondition:
    """Single version comparison condition."""

    operator: VersionOperator
    version: SemanticVersion

    def matches(self, detected: SemanticVersion) -> bool:
        """Check if detected version matches this condition."""
        if self.operator == VersionOperator.LT:
            return detected < self.version
        elif self.operator == VersionOperator.LE:
            return detected <= self.version
        elif self.operator == VersionOperator.GT:
            return detected > self.version
        elif self.operator == VersionOperator.GE:
            return detected >= self.version
        elif self.operator == VersionOperator.EQ:
            return detected == self.version
        elif self.operator == VersionOperator.NE:
            return detected != self.version
        return False


# Regex for parsing version strings
# Matches: 1.0, 1.0.0, 2.4.49, 8.2p1, 1.19.0-alpine, 7.4.3.1
VERSION_PATTERN = re.compile(
    r"^(\d+)"  # Major (required)
    r"(?:\.(\d+))?"  # Minor (optional)
    r"(?:\.(\d+))?"  # Patch (optional)
    r"(?:\.(\d+))?"  # Extra (optional, for versions like 1.0.0.1)
    r"(?:[p\-_]([a-zA-Z0-9\-_.]+))?"  # Prerelease (optional, after p/- or _)
)

# Regex for parsing version conditions
# Matches: <1.19, >=2.4.49, =1.0.0, !=2.0
CONDITION_PATTERN = re.compile(
    r"^(<=?|>=?|!=|=)?"  # Operator (optional, defaults to =)
    r"(\d+(?:\.\d+)*"  # Version numbers
    r"(?:[p\-_][a-zA-Z0-9\-_.]+)?)"  # Optional prerelease
    r"$"
)


def parse_version(version_str: str) -> Optional[SemanticVersion]:
    """
    Parse a version string into SemanticVersion.

    Examples:
        parse_version('1.19.0') -> SemanticVersion(1, 19, 0)
        parse_version('2.4.49') -> SemanticVersion(2, 4, 49)
        parse_version('8.2p1') -> SemanticVersion(8, 2, 0, 0, 'p1')
        parse_version('7.4.3-fpm') -> SemanticVersion(7, 4, 3, 0, 'fpm')

    Returns None if version cannot be parsed.
    """
    if not version_str:
        return None

    # Clean up common prefixes/suffixes
    version_str = version_str.strip()

    # Handle versions like "OpenSSH 8.2p1" - extract just the version part
    # Look for first digit sequence that looks like a version
    version_match = re.search(
        r"(\d+(?:\.\d+)*(?:[p\-_][a-zA-Z0-9\-_.]*)?)", version_str
    )
    if not version_match:
        return None

    version_str = version_match.group(1)

    match = VERSION_PATTERN.match(version_str)
    if not match:
        return None

    major = int(match.group(1))
    minor = int(match.group(2)) if match.group(2) else 0
    patch = int(match.group(3)) if match.group(3) else 0
    extra = int(match.group(4)) if match.group(4) else 0
    prerelease = match.group(5) or ""

    return SemanticVersion(
        major=major,
        minor=minor,
        patch=patch,
        extra=extra,
        prerelease=prerelease,
        raw=version_str,
    )


def parse_condition(condition_str: str) -> Optional[VersionCondition]:
    """
    Parse a single version condition.

    Examples:
        parse_condition('<1.19') -> VersionCondition(LT, SemanticVersion(1, 19, 0))
        parse_condition('>=2.4.49') -> VersionCondition(GE, SemanticVersion(2, 4, 49))
        parse_condition('2.4.49') -> VersionCondition(EQ, SemanticVersion(2, 4, 49))
    """
    if not condition_str:
        return None

    condition_str = condition_str.strip()
    match = CONDITION_PATTERN.match(condition_str)
    if not match:
        return None

    operator_str = match.group(1) or "="
    version_str = match.group(2)

    # Map operator string to enum
    operator_map = {
        "<": VersionOperator.LT,
        "<=": VersionOperator.LE,
        ">": VersionOperator.GT,
        ">=": VersionOperator.GE,
        "=": VersionOperator.EQ,
        "!=": VersionOperator.NE,
    }
    operator = operator_map.get(operator_str, VersionOperator.EQ)

    version = parse_version(version_str)
    if not version:
        return None

    return VersionCondition(operator=operator, version=version)


def parse_version_conditions(condition_str: str) -> List[VersionCondition]:
    """
    Parse multiple version conditions separated by comma.

    Examples:
        parse_version_conditions('>=2.4.49,<=2.4.50')
            -> [VersionCondition(GE, 2.4.49), VersionCondition(LE, 2.4.50)]
        parse_version_conditions('<1.19')
            -> [VersionCondition(LT, 1.19)]
    """
    if not condition_str:
        return []

    conditions = []
    for part in condition_str.split(","):
        part = part.strip()
        if part:
            cond = parse_condition(part)
            if cond:
                conditions.append(cond)

    return conditions


def parse_version_spec(spec: str) -> Tuple[str, List[VersionCondition]]:
    """
    Parse a full version specification (product:conditions).

    Examples:
        parse_version_spec('nginx:<1.19')
            -> ('nginx', [VersionCondition(LT, 1.19)])
        parse_version_spec('apache:>=2.4.49,<=2.4.50')
            -> ('apache', [VersionCondition(GE, 2.4.49), VersionCondition(LE, 2.4.50)])

    Returns (product_name, conditions_list).
    """
    if ":" not in spec:
        return ("", [])

    parts = spec.split(":", 1)
    product = parts[0].strip().lower()
    conditions = parse_version_conditions(parts[1]) if len(parts) > 1 else []

    return (product, conditions)


def matches_version(detected_version: str, conditions: List[VersionCondition]) -> bool:
    """
    Check if a detected version matches all conditions.

    Args:
        detected_version: Version string from service scan (e.g., "1.19.0")
        conditions: List of VersionCondition to check against

    Returns:
        True if detected version satisfies ALL conditions.
    """
    if not detected_version or not conditions:
        return False

    detected = parse_version(detected_version)
    if not detected:
        return False

    # All conditions must match
    return all(cond.matches(detected) for cond in conditions)


# Product name normalization mapping
PRODUCT_ALIASES = {
    # Apache
    "apache httpd": "apache",
    "apache http server": "apache",
    "apache/": "apache",
    "httpd": "apache",
    # nginx
    "nginx/": "nginx",
    # OpenSSH
    "openssh": "ssh",
    "openssh_": "ssh",
    "ssh": "ssh",
    # PHP
    "php/": "php",
    "php-fpm": "php",
    # MySQL
    "mysql": "mysql",
    "mariadb": "mysql",
    # PostgreSQL
    "postgresql": "postgres",
    "postgres": "postgres",
    # vsftpd
    "vsftpd": "vsftpd",
    "vsftp": "vsftpd",
    # ProFTPD
    "proftpd": "proftpd",
    # Samba
    "samba": "samba",
    "smbd": "samba",
    # Tomcat
    "apache tomcat": "tomcat",
    "tomcat": "tomcat",
    "coyote": "tomcat",
    # WordPress
    "wordpress": "wordpress",
    "wp": "wordpress",
    # Drupal
    "drupal": "drupal",
    # IIS
    "microsoft-iis": "iis",
    "iis": "iis",
    # Node.js/Express
    "node": "nodejs",
    "nodejs": "nodejs",
    "express": "express",
    # Redis
    "redis": "redis",
    # MongoDB
    "mongodb": "mongodb",
    "mongo": "mongodb",
    # Elasticsearch
    "elasticsearch": "elasticsearch",
    "elastic": "elasticsearch",
}


def normalize_product_name(product: str) -> str:
    """
    Normalize a product name for consistent matching.

    Examples:
        normalize_product_name('Apache httpd') -> 'apache'
        normalize_product_name('nginx/1.19.0') -> 'nginx'
        normalize_product_name('OpenSSH') -> 'ssh'
    """
    if not product:
        return ""

    product_lower = product.lower().strip()

    # Check direct match first
    if product_lower in PRODUCT_ALIASES:
        return PRODUCT_ALIASES[product_lower]

    # Check prefix matches
    for alias, normalized in PRODUCT_ALIASES.items():
        if product_lower.startswith(alias):
            return normalized

    # Return lowercase if no alias found
    return product_lower.split("/")[0].split(" ")[0]


def check_version_condition(product: str, version: str, condition_spec: str) -> bool:
    """
    Main entry point: check if a product/version matches a condition spec.

    Args:
        product: Product name from scan (e.g., "Apache httpd", "nginx")
        version: Version string from scan (e.g., "2.4.49", "1.19.0")
        condition_spec: Condition specification (e.g., "apache:>=2.4.49,<=2.4.50")

    Returns:
        True if product matches AND version satisfies all conditions.
    """
    if not product or not version or not condition_spec:
        return False

    # Parse the condition spec
    target_product, conditions = parse_version_spec(condition_spec)
    if not target_product or not conditions:
        return False

    # Normalize and compare product names
    normalized_product = normalize_product_name(product)
    if normalized_product != target_product:
        return False

    # Check version conditions
    return matches_version(version, conditions)
