#!/usr/bin/env python3
"""
PluginBase v2.2 — standardized plugin API for souleyez background jobs

Changes in v2.2:
- Added build_command() method for proper PID tracking
- Modified run() to support build_command() pattern
- Backward compatibility maintained
"""

from typing import Any, Dict, List, Optional


class PluginBase:
    """Minimal plugin base class for souleyez."""

    name: str = "unnamed"
    tool: str = "unnamed"
    category: str = "misc"
    HELP: Optional[Dict[str, Any]] = None

    def __init__(self):
        self.name = getattr(self, "name", self.__class__.__name__)
        self.tool = getattr(self, "tool", self.name).lower()
        self.category = getattr(self, "category", "misc")

    def check_tool_available(self) -> tuple:
        """
        Check if the tool is available on the system.

        Returns:
            Tuple of (is_available: bool, error_message: str or None)
        """
        import shutil
        import subprocess

        # Check if tool exists in PATH
        tool_path = shutil.which(self.tool)
        if not tool_path:
            return (
                False,
                f"{self.tool} not found in PATH. Install with: sudo apt install {self.tool}",
            )

        # Try running with --version or --help to check if it works
        try:
            result = subprocess.run(
                [self.tool, "--version"], capture_output=True, timeout=10, text=True
            )
            # Some tools don't support --version, try --help
            if result.returncode != 0:
                result = subprocess.run(
                    [self.tool, "--help"], capture_output=True, timeout=10, text=True
                )
            return True, None
        except subprocess.TimeoutExpired:
            return True, None  # Tool exists but version check timed out
        except FileNotFoundError:
            return False, f"{self.tool} not found"
        except Exception as e:
            # Tool might have Python import issues (like impacket pickle error)
            error_str = str(e)
            if "pickle" in error_str.lower() or "import" in error_str.lower():
                return False, f"{self.tool} has Python dependency issues: {error_str}"
            return True, None  # Assume available if error is unexpected

    def build_command(
        self, target: str, args: List[str] = None, label: str = "", log_path: str = None
    ) -> Optional[Dict[str, Any]]:
        """
        Build command specification for background execution.

        This method should be implemented by plugins instead of run() to enable
        proper PID tracking, status updates, and kill handling.

        Args:
            target: Target host/URL/file to scan
            args: Additional command-line arguments
            label: Optional job label
            log_path: Path where logs should be written

        Returns:
            Dictionary with command specification:
            {
                'cmd': List[str],           # Command array (required)
                'timeout': int,             # Timeout in seconds (optional, default: 3600)
                'env': Dict[str, str],      # Environment variables (optional)
                'cwd': str,                 # Working directory (optional)
                'needs_shell': bool         # Use shell=True (optional, default: False)
            }

            Return None to indicate command cannot be built (validation failure, etc.)

        Example:
            return {
                'cmd': ['nmap', '-sV', '-p', '1-1000', target],
                'timeout': 1800
            }
        """
        return None

    def run(
        self, target: str, args: List[str] = None, label: str = "", log_path: str = None
    ) -> int:
        """
        Execute the plugin action synchronously.

        DEPRECATED: New plugins should implement build_command() instead.
        This method is maintained for backward compatibility.

        If build_command() is implemented, run() will use it automatically.
        """
        # Try to use build_command() if available
        cmd_spec = self.build_command(target, args, label, log_path)
        if cmd_spec is not None:
            # build_command() is implemented, execute via subprocess
            import os
            import subprocess

            cmd = cmd_spec.get("cmd")
            if not cmd:
                return 1

            timeout = cmd_spec.get("timeout", 3600)
            env = cmd_spec.get("env")
            cwd = cmd_spec.get("cwd")
            needs_shell = cmd_spec.get("needs_shell", False)

            # Prepare environment
            proc_env = os.environ.copy()
            if env:
                proc_env.update(env)

            # Execute command
            try:
                if log_path:
                    with open(log_path, "a", encoding="utf-8", errors="replace") as fh:
                        result = subprocess.run(
                            cmd,
                            stdout=fh,
                            stderr=subprocess.STDOUT,
                            timeout=timeout,
                            env=proc_env if env else None,
                            cwd=cwd,
                            shell=needs_shell,
                        )
                        return result.returncode
                else:
                    result = subprocess.run(
                        cmd,
                        timeout=timeout,
                        env=proc_env if env else None,
                        cwd=cwd,
                        shell=needs_shell,
                        capture_output=True,
                    )
                    return result.returncode
            except subprocess.TimeoutExpired:
                return 124
            except Exception:
                return 1

        # build_command() not implemented, require subclass implementation
        raise NotImplementedError(f"{self.__class__.__name__}.run() not implemented")

    def enqueue(self, target: str, args: List[str] = None, label: str = "") -> int:
        """Enqueue the plugin action for background processing."""
        try:
            from ..engine.background import enqueue_job

            job_id = enqueue_job(
                tool=self.tool, target=target, args=args or [], label=label or ""
            )
            return job_id
        except ImportError:
            raise NotImplementedError("enqueue() requires background job system")


Plugin = PluginBase
