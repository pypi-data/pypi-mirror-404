#!/usr/bin/env python3
"""
Module for detecting sensitive tables during SQLMap enumeration.
"""

from typing import Dict, List, Optional, Tuple

# System databases to NEVER dump (true system metadata only)
# NOTE: Only skip databases that are ALWAYS system/metadata databases
# Do NOT skip application databases even if they seem like "test" or "lab" databases
# Real engagements may have legitimately named databases like these
SYSTEM_DATABASES = {
    "information_schema",  # MySQL metadata - no user data
    "mysql",  # MySQL system tables - no user data
    "performance_schema",  # MySQL performance metrics - no user data
    "sys",  # MySQL system views - no user data
}

# System table patterns to skip (even in application databases)
SYSTEM_TABLE_PATTERNS = [
    "USER_PRIVILEGES",
    "SCHEMA_PRIVILEGES",
    "TABLE_PRIVILEGES",
    "COLUMN_PRIVILEGES",
    "REFERENTIAL_CONSTRAINTS",
    "KEY_COLUMN_USAGE",
    "TABLE_CONSTRAINTS",
    "STATISTICS",
    "VIEWS",
    "TRIGGERS",
    "ROUTINES",
    "EVENTS",
    "PARAMETERS",
]

# Skip tables with these suffixes (logs, history, metadata)
SKIP_TABLE_SUFFIXES = [
    "_log",
    "_logs",
    "_history",
    "_audit",
    "_backup",
    "_temp",
    "_tmp",
    "_cache",
    "_meta",
    "_metadata",
]


def is_system_database(database_name: str) -> bool:
    """Check if database is a system database (should never dump)."""
    if not database_name:
        return False
    return database_name.lower().strip() in SYSTEM_DATABASES


def is_system_table(table_name: str) -> bool:
    """Check if table is a system table (should skip)."""
    if not table_name:
        return False

    table_lower = table_name.lower().strip()

    # Check against system table patterns
    for pattern in SYSTEM_TABLE_PATTERNS:
        if pattern.lower() in table_lower:
            return True

    # Check suffixes
    for suffix in SKIP_TABLE_SUFFIXES:
        if table_lower.endswith(suffix):
            return True

    return False


# Sensitive table name patterns by category
SENSITIVE_TABLE_PATTERNS = {
    "credentials": [
        "users",
        "user",
        "accounts",
        "account",
        "members",
        "member",
        "logins",
        "login",
        "auth",
        "authentication",
        "customers",
        "customer",
        "clients",
        "client",
        "administrators",
        "admin",
        "admins",
        "staff",
        "employees",
        "employee",
    ],
    "payment": [
        "credit_cards",
        "creditcards",
        "cards",
        "card",
        "payments",
        "payment",
        "transactions",
        "transaction",
        "billing",
        "invoices",
        "invoice",
        "orders",
        "order",
    ],
    "sensitive_pii": [
        "profiles",
        "profile",
        "persons",
        "person",
        "contacts",
        "contact",
        "addresses",
        "address",
        "personal_info",
        "pii",
        "identities",
        "identity",
        "social_security",
        "ssn",
        "drivers_license",
        "passport",
    ],
    "secrets": [
        "api_keys",
        "tokens",
        "secrets",
        "keys",
        "passwords",
        "password",
        "credentials",
        "creds",
        "sessions",
        "session",
        "oauth",
        "jwt",
    ],
}

# Column name patterns for validation
SENSITIVE_COLUMN_PATTERNS = {
    "credentials": [
        "password",
        "passwd",
        "pass",
        "pwd",
        "hash",
        "username",
        "user",
        "email",
        "login",
        "salt",
        "token",
        "secret",
        "api_key",
    ],
    "payment": [
        "card_number",
        "cvv",
        "expiry",
        "card_type",
        "account_number",
        "routing_number",
        "iban",
        "swift",
        "cardholder",
        "billing",
    ],
    "pii": [
        "ssn",
        "social_security",
        "tax_id",
        "national_id",
        "address",
        "phone",
        "dob",
        "birth_date",
        "drivers_license",
        "passport",
        "maiden_name",
    ],
}


