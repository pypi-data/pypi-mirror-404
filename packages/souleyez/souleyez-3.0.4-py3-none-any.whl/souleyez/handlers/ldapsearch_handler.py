#!/usr/bin/env python3
"""
Handler for ldapsearch LDAP enumeration tool.
"""

import logging
import os
import re
from typing import Any, Dict, Optional

import click

from souleyez.handlers.base import BaseToolHandler

logger = logging.getLogger(__name__)

STATUS_DONE = "done"
STATUS_ERROR = "error"
STATUS_WARNING = "warning"
STATUS_NO_RESULTS = "no_results"


class LdapsearchHandler(BaseToolHandler):
    """Handler for ldapsearch LDAP queries."""

    tool_name = "ldapsearch"
    display_name = "ldapsearch"

    has_error_handler = True
    has_warning_handler = True
    has_no_results_handler = True
    has_done_handler = True

    # Patterns indicating successful LDAP enumeration
    SUCCESS_PATTERNS = [
        r"namingContexts:",
        r"dn:\s+\S+",
        r"objectClass:",
        r"DC=\w+",
        r"CN=\w+",
        r"# numEntries:\s*[1-9]",
        r"result:\s*0\s+Success",
    ]

    # Patterns indicating errors
    ERROR_PATTERNS = [
        (r"Can\'t contact LDAP server", "LDAP server unreachable"),
        (r"Invalid credentials", "Authentication failed"),
        (r"No such object", "Base DN not found"),
        (r"Operations error", "LDAP operations error"),
        (r"Confidentiality required", "TLS/SSL required"),
    ]

    def parse_job(
        self,
        engagement_id: int,
        log_path: str,
        job: Dict[str, Any],
        host_manager: Optional[Any] = None,
        findings_manager: Optional[Any] = None,
        credentials_manager: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """Parse ldapsearch results."""
        try:
            target = job.get("target", "")

            if not log_path or not os.path.exists(log_path):
                return {
                    "tool": "ldapsearch",
                    "status": STATUS_ERROR,
                    "error": "Log file not found",
                }

            with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                log_content = f.read()

            # Check exit code first - non-zero means error
            exit_code_match = re.search(r"Exit Code:\s*(\d+)", log_content)
            if exit_code_match:
                exit_code = int(exit_code_match.group(1))
                if exit_code != 0:
                    # Special case: "successful bind must be completed" means anonymous access blocked
                    # This is not a hard error - kerbrute or authenticated ldapsearch will handle it
                    # Normalize LDIF line continuations (newline + space) before checking
                    normalized_content = re.sub(r"\n ", "", log_content.lower())
                    if (
                        "successful bind must be completed" in normalized_content
                        or "bind must be completed" in normalized_content
                        or "000004dc" in normalized_content
                    ):  # LDAP error code for anonymous blocked
                        return {
                            "tool": "ldapsearch",
                            "status": STATUS_NO_RESULTS,
                            "target": target,
                            "note": "Anonymous bind not allowed - authentication required",
                        }

                    # Map common LDAP exit codes to error messages
                    ldap_errors = {
                        32: "No such object (invalid base DN)",
                        49: "Invalid credentials",
                        1: "Operations error",
                        2: "Protocol error",
                        52: "Server unavailable",
                    }
                    error_msg = ldap_errors.get(
                        exit_code, f"LDAP error (exit code {exit_code})"
                    )
                    return {
                        "tool": "ldapsearch",
                        "status": STATUS_ERROR,
                        "target": target,
                        "error": error_msg,
                    }

            # Check for errors in output
            for pattern, error_msg in self.ERROR_PATTERNS:
                if re.search(pattern, log_content, re.IGNORECASE):
                    return {
                        "tool": "ldapsearch",
                        "status": STATUS_ERROR,
                        "target": target,
                        "error": error_msg,
                    }

            # Check for success patterns
            success_found = False
            naming_contexts = []
            entries_count = 0

            for pattern in self.SUCCESS_PATTERNS:
                if re.search(pattern, log_content, re.IGNORECASE):
                    success_found = True
                    break

            # Extract naming contexts (AD domain info)
            nc_matches = re.findall(r"namingContexts:\s*(.+)", log_content)
            naming_contexts = [nc.strip() for nc in nc_matches]

            # Extract entry count
            entries_match = re.search(r"# numEntries:\s*(\d+)", log_content)
            if entries_match:
                entries_count = int(entries_match.group(1))

            # Check for "result: 0 Success" which indicates successful query
            if "result: 0 Success" in log_content:
                success_found = True

            if success_found or naming_contexts or entries_count > 0:
                domains = self._extract_domains(naming_contexts)
                # Extract base DN for chaining (e.g., "DC=baby,DC=vl")
                base_dn = self._extract_base_dn(naming_contexts)

                # Parse user entries if this is a user enumeration query
                users = self._parse_user_entries(log_content)
                usernames = [
                    u.get("sAMAccountName", "")
                    for u in users
                    if u.get("sAMAccountName")
                ]

                # Check for passwords in descriptions
                credentials_found = []
                for user in users:
                    description = user.get("description", "")
                    if description:
                        password = self._extract_password_from_description(description)
                        if password:
                            credentials_found.append(
                                {
                                    "username": user.get("sAMAccountName", ""),
                                    "password": password,
                                    "source": "ldap_description",
                                }
                            )
                            logger.warning(
                                f"CREDENTIAL FOUND in LDAP description: "
                                f"{user.get('sAMAccountName')} - check description field"
                            )

                # Store credentials if found AND store enumerated users
                if (credentials_found or usernames) and credentials_manager:
                    if host_manager is None:
                        from souleyez.storage.hosts import HostManager

                        host_manager = HostManager()

                    host = host_manager.get_host_by_ip(engagement_id, target)
                    if host:
                        # Store passwords found in descriptions
                        for cred in credentials_found:
                            credentials_manager.add_credential(
                                engagement_id=engagement_id,
                                host_id=host["id"],
                                username=cred["username"],
                                password=cred["password"],
                                service="ldap",
                                credential_type="password",
                                tool="ldapsearch",
                                status="potential",
                                notes="Found in LDAP user description field",
                            )

                        # Store enumerated usernames (without passwords)
                        usernames_stored = 0
                        for username in usernames:
                            # Skip if already stored with a password
                            already_has_cred = any(
                                c["username"] == username for c in credentials_found
                            )
                            if not already_has_cred:
                                credentials_manager.add_credential(
                                    engagement_id=engagement_id,
                                    host_id=host["id"],
                                    username=username,
                                    password="",
                                    service="ldap",
                                    credential_type="ldap_user",
                                    tool="ldapsearch",
                                    status="enumerated",
                                    notes="Enumerated via LDAP",
                                )
                                usernames_stored += 1
                        if usernames_stored > 0:
                            logger.info(
                                f"Stored {usernames_stored} enumerated LDAP usernames"
                            )

                logger.info(
                    f"ldapsearch parse complete: {len(naming_contexts)} naming contexts, "
                    f"{len(domains)} domains, {len(users)} users, {len(credentials_found)} creds, base_dn={base_dn}"
                )
                return {
                    "tool": "ldapsearch",
                    "status": STATUS_DONE,
                    "target": target,
                    "naming_contexts": naming_contexts,
                    "entries_count": entries_count,
                    "domains": domains,
                    "base_dn": base_dn,  # For LDAP user enumeration chains
                    "users": usernames,
                    "users_found": len(users),
                    "credentials_found": credentials_found,
                }

            return {"tool": "ldapsearch", "status": STATUS_NO_RESULTS, "target": target}

        except Exception as e:
            logger.error(f"Error parsing ldapsearch job: {e}")
            return {"tool": "ldapsearch", "status": STATUS_ERROR, "error": str(e)}

    def _extract_base_dn(self, naming_contexts):
        """Extract the base DN for user enumeration (e.g., 'DC=baby,DC=vl').

        Returns the primary domain DN, filtering out zone-specific contexts.
        """
        # Zone prefixes to skip
        zone_prefixes = {"domaindnszones", "forestdnszones", "configuration", "schema"}

        for nc in naming_contexts:
            nc = nc.strip()
            # Match patterns like DC=active,DC=htb
            dc_match = re.findall(r"DC=([^,]+)", nc, re.IGNORECASE)
            if dc_match and len(dc_match) >= 2:
                # Skip if first component is a zone prefix
                if dc_match[0].lower() in zone_prefixes:
                    continue
                # This is the primary domain DN (e.g., DC=baby,DC=vl)
                return nc

        return ""

    def _extract_domains(self, naming_contexts):
        """Extract domain names from naming contexts like DC=active,DC=htb.

        Filters out zone-specific naming contexts (DomainDnsZones, ForestDnsZones)
        to extract the actual AD domain name.
        """
        domains = []
        seen_domains = set()

        # Zone prefixes to skip (these are subzones, not the main domain)
        zone_prefixes = {"domaindnszones", "forestdnszones", "configuration", "schema"}

        for nc in naming_contexts:
            # Match patterns like DC=active,DC=htb
            dc_match = re.findall(r"DC=([^,]+)", nc, re.IGNORECASE)
            if dc_match and len(dc_match) >= 2:
                # Skip if first component is a zone prefix
                if dc_match[0].lower() in zone_prefixes:
                    # Use remaining components as domain
                    dc_match = dc_match[1:]
                    if len(dc_match) < 2:
                        continue

                domain = ".".join(dc_match)
                domain_lower = domain.lower()

                if domain_lower not in seen_domains:
                    seen_domains.add(domain_lower)
                    domains.append({"domain": domain, "source": "ldapsearch"})
                    logger.info(f"Extracted AD domain from LDAP: {domain}")

        if domains:
            logger.info(
                f"ldapsearch found {len(domains)} domain(s): {[d['domain'] for d in domains]}"
            )
        else:
            logger.debug(
                f"ldapsearch: No domains extracted from naming contexts: {naming_contexts}"
            )

        return domains

    def display_done(
        self,
        job: Dict[str, Any],
        log_path: str,
        show_all: bool = False,
        show_passwords: bool = False,
    ) -> None:
        """Display successful ldapsearch results."""
        click.echo()
        click.echo(click.style("=" * 70, fg="green"))
        click.echo(click.style("LDAP ENUMERATION SUCCESSFUL", fg="green", bold=True))
        click.echo(click.style("=" * 70, fg="green"))
        click.echo()

        try:
            with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                log_content = f.read()

            # Show naming contexts (domain structure query)
            nc_matches = re.findall(r"namingContexts:\s*(.+)", log_content)
            if nc_matches:
                click.echo(
                    click.style("  NAMING CONTEXTS (Domain Structure)", bold=True)
                )
                for nc in nc_matches:
                    click.echo(f"    {nc.strip()}")
                click.echo()

            # Parse user enumeration results (sAMAccountName, description, memberOf)
            users = self._parse_user_entries(log_content)
            if users:
                click.echo(
                    click.style(f"  USERS FOUND ({len(users)})", bold=True, fg="cyan")
                )
                click.echo()

                # Check for passwords in descriptions
                password_hints = []
                for user in users:
                    username = user.get("sAMAccountName", "Unknown")
                    description = user.get("description", "")
                    groups = user.get("memberOf", [])
                    ou = user.get("ou", "")

                    # Display user
                    click.echo(f"    {click.style(username, bold=True)}")
                    if ou:
                        click.echo(f"      OU: {ou}")
                    if groups:
                        click.echo(f"      Groups: {', '.join(groups)}")

                    # Check for password hints in description
                    if description:
                        # Detect potential passwords
                        password_keywords = [
                            "password",
                            "pass",
                            "pwd",
                            "credential",
                            "secret",
                            "initial",
                        ]
                        has_password_hint = any(
                            kw in description.lower() for kw in password_keywords
                        )

                        if has_password_hint:
                            click.echo(
                                click.style(
                                    f"      Description: {description}",
                                    fg="red",
                                    bold=True,
                                )
                            )
                            click.echo(
                                click.style(
                                    "      ^^^ POTENTIAL PASSWORD IN DESCRIPTION!",
                                    fg="red",
                                    bold=True,
                                )
                            )
                            password_hints.append(
                                {"user": username, "description": description}
                            )
                        else:
                            click.echo(f"      Description: {description}")
                    click.echo()

                # Summary of password findings
                if password_hints:
                    click.echo()
                    click.echo(click.style("=" * 70, fg="red"))
                    click.echo(
                        click.style(
                            "  CREDENTIALS FOUND IN DESCRIPTIONS!", fg="red", bold=True
                        )
                    )
                    click.echo(click.style("=" * 70, fg="red"))
                    for hint in password_hints:
                        click.echo(f"    User: {click.style(hint['user'], bold=True)}")
                        click.echo(
                            f"    Desc: {click.style(hint['description'], fg='red')}"
                        )
                        # Try to extract actual password
                        password = self._extract_password_from_description(
                            hint["description"]
                        )
                        if password:
                            click.echo(
                                f"    Password: {click.style(password, fg='red', bold=True)}"
                            )
                        click.echo()

            # Show entry count
            entries_match = re.search(r"# numEntries:\s*(\d+)", log_content)
            if entries_match and not users:
                click.echo(f"  Entries found: {entries_match.group(1)}")
                click.echo()

        except Exception as e:
            click.echo(f"  Error reading log: {e}")
            logger.debug(f"Error in display_done: {e}")

        click.echo()

    def _parse_user_entries(self, log_content: str) -> list:
        """Parse user entries from ldapsearch output."""
        users = []
        current_user = {}

        for line in log_content.split("\n"):
            line = line.strip()

            # New entry starts with "dn:"
            if line.startswith("dn:"):
                # Save previous entry if it's not explicitly a group
                # Default to including (is_group=False) if no objectClass info
                if current_user and current_user.get("sAMAccountName"):
                    if not current_user.get("is_group", False):
                        users.append(current_user)
                current_user = {}
                # Extract OU from DN
                ou_match = re.search(r"OU=([^,]+)", line, re.IGNORECASE)
                if ou_match:
                    current_user["ou"] = ou_match.group(1)
                # Extract CN from DN as potential username (for broader queries)
                # DN format: CN=Caroline Robinson,OU=it,DC=baby,DC=vl
                cn_match = re.search(r"dn:\s*CN=([^,]+)", line, re.IGNORECASE)
                if cn_match:
                    cn_name = cn_match.group(1).strip()
                    # Convert "Caroline Robinson" to "Caroline.Robinson" format
                    # Skip non-user entries (groups, OUs, etc.)
                    if " " in cn_name and not cn_name.lower().startswith(
                        (
                            "domain ",
                            "enterprise ",
                            "schema ",
                            "cert ",
                            "group ",
                            "read-",
                            "allowed ",
                            "denied ",
                            "protected ",
                            "key ",
                            "dns",
                            "ras ",
                            "cloneable ",
                        )
                    ):
                        current_user["cn_username"] = cn_name.replace(" ", ".")

            elif line.startswith("objectClass:"):
                obj_class = line.split(":", 1)[1].strip().lower()
                # Mark as group if objectClass is group (blacklist approach)
                if obj_class == "group":
                    current_user["is_group"] = True

            elif line.startswith("sAMAccountName:"):
                sam = line.split(":", 1)[1].strip()
                current_user["sAMAccountName"] = sam
                # Filter out obvious group names by sAMAccountName pattern
                sam_lower = sam.lower()
                if sam_lower in (
                    "guest",
                    "domain users",
                    "domain computers",
                    "domain guests",
                    "domain admins",
                    "enterprise admins",
                    "schema admins",
                    "cert publishers",
                    "group policy creator owners",
                    "ras and ias servers",
                    "allowed rodc password replication group",
                    "denied rodc password replication group",
                    "read-only domain controllers",
                    "enterprise read-only domain controllers",
                    "cloneable domain controllers",
                    "protected users",
                    "dnsadmins",
                    "dnsupdateproxy",
                ):
                    current_user["is_group"] = True

            elif line.startswith("description:"):
                current_user["description"] = line.split(":", 1)[1].strip()

            elif line.startswith("memberOf:"):
                if "memberOf" not in current_user:
                    current_user["memberOf"] = []
                # Extract CN from memberOf
                cn_match = re.search(r"CN=([^,]+)", line, re.IGNORECASE)
                if cn_match:
                    current_user["memberOf"].append(cn_match.group(1))

        # Don't forget last user - only if it's not a group
        if current_user and current_user.get("sAMAccountName"):
            if not current_user.get("is_group", False):
                users.append(current_user)

        # Second pass: add users found only via CN (no sAMAccountName returned)
        # This catches users from broader queries like (objectClass=*)
        current_user = {}
        for line in log_content.split("\n"):
            line = line.strip()
            if line.startswith("dn:"):
                if (
                    current_user.get("cn_username")
                    and not current_user.get("sAMAccountName")
                    and not current_user.get("is_group", False)
                ):  # Default to user if no objectClass
                    # Check if we already have this user
                    existing = [
                        u
                        for u in users
                        if u.get("sAMAccountName") == current_user.get("cn_username")
                    ]
                    if not existing:
                        current_user["sAMAccountName"] = current_user["cn_username"]
                        users.append(current_user)
                current_user = {}
                cn_match = re.search(r"dn:\s*CN=([^,]+)", line, re.IGNORECASE)
                ou_match = re.search(r"OU=([^,]+)", line, re.IGNORECASE)
                if cn_match:
                    cn_name = cn_match.group(1).strip()
                    if " " in cn_name and not cn_name.lower().startswith(
                        (
                            "domain ",
                            "enterprise ",
                            "schema ",
                            "cert ",
                            "group ",
                            "read-",
                            "allowed ",
                            "denied ",
                            "protected ",
                            "key ",
                            "dns",
                            "ras ",
                            "cloneable ",
                        )
                    ):
                        current_user["cn_username"] = cn_name.replace(" ", ".")
                if ou_match:
                    current_user["ou"] = ou_match.group(1)
            elif line.startswith("objectClass:"):
                obj_class = line.split(":", 1)[1].strip().lower()
                # Blacklist groups - mark as group if objectClass is group
                if obj_class == "group":
                    current_user["is_group"] = True
            elif line.startswith("sAMAccountName:"):
                current_user["sAMAccountName"] = line.split(":", 1)[1].strip()

        # Last entry from second pass
        if current_user.get("cn_username") and not current_user.get("sAMAccountName"):
            if not current_user.get(
                "is_group", False
            ):  # Default to user if no objectClass
                existing = [
                    u
                    for u in users
                    if u.get("sAMAccountName") == current_user.get("cn_username")
                ]
                if not existing:
                    current_user["sAMAccountName"] = current_user["cn_username"]
                    users.append(current_user)

        return users

    def _extract_password_from_description(self, description: str) -> str:
        """Try to extract password from description text."""
        # Common patterns for passwords in descriptions
        # Order matters - more specific patterns first
        patterns = [
            # Phrases with "to" or "is" before the password
            r"password\s+(?:is|to|=)\s*[:\s]*(\S+)",
            r"set\s+.*?password\s+(?:to|is|=)\s*(\S+)",
            r"initial\s+password\s+(?:to|is|=)?\s*[:\s]*(\S+)",
            # Direct assignment patterns
            r"password[:\s]*=\s*(\S+)",
            r"pwd[:\s]*[:=]\s*(\S+)",
            r"pass[:\s]*[:=]\s*(\S+)",
            r"credential[:\s]*[:=]\s*(\S+)",
            # Fallback: password followed by colon then value
            r"password:\s*(\S+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                # Keep ! in passwords (common special char), only strip trailing periods/commas
                password = match.group(1).rstrip(".,")
                # Skip if captured word is a common filler (to, is, the, etc.)
                if password.lower() in ["to", "is", "the", "a", "an", "set", "as"]:
                    continue
                return password

        return ""

    def display_error(
        self,
        job: Dict[str, Any],
        log_path: str,
        show_all: bool = False,
    ) -> None:
        """Display ldapsearch error."""
        click.echo()
        click.echo(click.style("=" * 70, fg="red"))
        click.echo(click.style("LDAP QUERY FAILED", fg="red", bold=True))
        click.echo(click.style("=" * 70, fg="red"))
        click.echo()

        try:
            with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                log_content = f.read()

            for pattern, error_msg in self.ERROR_PATTERNS:
                if re.search(pattern, log_content, re.IGNORECASE):
                    click.echo(f"  Error: {error_msg}")
                    break
            else:
                click.echo("  LDAP query failed - check log for details")

        except Exception:
            click.echo("  Could not read error details")

        click.echo()

    def display_warning(
        self,
        job: Dict[str, Any],
        log_path: str,
        show_all: bool = False,
    ) -> None:
        """Display ldapsearch warning."""
        click.echo()
        click.echo(click.style("=" * 70, fg="yellow"))
        click.echo(click.style("LDAP QUERY - PARTIAL RESULTS", fg="yellow", bold=True))
        click.echo(click.style("=" * 70, fg="yellow"))
        click.echo()
        click.echo("  Query completed with warnings - may need authentication")
        click.echo()

    def display_no_results(
        self,
        job: Dict[str, Any],
        log_path: str,
        show_all: bool = False,
    ) -> None:
        """Display ldapsearch no results."""
        click.echo()
        click.echo(click.style("=" * 70, fg="yellow"))
        click.echo(click.style("LDAP QUERY - NO DATA RETURNED", fg="yellow", bold=True))
        click.echo(click.style("=" * 70, fg="yellow"))
        click.echo()

        # Check if this was an auth-required case
        parse_result = job.get("parse_result", {})
        note = parse_result.get("note", "")
        if "authentication required" in note.lower():
            click.echo("  Anonymous LDAP bind blocked - authentication required.")
            click.echo()
            click.echo(click.style("  Next steps:", dim=True))
            click.echo("    - kerbrute user enumeration (auto-chained)")
            click.echo(
                "    - Once valid credentials found, authenticated LDAP will run"
            )
        else:
            click.echo("  The LDAP query returned no entries.")
            click.echo()
            click.echo(click.style("  Tips:", dim=True))
            click.echo("    - Try a different base DN")
            click.echo("    - Anonymous binds may be disabled")
        click.echo("    - Try with credentials: -D 'user@domain' -W")
        click.echo()
