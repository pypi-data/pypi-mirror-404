"""
External Tool Dependency Checker

Verifies that external pentesting tools are installed and provides
installation instructions for missing tools.

Supports both Kali Linux (apt) and Ubuntu (mixed methods).
Includes version checking for tools that require specific versions.
"""

import os
import re
import shutil
import subprocess
from typing import Dict, List, Optional, Tuple


def parse_version(version_str: str) -> Tuple[int, ...]:
    """
    Parse a version string into a tuple of integers for comparison.

    Examples:
        '3.8.2' -> (3, 8, 2)
        'v3.8.2' -> (3, 8, 2)
        '2.0.1-1build2' -> (2, 0, 1)
    """
    if not version_str:
        return (0,)
    # Remove leading 'v' if present
    version_str = version_str.lstrip("v")
    # Extract just the numeric version part (before any dash or other suffix)
    match = re.match(r"(\d+(?:\.\d+)*)", version_str)
    if match:
        return tuple(int(x) for x in match.group(1).split("."))
    return (0,)


def version_meets_requirement(installed: str, required: str) -> bool:
    """
    Check if installed version meets the minimum required version.

    Args:
        installed: Installed version string (e.g., '2.0.1')
        required: Minimum required version string (e.g., '3.0.0')

    Returns:
        True if installed >= required
    """
    installed_tuple = parse_version(installed)
    required_tuple = parse_version(required)
    return installed_tuple >= required_tuple


def get_tool_version(
    command: str,
    version_cmd: str = None,
    version_regex: str = None,
    version_fallback: str = None,
) -> Optional[str]:
    """
    Get the version of an installed tool.

    Args:
        command: The tool command (e.g., 'gobuster')
        version_cmd: Command to get version (default: '{command} --version')
        version_regex: Regex to extract version from output
        version_fallback: Fallback version string if detection fails (e.g., 'v2.x (upgrade needed)')

    Returns:
        Version string or None if not found
    """
    if not shutil.which(command):
        return None

    # Default version command
    if version_cmd is None:
        version_cmd = f"{command} --version"
    else:
        version_cmd = version_cmd.replace("{command}", command)

    try:
        result = subprocess.run(
            version_cmd.split(), capture_output=True, text=True, timeout=10
        )
        output = result.stdout + result.stderr

        # Use provided regex or try common patterns
        if version_regex:
            match = re.search(version_regex, output)
            if match:
                return match.group(1)

        # Try common version patterns
        patterns = [
            r"(\d+\.\d+\.\d+)",  # 3.8.2
            r"v(\d+\.\d+\.\d+)",  # v3.8.2
            r"version\s+(\d+\.\d+\.\d+)",  # version 3.8.2
            r"(\d+\.\d+)",  # 3.8
        ]

        for pattern in patterns:
            match = re.search(pattern, output, re.IGNORECASE)
            if match:
                return match.group(1)

        # If no version found but tool exists, use fallback
        if version_fallback:
            return version_fallback

        return None
    except Exception:
        return None


def detect_distro() -> str:
    """Detect the Linux distribution."""
    try:
        with open("/etc/os-release", "r") as f:
            content = f.read().lower()
            if "kali" in content:
                return "kali"
            elif "parrot" in content:
                return "parrot"
            elif "ubuntu" in content:
                return "ubuntu"
            elif "debian" in content:
                return "debian"
    except FileNotFoundError:
        pass
    return "unknown"


