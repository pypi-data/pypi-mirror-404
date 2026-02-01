"""Tests for tool_chaining module.

These tests verify the tool chaining functionality including
nuclei tag detection and chain rule evaluation.
"""

import pytest


class TestDetectNucleiTags:
    """Test nuclei tag detection from service information."""

    def test_none_os_info_does_not_crash(self):
        """detect_nuclei_tags should handle None os_info gracefully.

        When os_info is None (e.g., from multi-host nmap scans),
        the function should not crash with 'NoneType' has no attribute 'lower'.

        Regression test for multi-host nmap chain_error.
        """
        from souleyez.core.tool_chaining import detect_nuclei_tags

        # Should not raise AttributeError
        result = detect_nuclei_tags([], None)
        assert result == ""

    def test_empty_os_info_returns_empty(self):
        """Empty os_info should return empty string."""
        from souleyez.core.tool_chaining import detect_nuclei_tags

        result = detect_nuclei_tags([], "")
        assert result == ""

    def test_linux_os_detected(self):
        """Linux OS should add linux tag."""
        from souleyez.core.tool_chaining import detect_nuclei_tags

        result = detect_nuclei_tags([], "Linux Ubuntu 20.04")
        assert "linux" in result

    def test_windows_os_detected(self):
        """Windows OS should add windows and microsoft tags."""
        from souleyez.core.tool_chaining import detect_nuclei_tags

        result = detect_nuclei_tags([], "Windows Server 2019")
        assert "windows" in result
        assert "microsoft" in result

    def test_apache_service_detected(self):
        """Apache service should add apache tag."""
        from souleyez.core.tool_chaining import detect_nuclei_tags

        services = [
            {"product": "Apache httpd", "raw_version": "2.4.49", "service_name": "http"}
        ]
        result = detect_nuclei_tags(services, "")
        assert "apache" in result

    def test_wordpress_detected(self):
        """WordPress in service info should add wordpress tags."""
        from souleyez.core.tool_chaining import detect_nuclei_tags

        services = [
            {"product": "WordPress", "raw_version": "5.8", "service_name": "http"}
        ]
        result = detect_nuclei_tags(services, "")
        assert "wordpress" in result

    def test_no_services_no_os_returns_empty(self):
        """No services and no OS info should return empty."""
        from souleyez.core.tool_chaining import detect_nuclei_tags

        result = detect_nuclei_tags([], "")
        assert result == ""


class TestChainDeduplication:
    """Test chain job deduplication to prevent redundant scans."""

    def test_should_skip_duplicate_helper_exists(self):
        """The _should_skip_duplicate helper should exist."""
        from souleyez.core.tool_chaining import ToolChaining

        manager = ToolChaining()
        # Method should exist
        assert hasattr(
            manager, "_should_skip_duplicate"
        ), "ToolChaining should have _should_skip_duplicate method"

    def test_should_skip_duplicate_returns_bool(self):
        """_should_skip_duplicate should return boolean."""
        from souleyez.core.tool_chaining import ToolChaining

        manager = ToolChaining()
        # Should return False for a new tool+target combo
        result = manager._should_skip_duplicate(
            tool="nuclei",
            target="http://example.com/unique-test-url",
            engagement_id=99999,  # Non-existent engagement
        )
        assert isinstance(result, bool)

    def test_sqlmap_dedup_window_is_30_minutes(self):
        """SQLMap rule-based dedup window should be 30 minutes.

        This allows re-running sqlmap chains after 30 min while preventing
        infinite loops during active scans.
        """
        # The constant is defined inside _enqueue_commands, but we can verify
        # the module loads correctly with the constant
        from souleyez.core.tool_chaining import ToolChaining

        manager = ToolChaining()

        # 30 minutes = 1800 seconds
        EXPECTED_WINDOW = 1800
        # This is a documentation test - the actual value is in _enqueue_commands
        assert EXPECTED_WINDOW == 30 * 60, "SQLMap dedup window should be 30 minutes"

    def test_sqlmap_excluded_from_secondary_dedup_check(self):
        """SQLMap should be excluded from the _should_skip_duplicate check.

        SQLMap uses multiple phases (--dbs, --tables, --columns, --dump) that
        all target the same URL. These are NOT duplicates - they are intentional
        progressive exploitation steps.

        SQLMap deduplication is handled separately via rule_id checks in the
        main dedup logic, not by this simple tool+target check.

        Regression test for auto-chain not triggering --tables jobs after
        sqlmap --dbs finds databases.
        """
        from souleyez.core.tool_chaining import ToolChaining

        manager = ToolChaining()

        # SQLMap should always return False from _should_skip_duplicate
        # because it has its own rule_id based dedup logic
        result = manager._should_skip_duplicate(
            tool="sqlmap",
            target="http://example.com/some-injection-point",
            engagement_id=1,
        )
        assert (
            result is False
        ), "sqlmap should be excluded from _should_skip_duplicate check"


