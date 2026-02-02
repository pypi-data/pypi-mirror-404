"""
Metasploit Sync Manager

Orchestrates bidirectional synchronization between Metasploit Framework
and SoulEyez, including:
- Importing MSF data (hosts, services, vulns, creds, sessions)
- Tracking exploit results
- Updating exploit status based on MSF success/failure
- Monitoring active sessions
"""

import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from souleyez.core.msf_database import MSFDatabase, MSFDatabaseSchemaError
from souleyez.core.msf_rpc_client import MSFRPCClient
from souleyez.storage.credentials import CredentialsManager
from souleyez.storage.exploit_attempts import record_attempt
from souleyez.storage.findings import FindingsManager
from souleyez.storage.hosts import HostManager
from souleyez.storage.msf_sessions import (
    add_msf_session,
    close_msf_session,
    get_msf_sessions,
)

logger = logging.getLogger(__name__)


def get_msf_database_config() -> Optional[Dict[str, Any]]:
    """
    Get MSF database configuration from ~/.msf4/database.yml or system-wide config.

    Checks user config first, then falls back to system-wide config (Kali Linux).

    Returns:
        Dictionary with database config or None if not found/parseable
    """
    # Check user config first, then system-wide config (Kali uses system-wide)
    user_db_path = Path.home() / ".msf4" / "database.yml"
    system_db_path = Path("/usr/share/metasploit-framework/config/database.yml")

    db_yml_path = None
    if user_db_path.exists():
        db_yml_path = user_db_path
    elif system_db_path.exists():
        db_yml_path = system_db_path

    if not db_yml_path:
        logger.debug("MSF database.yml not found in user or system config")
        return None

    try:
        import yaml

        with open(db_yml_path, "r") as f:
            config = yaml.safe_load(f)

        # MSF database.yml has environment sections (development, production, etc.)
        # Look for 'production' first, then 'development', then any section
        env_config = None
        for env in ["production", "development"]:
            if env in config:
                env_config = config[env]
                break

        if not env_config:
            # Take the first available section
            for key, val in config.items():
                if isinstance(val, dict) and "database" in val:
                    env_config = val
                    break

        if not env_config:
            logger.debug("No valid environment config found in database.yml")
            return None

        return {
            "host": env_config.get("host", "localhost"),
            "port": env_config.get("port", 5432),
            "database": env_config.get("database", "msf"),
            "username": env_config.get("username", "msf"),
            "password": env_config.get("password", ""),
            "workspace": "default",
        }
    except ImportError:
        logger.debug("PyYAML not available, cannot parse database.yml")
        return None
    except Exception as e:
        logger.debug(f"Failed to parse MSF database.yml: {e}")
        return None


def get_msf_active_sessions_count() -> Optional[int]:
    """
    Get count of active MSF sessions using multiple fallback methods.

    Tries in order:
    1. MSF RPC (if msfrpcd is running with default settings)
    2. MSF database (reading credentials from ~/.msf4/database.yml)
    3. MSF database with default credentials

    Returns:
        Number of active sessions, or None if MSF is not accessible
    """
    # Method 1: Try MSF RPC first (most reliable when msfrpcd is running)
    try:
        from souleyez.core.msf_rpc_client import MSGPACK_AVAILABLE, MSFRPCClient

        if MSGPACK_AVAILABLE:
            # Try connecting without password first (some setups don't require it)
            client = MSFRPCClient()
            if client.login():
                try:
                    sessions = client.list_sessions()
                    client.logout()
                    return len(sessions) if sessions else 0
                finally:
                    try:
                        client.logout()
                    except:
                        pass
    except Exception as e:
        logger.debug(f"MSF RPC connection failed: {e}")

    # Method 2: Try database with credentials from ~/.msf4/database.yml
    db_config = get_msf_database_config()
    if db_config:
        try:
            with MSFDatabase(**db_config) as msf_db:
                sessions = msf_db.get_sessions(active_only=True)
                return len(sessions) if sessions else 0
        except Exception as e:
            logger.debug(f"MSF database connection with config failed: {e}")

    # Method 3: Try database with default credentials (unlikely to work but worth a try)
    try:
        with MSFDatabase() as msf_db:
            sessions = msf_db.get_sessions(active_only=True)
            return len(sessions) if sessions else 0
    except Exception as e:
        logger.debug(f"MSF database connection with defaults failed: {e}")

    return None


