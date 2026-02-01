#!/usr/bin/env python3
"""
Service version extraction and parsing.
Extracts version info from services table and findings.
"""

import re
from typing import Dict, List, Optional


class ServiceVersionExtractor:
    """Extract and normalize service version information from multiple sources."""

    def __init__(self):
        # Version extraction patterns
        self.version_patterns = [
            # Apache: "Apache/2.4.41 (Ubuntu)"
            r"Apache/(\d+\.\d+(?:\.\d+)?)",
            # nginx: "nginx/1.18.0"
            r"nginx/(\d+\.\d+(?:\.\d+)?)",
            # OpenSSH: "OpenSSH 8.2p1 Ubuntu"
            r"OpenSSH[_\s](\d+\.\d+)(?:p\d+)?",
            # vsftpd: "vsftpd 2.3.4"
            r"vsftpd[_\s](\d+\.\d+(?:\.\d+)?)",
            # MySQL: "MySQL 5.0.51a"
            r"MySQL[_\s](\d+\.\d+(?:\.\d+)?)",
            # ProFTPD: "ProFTPD 1.3.5"
            r"ProFTPD[_\s](\d+\.\d+(?:\.\d+)?)",
            # Samba: "Samba 3.0.20"
            r"Samba[_\s](\d+\.\d+(?:\.\d+)?)",
            # PostgreSQL: "PostgreSQL 9.6.1"
            r"PostgreSQL[_\s](\d+\.\d+(?:\.\d+)?)",
            # Generic version pattern (last resort)
            r"v?(\d+\.\d+(?:\.\d+)?(?:\.\d+)?)",
        ]

    def extract_from_services_table(self, host_id: int) -> List[Dict]:
        """
        Get services from database with version info.

        Returns:
            List of service dicts with normalized version info
        """
        from souleyez.storage.database import get_db

        db = get_db()  # Use singleton instead of creating new connection
        services = []

        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT port, service_name, service_version, service_product
                FROM services
                WHERE host_id = ?
                ORDER BY port
            """,
                (host_id,),
            )

            for row in cursor.fetchall():
                port, service_name, service_version, service_product = row

                # Parse version string from service_version or service_name
                version_string = service_version or service_name or ""
                # Clean the version string to remove Nmap metadata
                cleaned_version = self.clean_version_string(version_string)
                parsed = self.parse_version_string(cleaned_version)

                services.append(
                    {
                        "port": port,
                        "service": service_name or "unknown",
                        "version": cleaned_version or parsed.get("version", "unknown"),
                        "product": service_product
                        or parsed.get("product", service_name or "unknown"),
                        "version_number": parsed.get("version", "unknown"),
                    }
                )

        return services

    def extract_from_findings(self, findings: List[Dict]) -> List[Dict]:
        """
        Parse version info from finding titles/descriptions.

        Example findings:
            - "Port 21: vsftpd 2.3.4 - Backdoor Command Execution"
            - "MySQL 5.0.51a - Remote Code Execution"

        Returns:
            List of service dicts
        """
        services = []

        for finding in findings:
            title = finding.get("title", "")
            description = finding.get("description", "")
            host = finding.get("host", "")

            # Try to extract port
            port_match = re.search(r"[Pp]ort\s+(\d+)", title)
            port = int(port_match.group(1)) if port_match else None

            # Parse version from title
            parsed = self.parse_version_string(title)
            if parsed.get("product") and parsed.get("version"):
                services.append(
                    {
                        "port": port,
                        "service": self._guess_service(parsed["product"], port),
                        "version": f"{parsed['product']} {parsed['version']}",
                        "product": parsed["product"],
                        "version_number": parsed["version"],
                        "source": "finding",
                        "finding_id": finding.get("id"),
                    }
                )

        return services

    def clean_version_string(self, version_str: str) -> str:
        """
        Remove Nmap metadata from version strings.

        Input: "syn-ack ttl 64 vsftpd 2.3.4"
        Output: "vsftpd 2.3.4"
        """
        if not version_str:
            return version_str

        # Remove common Nmap prefixes
        version_str = re.sub(r"^syn-ack\s+ttl\s+\d+\s+", "", version_str)
        version_str = re.sub(r"^no-response\s+", "", version_str)
        version_str = re.sub(r"^reset\s+ttl\s+\d+\s+", "", version_str)

        return version_str.strip()

    def parse_version_string(self, version_str: str) -> Dict:
        """
        Parse version string into structured data.

        Input: "OpenSSH 8.2p1 Ubuntu 4ubuntu0.1"
        Output: {
            'product': 'OpenSSH',
            'version': '8.2',
            'patch': 'p1',
            'build': 'Ubuntu 4ubuntu0.1'
        }
        """
        result = {"product": None, "version": None, "patch": None, "build": None}

        if not version_str:
            return result

        # Clean the version string first
        version_str = self.clean_version_string(version_str)

        # Known products
        products = [
            "OpenSSH",
            "Apache",
            "nginx",
            "vsftpd",
            "MySQL",
            "ProFTPD",
            "Samba",
            "PostgreSQL",
            "Microsoft",
            "Windows",
            "OpenSSL",
        ]

        for product in products:
            if product.lower() in version_str.lower():
                result["product"] = product
                break

        # Extract version number
        for pattern in self.version_patterns:
            match = re.search(pattern, version_str, re.IGNORECASE)
            if match:
                result["version"] = match.group(1)
                break

        # Extract patch level (e.g., p1)
        patch_match = re.search(r"p(\d+)", version_str, re.IGNORECASE)
        if patch_match:
            result["patch"] = patch_match.group(1)

        # Extract build info
        build_match = re.search(r"\((.*?)\)", version_str)
        if build_match:
            result["build"] = build_match.group(1)

        return result

    def combine_sources(self, host_id: int, findings: List[Dict]) -> List[Dict]:
        """
        Merge version info from all sources.
        Prioritize: services table > findings > defaults
        """
        # Get from services table
        services_from_db = self.extract_from_services_table(host_id)

        # Get from findings
        services_from_findings = self.extract_from_findings(findings)

        # Merge by port
        merged = {}

        # Add DB services first (highest priority)
        for svc in services_from_db:
            key = svc["port"]
            merged[key] = svc

        # Augment with finding data if better version info
        for svc in services_from_findings:
            key = svc.get("port")
            if key is None:
                continue

            if key not in merged:
                merged[key] = svc
            else:
                # Update if finding has more specific version
                if (
                    svc["version_number"] != "unknown"
                    and merged[key]["version_number"] == "unknown"
                ):
                    merged[key]["version_number"] = svc["version_number"]
                    merged[key]["product"] = svc["product"]

        return list(merged.values())

    def _guess_service(self, product: str, port: Optional[int]) -> str:
        """Guess service type from product name and port."""
        product_lower = product.lower()

        # Map products to service types
        if "ssh" in product_lower:
            return "ssh"
        elif "ftp" in product_lower:
            return "ftp"
        elif "mysql" in product_lower:
            return "mysql"
        elif "postgres" in product_lower:
            return "postgres"
        elif "apache" in product_lower or "nginx" in product_lower:
            return "http"
        elif "samba" in product_lower or "smb" in product_lower:
            return "smb"

        # Fallback to port-based guess
        if port:
            port_map = {
                21: "ftp",
                22: "ssh",
                23: "telnet",
                25: "smtp",
                80: "http",
                443: "https",
                445: "smb",
                3306: "mysql",
                5432: "postgres",
                8080: "http",
            }
            return port_map.get(port, "unknown")

        return "unknown"
