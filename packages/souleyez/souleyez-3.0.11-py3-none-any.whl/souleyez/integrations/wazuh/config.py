"""
SIEM Configuration Management.

Stores SIEM connection settings with encrypted credentials.
Supports multiple SIEM platforms: Wazuh, Splunk, Elastic, Sentinel.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from souleyez.storage.crypto import get_crypto_manager
from souleyez.storage.database import get_db

# Supported SIEM types (Open Source first, then Commercial)
SIEM_TYPES = ["wazuh", "elastic", "splunk", "sentinel", "google_secops"]


class WazuhConfig:
    """Manage SIEM connection configuration.

    Despite the name (kept for backwards compatibility), this class
    now supports multiple SIEM types through the siem_type field.
    """

    @staticmethod
    def get_config(
        engagement_id: int, siem_type: str = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get SIEM config for an engagement.

        Args:
            engagement_id: Engagement ID
            siem_type: Optional SIEM type to filter by. If None, returns first/active config.

        Returns:
            Config dict or None if not configured
        """
        db = get_db()
        conn = db.get_connection()
        cursor = conn.cursor()

        # Check if new columns exist (migration 025+)
        cursor.execute("PRAGMA table_info(wazuh_config)")
        columns = [col[1] for col in cursor.fetchall()]
        has_new_columns = "siem_type" in columns

        # Query with or without new columns
        if has_new_columns:
            if siem_type:
                cursor.execute(
                    """
                    SELECT api_url, api_user, api_password, indexer_url, indexer_user,
                           indexer_password, verify_ssl, enabled, siem_type, config_json
                    FROM wazuh_config
                    WHERE engagement_id = ? AND siem_type = ?
                """,
                    (engagement_id, siem_type),
                )
            else:
                # Get most recently updated config (the "current" selected SIEM)
                # Not filtering by enabled - user may have selected but not configured yet
                cursor.execute(
                    """
                    SELECT api_url, api_user, api_password, indexer_url, indexer_user,
                           indexer_password, verify_ssl, enabled, siem_type, config_json
                    FROM wazuh_config
                    WHERE engagement_id = ?
                    ORDER BY updated_at DESC
                    LIMIT 1
                """,
                    (engagement_id,),
                )
        else:
            cursor.execute(
                """
                SELECT api_url, api_user, api_password, indexer_url, indexer_user,
                       indexer_password, verify_ssl, enabled
                FROM wazuh_config
                WHERE engagement_id = ?
            """,
                (engagement_id,),
            )

        row = cursor.fetchone()
        if not row:
            return None

        # Decrypt passwords
        api_password = row[2]
        indexer_password = row[5]
        try:
            crypto = get_crypto_manager()
            if crypto:
                if api_password:
                    api_password = crypto.decrypt(api_password)
                if indexer_password:
                    indexer_password = crypto.decrypt(indexer_password)
        except Exception:
            pass  # Return encrypted if decryption fails

        # Base config (Wazuh fields for backwards compatibility)
        config = {
            "api_url": row[0],
            "api_user": row[1],
            "api_password": api_password,
            "indexer_url": row[3],
            "indexer_user": row[4] or "admin",
            "indexer_password": indexer_password,
            "verify_ssl": bool(row[6]),
            "enabled": bool(row[7]),
            "siem_type": row[8] if has_new_columns and len(row) > 8 else "wazuh",
        }

        # Merge config_json if present (for non-Wazuh SIEMs)
        if has_new_columns and len(row) > 9 and row[9]:
            try:
                extra_config = json.loads(row[9])
                # Decrypt any encrypted fields in extra config
                crypto = get_crypto_manager()
                if crypto and extra_config:
                    for key in ["password", "client_secret", "api_key", "token"]:
                        if key in extra_config and extra_config[key]:
                            try:
                                extra_config[key] = crypto.decrypt(extra_config[key])
                            except Exception:
                                pass
                config.update(extra_config)
            except json.JSONDecodeError:
                pass

        # Map Wazuh fields to generic names for SIEMFactory compatibility
        if config["siem_type"] == "wazuh":
            config["username"] = config.get("api_user")
            config["password"] = config.get("api_password")

        return config

    @staticmethod
    def _ensure_multi_siem_columns(cursor, conn):
        """Ensure siem_type and config_json columns exist."""
        cursor.execute("PRAGMA table_info(wazuh_config)")
        columns = [col[1] for col in cursor.fetchall()]

        if "siem_type" not in columns:
            cursor.execute(
                "ALTER TABLE wazuh_config ADD COLUMN siem_type TEXT DEFAULT 'wazuh'"
            )
        if "config_json" not in columns:
            cursor.execute("ALTER TABLE wazuh_config ADD COLUMN config_json TEXT")
        conn.commit()

    @staticmethod
    def save_config(
        engagement_id: int,
        api_url: str = "",
        api_user: str = "",
        api_password: str = "",
        indexer_url: Optional[str] = None,
        indexer_user: Optional[str] = None,
        indexer_password: Optional[str] = None,
        verify_ssl: bool = False,
        enabled: bool = True,
        siem_type: str = "wazuh",
        config_json: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Save SIEM config for an engagement.

        Passwords are encrypted before storage.

        Args:
            engagement_id: Engagement ID
            api_url: API URL (Wazuh Manager URL)
            api_user: API username
            api_password: API password
            indexer_url: Wazuh Indexer URL (Wazuh only)
            indexer_user: Indexer username (Wazuh only)
            indexer_password: Indexer password (Wazuh only)
            verify_ssl: Verify SSL certificates
            enabled: Whether integration is enabled
            siem_type: SIEM type ('wazuh', 'splunk', 'elastic', 'sentinel')
            config_json: Additional SIEM-specific config as dict
        """
        db = get_db()
        conn = db.get_connection()
        cursor = conn.cursor()

        # Ensure multi-SIEM columns exist (auto-migration)
        WazuhConfig._ensure_multi_siem_columns(cursor, conn)

        # Encrypt passwords
        encrypted_api_password = api_password
        encrypted_indexer_password = indexer_password
        try:
            crypto = get_crypto_manager()
            if crypto:
                if api_password:
                    encrypted_api_password = crypto.encrypt(api_password)
                if indexer_password:
                    encrypted_indexer_password = crypto.encrypt(indexer_password)
        except Exception:
            pass  # Store plaintext if encryption unavailable

        # Encrypt sensitive fields in config_json
        config_json_str = None
        if config_json:
            encrypted_config = config_json.copy()
            try:
                crypto = get_crypto_manager()
                if crypto:
                    for key in ["password", "client_secret", "api_key", "token"]:
                        if key in encrypted_config and encrypted_config[key]:
                            encrypted_config[key] = crypto.encrypt(
                                encrypted_config[key]
                            )
            except Exception:
                pass
            config_json_str = json.dumps(encrypted_config)

        # Upsert config - keyed by (engagement_id, siem_type) for multi-SIEM support
        cursor.execute(
            """
            INSERT INTO wazuh_config (
                engagement_id, api_url, api_user, api_password, indexer_url,
                indexer_user, indexer_password, verify_ssl, enabled,
                siem_type, config_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(engagement_id, siem_type) DO UPDATE SET
                api_url = excluded.api_url,
                api_user = excluded.api_user,
                api_password = excluded.api_password,
                indexer_url = excluded.indexer_url,
                indexer_user = excluded.indexer_user,
                indexer_password = excluded.indexer_password,
                verify_ssl = excluded.verify_ssl,
                enabled = excluded.enabled,
                config_json = excluded.config_json,
                updated_at = CURRENT_TIMESTAMP
        """,
            (
                engagement_id,
                api_url,
                api_user,
                encrypted_api_password,
                indexer_url,
                indexer_user or "admin",
                encrypted_indexer_password,
                verify_ssl,
                enabled,
                siem_type,
                config_json_str,
            ),
        )

        conn.commit()
        return True

    @staticmethod
    def save_siem_config(
        engagement_id: int, siem_type: str, config: Dict[str, Any], enabled: bool = True
    ) -> bool:
        """
        Save configuration for any SIEM type.

        This is the preferred method for new SIEM integrations.

        Args:
            engagement_id: Engagement ID
            siem_type: SIEM type ('wazuh', 'splunk', 'elastic', 'sentinel')
            config: SIEM-specific configuration dict
            enabled: Whether integration is enabled
        """
        if siem_type == "wazuh":
            # Use existing Wazuh fields for backwards compatibility
            return WazuhConfig.save_config(
                engagement_id=engagement_id,
                api_url=config.get("api_url", ""),
                api_user=config.get("username", config.get("api_user", "")),
                api_password=config.get("password", config.get("api_password", "")),
                indexer_url=config.get("indexer_url"),
                indexer_user=config.get("indexer_user"),
                indexer_password=config.get("indexer_password"),
                verify_ssl=config.get("verify_ssl", False),
                enabled=enabled,
                siem_type="wazuh",
            )
        else:
            # For other SIEMs, store config in config_json
            return WazuhConfig.save_config(
                engagement_id=engagement_id,
                api_url=config.get("api_url", config.get("elasticsearch_url", "")),
                verify_ssl=config.get("verify_ssl", False),
                enabled=enabled,
                siem_type=siem_type,
                config_json=config,
            )

    @staticmethod
    def delete_config(engagement_id: int, siem_type: str = None) -> bool:
        """
        Delete SIEM config for an engagement.

        Args:
            engagement_id: Engagement ID
            siem_type: Optional SIEM type. If None, deletes ALL SIEM configs for engagement.
        """
        db = get_db()
        conn = db.get_connection()
        cursor = conn.cursor()
        if siem_type:
            cursor.execute(
                "DELETE FROM wazuh_config WHERE engagement_id = ? AND siem_type = ?",
                (engagement_id, siem_type),
            )
        else:
            cursor.execute(
                "DELETE FROM wazuh_config WHERE engagement_id = ?", (engagement_id,)
            )
        conn.commit()
        return cursor.rowcount > 0

    @staticmethod
    def is_configured(engagement_id: int, siem_type: str = None) -> bool:
        """Check if SIEM is configured for an engagement."""
        config = WazuhConfig.get_config(engagement_id, siem_type)
        return config is not None and config.get("enabled", False)

    @staticmethod
    def list_configured_siems(engagement_id: int) -> List[Dict[str, Any]]:
        """
        List all configured SIEMs for an engagement.

        Returns:
            List of dicts with siem_type, enabled, and api_url for each configured SIEM
        """
        db = get_db()
        conn = db.get_connection()
        cursor = conn.cursor()

        cursor.execute("PRAGMA table_info(wazuh_config)")
        columns = [col[1] for col in cursor.fetchall()]

        if "siem_type" not in columns:
            # Old schema - only one config possible
            cursor.execute(
                """
                SELECT 'wazuh' as siem_type, enabled, api_url
                FROM wazuh_config
                WHERE engagement_id = ?
            """,
                (engagement_id,),
            )
        else:
            cursor.execute(
                """
                SELECT siem_type, enabled, api_url, updated_at
                FROM wazuh_config
                WHERE engagement_id = ?
                ORDER BY siem_type
            """,
                (engagement_id,),
            )

        rows = cursor.fetchall()
        return [
            {
                "siem_type": row[0],
                "enabled": bool(row[1]),
                "api_url": row[2],
                "updated_at": row[3] if len(row) > 3 else None,
            }
            for row in rows
        ]

    @staticmethod
    def get_all_configs(engagement_id: int) -> Dict[str, Dict[str, Any]]:
        """
        Get all SIEM configs for an engagement, keyed by siem_type.

        Returns:
            Dict mapping siem_type to config dict
        """
        configs = {}
        for siem in SIEM_TYPES:
            config = WazuhConfig.get_config(engagement_id, siem)
            if config:
                configs[siem] = config
        return configs

    @staticmethod
    def get_current_siem_type(engagement_id: int) -> str:
        """
        Get the currently selected SIEM type for an engagement.

        Returns the most recently selected SIEM type, even if not fully configured.

        Returns:
            SIEM type string ('wazuh', 'splunk', etc.) or 'wazuh' as default
        """
        config = WazuhConfig.get_config(engagement_id)
        if config:
            return config.get("siem_type", "wazuh")
        return "wazuh"

    @staticmethod
    def set_current_siem(engagement_id: int, siem_type: str) -> bool:
        """
        Set a SIEM type as current by updating its timestamp.

        This makes the specified SIEM the "active" one without changing its config.

        Args:
            engagement_id: Engagement ID
            siem_type: SIEM type to make current

        Returns:
            True if successful
        """
        db = get_db()
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE wazuh_config SET updated_at = CURRENT_TIMESTAMP WHERE engagement_id = ? AND siem_type = ?",
            (engagement_id, siem_type),
        )
        conn.commit()
        return cursor.rowcount > 0
