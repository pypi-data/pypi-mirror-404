#!/usr/bin/env python3
"""
SQLMap handler.

Consolidates parsing and display logic for SQLMap SQL injection scanner jobs.
"""

import logging
import os
import re
from typing import Any, Dict, Optional
from urllib.parse import urlparse

import click

from souleyez.engine.job_status import STATUS_DONE, STATUS_ERROR, STATUS_NO_RESULTS
from souleyez.handlers.base import BaseToolHandler

logger = logging.getLogger(__name__)


class SQLMapHandler(BaseToolHandler):
    """Handler for SQLMap SQL injection scanner jobs."""

    tool_name = "sqlmap"
    display_name = "SQLMap"

    # All handlers enabled
    has_error_handler = True
    has_warning_handler = True
    has_no_results_handler = True
    has_done_handler = True

    def parse_job(
        self,
        engagement_id: int,
        log_path: str,
        job: Dict[str, Any],
        host_manager: Optional[Any] = None,
        findings_manager: Optional[Any] = None,
        credentials_manager: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        Parse SQLMap job results.

        Extracts SQL injection vulnerabilities, databases, tables, and dumped data.
        """
        try:
            import socket

            from souleyez.engine.result_handler import detect_tool_error
            from souleyez.parsers.sqlmap_parser import (
                get_sqli_stats,
                parse_sqlmap_output,
            )
            from souleyez.storage.sqlmap_data import SQLMapDataManager

            # Import managers if not provided
            if host_manager is None:
                from souleyez.storage.hosts import HostManager

                host_manager = HostManager()
            if findings_manager is None:
                from souleyez.storage.findings import FindingsManager

                findings_manager = FindingsManager()
            if credentials_manager is None:
                from souleyez.storage.credentials import CredentialsManager

                credentials_manager = CredentialsManager()

            target = job.get("target", "")

            # Read log file
            with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                output = f.read()

            parsed = parse_sqlmap_output(output, target)
            stats = get_sqli_stats(parsed)

            # Get or create host from target URL
            host_id = None
            target_port = None

            if parsed.get("target_url"):
                parsed_url = urlparse(parsed["target_url"])
                hostname = parsed_url.hostname
                target_port = parsed_url.port or (
                    443 if parsed_url.scheme == "https" else 80
                )

                if hostname:
                    is_ip = re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", hostname)

                    if is_ip:
                        host = host_manager.get_host_by_ip(engagement_id, hostname)
                        if host:
                            host_id = host["id"]
                        else:
                            host_id = host_manager.add_or_update_host(
                                engagement_id, {"ip": hostname, "status": "up"}
                            )
                    else:
                        # Try to match by hostname
                        hosts = host_manager.list_hosts(engagement_id)
                        for h in hosts:
                            if (
                                h.get("hostname") == hostname
                                or h.get("ip") == hostname
                                or h.get("ip_address") == hostname
                            ):
                                host_id = h["id"]
                                break

                        if not host_id:
                            try:
                                ip_address = socket.gethostbyname(hostname)
                                host_id = host_manager.add_or_update_host(
                                    engagement_id,
                                    {
                                        "ip": ip_address,
                                        "hostname": hostname,
                                        "status": "up",
                                    },
                                )
                            except (socket.gaierror, socket.herror):
                                pass

            # Store vulnerabilities as findings
            findings_added = 0

            for vuln in parsed.get("vulnerabilities", []):
                vuln_type = vuln.get("vuln_type", "unknown")
                if vuln_type == "sqli" and vuln.get("injectable"):
                    severity = "critical"
                    finding_type = "sql_injection"
                    title = f"SQL Injection in parameter '{vuln['parameter']}'"
                elif vuln_type == "xss":
                    severity = vuln.get("severity", "medium")
                    finding_type = "xss"
                    title = f"Possible XSS in parameter '{vuln['parameter']}'"
                elif vuln_type == "file_inclusion":
                    severity = vuln.get("severity", "high")
                    finding_type = "file_inclusion"
                    title = (
                        f"Possible File Inclusion in parameter '{vuln['parameter']}'"
                    )
                else:
                    severity = "medium"
                    finding_type = "web_vulnerability"
                    title = f"Vulnerability in parameter '{vuln['parameter']}'"

                description = vuln.get("description", "")
                if vuln.get("technique"):
                    description += f"\nTechnique: {vuln['technique']}"
                if vuln.get("dbms"):
                    description += f"\nDBMS: {vuln['dbms']}"

                findings_manager.add_finding(
                    engagement_id=engagement_id,
                    host_id=host_id,
                    port=target_port,
                    title=title,
                    finding_type=finding_type,
                    severity=severity,
                    description=description,
                    tool="sqlmap",
                    path=vuln.get("url"),
                )
                findings_added += 1

            # Exploitation findings - Database Enumeration
            databases = parsed.get("databases", [])
            if databases and host_id:
                dbms_info = parsed.get("dbms", "Unknown")
                db_count = len(databases)
                db_list = databases[:10]
                db_list_str = ", ".join(db_list)
                if len(databases) > 10:
                    db_list_str += f" ... and {len(databases) - 10} more"

                description = f"SQL injection was successfully exploited to enumerate {db_count} database(s).\n\n"
                description += f"DBMS: {dbms_info}\n"
                description += f"Databases: {db_list_str}"

                findings_manager.add_finding(
                    engagement_id=engagement_id,
                    host_id=host_id,
                    port=target_port,
                    title=f"SQL Injection Exploited - {db_count} Database(s) Enumerated",
                    finding_type="sql_injection_exploitation",
                    severity="critical",
                    description=description,
                    tool="sqlmap",
                    path=parsed.get("target_url"),
                )
                findings_added += 1

            # Exploitation findings - Table Enumeration
            tables = parsed.get("tables", {})
            if tables and host_id:
                total_tables = sum(len(table_list) for table_list in tables.values())
                if total_tables > 0:
                    description = f"SQL injection was exploited to enumerate {total_tables} table(s) across {len(tables)} database(s)."

                    findings_manager.add_finding(
                        engagement_id=engagement_id,
                        host_id=host_id,
                        port=target_port,
                        title=f"SQL Injection Exploited - {total_tables} Table(s) Enumerated",
                        finding_type="sql_injection_exploitation",
                        severity="high",
                        description=description,
                        tool="sqlmap",
                        path=parsed.get("target_url"),
                    )
                    findings_added += 1

            # Exploitation findings - Data Dump
            dumped_data = parsed.get("dumped_data", {})
            credentials_added = 0
            extracted_credentials = []  # Default empty list for chaining
            total_users_found = 0  # Total users in credential tables (including those without passwords)
            all_users = (
                []
            )  # All users including those without passwords (for expanded view)
            if dumped_data and host_id:
                total_rows = sum(
                    d.get("row_count", len(d.get("rows", [])))
                    for d in dumped_data.values()
                )
                table_names = list(dumped_data.keys())

                if total_rows > 0:
                    description = f"SQL injection was exploited to dump {total_rows} row(s) from {len(table_names)} table(s).\n\n"
                    description += f"Tables dumped: {', '.join(table_names[:5])}"
                    if len(table_names) > 5:
                        description += f" ... and {len(table_names) - 5} more"

                    findings_manager.add_finding(
                        engagement_id=engagement_id,
                        host_id=host_id,
                        port=target_port,
                        title=f"SQL Injection Exploited - {total_rows} Row(s) Dumped",
                        finding_type="sql_injection_exploitation",
                        severity="critical",
                        description=description,
                        tool="sqlmap",
                        path=parsed.get("target_url"),
                    )
                    findings_added += 1

                # Extract credentials from dumped data
                (
                    credentials_added,
                    extracted_credentials,
                    total_users_found,
                    all_users,
                ) = self._extract_credentials_from_dump(
                    dumped_data=dumped_data,
                    engagement_id=engagement_id,
                    host_id=host_id,
                    credentials_manager=credentials_manager,
                )

                if credentials_added > 0:
                    logger.info(
                        f"SQLMap: Extracted {credentials_added} credentials from dumped tables"
                    )

            # Store SQLMap database discoveries to SQLMapDataManager
            has_data_to_store = (
                parsed.get("databases")
                or parsed.get("tables")
                or parsed.get("dumped_data")
            )

            if host_id and has_data_to_store:
                sdm = SQLMapDataManager()
                dbms_type = parsed.get("dbms", "Unknown")

                # Store databases
                db_ids = {}
                for db_name in parsed.get("databases", []):
                    db_id = sdm.add_database(engagement_id, host_id, db_name, dbms_type)
                    if db_id:
                        db_ids[db_name] = db_id

                # Store tables
                table_ids = {}
                for db_table_key, table_list in parsed.get("tables", {}).items():
                    for table_name in table_list:
                        db_id = db_ids.get(db_table_key)
                        if not db_id and db_ids:
                            db_id = list(db_ids.values())[0]

                        if db_id:
                            table_id = sdm.add_table(db_id, table_name)
                            if table_id:
                                full_key = f"{db_table_key}.{table_name}"
                                table_ids[full_key] = table_id

                # Store columns
                for table_key, column_list in parsed.get("columns", {}).items():
                    table_id = table_ids.get(table_key)
                    if table_id:
                        columns = [{"name": col} for col in column_list]
                        sdm.add_columns(table_id, columns)

                # Store dumped data
                for data_key, dump_info in parsed.get("dumped_data", {}).items():
                    table_id = table_ids.get(data_key)

                    if not table_id and "." in data_key:
                        db_name, table_name = data_key.rsplit(".", 1)

                        db_id = db_ids.get(db_name)
                        if not db_id:
                            db_id = sdm.add_database(
                                engagement_id, host_id, db_name, dbms_type
                            )
                            if db_id:
                                db_ids[db_name] = db_id

                        if db_id:
                            row_count = dump_info.get(
                                "row_count", len(dump_info.get("rows", []))
                            )
                            table_id = sdm.add_table(db_id, table_name, row_count)
                            if table_id:
                                table_ids[data_key] = table_id

                                if dump_info.get("columns"):
                                    columns = [
                                        {"name": col} for col in dump_info["columns"]
                                    ]
                                    sdm.add_columns(table_id, columns)

                    if table_id:
                        sdm.add_dumped_data(
                            table_id,
                            dump_info.get("rows", []),
                            dump_info.get("csv_path"),
                        )

            # Check for sqlmap errors
            sqlmap_error = detect_tool_error(output, "sqlmap")

            # Determine status
            if sqlmap_error:
                status = STATUS_ERROR
            elif stats["total_vulns"] > 0 or stats["databases_found"] > 0:
                status = STATUS_DONE
            else:
                status = STATUS_NO_RESULTS

            # Build summary for job queue display
            summary_parts = []
            if stats["total_vulns"] > 0:
                summary_parts.append(f"{stats['total_vulns']} SQLi vuln(s)")
            if stats["databases_found"] > 0:
                summary_parts.append(f"{stats['databases_found']} DB(s)")
            tables_count = sum(len(t) for t in tables.values()) if tables else 0
            if tables_count > 0:
                summary_parts.append(f"{tables_count} table(s)")
            dumped_tables = stats.get("dumped_tables", 0)
            dumped_rows = stats.get("dumped_rows", 0)
            if dumped_rows > 0:
                summary_parts.append(f"{dumped_rows} row(s) dumped")
            if credentials_added > 0:
                if total_users_found > 0 and total_users_found != credentials_added:
                    summary_parts.append(
                        f"{credentials_added}/{total_users_found} creds"
                    )
                else:
                    summary_parts.append(f"{credentials_added} credential(s)")
            summary = " | ".join(summary_parts) if summary_parts else "No findings"

            return {
                "tool": "sqlmap",
                "status": status,
                "summary": summary,
                "target": target,
                "target_url": parsed.get("target_url"),
                "dbms": parsed.get("dbms"),
                "total_vulns": stats["total_vulns"],
                "sqli_confirmed": stats["sqli_confirmed"],
                "databases_found": stats["databases_found"],
                "tables_found": sum(len(t) for t in tables.values()) if tables else 0,
                "findings_added": findings_added,
                # Additional stats from parser
                "xss_possible": stats.get("xss_possible", 0),
                "fi_possible": stats.get("fi_possible", 0),
                "urls_tested": stats.get("urls_tested", 0),
                "databases": parsed.get("databases", []),
                "tables": parsed.get("tables", {}),
                "columns": parsed.get("columns", {}),
                "dumped_tables": stats.get("dumped_tables", 0),
                "dumped_rows": stats.get("dumped_rows", 0),
                "dumped_data": parsed.get("dumped_data", {}),
                # CRITICAL: Chaining flags for auto-chain rules
                "sql_injection_confirmed": parsed.get("sql_injection_confirmed", False),
                "injectable_parameter": parsed.get("injectable_parameter", ""),
                "injectable_url": parsed.get("injectable_url", target),
                "injectable_post_data": parsed.get("injectable_post_data", ""),
                "injectable_method": parsed.get("injectable_method", "GET"),
                "all_injection_points": parsed.get("all_injection_points", []),
                "databases_enumerated": len(parsed.get("databases", [])) > 0,
                "tables_enumerated": len(parsed.get("tables", {})) > 0,
                "columns_enumerated": len(parsed.get("columns", {})) > 0,
                # Post-exploitation flags for advanced chaining
                "is_dba": parsed.get("is_dba", False),
                "privileges": parsed.get("privileges", []),
                "current_user": parsed.get("current_user"),
                "file_read_success": parsed.get("file_read_success", False),
                "os_command_success": parsed.get("os_command_success", False),
                # Credentials flag for cross-tool chaining
                "credentials_dumped": credentials_added > 0,
                "credentials_count": credentials_added,
                "total_users_count": total_users_found,  # All users found (including those without passwords)
                "credentials": extracted_credentials,  # For direct chaining without DB lookup
                "all_users": all_users,  # All users including those without passwords (for expanded view)
            }

        except Exception as e:
            logger.error(f"Error parsing sqlmap job: {e}")
            return {"error": str(e)}

    def _extract_credentials_from_dump(
        self,
        dumped_data: Dict[str, Any],
        engagement_id: int,
        host_id: int,
        credentials_manager: Any,
    ) -> tuple:
        """
        Extract credentials from SQLMap dumped data.

        Args:
            dumped_data: Dict of {table_key: {rows, columns, row_count, csv_path}}
            engagement_id: Engagement ID
            host_id: Host ID
            credentials_manager: CredentialsManager instance

        Returns:
            tuple: (count of credentials added, list of credential dicts, total users count)
        """
        from souleyez.intelligence.sensitive_tables import is_sensitive_table

        credentials_added = 0
        credentials_list = []
        all_users_list = []  # All users including those without passwords
        total_users = 0  # Track all users, not just those with passwords

        for table_key, data_info in dumped_data.items():
            # Parse table name
            parts = table_key.split(".")
            table_name = parts[-1]

            # Check if this is a credentials table
            is_sensitive, category, priority = is_sensitive_table(table_name)

            if category != "credentials":
                continue  # Only extract from credential tables

            rows = data_info.get("rows", [])
            columns = data_info.get("columns", [])

            if not rows or not columns:
                continue

            # Find username and password columns
            username_col = None
            password_col = None

            username_patterns = [
                "username",
                "uname",
                "user_name",
                "login",
                "account",
                "email",
                "user",
            ]
            password_patterns = [
                "password",
                "passwd",
                "pass",
                "pwd",
                "hash",
                "pwd_hash",
                "password_hash",
            ]
            id_columns = ["id", "user_id", "userid", "account_id", "user_fk"]

            # Try EXACT matches first for username
            for pattern in username_patterns:
                for col in columns:
                    if col.lower() == pattern and col.lower() not in id_columns:
                        username_col = col
                        break
                if username_col:
                    break

            # Fall back to SUBSTRING matches for username
            if not username_col:
                for pattern in username_patterns:
                    for col in columns:
                        if pattern in col.lower() and col.lower() not in id_columns:
                            username_col = col
                            break
                    if username_col:
                        break

            # Try EXACT matches first for password
            for pattern in password_patterns:
                for col in columns:
                    if col.lower() == pattern and col.lower() not in id_columns:
                        password_col = col
                        break
                if password_col:
                    break

            # Fall back to SUBSTRING matches for password
            if not password_col:
                for pattern in password_patterns:
                    for col in columns:
                        if pattern in col.lower() and col.lower() not in id_columns:
                            password_col = col
                            break
                    if password_col:
                        break

            if not username_col or not password_col:
                logger.debug(f"Skipping {table_key}: missing username/password columns")
                continue

            # Extract credentials from rows
            for row in rows:
                username = str(row.get(username_col, "")).strip()
                password = str(row.get(password_col, "")).strip()

                # Handle SQLMap's <blank> placeholder for NULL/empty values
                if username in ["<blank>", "NULL", "None", ""]:
                    email = str(row.get("email", "")).strip()
                    if email and email not in ["<blank>", "NULL", "None", ""]:
                        username = email
                    else:
                        continue

                # Validate username is not scanner garbage / injection payload
                if not self._is_valid_username(username):
                    logger.debug(
                        f"Skipping invalid username (scanner artifact): {username[:50]}..."
                    )
                    continue

                # Count this as a valid user (has username/email)
                total_users += 1

                # Check if user has a password
                has_password = password and password not in [
                    "NULL",
                    "None",
                    "",
                    "<blank>",
                ]

                # Add to all users list (for expanded view)
                all_users_list.append(
                    {
                        "username": username,
                        "password": password if has_password else None,
                        "has_password": has_password,
                    }
                )

                # Skip users without passwords for credential cracking
                if not has_password:
                    continue

                # Detect hash type
                credential_type = self._detect_hash_type(password)

                # Add to credentials database
                try:
                    credentials_manager.add_credential(
                        engagement_id=engagement_id,
                        host_id=host_id,
                        username=username,
                        password=password,
                        credential_type=credential_type,
                        tool="sqlmap",
                        service="web",
                    )
                    credentials_added += 1
                    # Add to list for chaining and 🔓 indicator
                    credentials_list.append(
                        {
                            "username": username,
                            "password": password,
                            "credential_type": credential_type,
                        }
                    )
                except Exception as e:
                    logger.warning(f"Failed to add credential {username}: {e}")

        return credentials_added, credentials_list, total_users, all_users_list

    def _is_valid_username(self, username: str) -> bool:
        """
        Validate that a username is legitimate and not scanner garbage.

        Rejects:
        - Injection payloads (netsparker, burp, etc.)
        - Scanner artifacts ({{, ${, %27, etc.)
        - Path patterns (/etc/passwd, .asp, .axd, etc.)
        - Command injection attempts (ping, whoami, etc.)
        - Overly long values (>100 chars)

        Args:
            username: Username string to validate

        Returns:
            bool: True if username appears legitimate
        """
        if not username or len(username) > 100:
            return False

        username_lower = username.lower()

        # Injection tool signatures
        scanner_patterns = [
            "netsparker",
            "burpsuite",
            "burp",
            "acunetix",
            "nikto",
            "sqlmap",
            "havij",
            "w3af",
            "owasp",
            "zap",
            "wvs",
        ]
        for pattern in scanner_patterns:
            if pattern in username_lower:
                return False

        # Template injection / expression patterns
        injection_patterns = [
            "{{",
            "}}",
            "${",
            "}$",
            "<%",
            "%>",
            "{%",
            "%}",
            "${7*7}",
            "{{7*7}}",
            "sleep(",
            "benchmark(",
            "waitfor delay",
            "pg_sleep",
        ]
        for pattern in injection_patterns:
            if pattern in username_lower:
                return False

        # Path traversal / file patterns
        path_patterns = [
            "/etc/",
            "\\etc\\",
            "/passwd",
            "/shadow",
            "/windows/",
            "c:\\",
            ".asp",
            ".aspx",
            ".axd",
            ".php",
            ".jsp",
            ".pl",
            "../",
            "..\\",
            "file://",
            "php://",
            "data://",
            "::1/",
            "[::1]",
            "/elmah",
            "/trace",
            "127.0.0.1/",
        ]
        for pattern in path_patterns:
            if pattern in username_lower:
                return False

        # Command injection patterns
        cmd_patterns = [
            "& ping ",
            "| ping ",
            "; ping ",
            "ping -",
            "& whoami",
            "| whoami",
            "; whoami",
            "`whoami`",
            "$(whoami)",
            "cmd.exe",
            "/bin/sh",
            "& dir",
            "| dir",
            "; dir",
            "& ls",
            "| ls",
            "; ls",
            "nc -",
            "ncat ",
            "netcat ",
        ]
        for pattern in cmd_patterns:
            if pattern in username_lower:
                return False

        # SQL injection patterns
        sql_patterns = [
            "' or ",
            "' and ",
            "1=1",
            "1'='1",
            "' union ",
            "select ",
            "insert ",
            "update ",
            "delete ",
            "drop ",
            "concat(",
            "char(",
            "chr(",
            "0x00",
            "@@version",
        ]
        for pattern in sql_patterns:
            if pattern in username_lower:
                return False

        # URL encoding patterns that indicate payloads
        if "%27" in username or "%22" in username or "%3c" in username_lower:
            return False

        # Hex patterns (0x...) that indicate payloads
        if re.search(r"0x[0-9a-f]{4,}", username_lower):
            return False

        # If it starts/ends with special injection chars, reject
        injection_chars = ['"', "'", ";", "|", "&", "`", "(", ")", "<", ">"]
        if username[0] in injection_chars or username[-1] in injection_chars:
            return False

        # Too many special characters (normal usernames don't have many)
        special_count = sum(1 for c in username if c in "{}[]()$%^&*|\\/<>\"`'")
        if special_count > 3:
            return False

        # If mostly digits/hex and long, likely a payload
        if len(username) > 20:
            alnum_only = re.sub(r"[^a-zA-Z0-9]", "", username)
            if len(alnum_only) > 0:
                digit_ratio = sum(1 for c in alnum_only if c.isdigit()) / len(
                    alnum_only
                )
                if digit_ratio > 0.7:
                    return False

        return True

    def _detect_hash_type(self, password: str) -> str:
        """
        Detect hash type from password string.

        Args:
            password: Password or hash string

        Returns:
            str: Credential type ('password', 'hash:bcrypt', 'hash:md5', etc.)
        """
        # Check for hash prefixes
        if (
            password.startswith("$2y$")
            or password.startswith("$2a$")
            or password.startswith("$2b$")
        ):
            return "hash:bcrypt"
        elif password.startswith("$1$"):
            return "hash:md5crypt"
        elif password.startswith("$5$"):
            return "hash:sha256crypt"
        elif password.startswith("$6$"):
            return "hash:sha512crypt"
        elif password.startswith("$apr1$"):
            return "hash:apr1"
        elif password.startswith("{SHA}") or password.startswith("{SSHA}"):
            return "hash:ldap"

        # Check hex patterns
        if re.match(r"^[a-fA-F0-9]{32}$", password):
            return "hash:md5"
        elif re.match(r"^[a-fA-F0-9]{40}$", password):
            return "hash:sha1"
        elif re.match(r"^[a-fA-F0-9]{64}$", password):
            return "hash:sha256"
        elif re.match(r"^[a-fA-F0-9]{128}$", password):
            return "hash:sha512"

        # Check for NTLM hash
        if re.match(r"^[a-fA-F0-9]{32}:[a-fA-F0-9]{32}$", password):
            return "hash:ntlm"

        # Likely plaintext if short and no special patterns
        if len(password) < 20 and not re.search(r"[\$\{\}]", password):
            return "password"

        # Default to generic hash
        return "hash"

    def display_done(
        self,
        job: Dict[str, Any],
        log_path: str,
        show_all: bool = False,
        show_passwords: bool = False,
    ) -> None:
        """Display successful SQLMap results."""
        try:
            from souleyez.parsers.sqlmap_parser import (
                get_sqli_stats,
                parse_sqlmap_output,
            )

            if not log_path or not os.path.exists(log_path):
                return

            with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                log_content = f.read()
            parsed = parse_sqlmap_output(log_content, job.get("target", ""))
            stats = get_sqli_stats(parsed)

            # Header
            click.echo(click.style("=" * 70, fg="cyan"))
            click.echo(click.style("SQL INJECTION SCAN", bold=True, fg="cyan"))
            click.echo(click.style("=" * 70, fg="cyan"))
            click.echo()

            click.echo(
                click.style(f"Target: {job.get('target', 'unknown')}", bold=True)
            )

            if stats["total_vulns"] == 0 and stats["databases_found"] == 0:
                self.display_no_results(job, log_path)
                return

            click.echo(
                click.style(
                    f"Result: {stats['total_vulns']} vulnerability(ies) found",
                    fg="red",
                    bold=True,
                )
            )
            click.echo()

            # Injection details with techniques and payloads
            if parsed.get("injection_techniques"):
                for inj in parsed["injection_techniques"]:
                    click.echo(
                        click.style(
                            f"[+] SQL Injection: {inj['parameter']} ({inj['method']})",
                            fg="red",
                            bold=True,
                        )
                    )
                    click.echo()

                    tech_limit = len(inj["techniques"]) if show_all else 4
                    click.echo(
                        click.style(
                            f"  Injection Techniques Found: {len(inj['techniques'])}",
                            bold=True,
                        )
                    )
                    for tech in inj["techniques"][:tech_limit]:
                        click.echo(click.style(f"    - {tech['type']}", fg="yellow"))
                        if tech.get("title"):
                            click.echo(f"      Title: {tech['title']}")
                        if tech.get("payload"):
                            payload = tech["payload"]
                            if not show_all and len(payload) > 80:
                                payload = payload[:77] + "..."
                            click.echo(f"      Payload: {payload}")
                        click.echo()

                    if not show_all and len(inj["techniques"]) > 4:
                        click.echo(
                            f"    ... and {len(inj['techniques']) - 4} more techniques"
                        )
                    click.echo()
            elif stats["sqli_confirmed"] > 0:
                click.echo(
                    click.style(
                        f"[+] SQL Injection Found: {stats['sqli_confirmed']} parameter(s)",
                        fg="red",
                        bold=True,
                    )
                )
                click.echo()

            # XSS and File Inclusion warnings
            if stats.get("xss_possible", 0) > 0:
                click.echo(
                    click.style(
                        f"[!] Possible XSS: {stats['xss_possible']} parameter(s)",
                        fg="yellow",
                    )
                )
            if stats.get("fi_possible", 0) > 0:
                click.echo(
                    click.style(
                        f"[!] Possible File Inclusion: {stats['fi_possible']} parameter(s)",
                        fg="yellow",
                    )
                )

            if stats.get("xss_possible", 0) > 0 or stats.get("fi_possible", 0) > 0:
                click.echo()

            # Web stack information
            if parsed.get("web_server_os"):
                click.echo(
                    click.style("Web Server OS: ", bold=True) + parsed["web_server_os"]
                )

            if parsed.get("web_app_technology"):
                click.echo(
                    click.style("Web Technology: ", bold=True)
                    + ", ".join(parsed["web_app_technology"])
                )

            if parsed.get("dbms"):
                click.echo(click.style("Database: ", bold=True) + parsed["dbms"])

            if (
                parsed.get("web_server_os")
                or parsed.get("web_app_technology")
                or parsed.get("dbms")
            ):
                click.echo()

            # Databases enumerated
            if parsed.get("databases"):
                click.echo(
                    click.style(
                        f"Databases Enumerated ({len(parsed['databases'])}):",
                        bold=True,
                        fg="green",
                    )
                )
                max_dbs = None if show_all else 10
                display_dbs = (
                    parsed["databases"]
                    if max_dbs is None
                    else parsed["databases"][:max_dbs]
                )
                for db in display_dbs:
                    click.echo(f"  - {db}")
                if max_dbs and len(parsed["databases"]) > max_dbs:
                    click.echo(f"  ... and {len(parsed['databases']) - max_dbs} more")
                click.echo()

            # Tables enumerated
            if parsed.get("tables"):
                total_tables = sum(len(tables) for tables in parsed["tables"].values())
                click.echo(
                    click.style(
                        f"Tables Enumerated ({total_tables}):", bold=True, fg="green"
                    )
                )
                max_tables = None if show_all else 15
                for db_name, tables in parsed["tables"].items():
                    if len(parsed["tables"]) > 1:
                        click.echo(f"  [{db_name}]")
                    display_tables = tables if show_all else tables[:15]
                    for table in display_tables:
                        click.echo(f"    - {table}")
                    if not show_all and len(tables) > 15:
                        click.echo(f"    ... and {len(tables) - 15} more")
                click.echo()

            # Dumped data
            if parsed.get("dumped_data"):
                click.echo(click.style("Data Dumped:", bold=True, fg="red"))
                for table_key, data in parsed["dumped_data"].items():
                    row_count = data.get("row_count", len(data.get("rows", [])))
                    columns = data.get("columns", [])
                    click.echo(f"  - {table_key}: {row_count} row(s)")
                    if columns:
                        col_limit = None if show_all else 8
                        display_cols = columns if show_all else columns[:col_limit]
                        click.echo(f"    Columns: {', '.join(display_cols)}")
                        if not show_all and len(columns) > 8:
                            click.echo(f"             ... and {len(columns) - 8} more")
                    # Skip raw data rows - shown cleaner in PARSED RESULTS
                click.echo()

            click.echo(click.style("=" * 70, fg="cyan"))
            click.echo()

        except Exception as e:
            logger.debug(f"Error in display_done: {e}")

    def display_warning(
        self,
        job: Dict[str, Any],
        log_path: str,
        log_content: Optional[str] = None,
    ) -> None:
        """Display warning status for SQLMap."""
        click.echo(click.style("=" * 70, fg="yellow"))
        click.echo(click.style("[WARNING] SQLMAP SCAN", bold=True, fg="yellow"))
        click.echo(click.style("=" * 70, fg="yellow"))
        click.echo()
        click.echo("  Scan completed with warnings. Check raw logs for details.")
        click.echo("  Press [r] to view raw logs.")
        click.echo()
        click.echo(click.style("=" * 70, fg="yellow"))
        click.echo()

    def display_error(
        self,
        job: Dict[str, Any],
        log_path: str,
        log_content: Optional[str] = None,
    ) -> None:
        """Display error status for SQLMap."""
        # Read log if not provided
        if log_content is None and log_path and os.path.exists(log_path):
            try:
                with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                    log_content = f.read()
            except Exception:
                log_content = ""

        click.echo(click.style("=" * 70, fg="red"))
        click.echo(click.style("[ERROR] SQLMAP SCAN FAILED", bold=True, fg="red"))
        click.echo(click.style("=" * 70, fg="red"))
        click.echo()

        # Check for common sqlmap errors
        error_msg = None
        if log_content:
            if "connection timed out" in log_content.lower():
                error_msg = "Connection timed out - target may be slow or filtering"
            elif "unable to connect" in log_content.lower():
                error_msg = "Unable to connect to target URL"
            elif "page not found" in log_content.lower() or "404" in log_content:
                error_msg = "Target page not found (404)"
            elif "invalid target url" in log_content.lower():
                error_msg = "Invalid target URL - check the URL format"
            elif (
                "blocked by WAF/IPS" in log_content
                or "rejected by the target" in log_content.lower()
            ):
                # Only flag actual WAF blocks, not heuristic "might be protected" checks
                error_msg = "WAF/IPS detected - try --tamper scripts"
            elif "all tested parameters do not appear" in log_content.lower():
                error_msg = "No injectable parameters found"
            elif "[CRITICAL]" in log_content:
                match = re.search(r"\[CRITICAL\]\s*(.+?)(?:\n|$)", log_content)
                if match:
                    error_msg = match.group(1).strip()[:100]

        if error_msg:
            click.echo(f"  {error_msg}")
        else:
            click.echo("  Scan failed - see raw logs for details (press 'r')")

        click.echo()
        click.echo(click.style("=" * 70, fg="red"))
        click.echo()

    def display_no_results(
        self,
        job: Dict[str, Any],
        log_path: str,
    ) -> None:
        """Display no_results status for SQLMap."""
        click.echo(click.style("=" * 70, fg="cyan"))
        click.echo(click.style("SQL INJECTION SCAN", bold=True, fg="cyan"))
        click.echo(click.style("=" * 70, fg="cyan"))
        click.echo()

        if job.get("target"):
            click.echo(click.style(f"Target: {job.get('target')}", bold=True))
            click.echo()

        click.echo(
            click.style("Result: No SQL injection vulnerabilities found", fg="yellow")
        )
        click.echo()
        click.echo("  The target was tested but no injectable parameters were found.")
        click.echo()
        click.echo(click.style("Tips:", dim=True))
        click.echo("  - Try increasing --level and --risk for deeper testing")
        click.echo("  - Test with authenticated session cookies")
        click.echo("  - Try different injection techniques (--technique=BEUST)")
        click.echo()
        click.echo(click.style("=" * 70, fg="cyan"))
        click.echo()
