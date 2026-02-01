#!/usr/bin/env python3
"""
Config helpers for SoulEyez.

Config file lives at ~/.souleyez/config.json.

Configuration Priority (highest to lowest):
1. Environment variables (SOULEYEZ_*)
2. Config file (~/.souleyez/config.json)
3. Default values

Environment Variable Overrides:
  SOULEYEZ_DATABASE_PATH                     -> database.path
  SOULEYEZ_CRYPTO_ITERATIONS                 -> crypto.iterations
  SOULEYEZ_LOGGING_LEVEL                     -> logging.level
  SOULEYEZ_LOGGING_FILE                      -> logging.file
  SOULEYEZ_SECURITY_SESSION_TIMEOUT_MINUTES  -> security.session_timeout_minutes

Example: export SOULEYEZ_DATABASE_PATH=/tmp/test.db
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path

CONFIG_PATH = Path.home() / ".souleyez" / "config.json"

DEFAULT_CONFIG = {
    "plugins": {"enabled": [], "disabled": []},
    "settings": {
        "wordlists": None,
        "proxy": None,
        "threads": 10,
        "ollama_model": "llama3.1:8b",
    },
    "database": {
        "path": "~/.souleyez/souleyez.db",
        "backup_enabled": True,
        "backup_interval_hours": 24,
    },
    "crypto": {
        "algorithm": "AES-256-GCM",
        "iterations": 600000,
        "key_derivation": "PBKDF2",
    },
    "logging": {
        "level": "INFO",
        "format": "json",
        "file": "~/.souleyez/souleyez.log",
        "max_bytes": 10485760,
        "backup_count": 5,
    },
    "security": {
        "session_timeout_minutes": 30,
        "max_login_attempts": 5,
        "lockout_duration_minutes": 15,
        "min_password_length": 12,
    },
    "ai": {
        "provider": "ollama",  # "ollama" or "claude"
        "claude_api_key": None,  # Encrypted via CryptoManager
        "claude_model": "claude-sonnet-4-20250514",
        "ollama_mode": "local",  # "local" or "remote"
        "ollama_url": "http://localhost:11434",  # Active Ollama endpoint
        "ollama_remote_url": None,  # Saved remote Ollama URL for switching
        "ollama_model": "llama3.1:8b",
        "max_tokens": 4096,
        "temperature": 0.3,
        # AI Chain Advisor settings
        "chain_mode": "suggest",  # "off", "suggest", or "auto"
        "chain_min_confidence": 0.6,  # Minimum confidence for AI recommendations
        "chain_max_recommendations": 5,  # Max AI suggestions per analysis
    },
    # MSF RPC Configuration (Pro feature)
    "msfrpc": {
        "enabled": False,  # Must be explicitly enabled
        "host": "127.0.0.1",
        "port": 55553,
        "username": "msf",
        "password": None,  # Encrypted via CryptoManager
        "ssl": False,
        "timeout": 30,  # Connection timeout in seconds
        "poll_interval": 2,  # Seconds between session polls
        "max_poll_time": 300,  # Max time to wait for session (5 min)
        "fallback_to_console": True,  # Use msfconsole if RPC unavailable
    },
}

CONFIG_SCHEMA = {
    "crypto.iterations": {
        "type": int,
        "min": 100000,
        "max": 10000000,
        "error": "Iterations must be between 100k and 10M for security",
    },
    "database.path": {
        "type": str,
        "validator": lambda p: not p.startswith(("http://", "https://", "ftp://")),
        "error": "Database path must be local filesystem",
    },
    "logging.level": {
        "type": str,
        "allowed": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        "error": "Invalid log level",
    },
    "security.max_login_attempts": {
        "type": int,
        "min": 1,
        "max": 10,
        "error": "Max login attempts must be 1-10",
    },
    "security.session_timeout_minutes": {
        "type": int,
        "min": 5,
        "max": 1440,
        "error": "Session timeout must be 5-1440 minutes",
    },
    "settings.threads": {
        "type": int,
        "min": 1,
        "max": 100,
        "error": "Threads must be 1-100",
    },
    "ai.ollama_mode": {
        "type": str,
        "allowed": ["local", "remote"],
        "error": "Ollama mode must be 'local' or 'remote'",
    },
    "ai.chain_mode": {
        "type": str,
        "allowed": ["off", "suggest", "auto"],
        "error": "AI chain mode must be 'off', 'suggest', or 'auto'",
    },
    "ai.chain_min_confidence": {
        "type": float,
        "min": 0.0,
        "max": 1.0,
        "error": "AI chain confidence must be 0.0-1.0",
    },
    "ai.chain_max_recommendations": {
        "type": int,
        "min": 1,
        "max": 20,
        "error": "AI chain max recommendations must be 1-20",
    },
    # MSF RPC validation
    "msfrpc.port": {
        "type": int,
        "min": 1,
        "max": 65535,
        "error": "MSF RPC port must be 1-65535",
    },
    "msfrpc.timeout": {
        "type": int,
        "min": 5,
        "max": 120,
        "error": "MSF RPC timeout must be 5-120 seconds",
    },
    "msfrpc.poll_interval": {
        "type": int,
        "min": 1,
        "max": 30,
        "error": "Poll interval must be 1-30 seconds",
    },
    "msfrpc.max_poll_time": {
        "type": int,
        "min": 30,
        "max": 600,
        "error": "Max poll time must be 30-600 seconds",
    },
}


def _ensure_dir():
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)


def _get_nested(data: dict, key: str, default=None):
    """
    Get nested dict value using dotted notation.
    Example: _get_nested(cfg, 'database.path') -> cfg['database']['path']
    """
    parts = key.split(".")
    current = data
    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return default
    return current


def _set_nested(data: dict, key: str, value):
    """
    Set nested dict value using dotted notation.
    Example: _set_nested(cfg, 'database.path', '/foo')
        -> cfg['database']['path'] = '/foo'
    """
    parts = key.split(".")
    current = data
    for part in parts[:-1]:
        if part not in current:
            current[part] = {}
        current = current[part]
    current[parts[-1]] = value


def validate_config(cfg: dict) -> tuple[bool, list[str]]:
    """
    Validate config against schema.
    Returns: (is_valid, list_of_errors)
    """
    errors = []

    for key, rules in CONFIG_SCHEMA.items():
        value = _get_nested(cfg, key)
        if value is None:
            continue

        if not isinstance(value, rules["type"]):
            expected = rules["type"].__name__
            got = type(value).__name__
            errors.append(f"{key}: expected {expected}, got {got}")
            continue

        if "min" in rules and value < rules["min"]:
            errors.append(f"{key}: {rules['error']}")
        if "max" in rules and value > rules["max"]:
            errors.append(f"{key}: {rules['error']}")

        if "allowed" in rules and value not in rules["allowed"]:
            errors.append(f"{key}: must be one of {rules['allowed']}")

        if "validator" in rules and not rules["validator"](value):
            errors.append(f"{key}: {rules['error']}")

    return len(errors) == 0, errors


def _merge_with_defaults(cfg: dict) -> dict:
    """Deep merge user config with defaults."""
    import copy

    merged = copy.deepcopy(DEFAULT_CONFIG)

    def deep_merge(base, updates):
        for key, value in updates.items():
            is_dict_merge = (
                key in base and isinstance(base[key], dict) and isinstance(value, dict)
            )
            if is_dict_merge:
                deep_merge(base[key], value)
            else:
                base[key] = value

    deep_merge(merged, cfg)
    return merged


def _normalize(data: dict) -> dict:
    # Accept both new {"plugins":{...}}
    # and old flat {"enabled":[], "disabled":[]}
    if not isinstance(data, dict):
        return DEFAULT_CONFIG.copy()
    if "plugins" in data and isinstance(data["plugins"], dict):
        plugins = data["plugins"]
        plugins.setdefault("enabled", [])
        plugins.setdefault("disabled", [])
        data.setdefault(
            "settings",
            {
                "wordlists": None,
                "proxy": None,
                "threads": 10,
                "ollama_model": "llama3.1:8b",
            },
        )
        return data
    # old flat form
    enabled = data.get("enabled", []) or []
    disabled = data.get("disabled", []) or []
    return {
        "plugins": {"enabled": enabled, "disabled": disabled},
        "settings": {
            "wordlists": None,
            "proxy": None,
            "threads": 10,
            "ollama_model": "llama3.1:8b",
        },
    }


def read_config() -> dict:
    """
    Read and validate config from file.
    Auto-creates with defaults if missing.
    Validates and logs errors if corrupted.
    """
    _ensure_dir()

    if not CONFIG_PATH.exists():
        try:
            CONFIG_PATH.write_text(json.dumps(DEFAULT_CONFIG, indent=2))
            os.chmod(CONFIG_PATH, 0o600)
            return DEFAULT_CONFIG.copy()
        except Exception as e:
            logging.warning(
                f"Cannot create config file: {e}. " "Using defaults in memory."
            )
            return DEFAULT_CONFIG.copy()

    try:
        data = json.loads(CONFIG_PATH.read_text())
        normalized = _normalize(data)

        is_valid, errors = validate_config(normalized)
        if not is_valid:
            logging.error(f"Invalid config file at {CONFIG_PATH}:")
            for err in errors:
                logging.error(f"  - {err}")
            logging.warning("Using defaults for invalid values")
            return _merge_with_defaults(normalized)

        return normalized

    except json.JSONDecodeError as e:
        logging.error(f"Corrupted config file at {CONFIG_PATH}: {e}")
        logging.warning("Using default config. Fix or delete config file to reset.")
        return DEFAULT_CONFIG.copy()
    except Exception as e:
        logging.error(f"Error reading config: {e}")
        return DEFAULT_CONFIG.copy()


def write_config(cfg: dict) -> None:
    _ensure_dir()
    CONFIG_PATH.write_text(json.dumps(_normalize(cfg), indent=2))
    os.chmod(CONFIG_PATH, 0o600)


def get(key: str, default=None):
    """
    Get config value with dotted notation.
    Priority: ENV VAR > config.json > DEFAULT_CONFIG

    Example:
        get('database.path') -> checks SOULEYEZ_DATABASE_PATH env,
        then config file, then default
    """
    env_key = "SOULEYEZ_" + key.upper().replace(".", "_")
    env_val = os.getenv(env_key)
    if env_val is not None:
        return env_val

    cfg = read_config()
    val = _get_nested(cfg, key)
    if val is not None:
        return val

    return _get_nested(DEFAULT_CONFIG, key, default)


def list_plugins_config() -> tuple[list[str], list[str]]:
    cfg = read_config()
    e = [x.lower() for x in cfg["plugins"]["enabled"]]
    d = [x.lower() for x in cfg["plugins"]["disabled"]]
    return e, d


def enable_plugin(name: str) -> None:
    name = name.lower()
    cfg = read_config()
    e, d = list_plugins_config()
    if name not in e:
        e.append(name)
    if name in d:
        d.remove(name)
    cfg["plugins"]["enabled"] = e
    cfg["plugins"]["disabled"] = d
    write_config(cfg)


def disable_plugin(name: str) -> None:
    name = name.lower()
    cfg = read_config()
    e, d = list_plugins_config()
    if name in e:
        e.remove(name)
    if name not in d:
        d.append(name)
    cfg["plugins"]["enabled"] = e
    cfg["plugins"]["disabled"] = d
    write_config(cfg)


def reset_plugins() -> None:
    cfg = read_config()
    cfg["plugins"] = {"enabled": [], "disabled": []}
    write_config(cfg)