# Install methods for different distributions
# 'apt' = available via apt on both Kali and Ubuntu
# 'kali_only' = apt on Kali, alternative method on Ubuntu
# 'manual' = requires manual installation on all distros
EXTERNAL_TOOLS = {
    "prerequisites": {
        "curl": {
            "command": "curl",
            "install_kali": "sudo apt install curl",
            "install_ubuntu": "sudo apt install curl",
            "install_method": "apt",
            "description": "Command-line tool for transferring data with URLs",
        },
        "pip3": {
            "command": "pip3",
            "install_kali": "sudo apt install python3-pip",
            "install_ubuntu": "sudo apt install python3-pip",
            "install_method": "apt",
            "description": "Python package installer (required for many tools)",
        },
        "sshpass": {
            "command": "sshpass",
            "install_kali": "sudo apt install sshpass",
            "install_ubuntu": "sudo apt install sshpass",
            "install_method": "apt",
            "description": "SSH password authentication (for shell spawning)",
        },
        "smbclient": {
            "command": "smbclient",
            "install_kali": "sudo apt install smbclient",
            "install_ubuntu": "sudo apt install smbclient",
            "install_method": "apt",
            "description": "SMB/CIFS client (for share enumeration)",
        },
        "unzip": {
            "command": "unzip",
            "install_kali": "sudo apt install unzip",
            "install_ubuntu": "sudo apt install unzip",
            "install_method": "apt",
            "description": "Archive extraction (required for some tool installs)",
        },
        "chromium": {
            "command": "chromium-browser",
            "alt_commands": [
                "chromium"
            ],  # Kali uses chromium, Ubuntu uses chromium-browser
            "install_kali": "sudo apt install chromium",
            "install_ubuntu": "sudo apt install chromium-browser",
            "install_method": "apt",
            "description": "Headless browser (required for katana web crawling)",
        },
    },
    "reconnaissance": {
        "nmap": {
            "command": "nmap",
            "install_kali": "sudo apt install nmap",
            "install_ubuntu": "sudo apt install nmap",
            "install_method": "apt",
            "description": "Network scanner for host/port discovery",
            "needs_sudo": True,  # Required for SYN/UDP/OS detection scans
        },
        "theharvester": {
            "command": "theHarvester",
            "install_kali": "sudo apt install theharvester",
            "install_ubuntu": "pipx install git+https://github.com/laramies/theHarvester.git@4.4.4 && pipx inject theharvester netaddr aiomultiprocess aiosqlite pyppeteer uvloop certifi PyYAML censys aiohttp aiodns beautifulsoup4 requests shodan dnspython ujson lxml python-dateutil",
            "install_method": "kali_only",
            "description": "OSINT tool for gathering emails, names, subdomains",
        },
        "whois": {
            "command": "whois",
            "install_kali": "sudo apt install whois",
            "install_ubuntu": "sudo apt install whois",
            "install_method": "apt",
            "description": "Domain registration information lookup",
        },
        "dnsrecon": {
            "command": "dnsrecon",
            "install_kali": "sudo apt install dnsrecon",
            "install_ubuntu": "pipx install dnsrecon",
            "install_method": "kali_only",
            "description": "DNS enumeration and reconnaissance",
        },
    },
    "web_scanning": {
        "nuclei": {
            "command": "nuclei",
            "install_kali": "sudo apt install nuclei",
            "install_ubuntu": 'cd /tmp && ARCH=$(uname -m | sed "s/x86_64/amd64/;s/aarch64/arm64/") && curl -sL $(curl -s https://api.github.com/repos/projectdiscovery/nuclei/releases/latest | grep browser_download_url | grep "linux_${ARCH}.zip" | cut -d \\" -f 4) -o nuclei.zip && unzip -o nuclei.zip nuclei && sudo mv nuclei /usr/local/bin/ && rm nuclei.zip',
            "install_method": "kali_only",
            "description": "Fast vulnerability scanner using templates",
        },
        "gobuster": {
            "command": "gobuster",
            "install_kali": "sudo apt install gobuster",
            "install_ubuntu": 'ARCH=$(uname -m | sed "s/aarch64/arm64/") && wget -q https://github.com/OJ/gobuster/releases/download/v3.8.2/gobuster_Linux_${ARCH}.tar.gz -O /tmp/gobuster.tar.gz && tar -xzf /tmp/gobuster.tar.gz -C /tmp && sudo mv /tmp/gobuster /usr/local/bin/ && sudo chmod +x /usr/local/bin/gobuster && rm /tmp/gobuster.tar.gz',
            "install_method": "kali_only",
            "description": "Directory/file & DNS brute-forcing tool (v3.x required)",
            "min_version": "3.0.0",
            "version_cmd": "{command} -v",
            "version_regex": r"version\s+(\d+\.\d+\.\d+)",
            "version_note": "SoulEyez requires gobuster v3+ (uses subcommand syntax)",
            "upgrade_kali": "go install github.com/OJ/gobuster/v3@latest",
            "upgrade_ubuntu": "go install github.com/OJ/gobuster/v3@latest",
        },
        "ffuf": {
            "command": "ffuf",
            "install_kali": "sudo apt install ffuf",
            "install_ubuntu": "sudo apt install ffuf",
            "install_method": "apt",
            "description": "Fast web fuzzer for content discovery",
        },
        "wpscan": {
            "command": "wpscan",
            "install_kali": "sudo apt install wpscan",
            "install_ubuntu": "sudo gem install wpscan",
            "install_method": "kali_only",
            "description": "WordPress vulnerability scanner",
        },
        "nikto": {
            "command": "nikto",
            "install_kali": "sudo apt install nikto",
            "install_ubuntu": "sudo apt install nikto",
            "install_method": "apt",
            "description": "Web server vulnerability scanner",
        },
        "dalfox": {
            "command": "dalfox",
            "install_kali": "go install github.com/hahwul/dalfox/v2@latest",
            "install_ubuntu": "go install github.com/hahwul/dalfox/v2@latest",
            "install_method": "go",
            "description": "XSS vulnerability scanner",
        },
        "katana": {
            "command": "katana",
            "install_kali": "go install github.com/projectdiscovery/katana/cmd/katana@latest",
            "install_ubuntu": "go install github.com/projectdiscovery/katana/cmd/katana@latest",
            "install_method": "go",
            "description": "Web crawling and spidering for parameter discovery",
            "dependencies": ["chromium"],
        },
    },
    "exploitation": {
        "sqlmap": {
            "command": "sqlmap",
            "install_kali": "sudo apt install sqlmap",
            "install_ubuntu": "sudo apt install sqlmap",
            "install_method": "apt",
            "description": "Automatic SQL injection exploitation tool",
        },
        "metasploit": {
            "command": "msfconsole",
            "alt_commands": ["/opt/metasploit-framework/bin/msfconsole"],
            "install_kali": "sudo apt install metasploit-framework",
            "install_ubuntu": "sudo apt install -y postgresql postgresql-contrib && sudo systemctl enable postgresql && sudo systemctl start postgresql && curl https://raw.githubusercontent.com/rapid7/metasploit-omnibus/master/config/templates/metasploit-framework-wrappers/msfupdate.erb > /tmp/msfinstall && chmod +x /tmp/msfinstall && sudo /tmp/msfinstall && rm /tmp/msfinstall",
            "install_method": "kali_only",
            "description": "Penetration testing framework",
            "dependencies": ["postgresql"],
        },
        "searchsploit": {
            "command": "searchsploit",
            "install_kali": "sudo apt install exploitdb",
            "install_ubuntu": "sudo git clone https://gitlab.com/exploit-database/exploitdb.git /opt/exploitdb && sudo ln -sf /opt/exploitdb/searchsploit /usr/local/bin/searchsploit",
            "install_method": "kali_only",
            "description": "Exploit database search tool",
        },
    },
    "credential_attacks": {
        "hydra": {
            "command": "hydra",
            "install_kali": "sudo apt install hydra",
            "install_ubuntu": "sudo apt install hydra",
            "install_method": "apt",
            "description": "Network login brute-forcing tool",
        },
        "john": {
            "command": "john",
            "install_kali": "sudo apt install john",
            "install_ubuntu": "sudo apt install john",
            "install_method": "apt",
            "description": "John the Ripper password cracker",
        },
        "hashcat": {
            "command": "hashcat",
            "install_kali": "sudo apt install hashcat",
            "install_ubuntu": "sudo apt install hashcat",
            "install_method": "apt",
            "description": "Advanced password recovery tool",
        },
    },
    "windows_ad": {
        "enum4linux": {
            "command": "enum4linux",
            "alt_commands": ["enum4linux-ng"],
            "install_kali": "sudo apt install enum4linux",
            "install_ubuntu": "sudo apt install -y smbclient && pipx install git+https://github.com/cddmp/enum4linux-ng",
            "install_method": "kali_only",
            "description": "Windows/Samba enumeration tool",
            "system_deps_ubuntu": ["smbclient"],
        },
        "smbmap": {
            "command": "smbmap",
            "install_kali": "sudo apt install smbmap",
            "install_ubuntu": "pipx install --force smbmap && pipx inject smbmap impacket",
            "install_method": "kali_only",
            "description": "SMB share enumeration tool",
            "known_issues": "All versions have pickling bug with impacket. Use netexec instead.",
            "optional": True,
        },
        "netexec": {
            "command": "nxc",
            "install_kali": "sudo apt install netexec",
            "install_ubuntu": "pipx install git+https://github.com/Pennyw0rth/NetExec",
            "install_method": "pipx",
            "description": "Swiss army knife for pentesting Windows/AD (formerly CrackMapExec)",
        },
        "impacket-scripts": {
            "command": "GetNPUsers.py",
            "alt_commands": ["impacket-GetNPUsers", "GetNPUsers"],
            "install_kali": "sudo apt install python3-impacket",
            "install_ubuntu": "pipx install impacket",
            "install_method": "pipx",
            "description": "Collection of Python classes for network protocols",
        },
        "gpp-decrypt": {
            "command": "gpp-decrypt",
            "install_kali": "sudo apt install gpp-decrypt",
            "install_ubuntu": "pip install pycryptodome",
            "install_method": "kali_only",
            "description": "Decrypt Group Policy Preferences (GPP) passwords",
            "note": "On Ubuntu, pycryptodome provides Python fallback for GPP decryption",
            "optional": True,
        },
        "bloodhound": {
            "command": "bloodhound-python",
            "install_kali": "sudo apt install bloodhound.py",
            "install_ubuntu": "pipx install bloodhound",
            "install_method": "pipx",
            "description": "Active Directory relationship mapper",
        },
        "responder": {
            "command": "responder",
            "install_kali": "sudo apt install responder && sudo pip install --break-system-packages --ignore-installed aioquic",
            "install_ubuntu": "sudo git clone https://github.com/lgandx/Responder.git /opt/Responder && sudo pip install --break-system-packages --ignore-installed -r /opt/Responder/requirements.txt aioquic && sudo ln -sf /opt/Responder/Responder.py /usr/local/bin/responder",
            "install_method": "kali_only",
            "description": "LLMNR, NBT-NS and MDNS poisoner",
            "needs_sudo": True,  # Required for network poisoning
        },
        "evil-winrm": {
            "command": "evil-winrm",
            "install_kali": "sudo gem install evil-winrm",
            "install_ubuntu": "sudo gem install evil-winrm",
            "install_method": "gem",
            "description": "WinRM shell for pentesting (remote PowerShell access)",
        },
        "certipy": {
            "command": "certipy",
            "alt_commands": ["certipy-ad"],
            "install_kali": "pipx install certipy-ad",
            "install_ubuntu": "pipx install certipy-ad",
            "install_method": "pipx",
            "description": "Active Directory Certificate Services (ADCS) enumeration and exploitation",
        },
        "kerbrute": {
            "command": "kerbrute",
            "install_kali": "go install github.com/ropnop/kerbrute@latest",
            "install_ubuntu": "go install github.com/ropnop/kerbrute@latest",
            "install_method": "go",
            "description": "Kerberos user enumeration and password spraying",
        },
        "rdp-sec-check": {
            "command": "rdp-sec-check",
            "install_kali": "sudo cpan Encoding::BER && sudo git clone https://github.com/CiscoCXSecurity/rdp-sec-check.git /opt/rdp-sec-check && sudo chmod +x /opt/rdp-sec-check/rdp-sec-check.pl && sudo ln -sf /opt/rdp-sec-check/rdp-sec-check.pl /usr/local/bin/rdp-sec-check",
            "install_ubuntu": "sudo cpan Encoding::BER && sudo git clone https://github.com/CiscoCXSecurity/rdp-sec-check.git /opt/rdp-sec-check && sudo chmod +x /opt/rdp-sec-check/rdp-sec-check.pl && sudo ln -sf /opt/rdp-sec-check/rdp-sec-check.pl /usr/local/bin/rdp-sec-check",
            "install_method": "manual",
            "description": "RDP security configuration checker (NLA, encryption)",
        },
    },
    "router_iot": {
        "routersploit": {
            "command": "rsf.py",
            "install_kali": "pipx install routersploit",
            "install_ubuntu": "pipx install routersploit",
            "install_method": "pipx",
            "description": "Router exploitation framework (like Metasploit for routers)",
        },
        "miniupnpc": {
            "command": "upnpc",
            "install_kali": "sudo apt install miniupnpc",
            "install_ubuntu": "sudo apt install miniupnpc",
            "install_method": "apt",
            "description": "UPnP client for port forwarding manipulation",
        },
        "binwalk": {
            "command": "binwalk",
            "install_kali": "sudo apt install binwalk",
            "install_ubuntu": "sudo apt install binwalk",
            "install_method": "apt",
            "description": "Firmware analysis and extraction tool",
        },
        "dnsutils": {
            "command": "dig",
            "install_kali": "sudo apt install dnsutils",
            "install_ubuntu": "sudo apt install dnsutils",
            "install_method": "apt",
            "description": "DNS lookup utilities (dig, nslookup)",
        },
    },
    "remote_access": {
        "tigervnc": {
            "command": "vncviewer",
            "install_kali": "sudo apt install tigervnc-viewer",
            "install_ubuntu": "sudo apt install tigervnc-viewer",
            "install_method": "apt",
            "description": "VNC client for remote desktop access",
        },
        "vncsnapshot": {
            "command": "vncsnapshot",
            "install_kali": "sudo apt install vncsnapshot",
            "install_ubuntu": "sudo apt install vncsnapshot",
            "install_method": "apt",
            "description": "VNC screenshot capture tool",
        },
    },
}


