#!/usr/bin/env python3
"""
Tests for enhanced configuration management system.
"""
from souleyez import config


def test_default_config_loads():
    """Test that defaults load correctly"""
    val = config.get("crypto.iterations")
    assert val == 600000


def test_database_path_default():
    """Test database path default"""
    val = config.get("database.path")
    assert val == "~/.souleyez/souleyez.db"


def test_env_var_override(monkeypatch):
    """Test env var has highest priority"""
    monkeypatch.setenv("SOULEYEZ_CRYPTO_ITERATIONS", "999999")
    val = config.get("crypto.iterations")
    assert val == "999999"


def test_env_var_database_path(monkeypatch):
    """Test env var overrides database path"""
    monkeypatch.setenv("SOULEYEZ_DATABASE_PATH", "/tmp/custom.db")
    val = config.get("database.path")
    assert val == "/tmp/custom.db"


def test_validation_rejects_low_iterations():
    """Test validation prevents weak crypto"""
    bad_config = {"crypto": {"iterations": 1000}}
    is_valid, errors = config.validate_config(bad_config)
    assert not is_valid
    assert any("100" in err.lower() for err in errors)


def test_validation_rejects_high_iterations():
    """Test validation prevents excessive iterations"""
    bad_config = {"crypto": {"iterations": 99999999}}
    is_valid, errors = config.validate_config(bad_config)
    assert not is_valid


def test_validation_accepts_valid_iterations():
    """Test validation accepts valid iteration count"""
    good_config = {"crypto": {"iterations": 600000}}
    is_valid, errors = config.validate_config(good_config)
    assert is_valid
    assert len(errors) == 0


def test_validation_rejects_invalid_log_level():
    """Test validation rejects bad log level"""
    bad_config = {"logging": {"level": "INVALID"}}
    is_valid, errors = config.validate_config(bad_config)
    assert not is_valid
    has_error = any(
        "invalid" in err.lower() or "must be one of" in err.lower() for err in errors
    )
    assert has_error


def test_validation_accepts_valid_log_level():
    """Test validation accepts valid log levels"""
    for level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
        good_config = {"logging": {"level": level}}
        is_valid, errors = config.validate_config(good_config)
        assert is_valid, f"Failed for level {level}: {errors}"


def test_validation_rejects_remote_database():
    """Test validation prevents remote database paths"""
    for url in ["http://evil.com/db", "https://bad.com/db", "ftp://no.com/db"]:
        bad_config = {"database": {"path": url}}
        is_valid, errors = config.validate_config(bad_config)
        assert not is_valid
        assert any("local" in err.lower() for err in errors)


def test_validation_accepts_local_database_path():
    """Test validation accepts local paths"""
    good_config = {"database": {"path": "/home/user/.souleyez/db.sqlite"}}
    is_valid, errors = config.validate_config(good_config)
    assert is_valid


def test_dotted_notation_get():
    """Test dotted key access"""
    cfg = {"database": {"path": "/test/path", "backup_enabled": True}}
    val = config._get_nested(cfg, "database.path")
    assert val == "/test/path"
    val2 = config._get_nested(cfg, "database.backup_enabled")
    assert val2 is True


def test_dotted_notation_get_missing():
    """Test dotted notation returns default for missing keys"""
    cfg = {"database": {"path": "/test"}}
    val = config._get_nested(cfg, "database.missing", default="DEFAULT")
    assert val == "DEFAULT"


def test_dotted_notation_set():
    """Test dotted notation setting values"""
    cfg = {}
    config._set_nested(cfg, "database.path", "/new/path")
    assert cfg == {"database": {"path": "/new/path"}}


def test_validation_thread_limits():
    """Test thread count validation"""
    bad_low = {"settings": {"threads": 0}}
    is_valid, _ = config.validate_config(bad_low)
    assert not is_valid

    bad_high = {"settings": {"threads": 999}}
    is_valid, _ = config.validate_config(bad_high)
    assert not is_valid

    good = {"settings": {"threads": 10}}
    is_valid, _ = config.validate_config(good)
    assert is_valid


def test_validation_session_timeout():
    """Test session timeout validation"""
    bad_low = {"security": {"session_timeout_minutes": 1}}
    is_valid, _ = config.validate_config(bad_low)
    assert not is_valid

    bad_high = {"security": {"session_timeout_minutes": 9999}}
    is_valid, _ = config.validate_config(bad_high)
    assert not is_valid

    good = {"security": {"session_timeout_minutes": 30}}
    is_valid, _ = config.validate_config(good)
    assert is_valid


def test_validation_max_login_attempts():
    """Test max login attempts validation"""
    bad_low = {"security": {"max_login_attempts": 0}}
    is_valid, _ = config.validate_config(bad_low)
    assert not is_valid

    bad_high = {"security": {"max_login_attempts": 99}}
    is_valid, _ = config.validate_config(bad_high)
    assert not is_valid

    good = {"security": {"max_login_attempts": 5}}
    is_valid, _ = config.validate_config(good)
    assert is_valid


def test_merge_with_defaults():
    """Test partial config merges with defaults"""
    partial = {"crypto": {"iterations": 700000}}
    merged = config._merge_with_defaults(partial)

    # Should have custom value
    assert merged["crypto"]["iterations"] == 700000
    # Should have default values for other keys
    assert merged["database"]["path"] == "~/.souleyez/souleyez.db"
    assert merged["logging"]["level"] == "INFO"


def test_backward_compatibility_old_plugin_format():
    """Test old flat plugin config still works"""
    old_format = {"enabled": ["nmap"], "disabled": ["gobuster"]}
    normalized = config._normalize(old_format)

    assert "plugins" in normalized
    assert normalized["plugins"]["enabled"] == ["nmap"]
    assert normalized["plugins"]["disabled"] == ["gobuster"]


def test_backward_compatibility_new_plugin_format():
    """Test new nested plugin config works"""
    new_format = {
        "plugins": {"enabled": ["nmap"], "disabled": ["gobuster"]},
        "settings": {"threads": 5},
    }
    normalized = config._normalize(new_format)

    assert normalized["plugins"]["enabled"] == ["nmap"]
    assert normalized["settings"]["threads"] == 5


def test_get_nested_key():
    """Test getting nested config value"""
    val = config.get("logging.level")
    assert val in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


def test_get_with_default():
    """Test get() with fallback default"""
    val = config.get("nonexistent.key", "FALLBACK")
    assert val == "FALLBACK"


def test_security_settings_exist():
    """Test that all security settings have defaults"""
    assert config.get("security.session_timeout_minutes") == 30
    assert config.get("security.max_login_attempts") == 5
    assert config.get("security.lockout_duration_minutes") == 15
    assert config.get("security.min_password_length") == 12
