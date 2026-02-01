#!/usr/bin/env python3
"""
souleyez.plugins.routersploit

RouterSploit vulnerability scanner plugin.
Scans routers and embedded devices for known vulnerabilities.
"""

import shutil
import subprocess
import time
from typing import List

from souleyez.security.validation import ValidationError, validate_target

from .plugin_base import PluginBase

HELP = {
    "name": "RouterSploit — Router Vulnerability Scanner",
    "description": (
        "RouterSploit is an exploitation framework dedicated to embedded devices.\n\n"
        "Like Metasploit but specifically for routers, access points, and IoT devices. "
        "It contains modules for:\n"
        "- Vulnerability scanning (autopwn-style detection)\n"
        "- Credential testing (default passwords)\n"
        "- Exploitation (RCE, auth bypass, backdoors)\n\n"
        "This plugin runs the scanner module to detect known vulnerabilities, "
        "which can then be exploited with the routersploit_exploit plugin.\n\n"
        "Quick tips:\n"
        "- Scan first to identify vulnerabilities\n"
        "- Common targets: consumer routers, IP cameras, NAS devices\n"
        "- Look for firmware version info from nmap/UPnP first\n"
        "- Supports 200+ exploits for various vendors\n"
    ),
    "usage": "souleyez jobs enqueue routersploit <target>",
    "examples": [
        "souleyez jobs enqueue routersploit 192.168.1.1",
        'souleyez jobs enqueue routersploit 192.168.1.1 --args "--port 8080"',
        'souleyez jobs enqueue routersploit 192.168.1.1 --args "--threads 4"',
    ],
    "flags": [
        ["--port PORT", "Target HTTP port (default: 80)"],
        ["--ssl", "Use HTTPS instead of HTTP"],
        ["--threads N", "Number of threads (default: 8)"],
    ],
    "presets": [
        # Scanning
        {"name": "Quick Scan", "args": [], "desc": "Standard vulnerability scan"},
        {"name": "HTTPS Scan", "args": ["--ssl"], "desc": "Scan over HTTPS (port 443)"},
        {
            "name": "Alt Port",
            "args": ["--port", "8080"],
            "desc": "Scan non-standard web port",
        },
        # Exploitation (specify module with --exploit)
        {
            "name": "Default Creds",
            "args": ["--exploit", "creds/generic/http_default_creds"],
            "desc": "Test default HTTP credentials",
        },
        {
            "name": "Netgear RCE",
            "args": ["--exploit", "exploits/routers/netgear/dgn1000_dgn2200_rce"],
            "desc": "Netgear DGN1000/2200 RCE",
        },
        {
            "name": "D-Link RCE",
            "args": ["--exploit", "exploits/routers/dlink/dir_815_850l_rce"],
            "desc": "D-Link DIR-815/850L RCE",
        },
    ],
    "help_sections": [
        {
            "title": "What is RouterSploit?",
            "color": "cyan",
            "content": [
                {
                    "title": "Overview",
                    "desc": "RouterSploit is like Metasploit for routers. It has 200+ exploits for embedded devices from major vendors.",
                },
                {
                    "title": "Vendors Covered",
                    "desc": "Supported device manufacturers",
                    "tips": [
                        "Netgear, Linksys, TP-Link, D-Link, ASUS",
                        "Cisco, Juniper, MikroTik",
                        "Huawei, ZTE, ZyXEL",
                        "IP cameras: Hikvision, Dahua, Foscam",
                        "Many more embedded Linux devices",
                    ],
                },
            ],
        },
        {
            "title": "Attack Workflow",
            "color": "green",
            "content": [
                {
                    "title": "Typical Flow",
                    "desc": "1. Identify device (nmap, UPnP)\n2. Run RouterSploit scanner\n3. Exploit vulnerable services\n4. Extract credentials or get shell",
                },
                {
                    "title": "What Gets Tested",
                    "desc": "Types of vulnerabilities checked",
                    "tips": [
                        "Default/hardcoded credentials",
                        "Authentication bypasses",
                        "Remote code execution (RCE)",
                        "Information disclosure",
                        "Backdoor accounts",
                    ],
                },
            ],
        },
    ],
}