def get_install_command(tool_info: dict, distro: Optional[str] = None) -> str:
    """Get the appropriate install command for the current distro."""
    if distro is None:
        distro = detect_distro()

    if distro in ("kali", "parrot"):
        return tool_info.get("install_kali", tool_info.get("install", ""))
    else:
        return tool_info.get("install_ubuntu", tool_info.get("install_kali", ""))


def get_upgrade_command(tool_info: dict, distro: Optional[str] = None) -> Optional[str]:
    """Get upgrade command if available, else None."""
    if distro is None:
        distro = detect_distro()
    if distro in ("kali", "parrot"):
        return tool_info.get("upgrade_kali")
    else:
        return tool_info.get("upgrade_ubuntu")


def check_tool(command: str, alt_commands: list = None) -> bool:
    """Check if a tool is installed and in PATH."""
    if shutil.which(command) is not None:
        return True
    # Check alternative command names or absolute paths
    if alt_commands:
        for alt in alt_commands:
            # Check if it's an absolute path that exists and is executable
            if alt.startswith("/") and os.path.isfile(alt) and os.access(alt, os.X_OK):
                return True
            # Otherwise check in PATH
            if shutil.which(alt) is not None:
                return True
    return False


def find_tool_command(command: str, alt_commands: list = None) -> Optional[str]:
    """
    Find which command is actually installed.

    Returns the primary command if found, or the first alt_command that's
    found, or None if the tool is not installed.
    """
    if shutil.which(command) is not None:
        return command
    # Check alternative command names or absolute paths
    if alt_commands:
        for alt in alt_commands:
            # Check if it's an absolute path that exists and is executable
            if alt.startswith("/") and os.path.isfile(alt) and os.access(alt, os.X_OK):
                return alt
            # Otherwise check in PATH
            if shutil.which(alt) is not None:
                return alt
    return None