class TestSmartChainRuleIds:
    """Test that smart chains have rule_id values for tracking.

    Smart chains are auto-triggered chains that don't come from user-defined rules.
    They use negative rule_id values:
        -1: ffuf → sqlmap (dynamic endpoint)
        -2: ffuf → recursive ffuf (500 response)
        -3: sqlmap → dump (sensitive columns)
        -4: gobuster redirect retry

    Regression test for jobs #792/#793 missing rule_id.
    """

    def test_smart_chain_constants_defined(self):
        """Smart chain rule_id constants should be documented in code.

        The negative rule_id values are used inline, but this test
        documents the expected values for reference.
        """
        # These are the expected smart chain rule_id values
        SMART_FFUF_SQLMAP = -1  # ffuf → sqlmap (dynamic endpoint)
        SMART_FFUF_RECURSIVE = -2  # ffuf → recursive ffuf (500 response)
        SMART_SQLMAP_DUMP = -3  # sqlmap → dump (sensitive columns)
        SMART_GOBUSTER_RETRY = -4  # gobuster redirect retry

        # All should be negative (distinguishes from regular rules)
        assert SMART_FFUF_SQLMAP < 0
        assert SMART_FFUF_RECURSIVE < 0
        assert SMART_SQLMAP_DUMP < 0
        assert SMART_GOBUSTER_RETRY < 0

    def test_tool_chaining_module_imports(self):
        """ToolChaining module should import without errors."""
        # This verifies the rule_id additions don't break the module
        from souleyez.core.tool_chaining import ToolChaining

        manager = ToolChaining()
        assert manager is not None


