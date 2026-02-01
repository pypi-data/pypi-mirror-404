#!/usr/bin/env python3
"""
Responder plugin - LLMNR/NBT-NS poisoning for credential capture.
"""

import os
import subprocess
from pathlib import Path

HELP = {
    "name": "Responder - LLMNR/NBT-NS/MDNS Poisoning",
    "description": (
        "Want to capture Windows credentials passively?\n\n"
        "Responder listens for LLMNR, NBT-NS, and MDNS broadcasts on the network and "
        "responds with poisoned answers, tricking Windows clients into sending their "
        "credentials (NTLMv2 hashes) to your machine.\n\n"
        "Use Responder during network reconnaissance to:\n"
        "- Capture NetNTLMv2 hashes without touching hosts\n"
        "- Intercept Windows authentication attempts\n"
        "- Identify active users and services\n"
        "- Get initial foothold credentials\n\n"
        "Quick tips:\n"
        "- Requires root/sudo (binds to ports 137, 138, 139, 389, 1433, etc.)\n"
        "- Works best on switched networks (same subnet)\n"
        "- Captured hashes can be cracked with hashcat mode 5600\n"
        "- Run for 15-30 minutes for best results\n"
        "- Disable poisoning modes if you just want to fingerprint\n"
        "- WPAD poisoning is aggressive - use with caution\n\n"
        "⚠️  Warning: This is an active network attack. Use only with permission!\n"
    ),
    "usage": 'souleyez jobs enqueue responder <interface> --args "[options]"',
    "examples": [
        'souleyez jobs enqueue responder eth0 --args "-v"',
        'souleyez jobs enqueue responder tun0 --args "-w -v"  # WPAD poisoning',
        'souleyez jobs enqueue responder wlan0 --args "-f -v"  # Fingerprint only',
    ],
    "flags": [
        ["-I <interface>", "Network interface to bind to (required)"],
        ["-A", "Analyze mode (default) - respond to poisoning requests"],
        ["-w", "Enable WPAD rogue proxy server (aggressive)"],
        ["-f", "Fingerprint mode - passive, no poisoning"],
        ["-v", "Verbose output"],
        ["-F", "Force WPAD authentication"],
        ["-P", "Force Basic Auth for proxy"],
        ["--lm", "Force LM hashing (downgrade attack)"],
        ["--disable-ess", "Disable Extended Security"],
    ],
    "notes": [
        "Requires root/sudo privileges",
        "Runs indefinitely - kill job when done",
        "Captured hashes auto-stored in credentials database",
        "Logs saved to ~/.souleyez/responder_logs/",
        "Default presets explained:",
        "  - Standard: LLMNR/NBT-NS poisoning only",
        "  - WPAD: Adds rogue proxy (very aggressive!)",
        "  - Fingerprint: Passive mode (no poisoning, just listen)",
        "  - SMB+HTTP Only: Reduced attack surface",
    ],
    "presets": [
        {
            "name": "Standard Poisoning",
            "args": ["-v"],
            "desc": "LLMNR/NBT-NS poisoning (default)",
        },
        {
            "name": "WPAD Poisoning",
            "args": ["-w", "-v"],
            "desc": "Add WPAD rogue proxy (aggressive)",
        },
        {
            "name": "Fingerprint Mode",
            "args": ["-f", "-v"],
            "desc": "Passive mode (no poisoning, just fingerprint)",
        },
        {
            "name": "SMB + HTTP Only",
            "args": ["-v", "--lm", "--disable-ess"],
            "desc": "Capture SMB and HTTP only",
        },
    ],
    "help_sections": [
        {
            "title": "What is Responder?",
            "color": "cyan",
            "content": [
                {
                    "title": "Overview",
                    "desc": "Responder performs LLMNR/NBT-NS/MDNS poisoning to passively capture Windows credentials (NTLMv2 hashes) when clients broadcast authentication requests.",
                },
                {
                    "title": "Use Cases",
                    "desc": "Passive credential capture on Windows networks",
                    "tips": [
                        "Capture NetNTLMv2 hashes without touching hosts",
                        "Intercept Windows authentication attempts",
                        "Identify active users and services",
                        "Get initial foothold credentials",
                    ],
                },
            ],
        },
        {
            "title": "How to Use",
            "color": "green",
            "content": [
                {
                    "title": "Basic Workflow",
                    "desc": "1. Select network interface to monitor\n     2. Choose poisoning mode (standard or WPAD)\n     3. Run for 15-30 minutes to capture hashes\n     4. Crack captured hashes with hashcat mode 5600",
                },
                {
                    "title": "Key Modes",
                    "desc": "Different levels of aggressiveness",
                    "tips": [
                        "Standard: LLMNR/NBT-NS poisoning only (default)",
                        "WPAD: Add rogue proxy (very aggressive)",
                        "Fingerprint: Passive mode (no poisoning)",
                        "SMB+HTTP Only: Reduced attack surface",
                    ],
                },
            ],
        },
        {
            "title": "Tips & Best Practices",
            "color": "yellow",
            "content": [
                (
                    "Best Practices:",
                    [
                        "Requires root/sudo for port binding",
                        "Run for 15-30 minutes for best results",
                        "Works best on switched networks (same subnet)",
                        "Captured hashes: hashcat -m 5600 hashes.txt wordlist.txt",
                        "Check ~/.souleyez/responder_logs/ for results",
                    ],
                ),
                (
                    "Common Issues:",
                    [
                        "Permission denied: Run with sudo",
                        "No hashes captured: May need WPAD mode or longer runtime",
                        "Interface not found: Verify interface name (eth0, wlan0)",
                        "Too aggressive: Use fingerprint mode (-f) if concerned",
                    ],
                ),
            ],
        },
    ],
}


