"""
MSF RPC Connection Manager

Manages persistent connections to msfrpcd with:
- Connection pooling and health checks
- Automatic reconnection on failure
- Pro license gating
- Fallback detection for msfconsole mode

This is a Pro-only feature. Free users fall back to msfconsole subprocess execution.
"""

import logging
import os
import shutil
import subprocess
import time
from typing import Any, Dict, Optional

from souleyez import config
from souleyez.core.msf_rpc_client import MSGPACK_AVAILABLE, MSFRPCClient

logger = logging.getLogger(__name__)


def is_pro_enabled() -> bool:
    """Check if user has an active Pro license."""
    try:
        from souleyez.licensing.validator import get_active_license

        license_info = get_active_license()
        if license_info and license_info.is_valid:
            return license_info.tier.upper() == "PRO"
        return False
    except Exception:
        return False


# Session file for sharing decrypted msfrpc password with background worker
# This file is written when vault is unlocked and cleared on logout
_SESSION_FILE = os.path.join(os.path.expanduser("~"), ".souleyez", ".msfrpc_session")


def write_msfrpc_session(password: str) -> bool:
    """
    Write decrypted msfrpc password to session file.

    Called by the dashboard when vault is unlocked to allow
    the background worker (separate process) to access RPC.

    The file is created with restrictive permissions (600).
    """
    try:
        import stat

        session_dir = os.path.dirname(_SESSION_FILE)
        os.makedirs(session_dir, exist_ok=True)

        # Write with secure permissions
        with open(_SESSION_FILE, "w") as f:
            f.write(password)
        os.chmod(_SESSION_FILE, stat.S_IRUSR | stat.S_IWUSR)  # 600

        logger.debug("MSF RPC session file written")
        return True
    except Exception as e:
        logger.debug(f"Failed to write msfrpc session: {e}")
        return False


def clear_msfrpc_session() -> bool:
    """
    Clear the msfrpc session file.

    Called on logout or dashboard exit to clean up credentials.
    """
    try:
        if os.path.exists(_SESSION_FILE):
            os.remove(_SESSION_FILE)
            logger.debug("MSF RPC session file cleared")
        return True
    except Exception as e:
        logger.debug(f"Failed to clear msfrpc session: {e}")
        return False


def _read_msfrpc_session() -> Optional[str]:
    """Read password from session file if it exists."""
    try:
        if os.path.exists(_SESSION_FILE):
            with open(_SESSION_FILE, "r") as f:
                password = f.read().strip()
            if password:
                return password
    except Exception:
        pass
    return None


def get_msfrpc_password() -> Optional[str]:
    """
    Get msfrpc password for authentication.

    Priority order:
    1. Session file (written by dashboard when vault is unlocked)
    2. Decrypt from config (if vault is unlocked in current process)
    3. Return None (vault locked, no session file)
    """
    # First check session file (allows background worker to authenticate)
    session_password = _read_msfrpc_session()
    if session_password:
        return session_password

    # Fall back to decryption (works if vault is unlocked in this process)
    try:
        from souleyez.storage.crypto import get_crypto_manager

        encrypted = config.get("msfrpc.password")
        if not encrypted:
            return None
        crypto = get_crypto_manager()
        if crypto and crypto.is_encryption_enabled():
            if not crypto.is_unlocked():
                logger.debug("Crypto vault locked - cannot decrypt msfrpc password")
                return None
            return crypto.decrypt(encrypted)
        return encrypted  # Not encrypted (legacy or plain text)
    except Exception as e:
        logger.debug(f"Failed to decrypt msfrpc password: {e}")
        return None


def set_msfrpc_password(password: str) -> bool:
    """Encrypt and store msfrpc password in config."""
    try:
        from souleyez.storage.crypto import get_crypto_manager

        crypto = get_crypto_manager()
        if crypto:
            encrypted = crypto.encrypt(password)
        else:
            encrypted = password  # No crypto manager, store plain

        cfg = config.read_config()
        if "msfrpc" not in cfg:
            cfg["msfrpc"] = {}
        cfg["msfrpc"]["password"] = encrypted
        config.write_config(cfg)
        return True
    except Exception as e:
        logger.error(f"Failed to save msfrpc password: {e}")
        return False


