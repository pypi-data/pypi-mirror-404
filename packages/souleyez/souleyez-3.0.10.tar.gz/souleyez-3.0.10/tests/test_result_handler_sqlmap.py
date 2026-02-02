#!/usr/bin/env python3
"""
Integration test for result_handler + parser to prevent the target_url/injectable_url bug.
"""
import tempfile
import os
from souleyez.engine.result_handler import parse_sqlmap_job


def test_result_handler_uses_injectable_url():
    """
    REGRESSION TEST: Ensure result_handler reads 'injectable_url' not 'target_url'.

    This test prevents the bug where result_handler was reading the wrong key,
    causing auto-chaining to use just the IP instead of the full URL.
    """
    # First create a test engagement (required for FK constraint)
    from souleyez.storage.database import get_db

    db = get_db()
    db.execute(
        "INSERT OR REPLACE INTO engagements (id, name, description) VALUES (1, 'test', 'Test engagement')"
    )

    # Create a temporary log file
    log_content = """
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

    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".log") as f:
        f.write(log_content)
        log_path = f.name

    try:
        # Mock job
        job = {
            "id": 999,
            "tool": "sqlmap",
            "target": "10.0.0.82",  # Just the IP - this is what gets passed
            "engagement_id": 1,
        }

        # Parse the job
        result = parse_sqlmap_job(1, log_path, job)

        # CRITICAL ASSERTION: injectable_url should be the FULL URL, not just the IP
        assert (
            result["injectable_url"]
            == "http://10.0.0.82/mutillidae/?page=add-to-your-blog.php"
        ), f"REGRESSION: injectable_url should be full URL from log, not target parameter! Got: {result['injectable_url']}"

        assert (
            result["sql_injection_confirmed"] == True
        ), "SQL injection should be confirmed"
        assert (
            result["injectable_parameter"] == "User-Agent"
        ), "Should detect User-Agent parameter"

        print(
            "✓ result_handler correctly uses injectable_url from parser (not target_url)"
        )

    finally:
        os.unlink(log_path)


if __name__ == "__main__":
    test_result_handler_uses_injectable_url()
    print("\n✓ All integration tests passed!")
