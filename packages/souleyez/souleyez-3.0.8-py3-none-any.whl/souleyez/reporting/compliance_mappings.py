#!/usr/bin/env python3
"""
Compliance mapping for pentest findings.
Maps findings to OWASP Top 10 and CWE standards.
"""

from typing import Dict, List, Set


class ComplianceMappings:
    """Map findings to compliance frameworks."""

    def __init__(self):
        # OWASP Top 10 2021 keyword mappings
        self.owasp_mappings = {
            "A01:2021": {
                "name": "Broken Access Control",
                "keywords": [
                    "access control",
                    "authorization",
                    "privilege escalation",
                    "directory traversal",
                    "path traversal",
                    "file inclusion",
                    "idor",
                    "insecure direct object",
                    "force browsing",
                    "missing authorization",
                    "cors",
                    "elevation of privilege",
                ],
            },
            "A02:2021": {
                "name": "Cryptographic Failures",
                "keywords": [
                    "encryption",
                    "weak cipher",
                    "ssl",
                    "tls",
                    "https",
                    "cryptographic",
                    "weak hash",
                    "md5",
                    "sha1",
                    "des",
                    "plaintext",
                    "clear text",
                    "sensitive data",
                    "pii",
                    "password storage",
                    "weak encryption",
                ],
            },
            "A03:2021": {
                "name": "Injection",
                "keywords": [
                    "sql injection",
                    "sqli",
                    "command injection",
                    "ldap injection",
                    "xpath injection",
                    "xml injection",
                    "nosql injection",
                    "os command",
                    "code injection",
                    "script injection",
                    "blind sql",
                    "union select",
                    "shell injection",
                ],
            },
            "A04:2021": {
                "name": "Insecure Design",
                "keywords": [
                    "insecure design",
                    "threat modeling",
                    "design flaw",
                    "architecture",
                    "security pattern",
                    "secure by design",
                    "business logic",
                    "logic flaw",
                ],
            },
            "A05:2021": {
                "name": "Security Misconfiguration",
                "keywords": [
                    "misconfiguration",
                    "default",
                    "unnecessary feature",
                    "verbose error",
                    "stack trace",
                    "information disclosure",
                    "debug",
                    "unused",
                    "unpatched",
                    "outdated",
                    "directory listing",
                    "server banner",
                    "version disclosure",
                ],
            },
            "A06:2021": {
                "name": "Vulnerable and Outdated Components",
                "keywords": [
                    "outdated",
                    "vulnerable component",
                    "cve",
                    "known vulnerability",
                    "old version",
                    "unpatched",
                    "vulnerable library",
                    "dependency",
                    "third party",
                    "component",
                ],
            },
            "A07:2021": {
                "name": "Identification and Authentication Failures",
                "keywords": [
                    "authentication",
                    "weak password",
                    "credential",
                    "session",
                    "brute force",
                    "password policy",
                    "default credentials",
                    "session fixation",
                    "session hijack",
                    "login",
                    "authentication bypass",
                    "weak credentials",
                ],
            },
            "A08:2021": {
                "name": "Software and Data Integrity Failures",
                "keywords": [
                    "integrity",
                    "deserialization",
                    "untrusted data",
                    "pipeline",
                    "update",
                    "auto-update",
                    "insecure deserialization",
                    "code signing",
                    "tamper",
                ],
            },
            "A09:2021": {
                "name": "Security Logging and Monitoring Failures",
                "keywords": [
                    "logging",
                    "monitoring",
                    "audit",
                    "log",
                    "alerting",
                    "detection",
                    "incident response",
                    "insufficient logging",
                    "no logging",
                ],
            },
            "A10:2021": {
                "name": "Server-Side Request Forgery (SSRF)",
                "keywords": [
                    "ssrf",
                    "server-side request forgery",
                    "request forgery",
                    "internal network",
                    "localhost",
                    "metadata",
                ],
            },
        }

        # CWE Top 25 2024 mappings
        self.cwe_mappings = {
            "CWE-89": {
                "name": "SQL Injection",
                "keywords": ["sql injection", "sqli", "union select", "blind sql"],
            },
            "CWE-79": {
                "name": "Cross-site Scripting (XSS)",
                "keywords": [
                    "xss",
                    "cross-site scripting",
                    "javascript injection",
                    "reflected xss",
                    "stored xss",
                ],
            },
            "CWE-78": {
                "name": "OS Command Injection",
                "keywords": [
                    "command injection",
                    "os command",
                    "shell injection",
                    "rce",
                ],
            },
            "CWE-22": {
                "name": "Path Traversal",
                "keywords": [
                    "path traversal",
                    "directory traversal",
                    "../",
                    "file inclusion",
                    "lfi",
                ],
            },
            "CWE-352": {
                "name": "Cross-Site Request Forgery (CSRF)",
                "keywords": ["csrf", "cross-site request forgery", "xsrf"],
            },
            "CWE-434": {
                "name": "Unrestricted Upload of Dangerous File",
                "keywords": [
                    "file upload",
                    "upload vulnerability",
                    "unrestricted upload",
                ],
            },
            "CWE-862": {
                "name": "Missing Authorization",
                "keywords": ["missing authorization", "authorization bypass", "idor"],
            },
            "CWE-798": {
                "name": "Hard-coded Credentials",
                "keywords": [
                    "hardcoded",
                    "hard-coded",
                    "default credentials",
                    "embedded password",
                ],
            },
            "CWE-287": {
                "name": "Improper Authentication",
                "keywords": [
                    "authentication bypass",
                    "weak authentication",
                    "broken auth",
                ],
            },
            "CWE-190": {
                "name": "Integer Overflow",
                "keywords": ["integer overflow", "buffer overflow", "overflow"],
            },
            "CWE-502": {
                "name": "Deserialization of Untrusted Data",
                "keywords": [
                    "deserialization",
                    "untrusted data",
                    "insecure deserialization",
                ],
            },
            "CWE-611": {
                "name": "XML External Entity (XXE)",
                "keywords": ["xxe", "xml external entity", "xml injection"],
            },
            "CWE-918": {
                "name": "Server-Side Request Forgery (SSRF)",
                "keywords": ["ssrf", "server-side request forgery"],
            },
            "CWE-94": {
                "name": "Code Injection",
                "keywords": ["code injection", "remote code execution", "rce"],
            },
            "CWE-269": {
                "name": "Improper Privilege Management",
                "keywords": [
                    "privilege escalation",
                    "elevation of privilege",
                    "privilege management",
                ],
            },
            "CWE-200": {
                "name": "Information Disclosure",
                "keywords": [
                    "information disclosure",
                    "sensitive data",
                    "data exposure",
                    "verbose error",
                ],
            },
            "CWE-522": {
                "name": "Insufficiently Protected Credentials",
                "keywords": [
                    "weak password",
                    "password policy",
                    "credential protection",
                ],
            },
            "CWE-306": {
                "name": "Missing Authentication",
                "keywords": [
                    "missing authentication",
                    "no authentication",
                    "unauthenticated",
                ],
            },
            "CWE-319": {
                "name": "Cleartext Transmission of Sensitive Information",
                "keywords": ["cleartext", "plain text", "unencrypted", "http"],
            },
            "CWE-326": {
                "name": "Inadequate Encryption Strength",
                "keywords": ["weak encryption", "weak cipher", "des", "md5", "sha1"],
            },
        }

    def map_finding_to_owasp(self, finding: Dict) -> List[str]:
        """Map a finding to OWASP Top 10 2021 categories."""
        matches = []

        # Combine title, description, and tool for keyword matching
        search_text = (
            f"{finding.get('title', '')} "
            f"{finding.get('description', '')} "
            f"{finding.get('tool', '')}"
        ).lower()

        for owasp_id, owasp_data in self.owasp_mappings.items():
            for keyword in owasp_data["keywords"]:
                if keyword.lower() in search_text:
                    matches.append(owasp_id)
                    break  # Only match once per category

        return matches

    def map_finding_to_cwe(self, finding: Dict) -> List[str]:
        """Map a finding to CWE Top 25 categories."""
        matches = []

        # Check if finding already has CWE
        if finding.get("cwe"):
            existing_cwe = finding["cwe"].upper()
            if existing_cwe.startswith("CWE-"):
                matches.append(existing_cwe)

        # Combine title, description, and tool for keyword matching
        search_text = (
            f"{finding.get('title', '')} "
            f"{finding.get('description', '')} "
            f"{finding.get('tool', '')}"
        ).lower()

        for cwe_id, cwe_data in self.cwe_mappings.items():
            if cwe_id in matches:
                continue  # Already have this CWE

            for keyword in cwe_data["keywords"]:
                if keyword.lower() in search_text:
                    matches.append(cwe_id)
                    break  # Only match once per category

        return matches

    def get_compliance_coverage(self, findings: List[Dict]) -> Dict:
        """Calculate compliance framework coverage."""
        owasp_covered = set()
        cwe_covered = set()

        for finding in findings:
            owasp_matches = self.map_finding_to_owasp(finding)
            cwe_matches = self.map_finding_to_cwe(finding)

            owasp_covered.update(owasp_matches)
            cwe_covered.update(cwe_matches)

        return {
            "owasp": {
                "covered": sorted(list(owasp_covered)),
                "total": len(self.owasp_mappings),
                "coverage_percent": round(
                    len(owasp_covered) / len(self.owasp_mappings) * 100, 1
                ),
                "gaps": sorted(
                    [k for k in self.owasp_mappings.keys() if k not in owasp_covered]
                ),
            },
            "cwe": {
                "covered": sorted(list(cwe_covered)),
                "total": len(self.cwe_mappings),
                "coverage_percent": round(
                    len(cwe_covered) / len(self.cwe_mappings) * 100, 1
                ),
                "gaps": sorted(
                    [k for k in self.cwe_mappings.keys() if k not in cwe_covered]
                ),
            },
        }

    def get_owasp_name(self, owasp_id: str) -> str:
        """Get full name for OWASP ID."""
        return self.owasp_mappings.get(owasp_id, {}).get("name", owasp_id)

    def get_cwe_name(self, cwe_id: str) -> str:
        """Get full name for CWE ID."""
        return self.cwe_mappings.get(cwe_id, {}).get("name", cwe_id)