def check_all_tools() -> Dict[str, Dict[str, bool]]:
    """
    Check installation status of all external tools.

    Returns:
        {
            'reconnaissance': {
                'nmap': True,
                'theharvester': False,
                ...
            },
            ...
        }
    """
    results = {}

    for category, tools in EXTERNAL_TOOLS.items():
        results[category] = {}
        for tool_name, tool_info in tools.items():
            alt_commands = tool_info.get("alt_commands")
            results[category][tool_name] = check_tool(
                tool_info["command"], alt_commands
            )

    return results


def get_tool_stats() -> Tuple[int, int]:
    """
    Get summary statistics of installed tools.

    Returns:
        (installed_count, total_count)
    """
    status = check_all_tools()
    installed = 0
    total = 0
    for category, tools in EXTERNAL_TOOLS.items():
        for tool_name, tool_info in tools.items():
            # Skip optional tools that aren't installed
            is_optional = tool_info.get("optional", False)
            is_installed = status[category][tool_name]
            if is_installed:
                installed += 1
                total += 1
            elif not is_optional:
                # Only count non-optional missing tools
                total += 1
    return installed, total


def get_missing_tools(distro: Optional[str] = None) -> List[Dict]:
    """
    Get list of missing tools with installation instructions.

    Args:
        distro: Optional distro override ('kali', 'ubuntu', etc.)

    Returns:
        [
            {
                'name': 'nuclei',
                'category': 'web_scanning',
                'command': 'nuclei',
                'install': 'go install ...',
                'description': '...'
            },
            ...
        ]
    """
    if distro is None:
        distro = detect_distro()

    missing = []
    status = check_all_tools()

    for category, tools in EXTERNAL_TOOLS.items():
        for tool_name, tool_info in tools.items():
            if not status[category][tool_name]:
                # Skip optional tools from missing list
                if tool_info.get("optional", False):
                    continue
                missing.append(
                    {
                        "name": tool_name,
                        "category": category,
                        "command": tool_info["command"],
                        "install": get_install_command(tool_info, distro),
                        "install_method": tool_info.get("install_method", "apt"),
                        "description": tool_info["description"],
                    }
                )

    return missing


