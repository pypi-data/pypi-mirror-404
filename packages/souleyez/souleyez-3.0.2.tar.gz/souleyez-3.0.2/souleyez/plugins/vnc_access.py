#!/usr/bin/env python3
"""
souleyez.plugins.vnc_access

VNC access plugin for connecting to VNC servers.
Used after successful credential discovery.
"""

import shutil
import subprocess
import time
from typing import List

from souleyez.security.validation import ValidationError, validate_target

from .plugin_base import PluginBase

HELP = {
    "name": "VNC Access — Connect to Screen Sharing",
    "description": (
        "Connect to a VNC server with known credentials.\n\n"
        "Use this after finding VNC credentials to establish a session.\n"
        "This launches a VNC viewer for interactive screen access.\n\n"
        "Quick tips:\n"
        "- Requires a VNC viewer (vncviewer, remmina, etc.)\n"
        "- For headless operation, use VNC screenshots instead\n"
        "- VNC gives full mouse/keyboard control\n"
        "- Some viewers support file transfer\n"
    ),
    "usage": 'souleyez jobs enqueue vnc_access <target> --args "--password <pass>"',
    "examples": [
        'souleyez jobs enqueue vnc_access 192.168.1.100 --args "--password secret"',
        'souleyez jobs enqueue vnc_access 192.168.1.100:5901 --args "--password secret"',
    ],
    "flags": [
        ["--password PASS", "VNC password"],
        ["--port PORT", "VNC port (default: 5900)"],
        ["--screenshot", "Take screenshot instead of interactive session"],
    ],
    "presets": [
        {"name": "Connect", "args": [], "desc": "Interactive VNC session"},
        {
            "name": "Screenshot",
            "args": ["--screenshot"],
            "desc": "Capture screenshot only",
        },
    ],
    "help_sections": [
        {
            "title": "What is VNC Access?",
            "color": "cyan",
            "content": [
                (
                    "Overview",
                    [
                        "Connects to VNC servers after obtaining credentials",
                        "Provides full graphical remote desktop access",
                        "Can take screenshots for headless/automated operation",
                    ],
                ),
                (
                    "When to Use",
                    [
                        "After VNC brute force discovers valid password",
                        "When you need GUI access (no command line available)",
                        "For accessing macOS Screen Sharing (port 5900)",
                        "To capture screenshots for documentation/evidence",
                    ],
                ),
            ],
        },
        {
            "title": "Usage & Examples",
            "color": "green",
            "content": [
                (
                    "Interactive Session",
                    [
                        'souleyez jobs enqueue vnc_access 192.168.1.100 --args "--password secret"',
                        "  → Opens VNC viewer for interactive control",
                    ],
                ),
                (
                    "Custom Port",
                    [
                        'souleyez jobs enqueue vnc_access 192.168.1.100:5901 --args "--password secret"',
                        "  → Connects to VNC on non-standard port",
                    ],
                ),
                (
                    "Screenshot Mode",
                    [
                        'souleyez jobs enqueue vnc_access 192.168.1.100 --args "--password secret --screenshot"',
                        "  → Captures screenshot without interactive session",
                    ],
                ),
            ],
        },
        {
            "title": "VNC Ports & Tips",
            "color": "yellow",
            "content": [
                (
                    "Common VNC Ports",
                    [
                        "5900 - Standard VNC / macOS Screen Sharing",
                        "5901 - VNC display :1",
                        "5902 - VNC display :2",
                        "5800 - Java VNC (web-based)",
                    ],
                ),
                (
                    "Access Capabilities",
                    [
                        "Full mouse and keyboard control",
                        "View running applications and files",
                        "Some viewers support file transfer",
                        "Can be used for credential harvesting (watch user type)",
                    ],
                ),
            ],
        },
    ],
}


