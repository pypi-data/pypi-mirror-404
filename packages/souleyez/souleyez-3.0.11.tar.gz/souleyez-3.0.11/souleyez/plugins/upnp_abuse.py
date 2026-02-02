#!/usr/bin/env python3
"""
souleyez.plugins.upnp_abuse

UPnP abuse plugin for adding/removing port forwards and extracting info.
Uses miniupnpc library to interact with UPnP-enabled routers.
"""

import shutil
import subprocess
import time
from typing import List

from souleyez.security.validation import ValidationError, validate_target

from .plugin_base import PluginBase

HELP = {
    "name": "UPnP Abuse — Port Forward Manipulation",
    "description": (
        "Abuse UPnP to add port forwards, extract connection info, or expose services.\n\n"
        "UPnP allows any device on the LAN to request port forwards from the router "
        "without authentication. This can be abused to:\n"
        "- Expose internal services to the internet\n"
        "- Redirect traffic through your machine\n"
        "- Extract external IP and connection info\n"
        "- Map existing port forwards\n\n"
        "This plugin uses upnpc (miniupnpc) to interact with UPnP IGD services.\n\n"
        "Quick tips:\n"
        "- Always run 'list' first to see existing forwards\n"
        "- Use 'info' to get external IP and gateway info\n"
        "- Port forwards persist until router reboot (usually)\n"
        "- Clean up your test forwards when done\n"
    ),
    "usage": 'souleyez jobs enqueue upnp_abuse <router_ip> --args "<action>"',
    "examples": [
        'souleyez jobs enqueue upnp_abuse 192.168.1.1 --args "list"',
        'souleyez jobs enqueue upnp_abuse 192.168.1.1 --args "info"',
        'souleyez jobs enqueue upnp_abuse 192.168.1.1 --args "add 8888 192.168.1.100 22 TCP"',
        'souleyez jobs enqueue upnp_abuse 192.168.1.1 --args "delete 8888 TCP"',
    ],
    "flags": [
        ["list", "List existing port mappings"],
        ["info", "Get external IP and gateway info"],
        ["add EXT_PORT INT_IP INT_PORT PROTO", "Add port forward (PROTO=TCP/UDP)"],
        ["delete EXT_PORT PROTO", "Remove port forward"],
    ],
    "presets": [
        {
            "name": "List Mappings",
            "args": ["list"],
            "desc": "Show existing port forwards",
        },
        {
            "name": "Get Info",
            "args": ["info"],
            "desc": "External IP and gateway details",
        },
        {
            "name": "Expose SSH",
            "args": ["add", "2222", "TARGET_IP", "22", "TCP"],
            "desc": "Expose SSH on port 2222",
        },
    ],
    "help_sections": [
        {
            "title": "What Can UPnP Abuse Do?",
            "color": "cyan",
            "content": [
                {
                    "title": "Capabilities",
                    "desc": "What this plugin enables",
                    "tips": [
                        "View all active port forwards on the router",
                        "Get the router's external (public) IP address",
                        "Add new port forwards without authentication",
                        "Remove port forwards you added",
                        "Redirect external traffic to internal hosts",
                    ],
                }
            ],
        },
        {
            "title": "Attack Scenarios",
            "color": "red",
            "content": [
                {
                    "title": "Common Uses",
                    "desc": "How attackers abuse UPnP",
                    "tips": [
                        "Expose internal services (SSH, RDP, web) to internet",
                        "Create persistent access through router",
                        "Pivot from compromised LAN device to WAN access",
                        "Map network by listing existing forwards",
                    ],
                }
            ],
        },
    ],
}


class UPnPAbusePlugin(PluginBase):
    name = "UPnP Abuse"
    tool = "upnpc"
    category = "exploitation"
    HELP = HELP

    def check_tool_available(self) -> tuple:
        """Check if upnpc is available."""
        if shutil.which("upnpc"):
            return True, None
        return False, "upnpc not found. Install with: sudo apt install miniupnpc"

    def build_command(
        self, target: str, args: List[str] = None, label: str = "", log_path: str = None
    ):
        """Build upnpc command for UPnP manipulation."""
        args = args or ["list"]

        # Validate target
        try:
            target = validate_target(target)
        except ValidationError as e:
            if log_path:
                with open(log_path, "w") as f:
                    f.write(f"ERROR: Invalid target: {e}\n")
            return None

        action = args[0] if args else "list"

        if action == "list":
            cmd = ["upnpc", "-l"]
        elif action == "info":
            cmd = ["upnpc", "-s"]
        elif action == "add" and len(args) >= 5:
            # add EXT_PORT INT_IP INT_PORT PROTO
            ext_port, int_ip, int_port, proto = args[1], args[2], args[3], args[4]
            cmd = ["upnpc", "-a", int_ip, int_port, ext_port, proto]
        elif action == "delete" and len(args) >= 3:
            # delete EXT_PORT PROTO
            ext_port, proto = args[1], args[2]
            cmd = ["upnpc", "-d", ext_port, proto]
        else:
            if log_path:
                with open(log_path, "w") as f:
                    f.write("ERROR: Invalid action. Use: list, info, add, or delete\n")
                    f.write("  list - List port mappings\n")
                    f.write("  info - Get external IP and gateway info\n")
                    f.write("  add EXT_PORT INT_IP INT_PORT PROTO - Add mapping\n")
                    f.write("  delete EXT_PORT PROTO - Remove mapping\n")
            return None

        return {"cmd": cmd, "timeout": 60}  # Quick timeout for UPnP operations

    def run(
        self, target: str, args: List[str] = None, label: str = "", log_path: str = None
    ) -> int:
        """Execute UPnP manipulation."""
        cmd_spec = self.build_command(target, args, label, log_path)
        if cmd_spec is None:
            return 1

        cmd = cmd_spec["cmd"]
        action = args[0] if args else "list"

        if log_path:
            with open(log_path, "w") as f:
                f.write(f"# UPnP Abuse on {target}\n")
                f.write(f"# Action: {action}\n")
                f.write(f"# Command: {' '.join(cmd)}\n")
                f.write(f"# Started: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        try:
            with open(log_path, "a") as f:
                result = subprocess.run(
                    cmd, stdout=f, stderr=subprocess.STDOUT, timeout=cmd_spec["timeout"]
                )
            return result.returncode

        except subprocess.TimeoutExpired:
            if log_path:
                with open(log_path, "a") as f:
                    f.write("\n\n# ERROR: Operation timed out\n")
            return 124
        except FileNotFoundError:
            if log_path:
                with open(log_path, "a") as f:
                    f.write("\n\n# ERROR: upnpc not found\n")
                    f.write("Install with: sudo apt install miniupnpc\n")
            return 127
        except Exception as e:
            if log_path:
                with open(log_path, "a") as f:
                    f.write(f"\n\n# ERROR: {e}\n")
            return 1


plugin = UPnPAbusePlugin()