def check_tool_version(tool_info: dict) -> Dict[str, any]:
    """
    Check if an installed tool meets version requirements.

    Args:
        tool_info: Tool info dict from EXTERNAL_TOOLS

    Returns:
        {
            'installed': bool,
            'version': str or None,
            'min_version': str or None,
            'version_ok': bool,
            'needs_upgrade': bool,
            'version_note': str or None,
            'actual_command': str or None  # The command that was found
        }
    """
    command = tool_info["command"]
    alt_commands = tool_info.get("alt_commands")
    min_version = tool_info.get("min_version")

    result = {
        "installed": False,
        "version": None,
        "min_version": min_version,
        "version_ok": True,
        "needs_upgrade": False,
        "version_note": tool_info.get("version_note"),
        "actual_command": None,
    }

    # Find which command is actually installed (primary or alt)
    actual_cmd = find_tool_command(command, alt_commands)
    if not actual_cmd:
        return result

    result["installed"] = True
    result["actual_command"] = actual_cmd

    # Always try to get version for display purposes
    version_cmd = tool_info.get("version_cmd")
    version_regex = tool_info.get("version_regex")
    version_fallback = tool_info.get("version_fallback")

    # Use actual_cmd for version detection, but version_cmd template uses {command}
    if version_cmd:
        # Replace {command} with the actual found command
        actual_version_cmd = version_cmd.replace("{command}", actual_cmd)
    else:
        actual_version_cmd = None

    installed_version = get_tool_version(
        actual_cmd, actual_version_cmd, version_regex, version_fallback
    )
    result["version"] = installed_version

    # Check against min_version if there is one
    if min_version and installed_version:
        result["version_ok"] = version_meets_requirement(installed_version, min_version)
        result["needs_upgrade"] = not result["version_ok"]
    elif min_version and not installed_version:
        # Couldn't determine version - assume it's OK but flag uncertainty
        result["version_ok"] = True

    return result


