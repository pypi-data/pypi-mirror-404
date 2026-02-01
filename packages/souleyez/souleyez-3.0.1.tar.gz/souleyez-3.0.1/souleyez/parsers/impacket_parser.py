#!/usr/bin/env python3
"""
souleyez.parsers.impacket_parser - Parse Impacket tool outputs

Handles parsing for:
- secretsdump (credential extraction)
- GetNPUsers (Kerberoasting)
- psexec (command execution)
- smbclient (file operations)
"""

import re
from typing import Any, Dict, List


def parse_secretsdump(log_path: str, target: str) -> Dict[str, Any]:
    """
    Parse secretsdump output for credentials and hashes.

    Output format:
        [*] Dumping local SAM hashes
        Administrator:500:aad3b435b51404eeaad3b435b51404ee:31d6cfe0d16ae931b73c59d7e0c089c0:::
        Guest:501:aad3b435b51404eeaad3b435b51404ee:31d6cfe0d16ae931b73c59d7e0c089c0:::
        ...
    """
    credentials = []
    hashes = []
    tickets = []
    lsa_secrets = []
    kerberos_keys = []

    try:
        with open(log_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Parse NTLM hashes with multiple format support
        # Format 1: username:RID:LM:NT::: (standard secretsdump)
        # Format 2: username:RID:LM:NT:: (without trailing colon)
        # Format 3: DOMAIN\username:RID:LM:NT::: (with domain prefix)
        # Format 4: username:$NT$hash (simplified format)

        # Standard format with 32-char hashes and trailing colons
        hash_patterns = [
            r"([^:\s\\]+):(\d+):([0-9a-fA-F]{32}):([0-9a-fA-F]{32}):::?",  # Standard
            r"([^:\s]+)\\([^:\s]+):(\d+):([0-9a-fA-F]{32}):([0-9a-fA-F]{32}):::?",  # Domain\user
        ]

        seen_hashes = set()  # Deduplicate hashes
        for pattern in hash_patterns:
            for match in re.finditer(pattern, content):
                groups = match.groups()
                if len(groups) == 4:
                    username, rid, lm_hash, nt_hash = groups
                elif len(groups) == 5:
                    # Domain\username format
                    domain, username, rid, lm_hash, nt_hash = groups
                    username = f"{domain}\\{username}"
                else:
                    continue

                # Skip empty hashes (blank password indicator) - but keep Guest for completeness
                if (
                    nt_hash.lower() == "31d6cfe0d16ae931b73c59d7e0c089c0"
                    and username.lower() != "guest"
                ):
                    continue

                # Deduplicate by username:nt_hash
                hash_key = f"{username}:{nt_hash}"
                if hash_key in seen_hashes:
                    continue
                seen_hashes.add(hash_key)

                hashes.append(
                    {
                        "username": username,
                        "rid": rid,
                        "lm_hash": lm_hash,
                        "nt_hash": nt_hash,
                        "hash_type": "NTLM",
                    }
                )

        # Parse LSA secrets (DefaultPassword, etc.)
        # Format: [*] DefaultPassword
        #         (Unknown User):ROOT#123
        lsa_pattern = r"\[\*\]\s*DefaultPassword\s*\n\s*\([^)]*\):([^\n]+)"
        for match in re.finditer(lsa_pattern, content):
            password = match.group(1).strip()
            if password and not password.startswith("(null)"):
                lsa_secrets.append(
                    {"secret_type": "DefaultPassword", "value": password}
                )
                # Also add as credential
                credentials.append(
                    {
                        "domain": "",
                        "username": "(DefaultPassword)",
                        "password": password,
                        "credential_type": "lsa_secret",
                    }
                )

        # Parse Kerberos keys (AES, DES formats)
        # Format: username:aes256-cts-hmac-sha1-96:hexkey
        kerb_key_pattern = (
            r"([^:\s]+):(aes\d+-cts-hmac-sha1-\d+|des-cbc-md5):([0-9a-fA-F]+)"
        )
        for match in re.finditer(kerb_key_pattern, content):
            username, key_type, key_value = match.groups()
            kerberos_keys.append(
                {"username": username, "key_type": key_type, "key": key_value}
            )

        # Parse plaintext passwords with multiple format support
        # Format 1: DOMAIN\username:password
        # Format 2: DOMAIN\\username:password (escaped backslash)
        # Format 3: username@DOMAIN:password
        # Format 4: [*] DOMAIN\username:password (with prefix)

        plaintext_patterns = [
            r"([^\\:\s]+)[\\]+([^:\s]+):([^\n\r]+)",  # DOMAIN\user:pass
            r"([^@:\s]+)@([^:\s]+):([^\n\r]+)",  # user@DOMAIN:pass
            r"\[\*\]\s*([^\\:\s]+)[\\]+([^:\s]+):([^\n\r]+)",  # [*] DOMAIN\user:pass
        ]

        for pattern in plaintext_patterns:
            for match in re.finditer(pattern, content):
                groups = match.groups()
                if len(groups) == 3:
                    part1, part2, password = groups
                    password = password.strip()

                    # Skip null/empty passwords and hash-like values
                    if not password or password.startswith("(null)"):
                        continue
                    # Skip if password looks like a hash (32+ hex chars)
                    if re.match(r"^[0-9a-fA-F]{32,}$", password):
                        continue
                    # Skip Kerberos key formats
                    if re.match(r"^(aes\d+|des)-", password):
                        continue

                    # Determine domain/username based on pattern
                    if "@" in match.group(0):
                        username, domain = part1, part2
                    else:
                        domain, username = part1, part2

                    credentials.append(
                        {
                            "domain": domain,
                            "username": username,
                            "password": password,
                            "credential_type": "plaintext",
                        }
                    )

        # Parse Kerberos tickets (format: username:$krb5...)
        krb_pattern = r"([^:\s]+):(\$krb5[^\s]+)"
        for match in re.finditer(krb_pattern, content):
            username, krb_key = match.groups()

            tickets.append(
                {"username": username, "ticket": krb_key, "ticket_type": "Kerberos"}
            )

    except FileNotFoundError:
        return {
            "tool": "secretsdump",
            "target": target,
            "error": "Log file not found",
            "credentials_count": 0,
            "hashes_count": 0,
        }
    except Exception as e:
        return {
            "tool": "secretsdump",
            "target": target,
            "error": str(e),
            "credentials_count": 0,
            "hashes_count": 0,
        }

    return {
        "tool": "secretsdump",
        "target": target,
        "credentials_count": len(credentials),
        "hashes_count": len(hashes),
        "tickets_count": len(tickets),
        "lsa_secrets_count": len(lsa_secrets),
        "kerberos_keys_count": len(kerberos_keys),
        "credentials": credentials,
        "hashes": hashes,
        "tickets": tickets,
        "lsa_secrets": lsa_secrets,
        "kerberos_keys": kerberos_keys,
    }


def parse_getnpusers(log_path: str, target: str) -> Dict[str, Any]:
    """
    Parse GetNPUsers output for AS-REP roastable hashes.

    Output format:
        $krb5asrep$23$user@DOMAIN:hash...
    """
    hashes = []

    try:
        with open(log_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Parse AS-REP hashes with multiple format support
        # Format 1: $krb5asrep$23$user@DOMAIN:hash (etype 23)
        # Format 2: $krb5asrep$18$user@DOMAIN:hash (etype 18)
        # Format 3: $krb5asrep$user@DOMAIN:hash (no etype)
        # Format 4: username:$krb5asrep... (username:hash format)

        # Full format with etype: $krb5asrep$ETYPE$user@DOMAIN:hash
        hash_patterns = [
            r"\$krb5asrep\$(\d+)\$([^@]+)@([^:]+):([^\s]+)",  # With etype
            r"\$krb5asrep\$([^@$]+)@([^:]+):([^\s]+)",  # Without etype
        ]

        for pattern in hash_patterns:
            for match in re.finditer(pattern, content):
                groups = match.groups()
                if len(groups) == 4:
                    etype, username, domain, hash_value = groups
                    full_hash = f"$krb5asrep${etype}${username}@{domain}:{hash_value}"
                elif len(groups) == 3:
                    username, domain, hash_value = groups
                    etype = "23"  # Default etype
                    full_hash = f"$krb5asrep${username}@{domain}:{hash_value}"
                else:
                    continue

                hashes.append(
                    {
                        "username": username,
                        "domain": domain,
                        "hash": full_hash,
                        "hash_type": "AS-REP",
                        "etype": etype,
                        "crackable": True,
                    }
                )

        # Also check for simple format (username:hash)
        if not hashes:
            simple_pattern = r"^([^:\s]+):(\$krb5asrep[^\s]+)"
            for match in re.finditer(simple_pattern, content, re.MULTILINE):
                username, hash_value = match.groups()

                hashes.append(
                    {
                        "username": username,
                        "hash": hash_value,
                        "hash_type": "AS-REP",
                        "crackable": True,
                    }
                )

    except FileNotFoundError:
        return {
            "tool": "GetNPUsers",
            "target": target,
            "error": "Log file not found",
            "hashes_count": 0,
        }
    except Exception as e:
        return {
            "tool": "GetNPUsers",
            "target": target,
            "error": str(e),
            "hashes_count": 0,
        }

    return {
        "tool": "GetNPUsers",
        "target": target,
        "hashes_count": len(hashes),
        "hashes": hashes,
        "asrep_hashes": hashes,  # For auto-chaining to hashcat
    }


def parse_psexec(log_path: str, target: str) -> Dict[str, Any]:
    """
    Parse psexec output for command execution results.
    """
    output_lines = []
    success = False

    try:
        with open(log_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Check for successful connection with multiple indicators
        # Use simple string matching for literal strings, regex for patterns
        literal_indicators = [
            "[*] Requesting shares on",
            "[*] Uploading",
            "[*] Opening SVCManager",
            "[*] Starting service",
            "C:\\Windows\\system32>",
            "C:\\WINDOWS\\system32>",
            "Microsoft Windows",
            "nt authority\\system",
            "ErrorCode: 0",
        ]

        for indicator in literal_indicators:
            if indicator.lower() in content.lower():
                success = True
                break

        # Extract command output (everything after the prompt)
        output_lines = [line for line in content.split("\n") if line.strip()]

    except FileNotFoundError:
        return {
            "tool": "psexec",
            "target": target,
            "error": "Log file not found",
            "success": False,
        }
    except Exception as e:
        return {"tool": "psexec", "target": target, "error": str(e), "success": False}

    return {
        "tool": "psexec",
        "target": target,
        "success": success,
        "output_lines": len(output_lines),
        "output": "\n".join(output_lines),
    }


def parse_smbclient(log_path: str, target: str) -> Dict[str, Any]:
    """
    Parse smbclient output for file listings and operations.
    """
    shares = []
    files = []
    success = False

    try:
        with open(log_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Check for successful connection
        if "Type Client" in content or "smb:" in content:
            success = True

        # Parse share listings
        share_pattern = r"^\s*([A-Z$]+)\s+(Disk|Printer|Device|IPC)\s*(.*)$"
        for match in re.finditer(share_pattern, content, re.MULTILINE):
            share_name, share_type, comment = match.groups()

            shares.append(
                {
                    "name": share_name.strip(),
                    "type": share_type.strip(),
                    "comment": comment.strip(),
                }
            )

        # Parse file listings (basic)
        file_pattern = r"^\s*([^\s]+)\s+([DAH]+)\s+(\d+)\s+"
        for match in re.finditer(file_pattern, content, re.MULTILINE):
            filename, attributes, size = match.groups()

            if filename not in [".", ".."]:
                files.append(
                    {"name": filename, "attributes": attributes, "size": int(size)}
                )

    except FileNotFoundError:
        return {
            "tool": "smbclient",
            "target": target,
            "error": "Log file not found",
            "success": False,
        }
    except Exception as e:
        return {
            "tool": "smbclient",
            "target": target,
            "error": str(e),
            "success": False,
        }

    return {
        "tool": "smbclient",
        "target": target,
        "success": success,
        "shares_count": len(shares),
        "files_count": len(files),
        "shares": shares,
        "files": files,
    }


def parse_impacket(log_path: str, target: str, tool: str) -> Dict[str, Any]:
    """
    Unified parser that routes to specific Impacket tool parsers.

    Args:
        log_path: Path to tool output file
        target: Target host/domain
        tool: Specific Impacket tool name

    Returns:
        Parsed results dictionary
    """
    tool_lower = tool.lower().replace("impacket-", "")

    if "secretsdump" in tool_lower:
        return parse_secretsdump(log_path, target)
    elif "getnpusers" in tool_lower:
        return parse_getnpusers(log_path, target)
    elif "psexec" in tool_lower:
        return parse_psexec(log_path, target)
    elif "smbclient" in tool_lower:
        return parse_smbclient(log_path, target)
    else:
        return {
            "tool": tool,
            "target": target,
            "error": f"Unknown Impacket tool: {tool}",
        }
