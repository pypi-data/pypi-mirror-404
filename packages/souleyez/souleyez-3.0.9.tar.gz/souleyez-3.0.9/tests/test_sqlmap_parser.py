#!/usr/bin/env python3
"""
Tests for SQLMap parser to prevent regressions.
"""
from souleyez.parsers.sqlmap_parser import parse_sqlmap_output


def test_injectable_url_with_resumed_session():
    """Test that injectable_url is set correctly when SQLMap resumes a session."""
    log = """
[INFO] testing URL 'http://10.0.0.82/mutillidae/?page=add-to-your-blog.php'
sqlmap resumed the following injection point(s) from stored session:
---
Parameter: User-Agent (User-Agent)
    Type: time-based blind
    Title: MySQL >= 5.0.12 AND time-based blind (query SLEEP)
---
[INFO] the back-end DBMS is MySQL
back-end DBMS: MySQL >= 5.0.12
"""

    result = parse_sqlmap_output(log, "10.0.0.82")

    # Critical assertions
    assert (
        result["sql_injection_confirmed"] == True
    ), "SQL injection should be confirmed"
    assert (
        result["injectable_parameter"] == "User-Agent"
    ), "Should detect User-Agent parameter"
    assert (
        result["injectable_url"]
        == "http://10.0.0.82/mutillidae/?page=add-to-your-blog.php"
    ), "injectable_url should be the FULL URL, not just the IP!"
    assert len(result["vulnerabilities"]) == 1, "Should have 1 vulnerability"


def test_injectable_url_with_normal_detection():
    """Test that injectable_url is set correctly with normal 'is vulnerable' detection."""
    log = """
[INFO] testing URL 'http://example.com/page.php?id=1'
[INFO] GET parameter 'id' is vulnerable. Do you want to...
[INFO] the back-end DBMS is MySQL
"""

    result = parse_sqlmap_output(log, "example.com")

    assert result["sql_injection_confirmed"] == True
    assert result["injectable_parameter"] == "id"
    assert (
        result["injectable_url"] == "http://example.com/page.php?id=1"
    ), "injectable_url should use current_url from log, not target parameter"


def test_injectable_url_fallback():
    """Test that injectable_url falls back to target when URL not found in log."""
    log = """
Parameter: test (GET)
    Type: time-based blind
"""

    result = parse_sqlmap_output(log, "http://fallback.com/test")

    # Should fall back to target since no 'testing URL' line
    assert result["injectable_url"] == "http://fallback.com/test"


def test_hyphenated_parameters():
    """Test that parameters with hyphens are detected (User-Agent, Content-Type, etc.)."""
    log = """
[INFO] testing URL 'http://test.com/page'
Parameter: User-Agent (User-Agent)
    Type: boolean-based blind
"""

    result = parse_sqlmap_output(log, "test.com")

    assert (
        result["injectable_parameter"] == "User-Agent"
    ), "Should handle hyphens in parameter names"
    assert result["sql_injection_confirmed"] == True


if __name__ == "__main__":
    # Run tests
    import sys

    tests = [
        test_injectable_url_with_resumed_session,
        test_injectable_url_with_normal_detection,
        test_injectable_url_fallback,
        test_hyphenated_parameters,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            print(f"✓ {test.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"✗ {test.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test.__name__}: {type(e).__name__}: {e}")
            failed += 1

    print(f"\n{passed} passed, {failed} failed")
    sys.exit(0 if failed == 0 else 1)