def get_tools_with_wrong_version(distro: Optional[str] = None) -> List[Dict]:
    """
    Get list of installed tools that don't meet version requirements.

    Args:
        distro: Optional distro override

    Returns:
        List of tools needing upgrade with install instructions
    """
    if distro is None:
        distro = detect_distro()

    wrong_version = []

    for category, tools in EXTERNAL_TOOLS.items():
        for tool_name, tool_info in tools.items():
            if not tool_info.get("min_version"):
                continue  # No version requirement

            version_status = check_tool_version(tool_info)

            if version_status["installed"] and version_status["needs_upgrade"]:
                wrong_version.append(
                    {
                        "name": tool_name,
                        "category": category,
                        "command": tool_info["command"],
                        "installed_version": version_status["version"],
                        "min_version": version_status["min_version"],
                        "install": get_install_command(tool_info, distro),
                        "description": tool_info["description"],
                        "version_note": version_status["version_note"],
                    }
                )

    return wrong_version


def check_all_tools_with_versions() -> Dict[str, Dict[str, Dict]]:
    """
    Check installation and version status of all external tools.

    Returns:
        {
            'reconnaissance': {
                'nmap': {
                    'installed': True,
                    'version': '7.94',
                    'min_version': None,
                    'version_ok': True,
                    'needs_upgrade': False
                },
                ...
            },
            ...
        }
    """
    results = {}

    for category, tools in EXTERNAL_TOOLS.items():
        results[category] = {}
        for tool_name, tool_info in tools.items():
            results[category][tool_name] = check_tool_version(tool_info)

    return results


