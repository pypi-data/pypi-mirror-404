#!/usr/bin/env python3
"""
souleyez.parsers.enum4linux_parser

Parses enum4linux SMB enumeration output into structured data.
"""

import re
from typing import Any, Dict


def parse_enum4linux_output(output: str, target: str = "") -> Dict[str, Any]:
    """
    Parse enum4linux or enum4linux-ng output and extract SMB information.

    Supports both formats:
    - Original enum4linux: Table-based output
    - enum4linux-ng: YAML-style output

    Args:
        output: Raw enum4linux output text
        target: Target IP/hostname from job

    Returns:
        Dict with structure:
        {
            'target': str,
            'workgroup': str,
            'domain_sid': str,
            'shares': [
                {
                    'name': str,
                    'type': str,
                    'comment': str,
                    'mapping': str,  # OK, DENIED, N/A
                    'listing': str,  # OK, N/A
                    'writing': str   # OK, N/A
                },
                ...
            ],
            'users': [str, ...],
            'groups': [str, ...]
        }
    """
    # Check if this is enum4linux-ng YAML-style output
    if _is_enum4linux_ng_output(output):
        return _parse_enum4linux_ng_output(output, target)

    # Original enum4linux format parsing
    return _parse_enum4linux_classic_output(output, target)


def _is_enum4linux_ng_output(output: str) -> bool:
    """Detect if output is from enum4linux-ng (YAML-style format)."""
    # Primary indicator - explicit version string (most reliable)
    if re.search(r"ENUM4LINUX\s*-\s*next\s*generation", output, re.IGNORECASE):
        return True
    if re.search(r"enum4linux-ng", output, re.IGNORECASE):
        return True

    # Secondary indicators - look for YAML-style patterns unique to ng
    ng_indicators = [
        re.search(r"After merging (user|share|group) results", output, re.IGNORECASE),
        re.search(r"^\s{2,}username:\s+", output, re.MULTILINE),  # Indented YAML-style
        re.search(
            r"^'?\d+'?:\s*$", output, re.MULTILINE
        ),  # RID entries: '1000': or 1000:
        re.search(r"^\s{2,}(groupname|name|type|comment):\s+", output, re.MULTILINE),
        re.search(r"Trying to get SID from lsaquery", output, re.IGNORECASE),
    ]

    # Classic enum4linux indicators (to confirm it's NOT ng)
    classic_indicators = [
        re.search(r"enum4linux v\d", output, re.IGNORECASE),
        re.search(r"Starting enum4linux v", output, re.IGNORECASE),
        re.search(r"Sharename\s+Type\s+Comment", output),  # Table header
        re.search(r"\|\s+Users on", output),
    ]

    ng_count = sum(1 for ind in ng_indicators if ind)
    classic_count = sum(1 for ind in classic_indicators if ind)

    # If we have classic indicators and no/few ng indicators, it's classic
    if classic_count >= 2 and ng_count < 2:
        return False

    # If we find at least 2 ng indicators, it's probably enum4linux-ng
    return ng_count >= 2