def _map_msf_state_to_status(msf_state: Optional[str]) -> str:
    """
    Map MSF host state to SoulEyez status.

    MSF uses 'alive'/'dead' while SoulEyez uses 'up'/'down'.

    Args:
        msf_state: MSF host state value

    Returns:
        SoulEyez status value ('up' or 'down')
    """
    if not msf_state:
        return "up"  # Default for null/empty

    state_lower = msf_state.lower()

    # Map MSF state to SoulEyez status
    if state_lower == "alive":
        return "up"
    elif state_lower == "dead":
        return "down"
    elif state_lower in ("up", "down"):
        # Already in correct format
        return state_lower
    else:
        # Unknown state - log warning and default to up
        logger.warning(f"Unknown MSF host state '{msf_state}', defaulting to 'up'")
        return "up"


class MSFSyncManager:
    """Manages synchronization between MSF and SoulEyez"""

    def __init__(
        self,
        db_path: str,
        engagement_id: int,
        msf_db_config: Optional[Dict[str, Any]] = None,
        msf_rpc_config: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize MSF sync manager

        Args:
            db_path: Path to SoulEyez database
            engagement_id: Current engagement ID
            msf_db_config: MSF database connection config
            msf_rpc_config: MSF RPC connection config
        """
        self.db_path = db_path
        self.engagement_id = engagement_id
        self.msf_db_config = msf_db_config or {
            "host": "localhost",
            "port": 5432,
            "database": "msf",
            "username": "msf",
            "password": "",
            "workspace": "default",
        }
        self.msf_rpc_config = msf_rpc_config or {
            "host": "127.0.0.1",
            "port": 55553,
            "username": "msf",
            "password": "",
            "ssl": False,
        }

    def import_msf_data(
        self,
        import_hosts: bool = True,
        import_services: bool = True,
        import_vulns: bool = True,
        import_creds: bool = True,
        import_sessions: bool = True,
    ) -> Dict[str, int]:
        """
        Import data from MSF database into SoulEyez

        Args:
            import_hosts: Import hosts
            import_services: Import services
            import_vulns: Import vulnerabilities
            import_creds: Import credentials
            import_sessions: Import sessions

        Returns:
            Dictionary with counts of imported items
        """
        stats = {
            "hosts": 0,
            "services": 0,
            "vulns": 0,
            "creds": 0,
            "sessions": 0,
            "errors": 0,
        }

        try:
            with MSFDatabase(**self.msf_db_config) as msf_db:
                # Import hosts
                if import_hosts:
                    try:
                        hosts_imported = self._import_hosts(msf_db)
                        stats["hosts"] = hosts_imported
                    except (KeyError, AttributeError) as e:
                        logger.error(f"Schema error importing hosts: {e}")
                        logger.error(
                            "MSF database schema may have changed. Consider using XML export."
                        )
                        stats["errors"] += 1

                # Import services
                if import_services:
                    try:
                        services_imported = self._import_services(msf_db)
                        stats["services"] = services_imported
                    except (KeyError, AttributeError) as e:
                        logger.error(f"Schema error importing services: {e}")
                        stats["errors"] += 1

                # Import vulnerabilities
                if import_vulns:
                    try:
                        vulns_imported = self._import_vulns(msf_db)
                        stats["vulns"] = vulns_imported
                    except (KeyError, AttributeError) as e:
                        logger.error(f"Schema error importing vulnerabilities: {e}")
                        stats["errors"] += 1

                # Import credentials
                if import_creds:
                    try:
                        creds_imported = self._import_creds(msf_db)
                        stats["creds"] = creds_imported
                    except (KeyError, AttributeError) as e:
                        logger.error(f"Schema error importing credentials: {e}")
                        stats["errors"] += 1

                # Import sessions
                if import_sessions:
                    try:
                        sessions_imported = self._import_sessions(msf_db)
                        stats["sessions"] = sessions_imported
                    except (KeyError, AttributeError) as e:
                        logger.error(f"Schema error importing sessions: {e}")
                        stats["errors"] += 1

        except MSFDatabaseSchemaError as e:
            logger.error(f"MSF database schema is incompatible: {e}")
            logger.error("RECOMMENDATION: Use MSF XML export instead:")
            logger.error("  In msfconsole: db_export -f xml /tmp/msf_export.xml")
            logger.error("  Then import the XML file into SoulEyez")
            stats["errors"] += 1
        except Exception as e:
            logger.error(f"Failed to import MSF data: {e}")
            logger.error(
                "If this error persists, try using MSF XML export as an alternative"
            )
            stats["errors"] += 1

        return stats

    def _import_hosts(self, msf_db: MSFDatabase) -> int:
        """Import hosts from MSF"""
        count = 0
        msf_hosts = msf_db.get_hosts()

        host_mgr = HostManager()

        for msf_host in msf_hosts:
            try:
                # Check if host already exists
                existing = host_mgr.get_host_by_ip(
                    self.engagement_id, msf_host["address"]
                )

                if not existing:
                    # Add new host
                    # Map MSF state ('alive'/'dead') to SoulEyez status ('up'/'down')
                    msf_state = msf_host.get("state")
                    souleyez_status = _map_msf_state_to_status(msf_state)

                    host_data = {
                        "ip": msf_host["address"],
                        "hostname": msf_host.get("name") or None,
                        "mac_address": msf_host.get("mac") or None,
                        "os": msf_host.get("os_name") or None,
                        "status": souleyez_status,
                    }
                    host_mgr.add_or_update_host(self.engagement_id, host_data)
                    count += 1
                    logger.debug(
                        f"Imported host {msf_host['address']} with status '{souleyez_status}' (MSF state: '{msf_state}')"
                    )
            except Exception as e:
                logger.error(f"Failed to import host {msf_host['address']}: {e}")

        return count

    def _import_services(self, msf_db: MSFDatabase) -> int:
        """Import services from MSF"""
        count = 0
        msf_services = msf_db.get_services()

        host_mgr = HostManager()
        skipped = 0

        for msf_svc in msf_services:
            try:
                # Get or create host
                host = host_mgr.get_host_by_ip(
                    self.engagement_id, msf_svc["host_address"]
                )
                if not host:
                    # Create host if it doesn't exist
                    logger.debug(
                        f"Creating host for service: {msf_svc['host_address']}"
                    )
                    host_data = {"ip": msf_svc["host_address"]}
                    host_id = host_mgr.add_or_update_host(self.engagement_id, host_data)
                else:
                    host_id = host["id"]

                # Add or update service (add_service handles duplicates)
                service_data = {
                    "port": msf_svc["port"],
                    "protocol": msf_svc.get("proto", "tcp"),
                    "state": msf_svc.get("state", "open"),
                    "service": msf_svc.get("name") or "unknown",
                    "product": msf_svc.get("info") or None,
                }
                host_mgr.add_service(host_id, service_data)
                count += 1
            except Exception as e:
                logger.error(
                    f"Failed to import service on {msf_svc.get('host_address')}:{msf_svc.get('port')}: {e}"
                )
                skipped += 1

        if skipped > 0:
            logger.warning(f"Skipped {skipped} services due to errors")

        return count

    def _import_vulns(self, msf_db: MSFDatabase) -> int:
        """Import vulnerabilities from MSF"""
        count = 0
        msf_vulns = msf_db.get_vulns()

        host_mgr = HostManager()
        findings_mgr = FindingsManager()
        skipped = 0

        for msf_vuln in msf_vulns:
            try:
                # Get host
                host = host_mgr.get_host_by_ip(
                    self.engagement_id, msf_vuln["host_address"]
                )
                if not host:
                    logger.debug(
                        f"Skipping vuln - host not found: {msf_vuln['host_address']}"
                    )
                    skipped += 1
                    continue

                # Get service if available
                port = msf_vuln.get("service_port")
                if port:
                    services = host_mgr.get_host_services(host["id"])
                    matching_services = [
                        s
                        for s in services
                        if s["port"] == port
                        and s["protocol"] == msf_vuln.get("service_proto", "tcp")
                    ]
                else:
                    matching_services = []

                # Determine severity from vuln name/info
                severity = self._determine_severity(msf_vuln.get("name", ""))

                # Add finding
                findings_mgr.add_finding(
                    engagement_id=self.engagement_id,
                    title=msf_vuln.get("name", "Unknown Vulnerability"),
                    finding_type="vulnerability",
                    severity=severity,
                    description=msf_vuln.get("info") or "",
                    host_id=host["id"],
                    tool="metasploit",
                    refs=msf_vuln.get("refs") or "",
                    port=port,
                    evidence=f"MSF Vuln ID: {msf_vuln['id']}",
                )
                count += 1
            except Exception as e:
                logger.error(
                    f"Failed to import vulnerability '{msf_vuln.get('name')}': {e}"
                )
                skipped += 1

        if skipped > 0:
            logger.warning(
                f"Skipped {skipped} vulnerabilities (host not found or errors)"
            )

        return count

    def _import_creds(self, msf_db: MSFDatabase) -> int:
        """Import credentials from MSF"""
        count = 0
        msf_creds = msf_db.get_creds()

        host_mgr = HostManager()
        findings_mgr = FindingsManager()
        skipped = 0

        for msf_cred in msf_creds:
            try:
                # Skip if no host address
                if not msf_cred.get("host_address"):
                    logger.debug(
                        f"Skipping credential - no host address (service-less credential)"
                    )
                    skipped += 1
                    continue

                # Get host
                host = host_mgr.get_host_by_ip(
                    self.engagement_id, msf_cred["host_address"]
                )
                if not host:
                    logger.debug(
                        f"Skipping credential - host not found: {msf_cred['host_address']}"
                    )
                    skipped += 1
                    continue

                # Create credential finding
                username = msf_cred.get("username", "N/A")
                private_data = msf_cred.get("private_data", "N/A")
                private_type = msf_cred.get("private_type", "password")

                findings_mgr.add_finding(
                    engagement_id=self.engagement_id,
                    title=f"Credential Found: {username}",
                    finding_type="credential",
                    severity="high",
                    description=f"Username: {username}\nType: {private_type}\nStatus: {msf_cred.get('status', 'unknown')}",
                    host_id=host["id"],
                    tool="metasploit",
                    port=msf_cred.get("service_port"),
                    evidence=(
                        f"Private: {private_data[:20]}..."
                        if len(private_data) > 20
                        else private_data
                    ),
                )
                count += 1
            except Exception as e:
                logger.error(
                    f"Failed to import credential for {msf_cred.get('username')}: {e}"
                )
                skipped += 1

        if skipped > 0:
            logger.warning(
                f"Skipped {skipped} credentials (no host address or host not found)"
            )

        return count

    def _import_sessions(self, msf_db: MSFDatabase) -> int:
        """Import sessions from MSF"""
        count = 0
        msf_sessions = msf_db.get_sessions(active_only=False)

        host_mgr = HostManager()
        skipped = 0

        # Get database connection for msf_sessions functions
        from souleyez.storage.database import get_db

        db = get_db()
        conn = db.get_connection()

        for msf_session in msf_sessions:
            try:
                # Get host
                host = host_mgr.get_host_by_ip(
                    self.engagement_id, msf_session["host_address"]
                )
                if not host:
                    session_num = msf_session.get("local_id") or msf_session["id"]
                    logger.debug(
                        f"Skipping session {session_num} - host not found: {msf_session['host_address']}"
                    )
                    skipped += 1
                    continue

                # Add session to msf_sessions table
                is_active = msf_session.get("closed_at") is None

                session_id = add_msf_session(
                    conn,
                    engagement_id=self.engagement_id,
                    host_id=host["id"],
                    msf_session_id=msf_session.get("local_id") or msf_session["id"],
                    session_type=msf_session.get("stype"),
                    via_exploit=msf_session.get("via_exploit"),
                    via_payload=msf_session.get("via_payload"),
                    platform=msf_session.get("platform"),
                    arch=None,  # Not available in DB schema
                    username=None,  # Not available in DB schema
                    port=msf_session.get("port"),
                    tunnel_peer=None,  # Not available in DB schema
                    opened_at=msf_session.get("opened_at"),
                    notes=msf_session.get("desc"),
                )

                # Mark as closed if applicable
                if not is_active:
                    close_msf_session(
                        conn,
                        self.engagement_id,
                        msf_session.get("local_id") or msf_session["id"],
                        msf_session.get("close_reason"),
                    )

                count += 1

                # If session was created via exploit, mark that exploit as successful
                via_exploit = msf_session.get("via_exploit")
                if via_exploit and via_exploit not in ["unknown", ""]:
                    session_num = msf_session.get("local_id") or msf_session["id"]
                    self._mark_exploit_success(
                        host["id"], via_exploit, f"Session {session_num} created"
                    )

            except Exception as e:
                session_num = msf_session.get("local_id") or msf_session.get(
                    "id", "unknown"
                )
                logger.error(f"Failed to import session {session_num}: {e}")
                skipped += 1

        conn.commit()
        conn.close()

        if skipped > 0:
            logger.warning(f"Skipped {skipped} sessions (host not found or errors)")

        return count

    def sync_exploit_results(self) -> Dict[str, int]:
        """
        Sync exploit results from MSF to SoulEyez

        Updates exploit attempt status based on:
        - Sessions created (success)
        - Vulnerabilities exploited (success)
        - Failed attempts (no session/vuln)

        Returns:
            Dictionary with counts of updated exploits
        """
        stats = {"success": 0, "failed": 0, "errors": 0}

        try:
            with MSFDatabase(**self.msf_db_config) as msf_db:
                # Get successful exploits (those that created sessions or have exploited_at timestamp)
                exploit_attempts = msf_db.get_exploit_attempts()

                host_mgr = HostManager()

                for attempt in exploit_attempts:
                    try:
                        # Get host
                        host = host_mgr.get_host_by_ip(
                            self.engagement_id, attempt["host_address"]
                        )
                        if not host:
                            continue

                        # Get service if available
                        service_id = None
                        if attempt.get("service_port"):
                            services = host_mgr.get_host_services(host["id"])
                            matching_services = [
                                s
                                for s in services
                                if s["port"] == attempt["service_port"]
                                and s["protocol"] == attempt.get("service_proto", "tcp")
                            ]
                            if matching_services:
                                service_id = matching_services[0]["id"]

                        # Record exploit attempt with success status
                        exploit_name = attempt.get("vuln_name", "unknown")
                        record_attempt(
                            engagement_id=self.engagement_id,
                            host_id=host["id"],
                            exploit_identifier=f"msf:{exploit_name}",
                            exploit_title=exploit_name,
                            status="success",
                            service_id=service_id,
                            notes=f"Exploited at: {attempt['exploited_at']}",
                        )
                        stats["success"] += 1

                    except Exception as e:
                        logger.error(f"Failed to sync exploit result: {e}")
                        stats["errors"] += 1

        except Exception as e:
            logger.error(f"Failed to sync exploit results: {e}")
            stats["errors"] += 1

        return stats

    def get_active_sessions(self) -> List[Dict[str, Any]]:
        """
        Get active MSF sessions

        Returns:
            List of active session dictionaries
        """
        sessions = []

        try:
            # Try RPC first (more detailed info)
            try:
                with MSFRPCClient(**self.msf_rpc_config) as rpc:
                    rpc_sessions = rpc.list_sessions()
                    for session_id, session_info in rpc_sessions.items():
                        sessions.append(
                            {
                                "id": session_id,
                                "type": session_info.get("type", "unknown"),
                                "tunnel": session_info.get("tunnel_peer", "unknown"),
                                "via_exploit": session_info.get(
                                    "via_exploit", "unknown"
                                ),
                                "via_payload": session_info.get(
                                    "via_payload", "unknown"
                                ),
                                "info": session_info.get("info", ""),
                                "username": session_info.get("username", ""),
                                "platform": session_info.get("platform", ""),
                                "arch": session_info.get("arch", ""),
                                "source": "rpc",
                            }
                        )
                    return sessions
            except Exception as rpc_error:
                logger.debug(
                    f"RPC not available, falling back to database: {rpc_error}"
                )

            # Fallback to database
            with MSFDatabase(**self.msf_db_config) as msf_db:
                msf_sessions = msf_db.get_sessions(active_only=True)
                for session in msf_sessions:
                    sessions.append(
                        {
                            "id": session["id"],
                            "type": session.get("stype", "unknown"),
                            "host": session.get("host_address", "unknown"),
                            "port": session.get("port", 0),
                            "via_exploit": session.get("via_exploit", "unknown"),
                            "via_payload": session.get("via_payload", "unknown"),
                            "platform": session.get("platform", ""),
                            "opened_at": session.get("opened_at"),
                            "last_seen": session.get("last_seen"),
                            "source": "database",
                        }
                    )

        except Exception as e:
            logger.error(f"Failed to get active sessions: {e}")

        return sessions

    def _mark_exploit_success(self, host_id: int, exploit_name: str, notes: str = ""):
        """Mark an exploit as successful"""
        try:
            # Record successful exploit attempt
            record_attempt(
                engagement_id=self.engagement_id,
                host_id=host_id,
                exploit_identifier=f"msf:{exploit_name}",
                exploit_title=exploit_name,
                status="success",
                service_id=None,
                notes=notes,
            )
        except Exception as e:
            logger.debug(f"Failed to mark exploit success: {e}")

    def _determine_severity(self, vuln_name: str) -> str:
        """Determine severity from vulnerability name"""
        vuln_lower = vuln_name.lower()

        if any(
            x in vuln_lower
            for x in ["rce", "remote code", "command execution", "backdoor"]
        ):
            return "critical"
        elif any(
            x in vuln_lower
            for x in ["exploit", "overflow", "injection", "authentication bypass"]
        ):
            return "high"
        elif any(
            x in vuln_lower for x in ["disclosure", "exposure", "misconfiguration"]
        ):
            return "medium"
        else:
            return "low"

    def get_msf_stats(self) -> Dict[str, Any]:
        """
        Get statistics from MSF database

        Returns:
            Dictionary with MSF database statistics
        """
        try:
            with MSFDatabase(**self.msf_db_config) as msf_db:
                return msf_db.get_database_stats()
        except Exception as e:
            logger.error(f"Failed to get MSF stats: {e}")
            return {}