def get_tools_by_category(distro: Optional[str] = None) -> Dict[str, List[Dict]]:
    """
    Get all tools organized by category with installation and version status.

    Args:
        distro: Optional distro override ('kali', 'ubuntu', etc.)

    Returns:
        {
            'reconnaissance': [
                {
                    'name': 'nmap',
                    'installed': True,
                    'version': '7.94',
                    'version_ok': True,
                    'command': 'nmap',
                    'install': '...',
                    'description': '...'
                },
                ...
            ],
            ...
        }
    """
    if distro is None:
        distro = detect_distro()

    status = check_all_tools_with_versions()
    organized = {}

    for category, tools in EXTERNAL_TOOLS.items():
        organized[category] = []
        for tool_name, tool_info in tools.items():
            tool_status = status[category][tool_name]
            organized[category].append(
                {
                    "name": tool_name,
                    "installed": tool_status["installed"],
                    "version": tool_status.get("version"),
                    "version_ok": tool_status.get("version_ok", True),
                    "needs_upgrade": tool_status.get("needs_upgrade", False),
                    "min_version": tool_status.get("min_version"),
                    "command": tool_info["command"],
                    "install": get_install_command(tool_info, distro),
                    "install_method": tool_info.get("install_method", "apt"),
                    "description": tool_info["description"],
                    "version_note": tool_info.get("version_note"),
                }
            )

    return organized