def _parse_enum4linux_ng_output(output: str, target: str = "") -> Dict[str, Any]:
    """
    Parse enum4linux-ng YAML-style output.

    The output format uses sections like:
        [+] After merging user results we have 35 user(s) total:
        '1000':
          username: root
          name: root
          ...
        [+] After merging share results we have 5 share(s) total:
        'print$':
          name: print$
          comment: Printer Drivers
          type: ...
    """
    result = {
        "target": target,
        "workgroup": None,
        "domain_sid": None,
        "shares": [],
        "users": [],
        "groups": [],
    }

    # Remove ANSI color codes
    output = re.sub(r"\x1b\[[0-9;]*m", "", output)
    lines = output.split("\n")

    current_section = None
    current_item = {}
    in_item = False

    def save_current_item():
        """Save the current item to the appropriate result list."""
        nonlocal current_item, in_item
        if current_section == "users" and current_item.get("username"):
            username = current_item["username"]
            if username not in result["users"]:
                result["users"].append(username)
        elif current_section == "shares" and current_item.get("name"):
            result["shares"].append(current_item.copy())
        elif current_section == "groups" and current_item.get("groupname"):
            groupname = current_item["groupname"]
            if groupname not in result["groups"]:
                result["groups"].append(groupname)
        current_item = {}
        in_item = False

    for i, line in enumerate(lines):
        stripped = line.rstrip()

        # Detect section headers from enum4linux-ng output
        if "After merging user results" in stripped:
            save_current_item()
            current_section = "users"
            continue
        elif "After merging share results" in stripped or re.search(
            r"Found \d+ share\(s\):", stripped
        ):
            save_current_item()
            current_section = "shares"
            continue
        elif "After merging group results" in stripped:
            save_current_item()
            current_section = "groups"
            continue

        # Extract workgroup/domain
        wg_match = re.search(r"Got domain/workgroup name:\s*(\S+)", stripped)
        if wg_match:
            result["workgroup"] = wg_match.group(1).strip()

        # Extract target
        target_match = re.search(r"Target\s+\.+\s+(\S+)", stripped)
        if target_match:
            result["target"] = target_match.group(1).strip()

        # Parse user entries in users section
        if current_section == "users":
            # Start of new user entry: '1000':
            rid_match = re.match(r"^'(\d+)':\s*$", stripped)
            if rid_match:
                save_current_item()
                in_item = True
                continue

            # Username field
            if in_item:
                username_match = re.match(r"^\s+username:\s*(.+)$", stripped)
                if username_match:
                    username = username_match.group(1).strip().strip("'\"")
                    if username and username != "(null)":
                        current_item["username"] = username

        # Parse share entries in shares section
        elif current_section == "shares":
            # Start of new share entry: 'print$': or ADMIN$:
            share_key_match = re.match(r"^'([^']+)':\s*$", stripped)
            if not share_key_match:
                # Try non-quoted format: ADMIN$:
                share_key_match = re.match(r"^([A-Za-z0-9_$]+):\s*$", stripped)
            if share_key_match:
                save_current_item()
                current_item = {"name": share_key_match.group(1)}
                in_item = True
                continue

            # Share properties
            if in_item:
                name_match = re.match(r"^\s+name:\s*(.+)$", stripped)
                if name_match:
                    current_item["name"] = name_match.group(1).strip()

                type_match = re.match(r"^\s+type:\s*(.+)$", stripped)
                if type_match:
                    current_item["type"] = type_match.group(1).strip()

                comment_match = re.match(r"^\s+comment:\s*(.*)$", stripped)
                if comment_match:
                    current_item["comment"] = comment_match.group(1).strip()

        # Parse group entries
        elif current_section == "groups":
            rid_match = re.match(r"^'(\d+)':\s*$", stripped)
            if rid_match:
                save_current_item()
                in_item = True
                continue

            if in_item:
                groupname_match = re.match(r"^\s+groupname:\s*(.+)$", stripped)
                if groupname_match:
                    groupname = groupname_match.group(1).strip().strip("'\"")
                    if groupname:
                        current_item["groupname"] = groupname

    # Don't forget the last item being parsed
    save_current_item()

    return result


