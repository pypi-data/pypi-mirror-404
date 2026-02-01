#!/usr/bin/env python3
"""
souleyez.engine.log_sanitizer - Sanitize sensitive data from logs

Redacts credentials and sensitive information from job logs to prevent
plaintext password exposure, while maintaining log readability.
"""

import re
from typing import Optional


class LogSanitizer:
    """
    Sanitizes logs by redacting credentials and sensitive information.

    Patterns detected:
    - Login successful messages with credentials
    - Username:password combinations
    - SSH/FTP/MySQL/PostgreSQL credentials
    - API keys and tokens
    """

    # Common credential patterns
    PATTERNS = [
        # Metasploit successful login: [+] 10.0.0.82:5432 - Login Successful: postgres:postgres@template1
        (r"(Login Successful:?\s+)([^:]+):([^@\s]+)(@\S+)?", r"\1\2:[REDACTED]\4"),
        # MSF telnet_login format: msfadmin:msfadmin login: Login OK
        (r"(\s)([^:\s]+):([^:\s]+)(\s+login:\s+Login OK)", r"\1\2:[REDACTED]\4"),
        # Hydra output format: login: username   password: secretpass
        (r"(login:\s+)(\S+)(\s+password:\s+)(\S+)", r"\1\2\3[REDACTED]"),
        # Hydra colon format in output: [port][service] host: X   login: Y   password: Z
        (
            r"(host:\s+\S+\s+login:\s+)(\S+)(\s+password:\s+)(.+?)(\s|$)",
            r"\1\2\3[REDACTED]\5",
        ),
        # SSH/FTP success: Successfully authenticated as 'root' with password 'toor'
        (
            r"(authenticated as ['\"]?\w+['\"]? with password ['\"]?)([^'\"]+)(['\"]?)",
            r"\1[REDACTED]\3",
        ),
        # MySQL/PostgreSQL connection strings - capture everything between : and last @
        # This handles passwords with @ symbols by matching the last @ before a hostname
        (
            r"((?:mysql|postgres|postgresql)://[^:]+:)(.+)(@(?:(?:\d{1,3}\.){3}\d{1,3}(?::\d+)?|[a-zA-Z0-9.-]+(?::\d+)?)(?:/|$))",
            r"\1[REDACTED]\3",
        ),
        # Direct credentials: username:password format (but not URLs)
        (r"(?<!://)\b(\w+):([^\s:@]{4,})@", r"\1:[REDACTED]@"),
        # Common password indicators (stop at & to preserve form parameters)
        (
            r'(password[=:\s]+["\']?)([^"\'\s&]{4,})(["\']?)',
            r"\1[REDACTED]\3",
            re.IGNORECASE,
        ),
        (
            r'(pass[=:\s]+["\']?)([^"\'\s&]{4,})(["\']?)',
            r"\1[REDACTED]\3",
            re.IGNORECASE,
        ),
        (
            r'(pwd[=:\s]+["\']?)([^"\'\s&]{4,})(["\']?)',
            r"\1[REDACTED]\3",
            re.IGNORECASE,
        ),
        # API keys and tokens (long alphanumeric strings)
        (
            r'(["\']?api[_-]?key["\']?\s*[=:]\s*["\']?)([A-Za-z0-9_-]{20,})(["\']?)',
            r"\1[REDACTED]\3",
            re.IGNORECASE,
        ),
        (
            r'(["\']?token["\']?\s*[=:]\s*["\']?)([A-Za-z0-9_.-]{20,})(["\']?)',
            r"\1[REDACTED]\3",
            re.IGNORECASE,
        ),
        # SSH private keys
        (
            r"(-----BEGIN[A-Z\s]+PRIVATE KEY-----)(.*?)(-----END[A-Z\s]+PRIVATE KEY-----)",
            r"\1\n[REDACTED]\n\3",
            re.DOTALL,
        ),
        # Hashes (common hash formats: MD5, SHA1, SHA256)
        (r"\b([a-f0-9]{32})\b", r"[HASH_REDACTED]"),  # MD5
        (r"\b([a-f0-9]{40})\b", r"[HASH_REDACTED]"),  # SHA1
        (r"\b([a-f0-9]{64})\b", r"[HASH_REDACTED]"),  # SHA256
        # Generic secret patterns
        (
            r'(secret[=:\s]+["\']?)([^"\'\s]{4,})(["\']?)',
            r"\1[REDACTED]\3",
            re.IGNORECASE,
        ),
    ]

    # Whitelist patterns (don't redact these even if they match)
    WHITELIST_PATTERNS = [
        r"http://",
        r"https://",
        r"localhost",
        r"127\.0\.0\.1",
        r"0\.0\.0\.0",
        r"example\.com",
    ]

    @classmethod
    def sanitize(cls, log_content: str, aggressive: bool = False) -> str:
        """
        Sanitize log content by redacting credentials.

        Args:
            log_content: Raw log content
            aggressive: If True, use more aggressive redaction (may over-redact)

        Returns:
            Sanitized log content with credentials redacted
        """
        if not log_content:
            return log_content

        sanitized = log_content

        # Apply all patterns
        for pattern_tuple in cls.PATTERNS:
            if len(pattern_tuple) == 2:
                pattern, replacement = pattern_tuple
                flags = 0
            else:
                pattern, replacement, flags = pattern_tuple

            try:
                sanitized = re.sub(pattern, replacement, sanitized, flags=flags)
            except Exception:
                # If regex fails, continue with next pattern
                continue

        return sanitized

    @classmethod
    def contains_credentials(cls, log_content: str) -> bool:
        """
        Check if log content appears to contain credentials.

        Args:
            log_content: Log content to check

        Returns:
            True if credentials detected, False otherwise
        """
        if not log_content:
            return False

        # Quick checks for common credential indicators
        indicators = [
            "login successful",
            "login ok",  # MSF telnet_login
            "authenticated",
            "password:",
            "credentials",
            "api_key",
            "api-key",
            "token:",
            "secret:",
            "BEGIN PRIVATE KEY",
            "login:",  # Hydra output
            "valid pair found",  # Hydra success
        ]

        log_lower = log_content.lower()
        return any(indicator in log_lower for indicator in indicators)

    @classmethod
    def get_redaction_summary(cls, original: str, sanitized: str) -> Optional[str]:
        """
        Generate a summary of what was redacted.

        Args:
            original: Original log content
            sanitized: Sanitized log content

        Returns:
            Summary message or None if nothing redacted
        """
        if original == sanitized:
            return None

        # Count how many times [REDACTED] appears in sanitized version
        redaction_count = sanitized.count("[REDACTED]")
        hash_count = sanitized.count("[HASH_REDACTED]")

        parts = []
        if redaction_count > 0:
            parts.append(f"{redaction_count} credential(s)")
        if hash_count > 0:
            parts.append(f"{hash_count} hash(es)")

        if parts:
            return f"Redacted: {', '.join(parts)}"

        return "Some sensitive data redacted"


def sanitize_log_file(log_path: str, output_path: Optional[str] = None) -> bool:
    """
    Sanitize a log file in place or write to new file.

    Args:
        log_path: Path to log file to sanitize
        output_path: Optional output path (if None, modifies in place)

    Returns:
        True if successful, False otherwise
    """
    try:
        with open(log_path, "r", encoding="utf-8", errors="replace") as f:
            original = f.read()

        sanitized = LogSanitizer.sanitize(original)

        target_path = output_path or log_path
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(sanitized)

        return True
    except Exception:
        return False
