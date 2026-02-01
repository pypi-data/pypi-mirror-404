#!/usr/bin/env python3
"""
Engagement scope validation for target validation.

This module provides validation of targets against engagement scope definitions
to prevent scanning unauthorized targets.
"""

import fnmatch
import ipaddress
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from souleyez.log_config import get_logger
from souleyez.storage.database import get_db

logger = get_logger(__name__)


class ScopeViolationError(Exception):
    """Raised when a target is out of scope and enforcement is 'block'."""

    pass


@dataclass
class ScopeValidationResult:
    """Result of scope validation check."""

    is_in_scope: bool
    matched_entry: Optional[Dict[str, Any]]
    reason: str
    scope_type: Optional[str]  # 'cidr', 'domain', 'url', 'hostname', None


class ScopeValidator:
    """
    Validates targets against engagement scope definitions.

    Usage:
        validator = ScopeValidator(engagement_id)
        result = validator.validate_target("192.168.1.100")
        if not result.is_in_scope:
            print(f"Out of scope: {result.reason}")
    """

    def __init__(self, engagement_id: int):
        """
        Initialize validator for an engagement.

        Args:
            engagement_id: The engagement to validate against
        """
        self.engagement_id = engagement_id
        self.db = get_db()
        self._scope_cache: Optional[List[Dict[str, Any]]] = None
        self._enforcement_cache: Optional[str] = None

    def get_scope_entries(self) -> List[Dict[str, Any]]:
        """
        Get all scope entries for this engagement.

        Returns:
            List of scope entry dicts with: id, scope_type, value, is_excluded, description
        """
        if self._scope_cache is not None:
            return self._scope_cache

        try:
            entries = self.db.execute(
                """SELECT id, scope_type, value, is_excluded, description
                   FROM engagement_scope
                   WHERE engagement_id = ?
                   ORDER BY is_excluded ASC, scope_type ASC""",
                (self.engagement_id,),
            )
            self._scope_cache = entries
            return entries
        except Exception as e:
            logger.warning(
                "Failed to get scope entries",
                extra={"engagement_id": self.engagement_id, "error": str(e)},
            )
            return []

    def has_scope_defined(self) -> bool:
        """
        Check if the engagement has any scope entries defined.

        Returns:
            True if scope is defined, False otherwise
        """
        entries = self.get_scope_entries()
        # Only count inclusion entries (not exclusions)
        inclusions = [e for e in entries if not e.get("is_excluded")]
        return len(inclusions) > 0

    def get_enforcement_mode(self) -> str:
        """
        Get the enforcement mode for this engagement.

        Returns:
            'off', 'warn', or 'block'
        """
        if self._enforcement_cache is not None:
            return self._enforcement_cache

        try:
            result = self.db.execute_one(
                "SELECT scope_enforcement FROM engagements WHERE id = ?",
                (self.engagement_id,),
            )
            mode = result.get("scope_enforcement", "off") if result else "off"
            self._enforcement_cache = mode or "off"
            return self._enforcement_cache
        except Exception as e:
            logger.warning(
                "Failed to get enforcement mode",
                extra={"engagement_id": self.engagement_id, "error": str(e)},
            )
            return "off"

    def validate_target(self, target: str) -> ScopeValidationResult:
        """
        Validate a target against the engagement scope.

        Handles:
        - URLs (extracts host for validation)
        - IP addresses
        - CIDR ranges
        - Hostnames/domains
        - Space-separated multiple targets (validates each, all must be in scope)

        Args:
            target: The target to validate (IP, URL, hostname, etc.)

        Returns:
            ScopeValidationResult with validation outcome
        """
        if not target or not target.strip():
            return ScopeValidationResult(
                is_in_scope=False,
                matched_entry=None,
                reason="Empty target",
                scope_type=None,
            )

        target = target.strip()

        # Handle space-separated multiple targets
        # Check if this looks like multiple targets (space-separated, not a URL with spaces)
        if " " in target and not target.startswith(("http://", "https://")):
            targets = target.split()
            # Validate each target - all must be in scope
            for t in targets:
                result = self._validate_single_target(t)
                if not result.is_in_scope:
                    return result  # Return first out-of-scope result
            # All targets are in scope
            return ScopeValidationResult(
                is_in_scope=True,
                matched_entry=None,
                reason=f"All {len(targets)} targets are in scope",
                scope_type=None,
            )

        return self._validate_single_target(target)

    def _validate_single_target(self, target: str) -> ScopeValidationResult:
        """
        Validate a single target against the engagement scope.

        Args:
            target: Single target to validate (IP, URL, hostname, etc.)

        Returns:
            ScopeValidationResult with validation outcome
        """

        # If no scope defined, everything is in scope (permissive default)
        if not self.has_scope_defined():
            return ScopeValidationResult(
                is_in_scope=True,
                matched_entry=None,
                reason="No scope defined (permissive)",
                scope_type=None,
            )

        # Determine target type and extract relevant part
        target_type, normalized = self._parse_target(target)

        # Check against scope entries
        entries = self.get_scope_entries()

        # First check exclusions (deny rules take precedence)
        for entry in entries:
            if not entry.get("is_excluded"):
                continue
            if self._matches_entry(normalized, target_type, entry):
                return ScopeValidationResult(
                    is_in_scope=False,
                    matched_entry=entry,
                    reason=f"Explicitly excluded by scope entry: {entry['value']}",
                    scope_type=entry["scope_type"],
                )

        # Then check inclusions
        for entry in entries:
            if entry.get("is_excluded"):
                continue
            if self._matches_entry(normalized, target_type, entry):
                return ScopeValidationResult(
                    is_in_scope=True,
                    matched_entry=entry,
                    reason=f"Matched scope entry: {entry['value']}",
                    scope_type=entry["scope_type"],
                )

        # No match found - out of scope
        return ScopeValidationResult(
            is_in_scope=False,
            matched_entry=None,
            reason=f"Target '{target}' does not match any scope entry",
            scope_type=None,
        )

    def validate_ip(self, ip: str) -> ScopeValidationResult:
        """
        Validate an IP address against scope.

        Args:
            ip: IP address string

        Returns:
            ScopeValidationResult
        """
        return self.validate_target(ip)

    def validate_domain(self, domain: str) -> ScopeValidationResult:
        """
        Validate a domain against scope.

        Args:
            domain: Domain name

        Returns:
            ScopeValidationResult
        """
        return self.validate_target(domain)

    def validate_url(self, url: str) -> ScopeValidationResult:
        """
        Validate a URL against scope.

        Args:
            url: URL string

        Returns:
            ScopeValidationResult
        """
        return self.validate_target(url)

    def log_validation(
        self,
        target: str,
        result: ScopeValidationResult,
        action: str,
        job_id: int = None,
    ) -> None:
        """
        Log a validation result to the audit trail.

        Args:
            target: The target that was validated
            result: The validation result
            action: Action taken ('allowed', 'blocked', 'warned')
            job_id: Optional job ID associated with this validation
        """
        try:
            from souleyez.auth import get_current_user

            user = get_current_user()
            user_id = user.id if user else None
        except Exception:
            user_id = None

        validation_result = "in_scope" if result.is_in_scope else "out_of_scope"
        if not self.has_scope_defined():
            validation_result = "no_scope_defined"

        try:
            self.db.insert(
                "scope_validation_log",
                {
                    "engagement_id": self.engagement_id,
                    "job_id": job_id,
                    "target": target,
                    "validation_result": validation_result,
                    "action_taken": action,
                    "matched_scope_id": (
                        result.matched_entry.get("id") if result.matched_entry else None
                    ),
                    "user_id": user_id,
                },
            )
        except Exception as e:
            logger.warning(
                "Failed to log scope validation",
                extra={
                    "engagement_id": self.engagement_id,
                    "target": target,
                    "error": str(e),
                },
            )

    def _parse_target(self, target: str) -> tuple:
        """
        Parse target to determine type and normalize.

        Returns:
            (target_type, normalized_value)
            target_type is one of: 'ip', 'cidr', 'domain', 'url'
        """
        # Check if URL
        if target.startswith(("http://", "https://")):
            parsed = urlparse(target)
            host = parsed.netloc.split(":")[0]  # Remove port
            # Check if host part is IP
            try:
                ipaddress.ip_address(host)
                return ("ip", host)
            except ValueError:
                return ("domain", host.lower())

        # Check if IP address
        try:
            ipaddress.ip_address(target)
            return ("ip", target)
        except ValueError:
            pass

        # Check if CIDR notation
        if "/" in target:
            try:
                ipaddress.ip_network(target, strict=False)
                return ("cidr", target)
            except ValueError:
                pass

        # Assume domain/hostname
        return ("domain", target.lower())

    def _matches_entry(
        self, target: str, target_type: str, entry: Dict[str, Any]
    ) -> bool:
        """
        Check if a target matches a scope entry.

        Args:
            target: Normalized target value
            target_type: Type of target ('ip', 'cidr', 'domain', 'url')
            entry: Scope entry dict

        Returns:
            True if matches, False otherwise
        """
        entry_type = entry["scope_type"]
        entry_value = entry["value"]

        # IP target
        if target_type == "ip":
            if entry_type == "cidr":
                return self._ip_in_cidr(target, entry_value)
            elif entry_type == "hostname":
                # Exact IP match
                return target == entry_value
            elif entry_type == "domain":
                # IP doesn't match domain patterns
                return False
            elif entry_type == "url":
                # Extract host from URL entry
                try:
                    parsed = urlparse(entry_value)
                    return target == parsed.netloc.split(":")[0]
                except Exception:
                    return False

        # CIDR target (less common - check containment)
        elif target_type == "cidr":
            if entry_type == "cidr":
                return self._cidr_overlaps(target, entry_value)
            return False

        # Domain target
        elif target_type == "domain":
            if entry_type == "domain":
                return self._domain_matches(target, entry_value)
            elif entry_type == "hostname":
                # Exact hostname match
                return target.lower() == entry_value.lower()
            elif entry_type == "url":
                # Extract host from URL entry
                try:
                    parsed = urlparse(entry_value)
                    entry_host = parsed.netloc.split(":")[0].lower()
                    return target == entry_host or self._domain_matches(
                        target, entry_host
                    )
                except Exception:
                    return False
            return False

        # URL target (handled by extracting host above)
        return False

    def _ip_in_cidr(self, ip: str, cidr: str) -> bool:
        """Check if IP is within CIDR range."""
        try:
            ip_obj = ipaddress.ip_address(ip)
            network = ipaddress.ip_network(cidr, strict=False)
            return ip_obj in network
        except ValueError:
            return False

    def _cidr_overlaps(self, cidr1: str, cidr2: str) -> bool:
        """Check if two CIDR ranges overlap."""
        try:
            net1 = ipaddress.ip_network(cidr1, strict=False)
            net2 = ipaddress.ip_network(cidr2, strict=False)
            return net1.overlaps(net2)
        except ValueError:
            return False

    def _domain_matches(self, target: str, pattern: str) -> bool:
        """
        Check if domain matches a pattern.

        Supports wildcards:
        - *.example.com matches sub.example.com, deep.sub.example.com
        - example.com matches example.com only

        Args:
            target: Target domain (lowercase)
            pattern: Pattern to match against

        Returns:
            True if matches
        """
        pattern = pattern.lower()
        target = target.lower()

        # Handle wildcard patterns
        if pattern.startswith("*."):
            # Remove the *. prefix for suffix matching
            suffix = pattern[2:]
            # Match exact suffix or .suffix
            return target == suffix or target.endswith("." + suffix)

        # Handle wildcards in other positions using fnmatch
        if "*" in pattern or "?" in pattern:
            return fnmatch.fnmatch(target, pattern)

        # Exact match
        return target == pattern