def _parse_enum4linux_classic_output(output: str, target: str = "") -> Dict[str, Any]:
    """
    Parse original enum4linux table-based output format.
    """
    result = {
        "target": target,
        "workgroup": None,
        "domain_sid": None,
        "shares": [],
        "users": [],
        "groups": [],
    }

    lines = output.split("\n")
    current_section = None
    in_share_table = False
    share_table_started = False

    for i, line in enumerate(lines):
        # Remove ANSI color codes
        line = re.sub(r"\x1b\[[0-9;]*m", "", line)
        line = line.strip()

        # Extract target
        if line.startswith("Target ..........."):
            target_match = re.search(r"Target\s+\.+\s+(\S+)", line)
            if target_match:
                result["target"] = target_match.group(1)

        # Extract workgroup/domain
        elif "[+] Got domain/workgroup name:" in line:
            wg_match = re.search(r"Got domain/workgroup name:\s+(\S+)", line)
            if wg_match:
                result["workgroup"] = wg_match.group(1)

        # Extract domain SID
        elif line.startswith("Domain Sid:"):
            sid_match = re.search(r"Domain Sid:\s+(.+)", line)
            if sid_match:
                sid = sid_match.group(1).strip()
                if sid != "(NULL SID)":
                    result["domain_sid"] = sid

        # Detect share enumeration section
        elif "Share Enumeration on" in line:
            current_section = "shares"
            in_share_table = False
            share_table_started = False

        # Parse share table header
        elif current_section == "shares" and "Sharename" in line and "Type" in line:
            in_share_table = True
            share_table_started = False
            continue

        # Parse share separator line
        elif current_section == "shares" and line.startswith("---"):
            if in_share_table:
                share_table_started = True
            continue

        # Parse share lines
        elif current_section == "shares" and in_share_table and share_table_started:
            # Check if we've left the table
            if (
                not line
                or line.startswith("Reconnecting")
                or line.startswith("Server")
                or line.startswith("Workgroup")
                or line.startswith("[")
            ):
                in_share_table = False
                continue

            # Parse share line: "sharename   Type   Comment"
            share = _parse_share_line(line)
            if share:
                result["shares"].append(share)

        # Parse share mapping results
        elif current_section == "shares" and line.startswith("//"):
            mapping_info = _parse_share_mapping(line)
            if mapping_info:
                # Find and update the matching share
                for share in result["shares"]:
                    if mapping_info["name"] in line:
                        share.update(mapping_info)
                        break

        # Parse users section
        elif "Users on" in line or "user(s) returned" in line:
            current_section = "users"

        # Parse groups section
        elif "Groups on" in line or "group(s) returned" in line:
            current_section = "groups"

        # Parse user lines from RID cycling output (Local User or Domain User)
        elif current_section == "users" and line and not line.startswith("="):
            # Format variations:
            # "S-1-5-21-...-RID DOMAIN\username (Local User)"
            # "S-1-5-21-...-RID DOMAIN\\username (Local User)"
            # "username (Local User)" - simplified format
            # "[+] DOMAIN\username" - alternate prefix

            # Try full SID format first (flexible escaping)
            user_match = re.search(
                r"S-1-5-21-[\d-]+\s+\S+[\\]+(\S+)\s+\((Local|Domain)\s*User\)",
                line,
                re.IGNORECASE,
            )
            if user_match:
                username = user_match.group(1)
                if username and username not in result["users"]:
                    result["users"].append(username)
            else:
                # Try simpler DOMAIN\username format
                user_match = re.search(
                    r"[\[\+\]\s]*\S+[\\]+(\S+)\s+\((Local|Domain)\s*User\)",
                    line,
                    re.IGNORECASE,
                )
                if user_match:
                    username = user_match.group(1)
                    if username and username not in result["users"]:
                        result["users"].append(username)

        # Also parse group lines from RID cycling (Domain Group, Local Group)
        elif current_section == "groups" and line and not line.startswith("="):
            # Format variations similar to users
            group_match = re.search(
                r"S-1-5-21-[\d-]+\s+\S+[\\]+(\S+)\s+\((Domain|Local)\s*Group\)",
                line,
                re.IGNORECASE,
            )
            if group_match:
                groupname = group_match.group(1)
                if groupname and groupname not in result["groups"]:
                    result["groups"].append(groupname)
            else:
                # Try simpler format
                group_match = re.search(
                    r"[\[\+\]\s]*\S+[\\]+(\S+)\s+\((Domain|Local)\s*Group\)",
                    line,
                    re.IGNORECASE,
                )
                if group_match:
                    groupname = group_match.group(1)
                    if groupname and groupname not in result["groups"]:
                        result["groups"].append(groupname)

    return result