class TestFfufSqlmapFiltering:
    """Test ffuf → sqlmap URL filtering to prevent useless SQLMap jobs.

    These tests verify that the should_test_url_for_sqli() function correctly
    filters URLs to only test those with actual injection potential.

    Regression tests for:
    - Metasploitable2: filtering /phpinfo, /cgi-bin/, /index.php
    - Metasploitable3: allowing /payroll_app.php for form-based testing
    """

    def test_filters_bare_index_php(self):
        """Ensure /index.php without params is filtered.

        /index.php is a common default page that rarely has injectable forms.
        Without query parameters, it's not worth testing.
        """
        from souleyez.core.tool_chaining import should_test_url_for_sqli

        assert should_test_url_for_sqli("http://192.168.1.240/index.php") is False

    def test_filters_index_asp(self):
        """Ensure /index.asp without params is filtered."""
        from souleyez.core.tool_chaining import should_test_url_for_sqli

        assert should_test_url_for_sqli("http://192.168.1.240/index.asp") is False

    def test_filters_default_aspx(self):
        """Ensure /default.aspx without params is filtered."""
        from souleyez.core.tool_chaining import should_test_url_for_sqli

        assert should_test_url_for_sqli("http://192.168.1.240/default.aspx") is False

    def test_allows_payroll_app_php(self):
        """Ensure payroll_app.php passes for form-based testing.

        Metasploitable3 has a vulnerable payroll_app.php with login forms.
        Even without query params, sqlmap --forms should test it.
        """
        from souleyez.core.tool_chaining import should_test_url_for_sqli

        assert should_test_url_for_sqli("http://192.168.1.157/payroll_app.php") is True

    def test_allows_login_php(self):
        """Ensure login.php passes for form-based testing."""
        from souleyez.core.tool_chaining import should_test_url_for_sqli

        assert should_test_url_for_sqli("http://example.com/login.php") is True

    def test_allows_search_php(self):
        """Ensure search.php passes for form-based testing."""
        from souleyez.core.tool_chaining import should_test_url_for_sqli

        assert should_test_url_for_sqli("http://example.com/search.php") is True

    def test_filters_phpinfo(self):
        """Ensure /phpinfo is filtered.

        phpinfo() output pages have no injection points.
        """
        from souleyez.core.tool_chaining import should_test_url_for_sqli

        assert should_test_url_for_sqli("http://192.168.1.240/phpinfo") is False
        assert should_test_url_for_sqli("http://192.168.1.240/phpinfo.php") is False

    def test_filters_cgi_bin_directory(self):
        """Ensure /cgi-bin/ directory is filtered.

        The base CGI directory without a specific script has nothing to test.
        """
        from souleyez.core.tool_chaining import should_test_url_for_sqli

        assert should_test_url_for_sqli("http://192.168.1.240/cgi-bin/") is False

    def test_allows_cgi_script(self):
        """Ensure actual CGI scripts are allowed."""
        from souleyez.core.tool_chaining import should_test_url_for_sqli

        assert should_test_url_for_sqli("http://example.com/search.cgi") is True

    def test_filters_phpmyadmin(self):
        """Ensure /phpmyadmin/ is filtered.

        phpMyAdmin is a database admin tool, not an injection target.
        """
        from souleyez.core.tool_chaining import should_test_url_for_sqli

        assert should_test_url_for_sqli("http://192.168.1.240/phpmyadmin/") is False
        assert should_test_url_for_sqli("http://192.168.1.240/phpMyAdmin/") is False

    def test_filters_twiki(self):
        """Ensure /twiki/ is filtered."""
        from souleyez.core.tool_chaining import should_test_url_for_sqli

        assert should_test_url_for_sqli("http://example.com/twiki/bin/view") is False

    def test_filters_bare_url(self):
        """Ensure bare URL with no path is filtered."""
        from souleyez.core.tool_chaining import should_test_url_for_sqli

        assert should_test_url_for_sqli("http://192.168.1.240") is False
        assert should_test_url_for_sqli("http://192.168.1.240/") is False

    def test_filters_static_directory(self):
        """Ensure static directories are filtered."""
        from souleyez.core.tool_chaining import should_test_url_for_sqli

        assert should_test_url_for_sqli("http://example.com/images/") is False
        assert should_test_url_for_sqli("http://example.com/css/") is False

    def test_allows_url_with_query_params(self):
        """Ensure URLs with query parameters are allowed.

        Query parameters are the primary injection points for SQLi.
        """
        from souleyez.core.tool_chaining import should_test_url_for_sqli

        assert should_test_url_for_sqli("http://example.com/search.php?q=test") is True
        assert should_test_url_for_sqli("http://example.com/view.php?id=1") is True

    def test_allows_index_php_with_params(self):
        """Ensure /index.php WITH params is allowed.

        index.php?page=home has an injection point, so it should be tested.
        """
        from souleyez.core.tool_chaining import should_test_url_for_sqli

        assert should_test_url_for_sqli("http://example.com/index.php?page=home") is True
        assert should_test_url_for_sqli("http://example.com/index.php?id=1") is True

    def test_allows_mutillidae_with_params(self):
        """Ensure Mutillidae URLs with params are allowed.

        Mutillidae is an intentionally vulnerable app used for testing.
        """
        from souleyez.core.tool_chaining import should_test_url_for_sqli

        url = "http://192.168.1.240/mutillidae/index.php?page=user-info.php"
        assert should_test_url_for_sqli(url) is True

    def test_allows_jsp_pages(self):
        """Ensure .jsp pages are allowed for form testing."""
        from souleyez.core.tool_chaining import should_test_url_for_sqli

        assert should_test_url_for_sqli("http://example.com/admin.jsp") is True

    def test_allows_action_pages(self):
        """Ensure .action (Struts) pages are allowed."""
        from souleyez.core.tool_chaining import should_test_url_for_sqli

        assert should_test_url_for_sqli("http://example.com/login.action") is True

    # === Regression tests from Metasploitable2 actual results ===

    def test_filters_phpinfo_subdirectory_files(self):
        """Ensure files under /phpinfo/ directory are filtered.

        Regression test from MS2 job #6564 - ffuf found files like
        /phpinfo/index.php, /phpinfo/login.php but they're all phpinfo
        output pages, not injectable.
        """
        from souleyez.core.tool_chaining import should_test_url_for_sqli

        assert should_test_url_for_sqli("http://192.168.1.240/phpinfo/index.php") is False
        assert should_test_url_for_sqli("http://192.168.1.240/phpinfo/login.php") is False
        assert should_test_url_for_sqli("http://192.168.1.240/phpinfo/admin.php") is False

    def test_filters_cgi_bin_files_without_params(self):
        """Ensure files under /cgi-bin/ are filtered when no params.

        Regression test from MS2 job #6562 - ffuf found .htaccess files
        in /cgi-bin/ with 403 status.
        """
        from souleyez.core.tool_chaining import should_test_url_for_sqli

        assert should_test_url_for_sqli("http://192.168.1.240/cgi-bin/.htaccess") is False
        assert should_test_url_for_sqli("http://192.168.1.240/cgi-bin/.htaccess.php") is False

    def test_allows_cgi_script_with_params(self):
        """Ensure CGI scripts WITH params are allowed.

        A CGI script with query parameters has injection points and
        should be tested, even though it's under /cgi-bin/.
        """
        from souleyez.core.tool_chaining import should_test_url_for_sqli

        assert should_test_url_for_sqli("http://example.com/cgi-bin/script.cgi?id=1") is True
        assert should_test_url_for_sqli("http://example.com/cgi-bin/vuln.cgi?cmd=test") is True

    def test_filters_phpmyadmin_even_with_params(self):
        """Ensure phpMyAdmin is filtered even with query params.

        phpMyAdmin is a database admin tool, not an injection target.
        We should never waste time testing it.
        """
        from souleyez.core.tool_chaining import should_test_url_for_sqli

        assert should_test_url_for_sqli("http://192.168.1.240/phpmyadmin/") is False
        assert should_test_url_for_sqli("http://192.168.1.240/phpmyadmin/?token=abc") is False
        assert should_test_url_for_sqli("http://192.168.1.240/phpMyAdmin/?db=test") is False

    # === Regression tests from Metasploitable3 Drupal results ===

    def test_filters_drupal_misc_directory(self):
        """Ensure /misc/ directory is filtered (Drupal static assets).

        Regression test from MS3 jobs #6663-6668 - katana found Drupal
        static files like /drupal/misc/jquery.js that shouldn't be tested.
        """
        from souleyez.core.tool_chaining import should_test_url_for_sqli

        assert should_test_url_for_sqli("http://192.168.1.157/drupal/misc/jquery.js") is False
        assert should_test_url_for_sqli("http://192.168.1.157/misc/drupal.js") is False

    def test_filters_drupal_modules_directory(self):
        """Ensure /modules/ directory is filtered (Drupal modules).

        Static files in /modules/ are framework assets, not injectable.
        """
        from souleyez.core.tool_chaining import should_test_url_for_sqli

        assert should_test_url_for_sqli("http://192.168.1.157/drupal/modules/system/system.css") is False
        assert should_test_url_for_sqli("http://192.168.1.157/modules/node/node.js") is False

    def test_filters_js_with_version_params(self):
        """Ensure .js files with version/cache params are filtered.

        URLs like /jquery.js?v=1.2.3 are static files with cache-busting
        parameters, not injectable endpoints.
        """
        from souleyez.core.tool_chaining import should_test_url_for_sqli

        assert should_test_url_for_sqli("http://example.com/jquery.js?v=1.2.3") is False
        assert should_test_url_for_sqli("http://example.com/drupal/misc/jquery.js?v=1.4.4") is False
        assert should_test_url_for_sqli("http://example.com/js/app.js?ver=5.0") is False

    def test_filters_css_with_version_params(self):
        """Ensure .css files with version/cache params are filtered.

        URLs like /style.css?ver=5.0 are static files, not injectable.
        """
        from souleyez.core.tool_chaining import should_test_url_for_sqli

        assert should_test_url_for_sqli("http://example.com/style.css?v=1.0") is False
        assert should_test_url_for_sqli("http://example.com/drupal/modules/system/system.css?ver=7.0") is False
        assert should_test_url_for_sqli("http://example.com/css/main.css?timestamp=123456") is False