def is_sensitive_table(
    table_name: str, category: Optional[str] = None
) -> Tuple[bool, Optional[str], int]:
    """
    Determine if a table name is sensitive.

    Args:
        table_name: Name of the table to check
        category: Optional category filter ('credentials', 'payment', 'pii', 'secrets')

    Returns:
        tuple: (is_sensitive, category, priority)
               priority: 1-10 (10 = most critical to dump)

    Examples:
        >>> is_sensitive_table('users')
        (True, 'credentials', 10)

        >>> is_sensitive_table('credit_cards')
        (True, 'payment', 10)

        >>> is_sensitive_table('tiki_user_bookmarks')
        (False, None, 0)  # "user" is just a prefix, not the table's purpose

        >>> is_sensitive_table('products')
        (False, None, 0)
    """
    import re

    # Normalize table name for matching
    table_lower = table_name.lower().strip()

    # Remove common prefixes (including tiki_, drupal_, etc.)
    for prefix in ["tbl_", "app_", "wp_", "db_", "sys_", "tiki_", "drupal_", "joomla_"]:
        if table_lower.startswith(prefix):
            table_lower = table_lower[len(prefix) :]
            break

    # Priority by category (credentials most important)
    category_priorities = {
        "credentials": 10,
        "payment": 9,
        "secrets": 8,
        "sensitive_pii": 7,
    }

    # Check against patterns
    categories_to_check = [category] if category else SENSITIVE_TABLE_PATTERNS.keys()

    for cat in categories_to_check:
        if cat not in SENSITIVE_TABLE_PATTERNS:
            continue

        patterns = SENSITIVE_TABLE_PATTERNS[cat]
        for pattern in patterns:
            pattern_lower = pattern.lower()

            # STRICT matching - pattern must be the CORE of the table name, not just a prefix
            # Match: users, user, wp_users, tiki_users, users_users
            # NO match: user_bookmarks, user_settings, user_preferences (these are about something else)

            # 1. Exact match (after prefix removal)
            if table_lower == pattern_lower:
                priority = category_priorities.get(cat, 5)
                return (True, cat, priority)

            # 2. Table ENDS with the pattern (e.g., "users_users" ends with "users")
            if table_lower.endswith("_" + pattern_lower) or table_lower.endswith(
                pattern_lower
            ):
                # Make sure it's a word boundary, not partial (e.g., "xusers" shouldn't match)
                if table_lower == pattern_lower or table_lower.endswith(
                    "_" + pattern_lower
                ):
                    priority = category_priorities.get(cat, 5)
                    return (True, cat, priority)

            # 3. Singular/plural variants at end only
            pattern_singular = pattern_lower.rstrip("s")
            table_singular = table_lower.rstrip("s")
            if table_singular == pattern_singular:
                priority = category_priorities.get(cat, 5)
                return (True, cat, priority)

    return (False, None, 0)


def validate_sensitive_columns(columns: List[str], expected_category: str) -> bool:
    """
    Validate that columns match the expected sensitive category.

    Reduces false positives by checking column names.

    Args:
        columns: List of column names
        expected_category: Expected category ('credentials', 'payment', etc.)

    Returns:
        bool: True if columns match expected pattern

    Examples:
        >>> validate_sensitive_columns(['username', 'password', 'email'], 'credentials')
        True

        >>> validate_sensitive_columns(['id', 'name'], 'credentials')
        False  # Missing password/username columns
    """
    if not columns:
        return False

    # Map category to column patterns
    category_map = {
        "credentials": SENSITIVE_COLUMN_PATTERNS["credentials"],
        "payment": SENSITIVE_COLUMN_PATTERNS["payment"],
        "sensitive_pii": SENSITIVE_COLUMN_PATTERNS["pii"],
        "secrets": SENSITIVE_COLUMN_PATTERNS[
            "credentials"
        ],  # Secrets use same patterns as credentials
    }

    expected_patterns = category_map.get(expected_category, [])
    if not expected_patterns:
        return True  # If no patterns defined, assume valid

    # Normalize column names
    columns_lower = [col.lower() for col in columns]

    # Check if any expected patterns match
    matches = 0
    for pattern in expected_patterns:
        pattern_lower = pattern.lower()
        for col in columns_lower:
            if pattern_lower in col or col in pattern_lower:
                matches += 1
                break

    # Require at least 2 matching columns for high confidence
    # (e.g., username + password, card_number + cvv)
    return matches >= 2


