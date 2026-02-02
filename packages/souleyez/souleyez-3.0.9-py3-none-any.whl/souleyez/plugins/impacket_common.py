#!/usr/bin/env python3
"""
souleyez.plugins.impacket_common - Shared utilities for Impacket plugins

Handles differences between Kali (apt) and Ubuntu (pipx) installations.
"""

import shutil
from typing import Optional


def find_impacket_command(tool_name: str) -> Optional[str]:
    """
    Find the correct Impacket command (varies by install method).

    On Kali (apt install python3-impacket):
        - Commands are: impacket-GetNPUsers, impacket-secretsdump, etc.

    On Ubuntu (pipx install impacket):
        - Commands are: GetNPUsers.py, secretsdump.py, etc.
        - Or without .py: GetNPUsers, secretsdump

    Args:
        tool_name: Base tool name like "GetNPUsers", "secretsdump", "psexec"

    Returns:
        The actual command that exists on the system, or None if not found
    """
    # Possible command names in order of preference
    candidates = [
        f"impacket-{tool_name}",  # Kali apt style
        f"{tool_name}.py",  # Ubuntu pipx style
        tool_name,  # Direct name
    ]

    for cmd in candidates:
        if shutil.which(cmd):
            return cmd

    return None