class ResponderPlugin:
    """Responder LLMNR/NBT-NS poisoning plugin."""

    name = "responder"
    category = "credential_access"
    description = "LLMNR/NBT-NS poisoning - passive credential capture"
    requires_root = True
    HELP = HELP

    def __init__(self):
        self.responder_path = self._find_responder()
        self.log_dir = Path.home() / ".souleyez" / "responder_logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def _find_responder(self):
        """Locate Responder installation."""
        paths = [
            "/usr/share/responder/Responder.py",
            "/opt/Responder/Responder.py",
            Path.home() / "tools/Responder/Responder.py",
        ]

        for path in paths:
            if Path(path).exists():
                return str(path)

        result = subprocess.run(["which", "responder"], capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip()

        return None

    def _get_interface_for_target(self, target_ip: str) -> str:
        """
        Auto-detect the network interface that can reach the target IP.

        Args:
            target_ip: Target IP address

        Returns:
            Interface name (e.g., 'eth0', 'wlan0') or None if detection fails
        """
        try:
            # Use 'ip route get' to find which interface routes to the target
            result = subprocess.run(
                ["ip", "route", "get", target_ip],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode == 0:
                # Parse output: "10.0.0.73 dev eth0 src 10.0.0.1 uid 1000"
                # Look for "dev <interface>"
                import re

                match = re.search(r"dev\s+(\S+)", result.stdout)
                if match:
                    return match.group(1)

            # Fallback: try to get default interface
            result = subprocess.run(
                ["ip", "route", "show", "default"],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode == 0:
                import re

                match = re.search(r"dev\s+(\S+)", result.stdout)
                if match:
                    return match.group(1)

        except Exception:
            pass

        # Last resort: return common default interfaces
        for iface in ["eth0", "ens33", "enp0s3", "wlan0"]:
            try:
                result = subprocess.run(
                    ["ip", "link", "show", iface],
                    capture_output=True,
                    text=True,
                    timeout=2,
                )
                if result.returncode == 0:
                    return iface
            except Exception:
                continue

        return None

    def _is_valid_interface(self, name: str) -> bool:
        """Check if the given name is a valid network interface."""
        try:
            result = subprocess.run(
                ["ip", "link", "show", name], capture_output=True, text=True, timeout=2
            )
            return result.returncode == 0
        except Exception:
            return False

    def build_command(self, target, args, label, log_path):
        """
        Build command specification for Responder.

        Uses build_command pattern for proper session isolation - the background
        worker handles subprocess execution with os.setsid() to detach from the
        controlling terminal, preventing sudo password prompts from appearing
        in the user's terminal.

        Args:
            target: Target IP or network interface name
            args: Additional arguments
            label: Job label
            log_path: Path to job log file

        Returns:
            Command spec dict or None if validation fails
        """
        if not self.responder_path:
            with open(log_path, "w") as f:
                f.write("ERROR: Responder not found. Install with:\n")
                f.write("git clone https://github.com/lgandx/Responder\n")
                f.write("cd Responder\n")
                f.write("sudo python3 Responder.py -I eth0\n")
            return None

        # Determine network interface to use
        # If target is already an interface name (e.g., eth0), use it directly
        # Otherwise, auto-detect the interface that can reach the target IP
        interface = None
        if self._is_valid_interface(target):
            interface = target
        else:
            # Target is likely an IP address - auto-detect interface
            interface = self._get_interface_for_target(target)
            if not interface:
                with open(log_path, "w") as f:
                    f.write(
                        f"ERROR: Could not determine network interface for target {target}\n"
                    )
                    f.write(
                        "Please specify a valid network interface (e.g., eth0, wlan0, tun0)\n"
                    )
                    f.write("\nAvailable interfaces:\n")
                    try:
                        result = subprocess.run(
                            ["ip", "-o", "link", "show"], capture_output=True, text=True
                        )
                        for line in result.stdout.strip().split("\n"):
                            parts = line.split(":")
                            if len(parts) >= 2:
                                iface = parts[1].strip()
                                f.write(f"  - {iface}\n")
                    except Exception:
                        f.write("  (could not list interfaces)\n")
                return None

        cmd = ["sudo", "-n", "python3", self.responder_path, "-I", interface]

        if args:
            # Handle both list and string args for backward compatibility
            if isinstance(args, str):
                cmd.extend(args.split())
            else:
                cmd.extend(args)

        if "-A" not in cmd:
            cmd.append("-A")

        env = {"RESPONDER_LOG_DIR": str(self.log_dir)}

        # Write initial log content
        with open(log_path, "w") as f:
            f.write(f"Starting Responder...\n")
            f.write(f"Target: {target}\n")
            f.write(f"Interface: {interface}\n")
            f.write(f"Command: {' '.join(cmd)}\n")
            f.write(f"Logs will be saved to: {self.log_dir}\n\n")
            f.write("NOTE: Responder requires root/sudo. If this fails, either:\n")
            f.write("  - Run souleyez as root, or\n")
            f.write("  - Configure passwordless sudo for responder\n\n")
            f.write(
                "NOTE: Responder runs indefinitely. Kill job when done capturing.\n"
            )
            f.write(
                "Captured hashes are automatically stored in credentials database.\n\n"
            )

        return {"cmd": cmd, "timeout": 3600, "env": env}  # 1 hour

    def get_presets(self):
        """Return Responder presets."""
        return {
            "Standard Poisoning": {
                "description": "LLMNR/NBT-NS poisoning (default)",
                "args": "-v",
            },
            "WPAD Poisoning": {
                "description": "Add WPAD rogue proxy (aggressive)",
                "args": "-w -v",
            },
            "Fingerprint Mode": {
                "description": "Passive mode (no poisoning, just fingerprint)",
                "args": "-f -v",
            },
            "SMB + HTTP Only": {
                "description": "Capture SMB and HTTP only",
                "args": "-v --lm --disable-ess",
            },
        }


plugin = ResponderPlugin()