def prioritize_tables(
    tables: Dict[str, List[str]], columns: Optional[Dict[str, List[str]]] = None
) -> List[Dict]:
    """
    Prioritize sensitive tables for dumping.

    Args:
        tables: Dict of {database: [table_names]}
        columns: Optional dict of {db.table: [column_names]} for validation

    Returns:
        List of dicts sorted by priority:
        [
            {
                'database': 'webapp',
                'table': 'users',
                'category': 'credentials',
                'priority': 10,
                'columns': ['id', 'username', 'password', 'email']
            },
            ...
        ]

    Limits:
        - Max 10 tables total across all databases
        - Priority 8-10 only (avoid dumping low-confidence matches)
    """
    sensitive_tables = []

    for database, table_list in tables.items():
        for table in table_list:
            # Check if table is sensitive
            is_sensitive, category, priority = is_sensitive_table(table)

            if not is_sensitive or priority < 5:
                continue  # Skip non-sensitive tables (lowered threshold for thoroughness)

            # Get columns for validation if available
            table_key = f"{database}.{table}"
            table_columns = columns.get(table_key, []) if columns else []

            # Validate columns if available (but don't skip - just note it)
            if table_columns:
                if not validate_sensitive_columns(table_columns, category):
                    # Columns don't match expected pattern - reduce priority slightly
                    # but still include for thoroughness
                    priority -= 1

            sensitive_tables.append(
                {
                    "database": database,
                    "table": table,
                    "category": category,
                    "priority": priority,
                    "columns": table_columns,
                }
            )

    # Sort by priority (highest first), then by category importance
    category_order = {"credentials": 0, "payment": 1, "secrets": 2, "sensitive_pii": 3}
    sensitive_tables.sort(
        key=lambda t: (-t["priority"], category_order.get(t["category"], 9))
    )

    # Limit to top 25 tables (increased for thoroughness in real engagements)
    return sensitive_tables[:25]


# Sensitive table names (for quick lookup without column validation)
SENSITIVE_TABLE_NAMES = {
    "users",
    "user",
    "accounts",
    "account",
    "members",
    "member",
    "customers",
    "customer",
    "clients",
    "client",
    "admins",
    "admin",
    "administrators",
    "credentials",
    "creds",
    "passwords",
    "passwd",
    "logins",
    "login",
    "auth",
    "authentication",
    "sessions",
    "tokens",
    "api_keys",
    "apikeys",
    "credit_cards",
    "creditcards",
    "cards",
    "payments",
    "orders",
    "transactions",
    "billing",
}


def is_sensitive_table_name(table_name: str) -> bool:
    """
    Check if table name suggests sensitive data (name-based only).

    Used for quick decisions without column information.

    Args:
        table_name: Name of the table to check

    Returns:
        bool: True if table name suggests sensitive data

    Examples:
        >>> is_sensitive_table_name('users')
        True
        >>> is_sensitive_table_name('products')
        False
    """
    if not table_name:
        return False
    return table_name.lower().strip() in SENSITIVE_TABLE_NAMES


# Sensitive column patterns (expanded for detection)
SENSITIVE_COLUMN_KEYWORDS = {
    "password",
    "passwd",
    "pass",
    "pwd",
    "secret",
    "email",
    "mail",
    "phone",
    "mobile",
    "cell",
    "ssn",
    "social_security",
    "national_id",
    "tax_id",
    "credit_card",
    "cc_number",
    "card_number",
    "cvv",
    "ccv",
    "token",
    "api_key",
    "apikey",
    "auth_token",
    "session",
    "address",
    "street",
    "city",
    "zip",
    "postal",
    "dob",
    "date_of_birth",
    "birthday",
    "birthdate",
    "salary",
    "income",
    "bank",
    "account_number",
    "routing",
}


def has_sensitive_columns(columns: List[str]) -> bool:
    """
    Check if any column name suggests sensitive data.

    Args:
        columns: List of column names or column dictionaries

    Returns:
        bool: True if sensitive columns detected

    Examples:
        >>> has_sensitive_columns(['id', 'username', 'password'])
        True
        >>> has_sensitive_columns(['id', 'name', 'description'])
        False
    """
    if not columns:
        return False

    for col in columns:
        # Handle both string column names and dict with 'name' key
        if isinstance(col, dict):
            col_name = col.get("name", col.get("column", ""))
        else:
            col_name = str(col)

        col_lower = col_name.lower()

        # Check if any sensitive keyword appears in column name
        for pattern in SENSITIVE_COLUMN_KEYWORDS:
            if pattern in col_lower:
                return True

    return False