class VNCAccessPlugin(PluginBase):
    name = "VNC Access"
    tool = "vncviewer"
    category = "discovery_collection"
    HELP = HELP

    def check_tool_available(self) -> tuple:
        """Check if a VNC viewer is available."""
        viewers = ["vncviewer", "vinagre", "remmina", "xtightvncviewer"]
        for viewer in viewers:
            if shutil.which(viewer):
                return True, None
        return (
            False,
            "VNC viewer not found. Install with: sudo apt install tigervnc-viewer",
        )

    def _find_viewer(self) -> str:
        """Find an available VNC viewer."""
        viewers = ["vncviewer", "xtightvncviewer", "vinagre", "remmina"]
        for viewer in viewers:
            if shutil.which(viewer):
                return viewer
        return "vncviewer"

    def build_command(
        self, target: str, args: List[str] = None, label: str = "", log_path: str = None
    ):
        """Build VNC viewer command."""
        args = args or []

        try:
            # Allow target:port format
            if ":" in target and target.count(":") == 1:
                host, port = target.rsplit(":", 1)
                try:
                    int(port)
                    target = host
                    args = ["--port", port] + args
                except ValueError:
                    pass
            target = validate_target(target)
        except ValidationError as e:
            if log_path:
                with open(log_path, "w") as f:
                    f.write(f"ERROR: Invalid target: {e}\n")
            return None

        password = None
        port = "5900"
        screenshot = False

        i = 0
        while i < len(args):
            if args[i] == "--password" and i + 1 < len(args):
                password = args[i + 1]
                i += 2
            elif args[i] == "--port" and i + 1 < len(args):
                port = args[i + 1]
                i += 2
            elif args[i] == "--screenshot":
                screenshot = True
                i += 1
            else:
                i += 1

        viewer = self._find_viewer()

        if screenshot:
            # Use vncsnapshot if available, otherwise vncviewer in headless mode
            if shutil.which("vncsnapshot"):
                cmd = ["vncsnapshot", f"{target}:{port}", "/tmp/vnc_screenshot.jpg"]
                if password:
                    cmd.extend(["-passwd", password])
            else:
                if log_path:
                    with open(log_path, "w") as f:
                        f.write("# Screenshot mode requires vncsnapshot\n")
                        f.write("Install with: sudo apt install vncsnapshot\n")
                return None
        else:
            # Interactive session
            cmd = [viewer, f"{target}::{port}"]
            # vncviewer password handling varies by implementation
            # Most accept password via stdin or password file

        return {
            "cmd": cmd,
            "timeout": 30,  # Just connection timeout, session runs until user closes
            "password": password,
        }

    def run(
        self, target: str, args: List[str] = None, label: str = "", log_path: str = None
    ) -> int:
        """Execute VNC connection."""
        cmd_spec = self.build_command(target, args, label, log_path)
        if cmd_spec is None:
            return 1

        cmd = cmd_spec["cmd"]
        password = cmd_spec.get("password")

        if log_path:
            with open(log_path, "w") as f:
                f.write(f"# VNC Access to {target}\n")
                f.write(f"# Command: {' '.join(cmd)}\n")
                f.write(f"# Started: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        try:
            # For screenshot mode, capture output
            if "vncsnapshot" in cmd[0]:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                if log_path:
                    with open(log_path, "a") as f:
                        f.write(result.stdout)
                        if result.stderr:
                            f.write(f"\nStderr: {result.stderr}\n")
                        if result.returncode == 0:
                            f.write(f"\nScreenshot saved to /tmp/vnc_screenshot.jpg\n")
                return result.returncode
            else:
                # Interactive mode - just launch and return
                if log_path:
                    with open(log_path, "a") as f:
                        f.write("Launching VNC viewer...\n")
                        f.write("Note: Interactive session - check viewer window\n")

                # Use Popen for non-blocking launch
                subprocess.Popen(
                    cmd,
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                return 0

        except subprocess.TimeoutExpired:
            if log_path:
                with open(log_path, "a") as f:
                    f.write("\n\n# ERROR: Connection timed out\n")
            return 124
        except FileNotFoundError:
            if log_path:
                with open(log_path, "a") as f:
                    f.write("\n\n# ERROR: VNC viewer not found\n")
            return 127
        except Exception as e:
            if log_path:
                with open(log_path, "a") as f:
                    f.write(f"\n\n# ERROR: {e}\n")
            return 1


plugin = VNCAccessPlugin()
