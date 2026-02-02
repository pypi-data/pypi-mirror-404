#!/usr/bin/env python3
"""
souleyez.parsers.sqlmap_parser

Parses SQLMap SQL injection detection output into structured findings.
"""

import re
from typing import Any, Dict


def parse_sqlmap_output(output: str, target: str = "") -> Dict[str, Any]:
    """
    Parse SQLMap output and extract SQL injection vulnerabilities.

    VERSION: 2.0 - Fixed injectable_url for auto-chaining

    SQLMap output contains:
    - Testing messages for each parameter
    - Warnings about potential vulnerabilities (XSS, FI, SQLi)
    - Results indicating if parameters are injectable
    - Database enumeration results

    Args:
        output: Raw sqlmap output text
        target: Target URL from job

    Returns:
        Dict with structure:
        {
            'target_url': str,
            'urls_tested': [str, ...],
            'vulnerabilities': [
                {
                    'url': str,
                    'parameter': str,
                    'vuln_type': str,  # 'sqli', 'xss', 'fi'
                    'injectable': bool,
                    'technique': str,  # if SQLi found
                    'dbms': str        # if identified
                },
                ...
            ],
            'databases': [str, ...]  # if enumerated
        }
    """
    result = {
        "target_url": target,
        "urls_tested": [],
        "vulnerabilities": [],
        "databases": [],
        "tables": {},  # {database: [table1, table2, ...]}
        "columns": {},  # {database.table: [col1, col2, ...]}
        "dumped_data": {},  # {db.table: {'rows': [...], 'csv_path': '...', 'columns': [...]}}
        "dbms": None,  # Database type (MySQL, PostgreSQL, etc.)
        # NEW: Add SQL injection confirmation flags
        "sql_injection_confirmed": False,
        "injectable_parameter": "",
        "injectable_url": target,
        "injectable_post_data": None,  # POST data for POST injections
        "injectable_method": "GET",  # GET or POST
        "all_injection_points": [],  # ALL injection points found (for fallback)
        # NEW: Web stack information
        "web_server_os": None,
        "web_app_technology": [],
        "injection_techniques": [],
        # NEW: Post-exploitation flags for auto-chaining
        "is_dba": False,
        "privileges": [],
        "current_user": None,
        "file_read_success": False,
        "os_command_success": False,
    }

    lines = output.split("\n")
    current_url = None
    current_param = None
    current_method = "GET"
    current_post_data = None

    # Track POST form URLs separately to prevent GET URL testing from overwriting them
    # This fixes bug where chain rules get wrong URL when SQLMap tests multiple URLs
    last_post_form_url = None
    last_post_form_data = None

    for i, line in enumerate(lines):
        line = line.strip()

        # Extract URL being tested (GET requests typically)
        # Format variations: "testing URL 'http://...'" or 'testing URL "http://..."' or testing URL http://...
        if "testing URL" in line or "testing url" in line.lower():
            # Try single quotes first
            url_match = re.search(
                r"testing URL ['\"]?([^'\"]+)['\"]?", line, re.IGNORECASE
            )
            if url_match:
                current_url = url_match.group(1).strip()
                if current_url and current_url not in result["urls_tested"]:
                    result["urls_tested"].append(current_url)

        # Extract POST/GET URLs from form testing (crawl mode)
        # Format: "POST http://testphp.vulnweb.com/search.php?test=query"
        if re.match(r"^(POST|GET)\s+http", line):
            url_match = re.search(r"^(POST|GET)\s+(https?://[^\s]+)", line)
            if url_match:
                current_method = url_match.group(1)
                current_url = url_match.group(2)
                if current_url not in result["urls_tested"]:
                    result["urls_tested"].append(current_url)
                # Save POST form URL separately for later use
                if current_method == "POST":
                    last_post_form_url = current_url

        # Extract POST data (appears after "POST http://..." line)
        # Format: "POST data: username=&password=&submit=Login"
        if line.startswith("POST data:"):
            post_data_match = re.search(r"^POST data:\s*(.+)$", line)
            if post_data_match:
                current_post_data = post_data_match.group(1).strip()
                # Associate POST data with the POST form URL
                last_post_form_data = current_post_data

        # Handle resumed injection points from stored session
        # Pattern: "sqlmap resumed the following injection point(s) from stored session:"
        # Followed by: "Parameter: User-Agent (User-Agent)" or similar
        if "resumed the following injection point" in line:
            # Look ahead for Parameter line
            for j in range(i + 1, min(i + 10, len(lines))):
                next_line = lines[j].strip()
                # Pattern: "Parameter: username (POST)" or "Parameter: User-Agent (User-Agent)"
                param_match = re.search(
                    r"^Parameter:\s*([^\s(]+)\s*\(([^)]+)\)", next_line
                )
                if param_match:
                    param = param_match.group(1)
                    param_location = param_match.group(2)

                    # Determine method from parameter location
                    if param_location in ("POST", "GET"):
                        method = param_location
                    else:
                        method = current_method  # Use current context

                    # For POST parameters, use the saved POST form URL instead of current_url
                    if method == "POST" and last_post_form_url:
                        effective_url = last_post_form_url
                        effective_post_data = last_post_form_data or current_post_data
                    else:
                        effective_url = current_url or target
                        effective_post_data = (
                            current_post_data if method == "POST" else None
                        )

                    # Mark as confirmed injection
                    result["sql_injection_confirmed"] = True
                    result["injectable_parameter"] = param
                    result["injectable_url"] = effective_url
                    result["injectable_method"] = method

                    # For POST injections, extract POST data from Payload line if not already set
                    if method == "POST" and not effective_post_data:
                        # Look ahead for Payload line that contains POST data
                        for k in range(j + 1, min(j + 15, len(lines))):
                            payload_line = lines[k].strip()
                            if payload_line.startswith("Payload:"):
                                # Extract the POST data from payload
                                # Format: "Payload: csrf-token=...&param=value&..."
                                payload_match = re.search(
                                    r"^Payload:\s*(.+)$", payload_line
                                )
                                if payload_match:
                                    payload_data = payload_match.group(1).strip()
                                    # Remove the injection payload part to get clean POST data
                                    # The payload contains the base POST data with injection appended
                                    effective_post_data = payload_data
                                    result["injectable_post_data"] = effective_post_data
                                break
                            if payload_line.startswith(
                                "---"
                            ) or payload_line.startswith("["):
                                break
                    elif method == "POST" and effective_post_data:
                        result["injectable_post_data"] = effective_post_data

                    # Look ahead for Type: lines to extract techniques
                    techniques = []
                    technique_str = None
                    for m in range(j + 1, min(j + 20, len(lines))):
                        type_line = lines[m].strip()
                        if type_line.startswith("Type:"):
                            tech_type = type_line.replace("Type:", "").strip()
                            techniques.append(tech_type)
                            if not technique_str:
                                technique_str = tech_type
                        elif type_line.startswith("---") and techniques:
                            break  # End of technique block
                        elif type_line.startswith("[") and techniques:
                            break  # Hit next section

                    # Determine technique string
                    if len(techniques) > 1:
                        technique_str = "multiple"
                    elif techniques:
                        technique_str = techniques[0]
                    else:
                        technique_str = "sqli"

                    # Add vulnerability entry
                    result["vulnerabilities"].append(
                        {
                            "url": effective_url,
                            "parameter": param,
                            "vuln_type": "sqli",
                            "injectable": True,
                            "severity": "critical",
                            "description": f"Parameter '{param}' is vulnerable to SQL injection (resumed from session)",
                            "technique": technique_str,
                            "dbms": "Unknown",  # Will be updated later if found
                        }
                    )

                    # Collect injection point
                    injection_point = {
                        "url": effective_url,
                        "parameter": param,
                        "method": method,
                        "post_data": effective_post_data,
                        "techniques": techniques,
                    }
                    if not any(
                        ip["url"] == injection_point["url"]
                        and ip["parameter"] == injection_point["parameter"]
                        for ip in result["all_injection_points"]
                    ):
                        result["all_injection_points"].append(injection_point)
                    break
                # Stop if we hit a delimiter
                if next_line == "---":
                    continue
                if next_line.startswith("[") or next_line.startswith("back-end"):
                    break

        # Extract DBMS type with full version info
        # Format variations:
        # "back-end DBMS: MySQL >= 5.0.12"
        # "back-end DBMS: Microsoft SQL Server 2019"
        # "back-end DBMS: PostgreSQL"
        if "back-end DBMS:" in line or "back-end dbms:" in line.lower():
            dbms_match = re.search(r"back-end DBMS:\s*(.+)", line, re.IGNORECASE)
            if dbms_match and not result["dbms"]:
                dbms_full = dbms_match.group(1).strip()
                # Extract just the DBMS name for the main field (first word)
                # but store full version in a separate field
                result["dbms"] = dbms_full.split()[0] if dbms_full else None
                result["dbms_full"] = dbms_full  # Keep full string

        # Extract web server OS
        if "web server operating system:" in line.lower():
            os_match = re.search(
                r"web server operating system:\s*(.+)", line, re.IGNORECASE
            )
            if os_match:
                result["web_server_os"] = os_match.group(1).strip()

        # Extract web application technology
        if "web application technology:" in line.lower():
            tech_match = re.search(
                r"web application technology:\s*(.+)", line, re.IGNORECASE
            )
            if tech_match:
                # Parse comma-separated technologies (e.g., "PHP 5.6.40, Nginx 1.19.0")
                tech_str = tech_match.group(1).strip()
                result["web_app_technology"] = [t.strip() for t in tech_str.split(",")]

        # === POST-EXPLOITATION FLAGS ===

        # Detect DBA status: "current user is DBA: True" or "current user is DBA: False"
        if "current user is dba:" in line.lower():
            if "true" in line.lower():
                result["is_dba"] = True
            # False is default, no need to set

        # Detect current user: "current user: 'root@localhost'"
        if "current user:" in line.lower() and "is dba" not in line.lower():
            user_match = re.search(r"current user:\s*'?([^']+)'?", line, re.IGNORECASE)
            if user_match:
                result["current_user"] = user_match.group(1).strip()

        # Detect privileges: Look for privilege enumeration output
        # SQLMap shows: "database management system users privileges:"
        # followed by "[*] 'user'@'host' [1]:" and privilege lists
        if "database management system users privileges" in line.lower():
            # Parse privileges from following lines
            j = i + 1
            while j < len(lines):
                priv_line = lines[j].strip()
                # Look for privilege entries like "privilege: FILE" or just "FILE"
                if priv_line.startswith("[*]") and "@" in priv_line:
                    # User entry like "[*] 'root'@'localhost' [1]:"
                    j += 1
                    continue
                elif priv_line.startswith("privilege:"):
                    priv = priv_line.replace("privilege:", "").strip()
                    if priv and priv not in result["privileges"]:
                        result["privileges"].append(priv)
                elif (
                    priv_line
                    and not priv_line.startswith("[")
                    and not priv_line.startswith("-")
                ):
                    # Direct privilege name
                    if priv_line.isupper() or priv_line in [
                        "FILE",
                        "SUPER",
                        "PROCESS",
                        "SHUTDOWN",
                    ]:
                        if priv_line not in result["privileges"]:
                            result["privileges"].append(priv_line)
                elif (
                    not priv_line
                    or priv_line.startswith("[INFO]")
                    or priv_line.startswith("---")
                ):
                    break
                j += 1

        # Detect file read success: "do you want to retrieve the content" followed by actual content
        # or "the file has been saved to:" indicating successful read
        if "the file has been saved to:" in line.lower() or "retrieved" in line.lower():
            if (
                "/etc/passwd" in output
                or "/etc/shadow" in output
                or "win.ini" in output.lower()
            ):
                result["file_read_success"] = True

        # Detect OS command success: Look for command output
        # SQLMap shows: "command standard output:" followed by output
        if "command standard output:" in line.lower():
            result["os_command_success"] = True

        # === END POST-EXPLOITATION FLAGS ===

        # Extract parameter being tested
        if "testing if" in line and "parameter" in line:
            param_match = re.search(
                r"(?:GET|POST|Cookie|User-Agent|Referer) parameter '([^']+)'", line
            )
            if param_match:
                current_param = param_match.group(1)

        # Detect XSS vulnerability hint
        if "might be vulnerable to cross-site scripting (XSS)" in line:
            param_match = re.search(r"parameter '([^']+)'", line)
            if param_match or current_param:
                param = param_match.group(1) if param_match else current_param
                result["vulnerabilities"].append(
                    {
                        "url": current_url or target,
                        "parameter": param,
                        "vuln_type": "xss",
                        "injectable": False,
                        "severity": "medium",
                        "description": f"Parameter '{param}' might be vulnerable to XSS",
                    }
                )

        # Detect File Inclusion vulnerability hint
        if "might be vulnerable to file inclusion (FI)" in line:
            param_match = re.search(r"parameter '([^']+)'", line)
            if param_match or current_param:
                param = param_match.group(1) if param_match else current_param
                result["vulnerabilities"].append(
                    {
                        "url": current_url or target,
                        "parameter": param,
                        "vuln_type": "file_inclusion",
                        "injectable": False,
                        "severity": "high",
                        "description": f"Parameter '{param}' might be vulnerable to File Inclusion",
                    }
                )

        # NEW: Detect SQL injection from resumed session (Parameter: X (GET/POST))
        # This catches cases where SQLMap resumes and shows injection point without saying "is vulnerable"
        if re.match(
            r"^Parameter:\s+[\w\-]+\s+\((GET|POST|COOKIE|URI|User-Agent|Referer|Host)\)",
            line,
        ):
            param_match = re.search(r"^Parameter:\s+([\w\-]+)\s+\(([\w\-]+)\)", line)
            if param_match:
                param = param_match.group(1)
                param_method = param_match.group(2)

                # Extract all injection techniques that follow
                techniques = []
                j = i + 1
                while j < len(lines):
                    next_line = lines[j].strip()

                    # Check for Type: line
                    if next_line.startswith("Type:"):
                        technique = {"type": "", "title": "", "payload": ""}
                        technique["type"] = next_line.replace("Type:", "").strip()

                        # Look for Title: on next lines
                        if j + 1 < len(lines) and "Title:" in lines[j + 1]:
                            technique["title"] = (
                                lines[j + 1].replace("Title:", "").strip()
                            )

                        # Look for Payload: on next lines
                        if j + 2 < len(lines) and "Payload:" in lines[j + 2]:
                            technique["payload"] = (
                                lines[j + 2].replace("Payload:", "").strip()
                            )

                        techniques.append(technique)
                        j += 3
                    # Stop when we hit next major section
                    elif next_line.startswith("---") or next_line.startswith(
                        "do you want"
                    ):
                        break
                    else:
                        j += 1

                # If we found injection techniques, this parameter is vulnerable
                if techniques:
                    # Check if we already added this parameter (avoid duplicates)
                    already_added = any(
                        v["parameter"] == param and v["vuln_type"] == "sqli"
                        for v in result["vulnerabilities"]
                    )

                    if not already_added:
                        # For POST parameters, use the saved POST form URL instead of current_url
                        # This prevents bug where GET URL testing overwrites the correct POST form URL
                        if param_method == "POST" and last_post_form_url:
                            effective_url = last_post_form_url
                            effective_post_data = (
                                last_post_form_data or current_post_data
                            )
                        else:
                            effective_url = current_url or target
                            effective_post_data = (
                                current_post_data if param_method == "POST" else None
                            )

                        result["vulnerabilities"].append(
                            {
                                "url": effective_url,
                                "parameter": param,
                                "vuln_type": "sqli",
                                "injectable": True,
                                "severity": "critical",
                                "description": f"Parameter '{param}' is vulnerable to SQL injection",
                                "technique": "multiple",  # SQLMap found multiple techniques
                                "dbms": result.get("dbms", "Unknown"),
                            }
                        )

                        # Set confirmation flags
                        result["sql_injection_confirmed"] = True
                        result["injectable_parameter"] = param
                        result["injectable_url"] = effective_url
                        result["injectable_method"] = param_method  # GET, POST, etc.
                        if param_method == "POST" and effective_post_data:
                            result["injectable_post_data"] = effective_post_data

                        # Collect ALL injection points for fallback
                        injection_point = {
                            "url": effective_url,
                            "parameter": param,
                            "method": param_method,
                            "post_data": effective_post_data,
                            "techniques": techniques,
                        }
                        # Avoid duplicates
                        if not any(
                            ip["url"] == injection_point["url"]
                            and ip["parameter"] == injection_point["parameter"]
                            for ip in result["all_injection_points"]
                        ):
                            result["all_injection_points"].append(injection_point)

                    # Add detailed injection techniques
                    result["injection_techniques"].append(
                        {
                            "parameter": param,
                            "method": param_method,
                            "techniques": techniques,
                        }
                    )

        # Detect SQL injection vulnerability
        # Pattern: "POST parameter 'username' is vulnerable" or "GET parameter 'id' is vulnerable"
        if "parameter" in line and "is vulnerable" in line:
            param_match = re.search(
                r"(GET|POST|Cookie|User-Agent|Referer|Host)?\s*parameter '([^']+)' is vulnerable",
                line,
            )
            if param_match:
                method = param_match.group(1) or current_method
                param = param_match.group(2)

                # For POST parameters, use the saved POST form URL instead of current_url
                # This prevents bug where GET URL testing overwrites the correct POST form URL
                if method == "POST" and last_post_form_url:
                    effective_url = last_post_form_url
                    effective_post_data = last_post_form_data or current_post_data
                else:
                    effective_url = current_url or target
                    effective_post_data = (
                        current_post_data if method == "POST" else None
                    )

                result["vulnerabilities"].append(
                    {
                        "url": effective_url,
                        "parameter": param,
                        "vuln_type": "sqli",
                        "injectable": True,
                        "severity": "critical",
                        "description": f"Parameter '{param}' is vulnerable to SQL injection",
                        "technique": "sqli",
                        "dbms": result.get("dbms", "Unknown"),
                    }
                )

                # Set confirmation flags
                result["sql_injection_confirmed"] = True
                result["injectable_parameter"] = param
                result["injectable_url"] = effective_url
                result["injectable_method"] = method
                if method == "POST" and effective_post_data:
                    result["injectable_post_data"] = effective_post_data

                # Collect ALL injection points for fallback
                injection_point = {
                    "url": effective_url,
                    "parameter": param,
                    "method": method,
                    "post_data": effective_post_data,
                    "techniques": [],  # Technique details not available at this detection point
                }
                # Avoid duplicates
                if not any(
                    ip["url"] == injection_point["url"]
                    and ip["parameter"] == injection_point["parameter"]
                    for ip in result["all_injection_points"]
                ):
                    result["all_injection_points"].append(injection_point)

        # Detect not injectable result
        if "does not seem to be injectable" in line:
            param_match = re.search(
                r"parameter '([^']+)' does not seem to be injectable", line
            )
            # We skip these - only store actual vulnerabilities

        # Extract databases (if enumerated)
        if "available databases" in line.lower():
            # Next few lines will contain database names
            j = i + 1
            while j < len(lines) and lines[j].strip().startswith("[*]"):
                db_line = lines[j].strip()
                if db_line.startswith("[*]"):
                    db_name = db_line.replace("[*]", "").strip()
                    if db_name and not db_name.startswith("INFO"):
                        result["databases"].append(db_name)
                j += 1

        # Extract tables for a database (from "Database: dbname" followed by table list)
        if re.match(r"^Database:\s*\w+", line):
            # Pattern: "Database: dbname"
            db_match = re.search(r"Database:\s*(\w+)", line)
            if db_match:
                current_db = db_match.group(1)
                # Check if next line says "[X table]" or "[X tables]"
                if i + 1 < len(lines) and "table" in lines[i + 1]:
                    # Look for ASCII table with | borders
                    j = i + 2
                    in_table = False
                    while j < len(lines):
                        table_line = lines[j].strip()

                        # Start of table (first +---+ border)
                        if table_line.startswith("+") and "-" in table_line:
                            in_table = True
                            j += 1
                            continue

                        # End of table
                        if in_table and (
                            not table_line
                            or table_line.startswith("[")
                            or table_line.startswith("SQL")
                        ):
                            break

                        # Extract table name from | table_name |
                        if (
                            in_table
                            and table_line.startswith("|")
                            and table_line != "|"
                        ):
                            # Skip header rows and separator rows
                            if not all(c in "|+- " for c in table_line):
                                # Extract content between pipes
                                parts = [p.strip() for p in table_line.split("|")]
                                for part in parts:
                                    if part and part not in ["", "table", "tables"]:
                                        if current_db not in result["tables"]:
                                            result["tables"][current_db] = []
                                        if part not in result["tables"][current_db]:
                                            result["tables"][current_db].append(part)
                        j += 1

        # Extract tables for SQLite (no database prefix, just "[X tables]" followed by table list)
        # SQLite format: "[21 tables]" then "+---+" then "| TableName |" rows
        if re.match(r"^\[\d+\s+tables?\]$", line):
            # SQLite uses implicit database name
            sqlite_db = "SQLite_masterdb"
            # Look for ASCII table with | borders starting after this line
            j = i + 1
            in_table = False
            while j < len(lines):
                table_line = lines[j].strip()

                # Start of table (first +---+ border)
                if table_line.startswith("+") and "-" in table_line:
                    in_table = True
                    j += 1
                    continue

                # End of table
                if in_table and (
                    not table_line
                    or table_line.startswith("[")
                    or table_line.startswith("SQL")
                ):
                    break

                # Extract table name from | table_name |
                if in_table and table_line.startswith("|") and table_line != "|":
                    # Skip separator rows
                    if not all(c in "|+- " for c in table_line):
                        # Extract content between pipes
                        parts = [p.strip() for p in table_line.split("|")]
                        for part in parts:
                            if part and part not in ["", "table", "tables"]:
                                if sqlite_db not in result["tables"]:
                                    result["tables"][sqlite_db] = []
                                if part not in result["tables"][sqlite_db]:
                                    result["tables"][sqlite_db].append(part)
                j += 1

        # Extract columns for a table (from "Table: tablename" with column list)
        if re.match(r"^(Database:.*)?Table:\s*\w+", line):
            # Pattern: "Table: tablename" or "Database: db\nTable: table"
            table_match = re.search(r"Table:\s*(\w+)", line)
            db_match = re.search(r"Database:\s*(\w+)", line)

            # If no db_match on same line, check previous line
            if not db_match and i > 0:
                prev_line = lines[i - 1].strip()
                db_match = re.search(r"Database:\s*(\w+)", prev_line)

            if table_match:
                table_name = table_match.group(1)
                db_name = db_match.group(1) if db_match else None

                # Check if next line says "[X columns]"
                if i + 1 < len(lines) and "column" in lines[i + 1]:
                    # Look for ASCII table with | Column | Type | borders
                    j = i + 2
                    in_table = False
                    columns = []

                    while j < len(lines):
                        col_line = lines[j].strip()

                        # Start of table (first +---+ border)
                        if col_line.startswith("+") and "-" in col_line:
                            in_table = True
                            j += 1
                            continue

                        # End of table
                        if in_table and (
                            not col_line
                            or col_line.startswith("[")
                            or col_line.startswith("SQL")
                        ):
                            break

                        # Extract column name from | column_name | type |
                        if in_table and col_line.startswith("|") and col_line != "|":
                            # Skip header rows "| Column | Type |" and separator rows
                            if "Column" not in col_line and "Type" not in col_line:
                                if not all(c in "|+- " for c in col_line):
                                    # Extract first column (column name)
                                    parts = [p.strip() for p in col_line.split("|")]
                                    if len(parts) >= 2 and parts[1]:
                                        col_name = parts[1]
                                        if col_name not in columns:
                                            columns.append(col_name)
                        j += 1

                    if columns:
                        # Store with db.table key if we have db, otherwise just table
                        key = f"{db_name}.{table_name}" if db_name else table_name
                        result["columns"][key] = columns

        # Extract dumped data (e.g., "Database: owasp10\nTable: credit_cards\n[5 entries]")
        if ("entries]" in line or "entry]" in line) and i > 0:
            # Check for "Table: tablename" in previous lines
            db_name = None
            table_name = None

            for k in range(max(0, i - 3), i):
                prev_line = lines[k].strip()
                if prev_line.startswith("Database:"):
                    db_name = prev_line.split("Database:")[1].strip()
                elif prev_line.startswith("Table:"):
                    table_name = prev_line.split("Table:")[1].strip()

            if table_name:
                # Parse the data table that follows
                j = i + 1
                in_data_table = False
                table_columns = []
                table_rows = []

                while j < len(lines):
                    data_line = lines[j].strip()

                    # Start of table (first +---+ border)
                    if data_line.startswith("+") and "-" in data_line:
                        if not in_data_table:
                            in_data_table = True
                        j += 1
                        continue

                    # End of table
                    if in_data_table and (
                        not data_line
                        or data_line.startswith("[")
                        or "dumped to CSV" in data_line
                    ):
                        break

                    # Extract column headers from first | ... | ... | row
                    if (
                        in_data_table
                        and data_line.startswith("|")
                        and not table_columns
                    ):
                        parts = [p.strip() for p in data_line.split("|")]
                        table_columns = [p for p in parts if p]
                        j += 1
                        continue

                    # Extract data rows
                    if in_data_table and table_columns and data_line.startswith("|"):
                        parts = [p.strip() for p in data_line.split("|")]
                        values = [p for p in parts if p != ""]
                        if len(values) == len(table_columns):
                            row_dict = dict(zip(table_columns, values))
                            table_rows.append(row_dict)

                    j += 1

                # Look for CSV file path
                csv_path = None
                for k in range(j, min(j + 5, len(lines))):
                    if "dumped to CSV file" in lines[k]:
                        csv_match = re.search(r"'([^']+\.csv)'", lines[k])
                        if csv_match:
                            csv_path = csv_match.group(1)
                        break

                if table_rows:
                    key = f"{db_name}.{table_name}" if db_name else table_name
                    result["dumped_data"][key] = {
                        "rows": table_rows,
                        "csv_path": csv_path,
                        "columns": table_columns,
                        "row_count": len(table_rows),
                    }

    # NEW: Detect SQL injection confirmation
    # Look for "Parameter: X (GET)" and "Type: boolean-based|error-based|time-based|UNION"
    injection_param_pattern = (
        r"Parameter:\s+([\w\-]+)\s+\((GET|POST|COOKIE|URI|User-Agent|Referer|Host)\)"
    )
    injection_type_patterns = [
        r"Type:\s+boolean-based blind",
        r"Type:\s+error-based",
        r"Type:\s+time-based blind",
        r"Type:\s+UNION query",
        r"Type:\s+stacked queries",
    ]

    # Search for injection parameter
    param_match = re.search(injection_param_pattern, output)
    if param_match:
        result["injectable_parameter"] = param_match.group(1)

        # Check if any injection type is confirmed
        for pattern in injection_type_patterns:
            if re.search(pattern, output, re.IGNORECASE):
                result["sql_injection_confirmed"] = True
                break

    # Add enumeration flags for tool chaining
    if result["databases"]:
        result["databases_enumerated"] = True
    if result["tables"]:
        result["tables_enumerated"] = True
    if result["columns"]:
        result["columns_enumerated"] = True

    # POST-PROCESSING: Select the BEST injection point
    # Prefer error-based over UNION (error-based is more reliable with redirects)
    if result["all_injection_points"] and len(result["all_injection_points"]) > 1:

        def score_injection_point(ip):
            """Score injection points - higher is better."""
            score = 0
            techniques = ip.get("techniques", [])
            for tech in techniques:
                if "error-based" in tech:
                    score += 100  # Best - works despite redirects
                elif "boolean-based" in tech:
                    score += 50
                elif "stacked" in tech:
                    score += 40
                elif "time-based" in tech:
                    score += 20
                elif "UNION" in tech:
                    score += 10  # Least reliable with redirects
            return score

        # Sort by score (highest first) and pick the best
        sorted_points = sorted(
            result["all_injection_points"], key=score_injection_point, reverse=True
        )
        best = sorted_points[0]

        # Update the primary injection point to the best one
        result["injectable_url"] = best["url"]
        result["injectable_parameter"] = best["parameter"]
        result["injectable_method"] = best["method"]
        if best["post_data"]:
            result["injectable_post_data"] = best["post_data"]

    # POST-PROCESSING: Update vulnerabilities with actual DBMS if it was parsed later
    if result.get("dbms"):
        for vuln in result["vulnerabilities"]:
            if vuln.get("dbms") == "Unknown" or vuln.get("dbms") is None:
                vuln["dbms"] = result["dbms"]

    return result


def get_sqli_stats(parsed: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get statistics from parsed SQLMap results.

    Returns:
        Dict with counts and summary info
    """
    sqli_count = sum(
        1
        for v in parsed.get("vulnerabilities", [])
        if v.get("vuln_type") == "sqli" and v.get("injectable")
    )

    xss_count = sum(
        1 for v in parsed.get("vulnerabilities", []) if v.get("vuln_type") == "xss"
    )

    fi_count = sum(
        1
        for v in parsed.get("vulnerabilities", [])
        if v.get("vuln_type") == "file_inclusion"
    )

    return {
        "total_vulns": len(parsed.get("vulnerabilities", [])),
        "sqli_confirmed": sqli_count,
        "xss_possible": xss_count,
        "fi_possible": fi_count,
        "urls_tested": len(parsed.get("urls_tested", [])),
        "databases_found": len(parsed.get("databases", [])),
        "tables_found": sum(
            len(tables) for tables in parsed.get("tables", {}).values()
        ),
        "columns_found": sum(len(cols) for cols in parsed.get("columns", {}).values()),
        "dumped_tables": len(parsed.get("dumped_data", {})),
        "dumped_rows": sum(
            data.get("row_count", 0) for data in parsed.get("dumped_data", {}).values()
        ),
    }