class MSFRPCManager:
    """
    Singleton manager for MSF RPC connections.

    Provides:
    - Connection pooling with health checks
    - Pro license verification
    - Graceful fallback when RPC unavailable
    """

    _instance = None
    _client: Optional[MSFRPCClient] = None
    _last_check: float = 0
    _check_interval: int = 30  # Re-check connection every 30 seconds

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def get_instance(cls) -> "MSFRPCManager":
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset(cls):
        """Reset singleton (useful for testing)."""
        if cls._instance and cls._instance._client:
            try:
                cls._instance._client.logout()
            except Exception:
                pass
        cls._instance = None
        cls._client = None

    def is_available(self) -> bool:
        """
        Check if msfrpcd is running and accessible.

        This checks:
        1. Pro license is active
        2. msfrpc is enabled in config
        3. msgpack is installed
        4. Can connect to msfrpcd
        """
        # Check Pro license
        if not is_pro_enabled():
            logger.debug("MSF RPC unavailable: Pro license required")
            return False

        # Check if enabled in config
        if not config.get("msfrpc.enabled", False):
            logger.debug("MSF RPC unavailable: Not enabled in config")
            return False

        # Check dependencies
        if not MSGPACK_AVAILABLE:
            logger.debug("MSF RPC unavailable: msgpack not installed")
            return False

        # Try connection
        try:
            client = self._get_client()
            if client and client.token:
                return True
            return False
        except Exception as e:
            logger.debug(f"MSF RPC unavailable: {e}")
            return False

    def _get_client(self) -> Optional[MSFRPCClient]:
        """Get or create RPC client connection."""
        # Return cached client if still valid
        if self._client and self._client.token:
            if time.time() - self._last_check < self._check_interval:
                return self._client
            # Verify connection is still alive
            try:
                self._client.get_version()
                self._last_check = time.time()
                return self._client
            except Exception:
                # Connection died, reconnect
                self._client = None

        # Create new client
        try:
            client = MSFRPCClient(
                host=config.get("msfrpc.host", "127.0.0.1"),
                port=config.get("msfrpc.port", 55553),
                username=config.get("msfrpc.username", "msf"),
                password=get_msfrpc_password() or "",
                ssl=config.get("msfrpc.ssl", False),
            )

            if client.login():
                self._client = client
                self._last_check = time.time()
                logger.info(f"Connected to msfrpcd at {client.host}:{client.port}")
                return client
            else:
                logger.warning("msfrpcd login failed")
                return None

        except Exception as e:
            logger.debug(f"MSF RPC connection failed: {e}")
            return None

    def get_client(self) -> Optional[MSFRPCClient]:
        """Public method to get RPC client."""
        if not is_pro_enabled():
            return None
        if not config.get("msfrpc.enabled", False):
            return None
        return self._get_client()

    def check_health(self) -> Dict[str, Any]:
        """
        Return health status for display.

        Returns dict with:
        - status: 'connected', 'disabled', 'unavailable', 'error', 'no_license'
        - reason: Human-readable explanation
        - version: MSF version if connected
        """
        # Check Pro license first
        if not is_pro_enabled():
            return {
                "status": "no_license",
                "reason": "Pro license required for msfrpcd integration",
            }

        if not MSGPACK_AVAILABLE:
            return {
                "status": "unavailable",
                "reason": "msgpack not installed (pip install msgpack)",
            }

        if not config.get("msfrpc.enabled", False):
            return {"status": "disabled", "reason": "msfrpc.enabled is False in config"}

        # Check if password can be retrieved (vault must be unlocked)
        password = get_msfrpc_password()
        if not password and config.get("msfrpc.password"):
            return {
                "status": "vault_locked",
                "reason": "Credential vault is locked - unlock to connect",
            }

        try:
            client = self._get_client()
            if client:
                version = client.get_version()
                sessions = client.list_sessions()
                return {
                    "status": "connected",
                    "version": version.get("version", "unknown"),
                    "ruby": version.get("ruby", "unknown"),
                    "active_sessions": len(sessions),
                }
        except Exception as e:
            return {"status": "error", "reason": str(e)}

        return {"status": "unavailable", "reason": "Could not connect to msfrpcd"}

    def get_start_command(self) -> str:
        """Get the command to start msfrpcd with current config."""
        host = config.get("msfrpc.host", "127.0.0.1")
        port = config.get("msfrpc.port", 55553)
        username = config.get("msfrpc.username", "msf")
        password = get_msfrpc_password() or "YOUR_PASSWORD"
        ssl = config.get("msfrpc.ssl", False)

        cmd = f"msfrpcd -U {username} -P {password} -a {host} -p {port}"
        if not ssl:
            cmd += " -S"  # -S flag DISABLES SSL

        return cmd

    def start_daemon(self) -> Dict[str, Any]:
        """
        Attempt to start msfrpcd daemon.

        Returns:
            dict with 'success', 'message', and optionally 'command'
        """
        # Check if msfrpcd is already running
        if self.is_available():
            return {"success": True, "message": "msfrpcd is already running"}

        # Check if msfrpcd binary exists
        msfrpcd_path = shutil.which("msfrpcd")
        if not msfrpcd_path:
            # Check common MSF install locations
            common_paths = [
                "/opt/metasploit-framework/bin/msfrpcd",
                "/usr/share/metasploit-framework/msfrpcd",
                "/usr/bin/msfrpcd",
            ]
            for path in common_paths:
                if shutil.which(path):
                    msfrpcd_path = path
                    break

        if not msfrpcd_path:
            return {
                "success": False,
                "message": "msfrpcd not found. Is Metasploit Framework installed?",
                "command": self.get_start_command(),
            }

        # Check if password is configured
        password = get_msfrpc_password()
        if not password:
            return {
                "success": False,
                "message": "msfrpc password not configured. Set it in Settings first.",
                "command": self.get_start_command(),
            }

        # Try to start msfrpcd
        try:
            host = config.get("msfrpc.host", "127.0.0.1")
            port = config.get("msfrpc.port", 55553)
            username = config.get("msfrpc.username", "msf")
            ssl = config.get("msfrpc.ssl", False)

            cmd = [
                msfrpcd_path,
                "-U",
                username,
                "-P",
                password,
                "-a",
                host,
                "-p",
                str(port),
            ]
            if not ssl:
                cmd.append("-S")  # -S flag DISABLES SSL

            # Start in background
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )

            # Wait a moment for it to start
            time.sleep(2)

            # Check if it's running
            if proc.poll() is not None:
                return {
                    "success": False,
                    "message": "msfrpcd failed to start. Check if port is in use.",
                    "command": self.get_start_command(),
                }

            # Try to connect
            time.sleep(1)
            if self.is_available():
                return {"success": True, "message": f"msfrpcd started on {host}:{port}"}
            else:
                return {
                    "success": False,
                    "message": "msfrpcd started but connection failed. Check credentials.",
                    "command": self.get_start_command(),
                }

        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to start msfrpcd: {e}",
                "command": self.get_start_command(),
            }

    def list_sessions(self) -> Dict[str, Dict[str, Any]]:
        """List all active sessions from msfrpcd."""
        client = self.get_client()
        if not client:
            return {}
        try:
            return client.list_sessions()
        except Exception as e:
            logger.error(f"Failed to list sessions: {e}")
            return {}

    def get_session_info(self, session_id: int) -> Dict[str, Any]:
        """Get info for a specific session."""
        client = self.get_client()
        if not client:
            return {}
        try:
            return client.get_session_info(session_id)
        except Exception as e:
            logger.error(f"Failed to get session info: {e}")
            return {}

    def kill_session(self, session_id: int) -> bool:
        """Kill a session."""
        client = self.get_client()
        if not client:
            return False
        try:
            return client.stop_session(session_id)
        except Exception as e:
            logger.error(f"Failed to kill session: {e}")
            return False

    def run_session_command(
        self, session_id: int, command: str, timeout: int = 30
    ) -> str:
        """Run a command in a session."""
        client = self.get_client()
        if not client:
            return "Error: Not connected to msfrpcd"
        try:
            return client.run_session_command(session_id, command, timeout)
        except Exception as e:
            return f"Error: {e}"