class ScopeManager:
    """
    Manages scope definitions for engagements.

    Usage:
        manager = ScopeManager()
        manager.add_scope(engagement_id, 'cidr', '192.168.1.0/24')
        manager.add_scope(engagement_id, 'domain', '*.example.com')
        manager.set_enforcement(engagement_id, 'warn')
    """

    def __init__(self):
        self.db = get_db()

    def add_scope(
        self,
        engagement_id: int,
        scope_type: str,
        value: str,
        is_excluded: bool = False,
        description: str = None,
    ) -> int:
        """
        Add a scope entry for an engagement.

        Args:
            engagement_id: Engagement ID
            scope_type: Type of scope ('cidr', 'domain', 'url', 'hostname')
            value: Scope value (e.g., '192.168.1.0/24', '*.example.com')
            is_excluded: If True, this is an exclusion (deny rule)
            description: Optional description

        Returns:
            ID of created scope entry

        Raises:
            ValueError: If scope_type or value is invalid
        """
        valid_types = ["cidr", "domain", "url", "hostname"]
        if scope_type not in valid_types:
            raise ValueError(
                f"Invalid scope_type: {scope_type}. Must be one of: {valid_types}"
            )

        # Validate the value based on type
        self._validate_scope_value(scope_type, value)

        try:
            from souleyez.auth import get_current_user

            user = get_current_user()
            added_by = user.id if user else None
        except Exception:
            added_by = None

        return self.db.insert(
            "engagement_scope",
            {
                "engagement_id": engagement_id,
                "scope_type": scope_type,
                "value": value,
                "is_excluded": is_excluded,
                "description": description,
                "added_by": added_by,
            },
        )

    def remove_scope(self, scope_id: int) -> bool:
        """
        Remove a scope entry by ID.

        Args:
            scope_id: ID of scope entry to remove

        Returns:
            True if removed, False if not found
        """
        try:
            self.db.execute("DELETE FROM engagement_scope WHERE id = ?", (scope_id,))
            return True
        except Exception as e:
            logger.warning(
                "Failed to remove scope entry",
                extra={"scope_id": scope_id, "error": str(e)},
            )
            return False

    def list_scope(self, engagement_id: int) -> List[Dict[str, Any]]:
        """
        List all scope entries for an engagement.

        Args:
            engagement_id: Engagement ID

        Returns:
            List of scope entry dicts
        """
        return self.db.execute(
            """SELECT id, scope_type, value, is_excluded, description, added_by, created_at
               FROM engagement_scope
               WHERE engagement_id = ?
               ORDER BY is_excluded ASC, scope_type ASC, value ASC""",
            (engagement_id,),
        )

    def set_enforcement(self, engagement_id: int, mode: str) -> bool:
        """
        Set enforcement mode for an engagement.

        Args:
            engagement_id: Engagement ID
            mode: 'off', 'warn', or 'block'

        Returns:
            True if updated successfully

        Raises:
            ValueError: If mode is invalid
        """
        valid_modes = ["off", "warn", "block"]
        if mode not in valid_modes:
            raise ValueError(
                f"Invalid enforcement mode: {mode}. Must be one of: {valid_modes}"
            )

        try:
            self.db.execute(
                "UPDATE engagements SET scope_enforcement = ? WHERE id = ?",
                (mode, engagement_id),
            )
            return True
        except Exception as e:
            logger.warning(
                "Failed to set enforcement mode",
                extra={"engagement_id": engagement_id, "mode": mode, "error": str(e)},
            )
            return False

    def get_validation_log(
        self, engagement_id: int, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get scope validation log for an engagement.

        Args:
            engagement_id: Engagement ID
            limit: Maximum entries to return

        Returns:
            List of validation log entries
        """
        return self.db.execute(
            """SELECT id, job_id, target, validation_result, action_taken,
                      matched_scope_id, user_id, created_at
               FROM scope_validation_log
               WHERE engagement_id = ?
               ORDER BY created_at DESC
               LIMIT ?""",
            (engagement_id, limit),
        )

    def _validate_scope_value(self, scope_type: str, value: str) -> None:
        """
        Validate scope value based on type.

        Raises:
            ValueError: If value is invalid for the scope type
        """
        if not value or not value.strip():
            raise ValueError("Scope value cannot be empty")

        value = value.strip()

        if scope_type == "cidr":
            try:
                ipaddress.ip_network(value, strict=False)
            except ValueError:
                raise ValueError(f"Invalid CIDR notation: {value}")

        elif scope_type == "hostname":
            # Basic hostname validation (can be IP or hostname)
            try:
                ipaddress.ip_address(value)
            except ValueError:
                # Not an IP, validate as hostname
                if len(value) > 253:
                    raise ValueError("Hostname too long (max 253 characters)")
                if not re.match(
                    r"^[a-zA-Z0-9]([a-zA-Z0-9\-]*[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]*[a-zA-Z0-9])?)*$",
                    value,
                ):
                    raise ValueError(f"Invalid hostname format: {value}")

        elif scope_type == "domain":
            # Allow wildcards like *.example.com
            if value.startswith("*."):
                domain_part = value[2:]
            else:
                domain_part = value

            if len(domain_part) > 253:
                raise ValueError("Domain too long (max 253 characters)")
            if not re.match(
                r"^[a-zA-Z0-9]([a-zA-Z0-9\-]*[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]*[a-zA-Z0-9])?)*$",
                domain_part,
            ):
                raise ValueError(f"Invalid domain format: {value}")

        elif scope_type == "url":
            if not value.startswith(("http://", "https://")):
                raise ValueError("URL must start with http:// or https://")
            try:
                parsed = urlparse(value)
                if not parsed.netloc:
                    raise ValueError(f"Invalid URL (no host): {value}")
            except Exception:
                raise ValueError(f"Invalid URL format: {value}")