def _parse_share_line(line: str) -> Dict[str, Any]:
    """
    Parse a share table line.

    Example: "print$          Disk      Printer Drivers"
    Example: "tmp             Disk      oh noes!"
    Example: "IPC$    IPC       IPC Service (Samba)"
    """
    line = line.strip()
    if not line:
        return None

    # Try multiple parsing strategies for different formats

    # Strategy 1: Split on 2+ whitespace (most common)
    parts = re.split(r"\s{2,}", line)
    if len(parts) >= 2:
        share_name = parts[0].strip()
        share_type = parts[1].strip()
        comment = parts[2].strip() if len(parts) > 2 else ""

        # Validate share type is a known type
        if share_type.upper() in ["DISK", "IPC", "PRINT", "PRINTER", "COMM", "DEVICE"]:
            return {
                "name": share_name,
                "type": share_type,
                "comment": comment,
                "mapping": None,
                "listing": None,
                "writing": None,
            }

    # Strategy 2: Tab-separated
    parts = line.split("\t")
    if len(parts) >= 2:
        share_name = parts[0].strip()
        share_type = parts[1].strip()
        comment = parts[2].strip() if len(parts) > 2 else ""

        if share_type.upper() in ["DISK", "IPC", "PRINT", "PRINTER", "COMM", "DEVICE"]:
            return {
                "name": share_name,
                "type": share_type,
                "comment": comment,
                "mapping": None,
                "listing": None,
                "writing": None,
            }

    # Strategy 3: Regex for flexible whitespace (single space minimum)
    match = re.match(
        r"^(\S+)\s+(Disk|IPC|Print|Printer|Comm|Device)\s*(.*)?$", line, re.IGNORECASE
    )
    if match:
        return {
            "name": match.group(1),
            "type": match.group(2),
            "comment": match.group(3).strip() if match.group(3) else "",
            "mapping": None,
            "listing": None,
            "writing": None,
        }

    return None


def _parse_share_mapping(line: str) -> Dict[str, Any]:
    """
    Parse share mapping result line.

    Example: "//10.0.0.82/tmp	Mapping: OK Listing: OK Writing: N/A"
    Example: "//10.0.0.82/print$	Mapping: DENIED Listing: N/A Writing: N/A"
    """
    try:
        # Extract share name from path
        share_match = re.search(r"//[^/]+/(\S+)", line)
        if not share_match:
            return None

        share_name = share_match.group(1)

        # Extract mapping status
        mapping_match = re.search(r"Mapping:\s*(\S+)", line)
        listing_match = re.search(r"Listing:\s*(\S+)", line)
        writing_match = re.search(r"Writing:\s*(\S+)", line)

        return {
            "name": share_name,
            "mapping": mapping_match.group(1) if mapping_match else None,
            "listing": listing_match.group(1) if listing_match else None,
            "writing": writing_match.group(1) if writing_match else None,
        }
    except Exception:
        return None


def get_smb_stats(parsed: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get statistics from parsed enum4linux results.

    Returns:
        Dict with counts and summary info
    """
    accessible_shares = sum(
        1 for s in parsed.get("shares", []) if s.get("mapping") == "OK"
    )

    writable_shares = sum(
        1 for s in parsed.get("shares", []) if s.get("writing") == "OK"
    )

    return {
        "total_shares": len(parsed.get("shares", [])),
        "accessible_shares": accessible_shares,
        "writable_shares": writable_shares,
        "workgroup": parsed.get("workgroup"),
        "has_domain_sid": parsed.get("domain_sid") is not None,
    }


def categorize_share(share: Dict[str, Any]) -> str:
    """
    Categorize a share's security posture.

    Returns: 'open', 'readable', 'restricted', 'denied'
    """
    mapping = share.get("mapping", "N/A")
    listing = share.get("listing", "N/A")
    writing = share.get("writing", "N/A")

    if writing == "OK":
        return "open"  # Writable = high risk
    elif listing == "OK":
        return "readable"  # Readable = medium risk
    elif mapping == "OK":
        return "restricted"  # Accessible but limited
    else:
        return "denied"  # Not accessible
