"""
Metasploit RPC Client

This module provides a client for Metasploit's RPC API (msfrpcd),
allowing real-time monitoring and control of exploit execution,
session management, and result tracking.
"""

import logging
import time
import warnings
from typing import Any, Dict, List, Optional, Tuple

import requests

# Suppress SSL warnings for self-signed certs (msfrpcd uses self-signed)
from urllib3.exceptions import InsecureRequestWarning

warnings.filterwarnings("ignore", category=InsecureRequestWarning)

try:
    import msgpack

    MSGPACK_AVAILABLE = True
except ImportError:
    MSGPACK_AVAILABLE = False

logger = logging.getLogger(__name__)


class MSFRPCClient:
    """Client for Metasploit RPC API"""

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 55553,
        username: str = "msf",
        password: str = "",
        ssl: bool = False,
    ):
        """
        Initialize MSF RPC client

        Args:
            host: MSF RPC host
            port: MSF RPC port (default: 55553)
            username: RPC username
            password: RPC password
            ssl: Use HTTPS (default: False)
        """
        if not MSGPACK_AVAILABLE:
            raise ImportError(
                "msgpack is required for MSF RPC. " "Install with: pip install msgpack"
            )

        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.ssl = ssl
        self.token = None
        self.headers = {"Content-Type": "binary/message-pack"}

    @property
    def url(self) -> str:
        """Get RPC endpoint URL"""
        protocol = "https" if self.ssl else "http"
        return f"{protocol}://{self.host}:{self.port}/api"

    def _normalize_keys(self, obj: Any) -> Any:
        """
        Recursively convert bytes keys/values to strings.
        msgpack can return bytes or strings depending on the data.
        """
        if isinstance(obj, dict):
            return {
                (k.decode() if isinstance(k, bytes) else k): self._normalize_keys(v)
                for k, v in obj.items()
            }
        elif isinstance(obj, list):
            return [self._normalize_keys(item) for item in obj]
        elif isinstance(obj, bytes):
            return obj.decode()
        return obj

    def _call(self, method: str, *params) -> Any:
        """
        Make RPC call to MSF

        Args:
            method: RPC method name
            *params: Method parameters

        Returns:
            Response data

        Raises:
            Exception: If RPC call fails
        """
        # Build request payload
        if self.token and method != "auth.login":
            request_data = msgpack.packb([method, self.token] + list(params))
        else:
            request_data = msgpack.packb([method] + list(params))

        # Make request
        try:
            response = requests.post(
                self.url,
                data=request_data,
                headers=self.headers,
                verify=False,  # nosec B501 - Metasploit RPC uses self-signed certs
                timeout=(
                    5,
                    30,
                ),  # (connect_timeout, read_timeout) - fast fail on SSL mismatch
            )
            response.raise_for_status()

            # Unpack response
            result = msgpack.unpackb(response.content, raw=False)

            # Normalize bytes keys to strings (msgpack can return either)
            result = self._normalize_keys(result)

            # Check for errors
            if isinstance(result, dict):
                if "error" in result:
                    raise Exception(
                        f"RPC error: {result.get('error_message', 'Unknown error')}"
                    )
                if "error_message" in result:
                    raise Exception(f"RPC error: {result['error_message']}")

            return result

        except requests.exceptions.RequestException as e:
            raise Exception(f"RPC request failed: {e}")

    def login(self) -> bool:
        """
        Authenticate with MSF RPC

        Returns:
            True if authentication successful, False otherwise
        """
        try:
            result = self._call("auth.login", self.username, self.password)
            if isinstance(result, dict) and "token" in result:
                self.token = result["token"]
                logger.info(f"Authenticated with MSF RPC at {self.host}:{self.port}")
                return True
            logger.error("Authentication failed: No token received")
            return False
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return False

    def logout(self) -> bool:
        """
        Logout from MSF RPC

        Returns:
            True if logout successful, False otherwise
        """
        try:
            result = self._call("auth.logout")
            self.token = None
            logger.info("Logged out from MSF RPC")
            return True
        except Exception as e:
            logger.error(f"Logout failed: {e}")
            return False

    def get_version(self) -> Dict[str, str]:
        """
        Get MSF version information

        Returns:
            Dictionary with version, ruby, and api keys
        """
        try:
            result = self._call("core.version")
            return result
        except Exception as e:
            logger.error(f"Failed to get version: {e}")
            return {}

    def list_modules(self, module_type: str = "exploit") -> List[str]:
        """
        List all modules of a given type

        Args:
            module_type: Module type (exploit, auxiliary, post, payload, etc.)

        Returns:
            List of module names
        """
        try:
            result = self._call(
                "module.exploits"
                if module_type == "exploit"
                else f"module.{module_type}s"
            )
            if isinstance(result, dict) and "modules" in result:
                return result["modules"]
            return []
        except Exception as e:
            logger.error(f"Failed to list modules: {e}")
            return []

    def get_module_info(self, module_type: str, module_name: str) -> Dict[str, Any]:
        """
        Get information about a specific module

        Args:
            module_type: Module type (exploit, auxiliary, post, payload)
            module_name: Module name

        Returns:
            Dictionary with module information
        """
        try:
            result = self._call("module.info", module_type, module_name)
            return result
        except Exception as e:
            logger.error(f"Failed to get module info: {e}")
            return {}

    def get_module_options(self, module_type: str, module_name: str) -> Dict[str, Any]:
        """
        Get options for a specific module

        Args:
            module_type: Module type
            module_name: Module name

        Returns:
            Dictionary with module options
        """
        try:
            result = self._call("module.options", module_type, module_name)
            return result
        except Exception as e:
            logger.error(f"Failed to get module options: {e}")
            return {}

    def execute_module(
        self, module_type: str, module_name: str, options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a module

        Args:
            module_type: Module type (exploit, auxiliary, etc.)
            module_name: Module name
            options: Module options as dictionary

        Returns:
            Execution result dictionary
        """
        try:
            result = self._call("module.execute", module_type, module_name, options)
            return result
        except Exception as e:
            logger.error(f"Failed to execute module: {e}")
            return {"error": str(e)}

    def list_sessions(self) -> Dict[str, Dict[str, Any]]:
        """
        List all active sessions

        Returns:
            Dictionary mapping session IDs to session info
        """
        try:
            result = self._call("session.list")
            if isinstance(result, dict):
                return result
            return {}
        except Exception as e:
            logger.error(f"Failed to list sessions: {e}")
            return {}

    def get_session_info(self, session_id: int) -> Dict[str, Any]:
        """
        Get information about a specific session

        Args:
            session_id: Session ID

        Returns:
            Session information dictionary
        """
        sessions = self.list_sessions()
        return sessions.get(str(session_id), {})

    def stop_session(self, session_id: int) -> bool:
        """
        Stop/kill a session

        Args:
            session_id: Session ID to stop

        Returns:
            True if successful, False otherwise
        """
        try:
            result = self._call("session.stop", str(session_id))
            return result.get("result") == "success"
        except Exception as e:
            logger.error(f"Failed to stop session: {e}")
            return False

    def run_session_command(
        self, session_id: int, command: str, timeout: int = 30
    ) -> str:
        """
        Run a command in a session

        Args:
            session_id: Session ID
            command: Command to run
            timeout: Command timeout in seconds

        Returns:
            Command output
        """
        try:
            # Write command
            self._call("session.shell_write", str(session_id), command + "\n")

            # Wait a bit for command to execute
            time.sleep(1)

            # Read output
            result = self._call("session.shell_read", str(session_id))
            if isinstance(result, dict) and "data" in result:
                return result["data"]
            return ""
        except Exception as e:
            logger.error(f"Failed to run session command: {e}")
            return ""

    def get_jobs(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all running jobs

        Returns:
            Dictionary mapping job IDs to job info
        """
        try:
            result = self._call("job.list")
            if isinstance(result, dict):
                return result
            return {}
        except Exception as e:
            logger.error(f"Failed to get jobs: {e}")
            return {}

    def get_job_info(self, job_id: int) -> Dict[str, Any]:
        """
        Get information about a specific job

        Args:
            job_id: Job ID

        Returns:
            Job information dictionary
        """
        try:
            result = self._call("job.info", str(job_id))
            return result
        except Exception as e:
            logger.error(f"Failed to get job info: {e}")
            return {}

    def stop_job(self, job_id: int) -> bool:
        """
        Stop a running job

        Args:
            job_id: Job ID to stop

        Returns:
            True if successful, False otherwise
        """
        try:
            result = self._call("job.stop", str(job_id))
            return result.get("result") == "success"
        except Exception as e:
            logger.error(f"Failed to stop job: {e}")
            return False

    def get_console_list(self) -> List[Dict[str, Any]]:
        """
        Get list of active consoles

        Returns:
            List of console dictionaries
        """
        try:
            result = self._call("console.list")
            if isinstance(result, dict) and "consoles" in result:
                return result["consoles"]
            return []
        except Exception as e:
            logger.error(f"Failed to get console list: {e}")
            return []

    def create_console(self) -> Optional[str]:
        """
        Create a new console

        Returns:
            Console ID if successful, None otherwise
        """
        try:
            result = self._call("console.create")
            if isinstance(result, dict) and "id" in result:
                return result["id"]
            return None
        except Exception as e:
            logger.error(f"Failed to create console: {e}")
            return None

    def destroy_console(self, console_id: str) -> bool:
        """
        Destroy a console

        Args:
            console_id: Console ID to destroy

        Returns:
            True if successful, False otherwise
        """
        try:
            result = self._call("console.destroy", console_id)
            return result.get("result") == "success"
        except Exception as e:
            logger.error(f"Failed to destroy console: {e}")
            return False

    def write_console(self, console_id: str, command: str) -> int:
        """
        Write command to console

        Args:
            console_id: Console ID
            command: Command to write

        Returns:
            Number of bytes written
        """
        try:
            result = self._call("console.write", console_id, command + "\n")
            if isinstance(result, dict) and "wrote" in result:
                return result["wrote"]
            return 0
        except Exception as e:
            logger.error(f"Failed to write to console: {e}")
            return 0

    def read_console(self, console_id: str) -> Tuple[str, bool]:
        """
        Read output from console

        Args:
            console_id: Console ID

        Returns:
            Tuple of (output, busy) where busy indicates if console is processing
        """
        try:
            result = self._call("console.read", console_id)
            if isinstance(result, dict):
                output = result.get("data", "")
                busy = result.get("busy", False)
                return (output, busy)
            return ("", False)
        except Exception as e:
            logger.error(f"Failed to read from console: {e}")
            return ("", False)

    def run_console_command(
        self, console_id: str, command: str, timeout: int = 30
    ) -> str:
        """
        Run a command in console and wait for output

        Args:
            console_id: Console ID
            command: Command to run
            timeout: Maximum time to wait for output

        Returns:
            Command output
        """
        # Write command
        self.write_console(console_id, command)

        # Wait for output
        output = ""
        start_time = time.time()
        while time.time() - start_time < timeout:
            time.sleep(0.5)
            new_output, busy = self.read_console(console_id)
            output += new_output

            if not busy and new_output:
                # Wait a bit more to ensure all output is received
                time.sleep(0.5)
                final_output, _ = self.read_console(console_id)
                output += final_output
                break

        return output

    def __enter__(self):
        """Context manager entry"""
        self.login()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.logout()


def test_msf_rpc_connection(
    host: str = "127.0.0.1",
    port: int = 55553,
    username: str = "msf",
    password: str = "",
) -> bool:
    """
    Test MSF RPC connection

    Returns:
        True if connection successful, False otherwise
    """
    if not MSGPACK_AVAILABLE:
        logger.error("msgpack not available")
        return False

    try:
        with MSFRPCClient(host, port, username, password) as client:
            version = client.get_version()
            logger.info(f"Connected to MSF RPC: {version}")
            return True
    except Exception as e:
        logger.error(f"RPC connection test failed: {e}")
        return False