def get_category_name(category: str) -> str:
    """Get human-readable category name."""
    names = {
        "prerequisites": "⚙️ Prerequisites",
        "reconnaissance": "🔍 Reconnaissance",
        "web_scanning": "🌐 Web Scanning",
        "exploitation": "💥 Exploitation",
        "credential_attacks": "🔑 Credential Attacks",
        "windows_ad": "🪟 Windows/Active Directory",
        "router_iot": "📡 Router/IoT Testing",
        "remote_access": "🖥️ Remote Access",
    }
    return names.get(category, category.replace("_", " ").title())


def check_msfdb_status() -> Dict[str, any]:
    """
    Check Metasploit database initialization status.

    Returns dict with:
        - initialized: bool - Whether msfdb has been initialized
        - running: bool - Whether PostgreSQL is running
        - connected: bool - Whether MSF can connect to the database
        - message: str - Human-readable status message
    """
    import subprocess
    from pathlib import Path

    result = {
        "initialized": False,
        "running": False,
        "connected": False,
        "message": "Unknown status",
    }

    # Check if msfdb command exists
    if not shutil.which("msfdb"):
        result["message"] = "msfdb command not found - Metasploit may not be installed"
        return result

    # Helper to check if PostgreSQL is running
    def check_postgresql_running() -> bool:
        try:
            proc = subprocess.run(
                ["systemctl", "is-active", "postgresql"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return proc.returncode == 0 and "active" in proc.stdout.lower()
        except Exception:
            return False

    # Helper to check system-wide MSF database config (Kali fallback)
    def check_system_config() -> bool:
        """Check if system-wide database.yml exists with valid PostgreSQL config."""
        config_path = Path("/usr/share/metasploit-framework/config/database.yml")
        if config_path.exists():
            try:
                content = config_path.read_text()
                # Check for PostgreSQL adapter configuration
                return "adapter: postgresql" in content and "database: msf" in content
            except Exception:
                return False
        return False

    try:
        # Run msfdb status
        proc = subprocess.run(
            ["msfdb", "status"], capture_output=True, text=True, timeout=10
        )
        output = proc.stdout + proc.stderr
        output_lower = output.lower()

        # Check if msfdb requires root (common on Kali)
        if "run as root" in output_lower or (
            proc.returncode != 0 and "error" in output_lower
        ):
            # Fall back to checking system config file and PostgreSQL status
            result["running"] = check_postgresql_running()
            if check_system_config():
                result["initialized"] = True
                if result["running"]:
                    result["connected"] = True
                    result["message"] = "Database initialized and running"
                else:
                    result["message"] = (
                        "Database initialized but PostgreSQL not running - run: sudo systemctl start postgresql"
                    )
            else:
                result["message"] = "Need sudo to verify - run: sudo msfdb status"
            return result

        # Check if database is initialized
        if "no database" in output_lower or "not initialized" in output_lower:
            result["message"] = "Database not initialized - run: msfdb init"
            return result

        # Check PostgreSQL status
        if "postgresql" in output_lower:
            if "running" in output_lower or "active" in output_lower:
                result["running"] = True

        # Check for successful connection indicators
        if "msf" in output_lower and (
            "database" in output_lower or "connected" in output_lower
        ):
            if "no connection" not in output_lower:
                result["initialized"] = True
                result["connected"] = True

        # If we see the database name, it's initialized
        if "msf" in output_lower and result["running"]:
            result["initialized"] = True

        # Build status message
        if result["initialized"] and result["running"]:
            result["connected"] = True
            result["message"] = "Database initialized and running"
        elif result["initialized"] and not result["running"]:
            result["message"] = (
                "Database initialized but PostgreSQL not running - run: sudo systemctl start postgresql"
            )
        elif not result["initialized"]:
            result["message"] = "Database not initialized - run: msfdb init"

    except subprocess.TimeoutExpired:
        result["message"] = "msfdb status timed out"
    except Exception as e:
        result["message"] = f"Error checking msfdb status: {e}"

    return result