class RouterSploitPlugin(PluginBase):
    name = "RouterSploit"
    tool = "rsf"
    category = "vulnerability_analysis"
    HELP = HELP

    def check_tool_available(self) -> tuple:
        """Check if RouterSploit is available."""
        # RouterSploit can be installed as 'rsf', 'rsf.py' (pipx), or run via python
        rsf_path = shutil.which("rsf") or shutil.which("rsf.py")
        if rsf_path:
            return True, None

        # Check for routersploit Python module
        try:
            import routersploit

            return True, None
        except ImportError:
            pass

        return False, (
            "RouterSploit not found. Install with:\n"
            "  pipx install routersploit\n"
            "  # or\n"
            "  git clone https://github.com/threat9/routersploit\n"
            "  cd routersploit && pip install -r requirements.txt"
        )

    def build_command(
        self, target: str, args: List[str] = None, label: str = "", log_path: str = None
    ):
        """Build RouterSploit scan command."""
        args = args or []

        # Validate target
        try:
            target = validate_target(target)
        except ValidationError as e:
            if log_path:
                with open(log_path, "w") as f:
                    f.write(f"ERROR: Invalid target: {e}\n")
            return None

        # Parse arguments
        port = "80"
        ssl = False
        threads = "8"
        exploit_module = None

        i = 0
        while i < len(args):
            if args[i] == "--port" and i + 1 < len(args):
                port = args[i + 1]
                i += 2
            elif args[i] == "--ssl":
                ssl = True
                port = "443" if port == "80" else port
                i += 1
            elif args[i] == "--threads" and i + 1 < len(args):
                threads = args[i + 1]
                i += 2
            elif args[i] == "--exploit" and i + 1 < len(args):
                exploit_module = args[i + 1]
                i += 2
            else:
                i += 1

        # Build RSF command script
        # RouterSploit uses an interactive shell, so we create a script file
        protocol = "https" if ssl else "http"

        # Create RouterSploit resource script
        # Use exploit module if specified, otherwise use scanner
        if exploit_module:
            rsf_commands = f"""use {exploit_module}
set target {target}
set port {port}
run
exit
"""
        else:
            rsf_commands = f"""use scanners/autopwn
set target {target}
set port {port}
set threads {threads}
run
exit
"""

        # Write resource script and run rsf
        import os
        import tempfile

        fd, rc_file = tempfile.mkstemp(suffix=".rsf", prefix="routersploit_")
        try:
            with os.fdopen(fd, "w") as f:
                f.write(rsf_commands)
        except Exception as e:
            if log_path:
                with open(log_path, "w") as f:
                    f.write(f"ERROR: Failed to create RSF script: {e}\n")
            return None

        # Check which RSF binary is available (rsf or rsf.py from pipx)
        rsf_bin = shutil.which("rsf") or shutil.which("rsf.py")
        if rsf_bin:
            cmd = [rsf_bin, "-m", rc_file]
        else:
            # Try running as Python module
            cmd = ["python3", "-m", "routersploit", "-m", rc_file]

        return {
            "cmd": cmd,
            "timeout": 1800,  # 30 minute timeout
            "env": {"RSF_RC_FILE": rc_file},
            "_rc_file": rc_file,  # Track for cleanup
        }

    def run(
        self, target: str, args: List[str] = None, label: str = "", log_path: str = None
    ) -> int:
        """Execute RouterSploit scan."""
        import os

        cmd_spec = self.build_command(target, args, label, log_path)
        if cmd_spec is None:
            return 1

        cmd = cmd_spec["cmd"]
        rc_file = cmd_spec.get("_rc_file")

        if log_path:
            with open(log_path, "w") as f:
                f.write(f"# RouterSploit Vulnerability Scan on {target}\n")
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
                    f.write("\n\n# ERROR: Scan timed out\n")
            return 124
        except FileNotFoundError:
            if log_path:
                with open(log_path, "a") as f:
                    f.write("\n\n# ERROR: RouterSploit not found\n")
                    f.write("Install with: pipx install routersploit\n")
            return 127
        except Exception as e:
            if log_path:
                with open(log_path, "a") as f:
                    f.write(f"\n\n# ERROR: {e}\n")
            return 1
        finally:
            # Cleanup resource file
            if rc_file and os.path.exists(rc_file):
                try:
                    os.unlink(rc_file)
                except:
                    pass


plugin = RouterSploitPlugin()
