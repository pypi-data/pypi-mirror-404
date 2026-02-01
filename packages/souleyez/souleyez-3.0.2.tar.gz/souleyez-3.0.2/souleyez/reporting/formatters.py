#!/usr/bin/env python3
"""
Report formatting utilities.
Handles Markdown and HTML output with professional styling.
"""

from datetime import datetime
from typing import Dict, List


class MarkdownFormatter:
    """Format report sections as Markdown."""

    def title_page(self, engagement: Dict, generated_at: datetime) -> str:
        """Generate title page."""
        return f"""# PENETRATION TEST REPORT
## {engagement['name']}

**Generated:** {generated_at.strftime('%B %d, %Y at %H:%M:%S')}

---"""

    def table_of_contents(self) -> str:
        """Generate table of contents."""
        return """## TABLE OF CONTENTS

1. [Executive Summary](#executive-summary)
2. [Engagement Overview](#engagement-overview)
3. [Attack Surface Analysis](#attack-surface-analysis)
4. [Findings Summary](#findings-summary)
5. [Detailed Findings](#detailed-findings)
6. [Evidence Collection](#evidence-collection)
7. [Recommendations](#recommendations)
8. [Methodology](#methodology)
9. [Appendix](#appendix)

---"""

    def executive_summary(
        self,
        engagement: Dict,
        findings: Dict,
        overview: Dict,
        report_type: str = "technical",
    ) -> str:
        """
        Generate executive summary with business impact context.

        Args:
            engagement: Engagement details
            findings: Findings grouped by severity
            overview: Attack surface overview
            report_type: 'executive', 'technical', or 'summary'
        """
        critical_count = len(findings["critical"])
        high_count = len(findings["high"])
        medium_count = len(findings["medium"])
        total_hosts = overview["total_hosts"]
        exploited = overview["exploited_services"]

        # Determine risk level
        if critical_count > 0:
            risk_level = "**CRITICAL**"
            risk_color = "🔴"
        elif high_count > 5:
            risk_level = "**HIGH**"
            risk_color = "🟠"
        elif high_count > 0:
            risk_level = "**MEDIUM**"
            risk_color = "🟡"
        else:
            risk_level = "**LOW**"
            risk_color = "🟢"

        summary = f"""## EXECUTIVE SUMMARY

**Engagement:** {engagement['name']}  
**Date Range:** {engagement.get('created_at', 'N/A')[:10]} - Present  
**Status:** Complete

### KEY FINDINGS

- {critical_count} Critical vulnerabilities identified
- {high_count} High severity findings
- {medium_count} Medium severity findings
- {total_hosts} Total hosts assessed
- {exploited} Services successfully exploited

### RISK LEVEL: {risk_color} {risk_level}

The penetration test identified **{critical_count} critical** and **{high_count} high** severity vulnerabilities across {total_hosts} target systems."""

        if critical_count > 0:
            summary += " Immediate remediation is recommended for critical findings to prevent potential compromise."

        # Business Impact Section (for executive reports)
        if report_type == "executive" and (critical_count > 0 or high_count > 0):
            summary += "\n\n### BUSINESS IMPACT\n\n"

            # Analyze top findings for business impact
            top_findings = (
                findings["critical"][:3] if critical_count > 0 else findings["high"][:3]
            )
            impacts = self._calculate_business_impacts(top_findings)

            # Overall business risks
            summary += "**Key Business Risks:**\n\n"

            if any(
                "data breach" in str(f.get("title", "")).lower()
                or "sql injection" in str(f.get("title", "")).lower()
                for f in findings["critical"]
            ):
                summary += "- **Data Breach Risk:** Vulnerabilities could expose sensitive customer data, leading to regulatory fines (GDPR up to €20M/4% revenue) and reputational damage\n"

            if critical_count > 0:
                summary += f"- **System Compromise:** {critical_count} critical vulnerabilit{'y' if critical_count == 1 else 'ies'} could allow attackers full system access\n"

            if high_count >= 3:
                summary += f"- **Security Posture:** {high_count} high-severity issues indicate systematic security gaps requiring attention\n"

            summary += "\n**Compliance Impact:**\n\n"

            # Estimate compliance implications
            if critical_count > 0 or high_count >= 5:
                summary += "- Current security posture may not meet PCI-DSS, ISO 27001, or SOC 2 requirements\n"
                summary += "- Non-compliance could block customer contracts, certifications, or partnerships\n"

            # Financial impact estimate
            summary += "\n**Estimated Financial Impact (if exploited):**\n\n"
            if critical_count > 0:
                summary += f"- Incident response costs: ${50000 * critical_count:,} - ${200000 * critical_count:,}\n"
                summary += (
                    f"- Potential breach notification and remediation: ${100000:,}+\n"
                )
                summary += "- Reputational damage and customer loss: Significant\n"

        # Top risks with business context
        if critical_count > 0 or high_count > 0:
            summary += "\n\n### TOP RISKS\n\n"
            top_findings = findings["critical"][:3] + findings["high"][:3]
            for idx, finding in enumerate(top_findings[:5], 1):
                severity = finding.get("severity", "unknown").upper()
                title = finding["title"]
                summary += f"**{idx}. {title}** - {severity}\n"

                # Add business impact for executive reports
                if report_type == "executive":
                    impact = self._get_finding_business_context(finding)
                    summary += f"   *Impact:* {impact}\n"

                summary += "\n"

        # Action Timeline (for executive reports)
        if report_type == "executive" and (critical_count > 0 or high_count > 0):
            summary += "### ACTION TIMELINE\n\n"

            if critical_count > 0:
                summary += f"**Immediate (This Week):** Address {critical_count} critical finding{'s' if critical_count != 1 else ''}\n"
                summary += "- Deploy emergency patches\n"
                summary += "- Implement temporary mitigations\n"
                summary += "- Begin incident response preparation\n\n"

            if high_count > 0:
                summary += f"**Short-Term (Within 2 Weeks):** Remediate {high_count} high-priority issue{'s' if high_count != 1 else ''}\n"
                summary += "- Plan and schedule fixes\n"
                summary += "- Update security configurations\n"
                summary += "- Review access controls\n\n"

            if medium_count > 0:
                summary += f"**Medium-Term (30 Days):** Address {medium_count} medium-severity finding{'s' if medium_count != 1 else ''}\n"
                summary += "- Systematic security improvements\n"
                summary += "- Policy and procedure updates\n\n"

            # Resource estimate
            total_hours = (critical_count * 4) + (high_count * 2) + (medium_count * 1)
            summary += f"**Estimated Remediation Effort:** {total_hours}-{total_hours * 2} hours\n"
            summary += (
                "*See Recommendations section for detailed remediation guidance.*\n"
            )

        summary += "\n---"
        return summary

    def _calculate_business_impacts(self, findings: List[Dict]) -> List[str]:
        """Calculate business impacts for top findings."""
        impacts = []
        for finding in findings:
            impact = self._get_finding_business_context(finding)
            impacts.append(impact)
        return impacts

    def _get_finding_business_context(self, finding: Dict) -> str:
        """Get business context for a specific finding."""
        title_lower = finding.get("title", "").lower()

        # Data breach scenarios
        if (
            "sql injection" in title_lower
            or "data breach" in title_lower
            or "dump" in title_lower
        ):
            return "Data breach risk with regulatory and reputational consequences"

        # Authentication/Access
        if (
            "authentication" in title_lower
            or "credential" in title_lower
            or "password" in title_lower
        ):
            return "Unauthorized access could compromise confidential systems and data"

        # Injection attacks
        if "injection" in title_lower or "xss" in title_lower:
            return "User account compromise and potential malware distribution"

        # Information disclosure
        if "disclosure" in title_lower or "exposure" in title_lower:
            return "Information leakage aids attacker reconnaissance and planning"

        # Configuration issues
        if "configuration" in title_lower or "misconfiguration" in title_lower:
            return "Security weaknesses that lower defense effectiveness"

        # Default severity-based context
        severity = finding.get("severity", "").lower()
        if severity == "critical":
            return "High-impact vulnerability requiring immediate attention"
        elif severity == "high":
            return "Significant security risk requiring timely remediation"
        else:
            return "Security issue requiring attention"

    def engagement_overview(
        self,
        engagement: Dict,
        tools_used: List[str] = None,
        report_type: str = "technical",
    ) -> str:
        """
        Generate engagement overview section.

        Args:
            engagement: Engagement details
            tools_used: List of tools used in assessment
            report_type: 'executive', 'technical', or 'summary'
        """
        section = f"""## ENGAGEMENT OVERVIEW

**Engagement Name:** {engagement['name']}  
**Created:** {engagement.get('created_at', 'N/A')[:10]}  
**Description:** {engagement.get('description', 'No description provided')}

### Scope

Testing was conducted against systems within the defined scope. All testing activities were authorized and conducted in accordance with the rules of engagement.

### Tools Used

"""

        # If tools list provided, use it dynamically
        if tools_used:
            # Executive: Just show count
            if report_type == "executive":
                section += f"{len(tools_used)} industry-standard security testing tools were utilized during this assessment.\n\n"
                section += "---"
                return section

            # Tool descriptions and categories
            tool_info = {
                "nmap": {
                    "desc": "Port scanning and service enumeration",
                    "cat": "Reconnaissance",
                },
                "metasploit": {
                    "desc": "Exploitation and post-exploitation",
                    "cat": "Exploitation",
                },
                "msf": {
                    "desc": "Exploitation and post-exploitation",
                    "cat": "Exploitation",
                },
                "nuclei": {
                    "desc": "Web vulnerability scanning with templated checks",
                    "cat": "Vulnerability Scanning",
                },
                "sqlmap": {
                    "desc": "SQL injection testing and database exploitation",
                    "cat": "Exploitation",
                },
                "gobuster": {
                    "desc": "Directory and DNS brute forcing",
                    "cat": "Enumeration",
                },
                "ffuf": {
                    "desc": "Fast web fuzzer for directory and parameter discovery",
                    "cat": "Enumeration",
                },
                "hydra": {
                    "desc": "Credential brute forcing",
                    "cat": "Password Attacks",
                },
                "theharvester": {
                    "desc": "OSINT and email/subdomain gathering",
                    "cat": "Reconnaissance",
                },
                "dnsrecon": {
                    "desc": "DNS enumeration and zone transfer testing",
                    "cat": "Reconnaissance",
                },
                "whois": {
                    "desc": "Domain registration and ownership information",
                    "cat": "Reconnaissance",
                },
                "enum4linux": {"desc": "SMB/Windows enumeration", "cat": "Enumeration"},
                "smbmap": {
                    "desc": "SMB share enumeration and access testing",
                    "cat": "Enumeration",
                },
                "wpscan": {
                    "desc": "WordPress vulnerability scanning",
                    "cat": "Vulnerability Scanning",
                },
                "dirb": {"desc": "Web content scanner", "cat": "Enumeration"},
                "searchsploit": {
                    "desc": "Exploit database search",
                    "cat": "Exploitation",
                },
                "john": {"desc": "Password cracking", "cat": "Password Attacks"},
                "hashcat": {
                    "desc": "Advanced password recovery",
                    "cat": "Password Attacks",
                },
                "medusa": {
                    "desc": "Parallel password brute forcer",
                    "cat": "Password Attacks",
                },
                "crackmapexec": {
                    "desc": "Network authentication testing",
                    "cat": "Exploitation",
                },
                "responder": {
                    "desc": "LLMNR/NBT-NS/MDNS poisoner",
                    "cat": "Exploitation",
                },
                "bloodhound": {
                    "desc": "Active Directory attack path analysis",
                    "cat": "Post-Exploitation",
                },
                "mimikatz": {
                    "desc": "Credential extraction",
                    "cat": "Post-Exploitation",
                },
                "linpeas": {
                    "desc": "Linux privilege escalation checker",
                    "cat": "Post-Exploitation",
                },
                "winpeas": {
                    "desc": "Windows privilege escalation checker",
                    "cat": "Post-Exploitation",
                },
            }

            # Group tools by category
            categorized = {}
            unknown_tools = []

            for tool in tools_used:
                tool_lower = tool.lower()
                info = tool_info.get(tool_lower)

                if info:
                    category = info["cat"]
                    if category not in categorized:
                        categorized[category] = []
                    categorized[category].append({"name": tool, "desc": info["desc"]})
                else:
                    unknown_tools.append(tool)

            # Display by category in logical order
            category_order = [
                "Reconnaissance",
                "Enumeration",
                "Vulnerability Scanning",
                "Exploitation",
                "Password Attacks",
                "Post-Exploitation",
            ]

            for category in category_order:
                if category in categorized:
                    section += f"**{category}:**\n"
                    for tool in sorted(
                        categorized[category], key=lambda x: x["name"].lower()
                    ):
                        # Capitalize tool name properly
                        tool_lower = tool["name"].lower()
                        tool_name = (
                            tool["name"].upper()
                            if tool_lower in ["smb", "dns", "osint"]
                            else tool["name"].title()
                        )
                        section += f"- {tool_name} - {tool['desc']}\n"
                    section += "\n"

            # Add any unknown tools at the end
            if unknown_tools:
                section += "**Other Tools:**\n"
                for tool in sorted(unknown_tools):
                    section += f"- {tool.title()} - Security testing tool\n"
                section += "\n"
        else:
            # Fallback to common tools if none provided (grouped)
            section += """**Reconnaissance:**
- Nmap - Port scanning and service enumeration
- theHarvester - OSINT gathering
- DNSRecon - DNS enumeration

**Vulnerability Scanning:**
- Nuclei - Web vulnerability scanning with templated checks

**Exploitation:**
- Metasploit Framework - Exploitation and post-exploitation
- SQLMap - SQL injection testing

**Enumeration:**
- Gobuster - Directory brute forcing

"""

        section += "---"
        return section

    def attack_surface_section(self, attack_surface: Dict) -> str:
        """Generate attack surface analysis section."""
        hosts = attack_surface["hosts"][:5]
        overview = attack_surface["overview"]

        section = """## ATTACK SURFACE ANALYSIS

### Overview Statistics

"""
        section += f"- **Total Services:** {overview['total_services']}\n"
        section += f"- **Exploited:** {overview['exploited_services']} ({overview['exploitation_percentage']}%)\n"
        section += f"- **Credentials Found:** {overview['credentials_found']}\n"
        section += f"- **Critical Findings:** {overview['critical_findings']}\n\n"

        section += "### Top Targets (by attack surface score)\n\n"

        for idx, host in enumerate(hosts, 1):
            prog = host["exploitation_progress"]
            pct = round(
                (prog["exploited"] / prog["total"] * 100) if prog["total"] > 0 else 0, 0
            )

            section += f"#### #{idx} {host['host']}"
            if host.get("hostname"):
                section += f" ({host['hostname']})"
            section += f" - Score: {host['score']}\n\n"

            # Format services count properly (handle list, int, or empty)
            services_data = host.get("services", 0)
            if isinstance(services_data, list):
                services_count = len(services_data)
            else:
                services_count = services_data

            section += f"- **{host['open_ports']} open ports**\n"
            section += f"- **{services_count} services** identified\n"
            section += f"- **{host['findings']} vulnerabilities** found"
            if host["critical_findings"] > 0:
                section += f" ({host['critical_findings']} critical)"
            section += "\n"
            section += f"- **Exploitation:** {prog['exploited']}/{prog['total']} services ({pct}%)\n\n"

        section += "---"
        return section

    def findings_summary(self, findings: Dict) -> str:
        """Generate findings summary section."""
        critical = len(findings["critical"])
        high = len(findings["high"])
        medium = len(findings["medium"])
        low = len(findings["low"])
        info = len(findings["info"])
        total = critical + high + medium + low + info

        return f"""## FINDINGS SUMMARY

### Severity Breakdown

| Severity | Count | Percentage |
|----------|-------|------------|
| 🔴 Critical | {critical} | {round(critical/total*100) if total > 0 else 0}% |
| 🟠 High | {high} | {round(high/total*100) if total > 0 else 0}% |
| 🟡 Medium | {medium} | {round(medium/total*100) if total > 0 else 0}% |
| 🟢 Low | {low} | {round(low/total*100) if total > 0 else 0}% |
| ℹ️ Info | {info} | {round(info/total*100) if total > 0 else 0}% |
| **Total** | **{total}** | **100%** |

---"""

    def key_findings_summary(self, findings: Dict) -> str:
        """
        Generate key findings summary - shows top critical/high findings upfront.
        This helps executives quickly understand the most important issues.
        """
        section = """## KEY FINDINGS SUMMARY

*Quick overview of the most critical security issues discovered*

"""

        critical_findings = findings["critical"]
        high_findings = findings["high"]

        # Immediate Action Required (Critical)
        if critical_findings:
            section += "### 🚨 Immediate Action Required (Critical)\n\n"
            for idx, finding in enumerate(critical_findings[:5], 1):  # Top 5 critical
                title = finding.get("title", "Untitled Finding")
                host = self._format_affected_host(finding)
                section += f"{idx}. **{title}**\n"
                section += f"   - Host: {host}\n"
                if finding.get("description"):
                    # Get first sentence or first 100 chars
                    desc = finding["description"].split(".")[0][:100]
                    section += f"   - Impact: {desc}...\n"
                section += "\n"

            if len(critical_findings) > 5:
                section += f"*...and {len(critical_findings) - 5} more critical finding(s)*\n\n"

        # High Priority (Within 7 days)
        if high_findings:
            section += "### ⚠️  High Priority (Address within 7 days)\n\n"
            for idx, finding in enumerate(high_findings[:3], 1):  # Top 3 high
                title = finding.get("title", "Untitled Finding")
                host = self._format_affected_host(finding)
                section += f"{idx}. **{title}** - {host}\n"

            if len(high_findings) > 3:
                section += f"\n*...and {len(high_findings) - 3} more high-priority finding(s)*\n"
            section += "\n"

        # Overall stats
        total_critical = len(critical_findings)
        total_high = len(high_findings)
        total_medium = len(findings["medium"])
        total_low = len(findings["low"])

        section += f"**Total Findings:** {total_critical} Critical, {total_high} High, {total_medium} Medium, {total_low} Low\n\n"
        section += "**Recommendation:** Address all critical findings immediately, high findings within 7 days.\n\n"
        section += "*See Detailed Findings section below for complete information.*\n\n"
        section += "---\n"

        return section

    def compliance_section(
        self,
        findings: List[Dict],
        compliance_data: Dict,
        report_type: str = "technical",
    ) -> str:
        """
        Generate compliance mapping section.

        Args:
            findings: List of all findings
            compliance_data: Compliance coverage data
            report_type: 'executive', 'technical', or 'summary'
                        - executive: Only show matched categories (cleaner)
                        - technical: Show all categories with gaps
                        - summary: Brief summary only
        """
        from souleyez.reporting.compliance_mappings import ComplianceMappings

        mapper = ComplianceMappings()
        section = """## COMPLIANCE MAPPING

### OWASP Top 10 2021 Coverage

"""

        owasp_coverage = compliance_data["owasp"]
        section += f"**Coverage: {owasp_coverage['coverage_percent']}%** ({len(owasp_coverage['covered'])}/{owasp_coverage['total']} categories)\n\n"

        # Count findings per category
        owasp_findings_count = {}
        for finding in findings:
            owasp_matches = mapper.map_finding_to_owasp(finding)
            for owasp_id in owasp_matches:
                owasp_findings_count[owasp_id] = (
                    owasp_findings_count.get(owasp_id, 0) + 1
                )

        # OWASP Coverage Table
        if report_type == "executive":
            # Executive: Only show matched categories (reduce clutter)
            if owasp_coverage["covered"]:
                section += "**OWASP Categories Identified:**\n\n"
                section += "| Category | Findings |\n"
                section += "|----------|----------|\n"

                for owasp_id in sorted(owasp_coverage["covered"]):
                    name = mapper.get_owasp_name(owasp_id)
                    count = owasp_findings_count.get(owasp_id, 0)
                    section += f"| {owasp_id}: {name} | {count} |\n"
            else:
                section += "No OWASP Top 10 vulnerabilities identified.\n"
        else:
            # Technical/Summary: Show all categories with status
            section += "| Category | Status | Findings |\n"
            section += "|----------|--------|----------|\n"

            for owasp_id in sorted(mapper.owasp_mappings.keys()):
                name = mapper.get_owasp_name(owasp_id)
                if owasp_id in owasp_coverage["covered"]:
                    count = owasp_findings_count.get(owasp_id, 0)
                    status = "✅ Covered"
                    section += f"| {owasp_id}: {name} | {status} | {count} |\n"
                else:
                    section += f"| {owasp_id}: {name} | ⚪ Not Found | 0 |\n"

        section += "\n### CWE Top 25 Coverage\n\n"

        cwe_coverage = compliance_data["cwe"]
        section += f"**Coverage: {cwe_coverage['coverage_percent']}%** ({len(cwe_coverage['covered'])}/{cwe_coverage['total']} categories)\n\n"

        if cwe_coverage["covered"]:
            section += "**CWEs Identified:**\n\n"

            # Count findings per CWE
            cwe_findings_count = {}
            for finding in findings:
                cwe_matches = mapper.map_finding_to_cwe(finding)
                for cwe_id in cwe_matches:
                    cwe_findings_count[cwe_id] = cwe_findings_count.get(cwe_id, 0) + 1

            # Limit to top 10 for executive reports
            cwe_list = sorted(cwe_coverage["covered"])
            if report_type == "executive" and len(cwe_list) > 10:
                cwe_list = cwe_list[:10]
                show_more = True
            else:
                show_more = False

            for cwe_id in cwe_list:
                name = mapper.get_cwe_name(cwe_id)
                count = cwe_findings_count.get(cwe_id, 0)
                section += f"- **{cwe_id}**: {name} ({count} finding{'s' if count != 1 else ''})\n"

            if show_more:
                section += f"\n*...and {len(cwe_coverage['covered']) - 10} more CWEs*\n"
        else:
            section += "No CWE Top 25 vulnerabilities identified.\n"

        # Compliance Gaps (only for technical reports)
        if report_type == "technical" and (
            compliance_data["owasp"]["gaps"] or compliance_data["cwe"]["gaps"]
        ):
            section += "\n### Compliance Gaps\n\n"

            if compliance_data["owasp"]["gaps"]:
                section += f"**OWASP Categories Not Found:** {len(compliance_data['owasp']['gaps'])} categories not represented in findings.\n\n"

            if compliance_data["cwe"]["gaps"]:
                section += f"**CWE Categories Not Found:** {len(compliance_data['cwe']['gaps'])} weakness types not identified.\n\n"

            section += "*Note: Gaps indicate vulnerability types not found during testing, which may be positive (not present) or indicate areas requiring deeper assessment.*\n"

        section += "\n---"
        return section

    def detailed_findings(self, findings: Dict, report_type: str = "technical") -> str:
        """Generate detailed findings section."""
        section = "## DETAILED FINDINGS\n\n"

        finding_number = 1
        for severity in ["critical", "high", "medium", "low", "info"]:
            for finding in findings[severity]:
                section += f"### Finding #{finding_number}: {finding['title']}\n\n"

                # Severity badge
                severity_upper = severity.upper()
                emoji_map = {
                    "critical": "🔴",
                    "high": "🟠",
                    "medium": "🟡",
                    "low": "🟢",
                    "info": "ℹ️",
                }
                section += f"**Severity:** {emoji_map[severity]} {severity_upper}  \n"

                if finding.get("cvss"):
                    section += f"**CVSS Score:** {finding['cvss']}  \n"
                if finding.get("cve"):
                    section += f"**CVE:** {finding['cve']}  \n"

                # Format affected host display
                affected_host = self._format_affected_host(finding)
                section += f"**Affected Host:** {affected_host}  \n"
                section += f"**Tool:** {finding['tool']}  \n\n"

                # Description
                if finding.get("description"):
                    section += f"**Description:**\n\n{finding['description']}\n\n"

                # Remediation - Always include
                remediation_text = finding.get("remediation", "")
                if not remediation_text:
                    remediation_text = self._generate_default_remediation(
                        finding, severity
                    )

                section += f"**Recommendation:**\n\n{remediation_text}\n\n"

                section += "---\n\n"
                finding_number += 1

        return section

    def evidence_section(self, evidence_counts: Dict, credentials: List[Dict]) -> str:
        """Generate evidence collection section."""
        section = """## EVIDENCE COLLECTION

### Evidence by Phase

"""
        section += f"- **Reconnaissance:** {evidence_counts['reconnaissance']} items\n"
        section += f"- **Enumeration:** {evidence_counts['enumeration']} items\n"
        section += f"- **Exploitation:** {evidence_counts['exploitation']} items\n"
        section += (
            f"- **Post-Exploitation:** {evidence_counts['post_exploitation']} items\n\n"
        )

        if credentials:
            section += f"### Credentials Discovered ({len(credentials)} total)\n\n"
            section += "| Host | Port | Service | Username |\n"
            section += "|------|------|---------|----------|\n"

            for cred in credentials[:10]:  # Show first 10
                section += f"| {cred.get('host', 'N/A')} | {cred.get('port', '?')} | {cred.get('service', 'unknown')} | {cred.get('username', 'N/A')} |\n"

            if len(credentials) > 10:
                section += f"\n*... and {len(credentials) - 10} more credentials*\n"

        section += "\n---"
        return section

    def recommendations(self, findings: Dict, attack_recs: List[Dict]) -> str:
        """
        Generate recommendations section with specific, actionable guidance.
        Organized by timeline with resource estimates.
        """
        section = """## RECOMMENDATIONS

*Prioritized remediation roadmap with estimated effort and impact*

"""

        # Quick Wins (< 1 hour, high impact)
        quick_wins = self._identify_quick_wins(findings)
        if quick_wins:
            section += "### 🎯 Quick Wins (< 1 Hour Each)\n\n"
            section += "*High-impact fixes that can be completed quickly*\n\n"
            for idx, win in enumerate(quick_wins, 1):
                section += f"{idx}. **{win['title']}** ⏱️ {win['effort']}\n"
                section += f"   - **Action:** {win['action']}\n"
                section += f"   - **Impact:** {win['impact']}\n\n"

        # Immediate Actions (Critical Priority - Today/This Week)
        section += (
            "### 🚨 Immediate Actions (Critical Priority - Complete This Week)\n\n"
        )

        if findings["critical"]:
            total_critical = len(findings["critical"])
            section += f"**{total_critical} critical finding{'s' if total_critical != 1 else ''} requiring immediate attention:**\n\n"

            for idx, finding in enumerate(findings["critical"][:5], 1):
                section += f"**{idx}. {finding['title']}**\n"

                # Add specific remediation steps
                if finding.get("remediation"):
                    section += f"   - **Fix:** {finding['remediation']}\n"

                # Add resource estimate based on finding type
                effort = self._estimate_remediation_effort(finding)
                section += f"   - **Estimated Effort:** {effort}\n"

                # Add business impact context
                impact = self._get_business_impact(finding, "critical")
                section += f"   - **Business Impact:** {impact}\n\n"

            if total_critical > 5:
                section += f"*...and {total_critical - 5} more critical finding(s). See Detailed Findings section.*\n\n"
        else:
            section += "✅ No critical findings identified.\n\n"

        # Short-Term (High Priority - 1-2 Weeks)
        section += "### ⚠️  Short-Term Actions (High Priority - Within 2 Weeks)\n\n"

        if findings["high"]:
            total_high = len(findings["high"])
            section += f"**{total_high} high-priority finding{'s' if total_high != 1 else ''} to address:**\n\n"

            for idx, finding in enumerate(findings["high"][:3], 1):
                section += f"{idx}. **{finding['title']}**\n"
                if finding.get("remediation"):
                    # Shorten if too long
                    rem = finding["remediation"]
                    if len(rem) > 150:
                        rem = rem[:147] + "..."
                    section += f"   - {rem}\n"
                effort = self._estimate_remediation_effort(finding)
                section += f"   - Effort: {effort}\n\n"

            if total_high > 3:
                section += f"*...and {total_high - 3} more high-priority findings.*\n\n"
        else:
            section += "✅ No high-priority findings identified.\n\n"

        # Medium-Term (Medium Severity - 30 Days)
        if findings["medium"]:
            section += "### 📋 Medium-Term Actions (Within 30 Days)\n\n"
            total_medium = len(findings["medium"])
            section += f"**{total_medium} medium-severity finding{'s' if total_medium != 1 else ''} identified.** "
            section += "Prioritize based on asset criticality and exposure.\n\n"
            section += "Review the Detailed Findings section for specific remediation guidance on each issue.\n\n"

        # Resource Summary
        section += "### 📊 Resource Planning\n\n"
        resource_summary = self._calculate_resource_summary(findings)
        section += f"**Estimated Total Remediation Effort:**\n\n"
        section += f"- Critical: {resource_summary['critical']} hours\n"
        section += f"- High: {resource_summary['high']} hours\n"
        section += f"- Medium: {resource_summary['medium']} hours\n"
        section += f"- **Total: {resource_summary['total']} hours**\n\n"
        section += "*Note: Estimates are approximate and may vary based on environment complexity.*\n"

        section += "\n---"
        return section

    def _identify_quick_wins(self, findings: Dict) -> List[Dict]:
        """Identify quick-win fixes (< 1 hour, high impact)."""
        quick_wins = []

        # Common quick-win patterns
        quick_win_patterns = {
            "information disclosure": {
                "action": "Remove or restrict access to exposed information",
                "impact": "Reduces reconnaissance opportunities for attackers",
                "effort": "15-30 min",
            },
            "default credentials": {
                "action": "Change all default passwords immediately",
                "impact": "Prevents trivial unauthorized access",
                "effort": "5-10 min per system",
            },
            "missing security headers": {
                "action": "Configure web server security headers",
                "impact": "Protects against common web attacks",
                "effort": "30-45 min",
            },
            "unencrypted": {
                "action": "Enable SSL/TLS encryption",
                "impact": "Protects data in transit",
                "effort": "30-60 min",
            },
            "directory listing": {
                "action": "Disable directory indexing in web server config",
                "impact": "Prevents information disclosure",
                "effort": "10-15 min",
            },
        }

        # Check critical and high findings for quick wins
        for finding in findings["critical"] + findings["high"]:
            title_lower = finding["title"].lower()
            for pattern, details in quick_win_patterns.items():
                if pattern in title_lower:
                    quick_wins.append(
                        {
                            "title": finding["title"],
                            "action": details["action"],
                            "impact": details["impact"],
                            "effort": details["effort"],
                        }
                    )
                    break

            # Limit to top 5 quick wins
            if len(quick_wins) >= 5:
                break

        return quick_wins

    def _estimate_remediation_effort(self, finding: Dict) -> str:
        """Estimate remediation effort based on finding type."""
        title_lower = finding["title"].lower()

        # High effort (4+ hours)
        if any(
            x in title_lower
            for x in ["architecture", "redesign", "refactor", "encryption scheme"]
        ):
            return "4-8 hours (Complex)"

        # Medium effort (1-4 hours)
        if any(
            x in title_lower
            for x in ["sql injection", "xss", "authentication", "access control"]
        ):
            return "2-4 hours (Moderate)"

        # Low effort (< 1 hour)
        if any(
            x in title_lower
            for x in ["default", "disclosure", "header", "configuration"]
        ):
            return "30-60 minutes (Simple)"

        # Default to medium
        return "1-3 hours (Moderate)"

    def _get_business_impact(self, finding: Dict, severity: str) -> str:
        """Get business impact context for finding."""
        title_lower = finding["title"].lower()

        # Data breach scenarios
        if "sql injection" in title_lower or "data breach" in title_lower:
            return (
                "Data breach, regulatory penalties (GDPR/PCI-DSS), reputational damage"
            )

        # Authentication issues
        if "authentication" in title_lower or "credentials" in title_lower:
            return "Unauthorized access, potential system compromise"

        # XSS/injection
        if "xss" in title_lower or "injection" in title_lower:
            return "User account compromise, data theft, malware distribution"

        # Default by severity
        if severity == "critical":
            return "High risk of immediate exploitation and business disruption"
        else:
            return "Security exposure requiring timely remediation"

    def _calculate_resource_summary(self, findings: Dict) -> Dict:
        """Calculate total remediation effort summary."""
        effort_map = {
            "5-10 min per system": 0.2,
            "10-15 min": 0.25,
            "15-30 min": 0.5,
            "30-45 min": 0.75,
            "30-60 min": 1,
            "30-60 minutes (Simple)": 1,
            "1-3 hours (Moderate)": 2,
            "2-4 hours (Moderate)": 3,
            "4-8 hours (Complex)": 6,
        }

        summary = {"critical": 0, "high": 0, "medium": 0}

        for severity in ["critical", "high", "medium"]:
            for finding in findings[severity]:
                effort_str = self._estimate_remediation_effort(finding)
                # Default to 2 hours if not in map
                hours = effort_map.get(effort_str, 2)
                summary[severity] += hours

        summary["total"] = summary["critical"] + summary["high"] + summary["medium"]

        return summary

    def methodology(self) -> str:
        """Generate methodology section."""
        return """## METHODOLOGY

This penetration test followed industry-standard methodology based on PTES (Penetration Testing Execution Standard).

### Phase 1: Reconnaissance
- Network discovery and port scanning
- Service version enumeration
- OSINT gathering (DNS, WHOIS, public data)

### Phase 2: Enumeration
- User account enumeration
- Share and directory enumeration
- Service-specific enumeration
- Vulnerability scanning

### Phase 3: Exploitation
- Exploit development and execution
- Credential-based attacks
- Web application testing
- Privilege escalation attempts

### Phase 4: Post-Exploitation
- System file collection
- Database enumeration and extraction
- Evidence gathering
- Lateral movement testing (if authorized)

All testing was conducted in accordance with the agreed-upon rules of engagement and with explicit authorization.

---"""

    def attack_chain_section(
        self, chain: Dict, summary: Dict, host_centric_chain: Dict = None
    ) -> str:
        """Generate attack chain visualization section.

        Args:
            chain: Legacy attack chain (for fallback)
            summary: Legacy summary (for fallback)
            host_centric_chain: New host-centric chain structure (preferred)
        """
        from souleyez.reporting.attack_chain import AttackChainAnalyzer

        analyzer = AttackChainAnalyzer()

        # Use host-centric chain if available
        if host_centric_chain and host_centric_chain.get("hosts"):
            return self._host_centric_attack_section(host_centric_chain, analyzer)

        # Fallback to legacy visualization
        if not chain or not chain.get("nodes"):
            return ""

        section = """## ATTACK CHAIN ANALYSIS

### Attack Path Visualization

The following diagram shows the progression of the attack from initial reconnaissance through post-exploitation:

"""

        mermaid_diagram = analyzer.generate_mermaid_diagram(chain)

        section += f"""<div class="mermaid-container">
<pre class="mermaid">
{mermaid_diagram}
</pre>
</div>

"""

        # Add attack summary
        section += "### Attack Path Summary\n\n"
        section += f"- **Total Attack Steps:** {summary['total_nodes']} nodes, {summary['total_edges']} transitions\n"
        section += f"- **Hosts Compromised:** {summary['hosts_compromised']}\n"
        section += f"- **Active Phases:** {summary['phases_active']}/4 penetration testing phases\n"
        section += (
            f"- **Attack Depth:** {summary['longest_path']} levels (longest path)\n"
        )

        if summary["critical_nodes"]:
            section += f"- **Critical Nodes:** {len(summary['critical_nodes'])} high-connectivity points\n"

        section += "\n**Phase Breakdown:**\n\n"
        for phase, count in chain["phases"].items():
            if count > 0:
                phase_name = phase.replace("_", " ").title()
                section += f"- **{phase_name}:** {count} evidence items\n"

        section += "\n### Attack Flow Interpretation\n\n"
        section += "This visualization demonstrates:\n\n"
        section += "- The sequential progression of the penetration test\n"
        section += "- How initial reconnaissance led to service discovery\n"
        section += "- Exploitation paths taken against identified vulnerabilities\n"
        section += "- Credential harvesting and access escalation\n"
        section += "- Post-exploitation activities on compromised hosts\n"

        if summary["hosts_compromised"] > 1:
            section += "\n**Lateral Movement:** The attack chain shows movement across "
            section += f"{summary['hosts_compromised']} different hosts, indicating potential for lateral movement within the network.\n"

        section += "\n---"
        return section

    def _host_centric_attack_section(self, chain: Dict, analyzer) -> str:
        """Generate host-centric attack chain visualization."""
        summary = analyzer.get_host_centric_summary(chain)
        hosts = chain.get("hosts", [])
        lateral_edges = chain.get("lateral_edges", [])

        section = """## ATTACK PATH VISUALIZATION

### Host-Centric Attack Flow

Each box represents a target host with its attack progression. Arrows show the path from discovery through exploitation. Dashed lines indicate lateral movement between hosts.

"""

        # Generate Mermaid diagram
        mermaid_diagram = analyzer.generate_host_centric_mermaid(chain)

        section += f"""<div class="mermaid-container">
<pre class="mermaid">
{mermaid_diagram}
</pre>
</div>

"""

        # Legend
        section += """### Legend

| Color | Phase |
|-------|-------|
| Blue | Discovery/Reconnaissance |
| Green | Enumeration |
| Yellow | Vulnerability Found |
| Orange | Exploitation |
| Purple | Credentials Obtained |
| Red | Post-Exploitation |

"""

        # Summary stats
        section += "### Attack Path Summary\n\n"
        section += f"- **Hosts Analyzed:** {summary['total_hosts']}\n"
        section += f"- **Hosts Exploited:** {summary['hosts_exploited']}\n"
        section += f"- **Total Attack Steps:** {summary['total_nodes']}\n"
        section += f"- **Deepest Penetration:** {summary['deepest_attack']} phases"
        if summary.get("deepest_host"):
            section += f" (on {summary['deepest_host']})"
        section += "\n"

        if summary["lateral_movements"] > 0:
            section += f"- **Lateral Movements:** {summary['lateral_movements']} cross-host transitions\n"

        # Phase breakdown
        phase_counts = summary.get("phase_counts", {})
        if any(v > 0 for v in phase_counts.values()):
            section += "\n**Attack Phase Distribution:**\n\n"
            phase_labels = {
                "discovery": "Discovery",
                "enumeration": "Enumeration",
                "vulnerability": "Vulnerabilities",
                "exploitation": "Exploitation",
                "credential": "Credentials",
                "post_exploitation": "Post-Exploitation",
            }
            for phase, count in phase_counts.items():
                if count > 0:
                    label = phase_labels.get(phase, phase.replace("_", " ").title())
                    section += f"- **{label}:** {count} instances\n"

        # Interpretation
        section += "\n### Attack Flow Interpretation\n\n"

        if summary["hosts_exploited"] == 0:
            section += "No hosts were fully exploited during this engagement. "
            section += (
                "The attack progressed through reconnaissance and enumeration phases.\n"
            )
        elif summary["hosts_exploited"] == 1:
            section += f"One host was successfully exploited. "
            if summary["lateral_movements"] > 0:
                section += "Lateral movement was detected, suggesting the attacker attempted to pivot to other systems.\n"
            else:
                section += "No lateral movement was detected.\n"
        else:
            section += (
                f"**{summary['hosts_exploited']} hosts** were successfully exploited. "
            )
            if summary["lateral_movements"] > 0:
                section += f"**{summary['lateral_movements']} lateral movements** were detected, "
                section += "demonstrating the attacker's ability to pivot between systems using harvested credentials.\n"
            else:
                section += "Each host was compromised independently without detected lateral movement.\n"

        section += "\n---"
        return section

    def appendix(
        self,
        hosts: List[Dict],
        credentials: List[Dict],
        include_methodology: bool = True,
    ) -> str:
        """Generate appendix section with optional methodology."""
        section = """## APPENDIX

"""
        # A. Methodology (moved here from main report body)
        if include_methodology:
            section += """### A. Testing Methodology

This penetration test followed industry-standard methodology based on PTES (Penetration Testing Execution Standard).

**Phase 1: Reconnaissance**
- Network discovery and port scanning
- Service version enumeration
- OSINT gathering (DNS, WHOIS, public data)

**Phase 2: Enumeration**
- User account enumeration
- Share and directory enumeration
- Service-specific enumeration
- Vulnerability scanning

**Phase 3: Exploitation**
- Exploit development and execution
- Credential-based attacks
- Web application testing
- Privilege escalation attempts

**Phase 4: Post-Exploitation**
- System file collection
- Database enumeration and extraction
- Evidence gathering
- Lateral movement testing (if authorized)

All testing was conducted in accordance with the agreed-upon rules of engagement and with explicit authorization.

"""
            host_section = "B"
            tools_section = "C"
            glossary_section = "D"
        else:
            host_section = "A"
            tools_section = "B"
            glossary_section = "C"

        section += f"### {host_section}. Complete Host List\n\n"

        for host in hosts:
            # Format services count properly (handle list, int, or empty)
            services_data = host.get("services", 0)
            if isinstance(services_data, list):
                services_count = len(services_data)
            else:
                services_count = services_data

            section += f"- **{host['host']}**"
            if host.get("hostname"):
                section += f" ({host['hostname']})"
            section += f" - {services_count} services, {host['findings']} findings\n"

        section += f"\n### {tools_section}. Testing Tools\n\n"
        section += "All tools used are industry-standard, open-source security testing tools.\n\n"

        section += f"### {glossary_section}. Glossary\n\n"
        section += "- **CVE:** Common Vulnerabilities and Exposures identifier\n"
        section += "- **CVSS:** Common Vulnerability Scoring System\n"
        section += "- **Exploit:** Code or technique used to take advantage of a vulnerability\n"
        section += "- **OSINT:** Open Source Intelligence\n"
        section += "- **Privilege Escalation:** Gaining higher access rights than initially authorized\n"

        section += "\n---"
        return section

    def footer(self, generated_at: datetime) -> str:
        """Generate report footer."""
        return f"""---

**Report Generated:** {generated_at.strftime('%B %d, %Y at %H:%M:%S')}
**Generated By:** SoulEyez 👁️ Pentest Platform
**Version:** 1.0

---

*This report contains confidential information. Unauthorized distribution is prohibited.*
"""

    def _format_affected_host(self, finding: Dict) -> str:
        """
        Format affected host display from finding data.

        Tries multiple fields in order:
        1. ip_address (from JOIN with hosts table)
        2. hostname (from JOIN with hosts table)
        3. path (for web findings with URL path)
        4. port (show port number)
        5. 'Unknown' as fallback

        Args:
            finding: Finding dictionary with host data

        Returns:
            Formatted host string
        """
        # Try IP address first (most common)
        if finding.get("ip_address"):
            host_str = finding["ip_address"]
            # Add hostname if available
            if finding.get("hostname"):
                host_str += f" ({finding['hostname']})"
            # Add port if available
            if finding.get("port"):
                host_str += f":{finding['port']}"
            # Add path for web findings - but only if it's a clean path (not a full URL)
            if (
                finding.get("path")
                and finding["path"] != "/"
                and not finding["path"].startswith("http")
            ):
                host_str += finding["path"]
            return host_str

        # Try hostname alone
        if finding.get("hostname"):
            host_str = finding["hostname"]
            if finding.get("port"):
                host_str += f":{finding['port']}"
            # Only add path if it's a clean path (not a full URL)
            if (
                finding.get("path")
                and finding["path"] != "/"
                and not finding["path"].startswith("http")
            ):
                host_str += finding["path"]
            return host_str

        # Try path alone (web findings without host) - but only if not a full URL
        if finding.get("path") and not finding["path"].startswith("http"):
            return finding["path"]

        # Try port alone
        if finding.get("port"):
            return f"Port {finding['port']}"

        # Fallback
        return "Unknown"

    def _generate_default_remediation(self, finding: Dict, severity: str) -> str:
        """Generate default remediation recommendation based on finding details."""
        title_lower = finding.get("title", "").lower()
        tool = finding.get("tool", "").lower()

        # SQL Injection
        if "sql injection" in title_lower or "sqli" in title_lower:
            return """1. Implement parameterized queries/prepared statements for all database operations
2. Apply input validation and sanitization for all user inputs
3. Use stored procedures with properly defined parameters
4. Implement least privilege database access controls
5. Deploy a Web Application Firewall (WAF) to block SQL injection attempts
6. Review and patch all vulnerable parameters immediately"""

        # XSS
        if "xss" in title_lower or "cross-site scripting" in title_lower:
            return """1. Implement proper output encoding for all user-controlled data
2. Use Content Security Policy (CSP) headers
3. Apply HTML sanitization on user inputs
4. Enable HTTPOnly and Secure flags on cookies
5. Validate and sanitize all input on server-side
6. Use modern frameworks with built-in XSS protection"""

        # Authentication issues
        if (
            "auth" in title_lower
            or "login" in title_lower
            or "password" in title_lower
            or "credential" in title_lower
        ):
            return """1. Implement multi-factor authentication (MFA)
2. Enforce strong password policies (minimum 12 characters, complexity)
3. Use bcrypt or Argon2 for password hashing
4. Implement account lockout after failed attempts
5. Use secure session management with proper timeouts
6. Review and update authentication mechanisms"""

        # SSL/TLS issues
        if "ssl" in title_lower or "tls" in title_lower or "certificate" in title_lower:
            return """1. Update to TLS 1.2 or higher (disable TLS 1.0/1.1)
2. Use strong cipher suites only
3. Obtain and install valid SSL/TLS certificates
4. Enable HSTS (HTTP Strict Transport Security)
5. Configure proper certificate chain validation
6. Regular certificate monitoring and renewal"""

        # File upload
        if "upload" in title_lower or "file" in title_lower:
            return """1. Validate file types using whitelist approach
2. Implement file size restrictions
3. Scan uploaded files for malware
4. Store uploaded files outside web root
5. Use random filenames to prevent path traversal
6. Implement proper access controls on uploaded content"""

        # Command injection
        if "command injection" in title_lower or "command execution" in title_lower:
            return """1. Avoid system calls that use user input
2. Implement strict input validation and sanitization
3. Use safe APIs that don't invoke shell commands
4. Apply the principle of least privilege for process execution
5. Use parameterized commands when shell execution is necessary
6. Implement command whitelisting"""

        # Directory traversal
        if "directory traversal" in title_lower or "path traversal" in title_lower:
            return """1. Validate and sanitize all file path inputs
2. Use whitelisting for allowed paths
3. Reject paths with '..' sequences
4. Implement proper access controls on file systems
5. Use secure file access APIs
6. Chroot/jail file operations where possible"""

        # Information disclosure
        if (
            "disclosure" in title_lower
            or "exposure" in title_lower
            or "leakage" in title_lower
        ):
            return """1. Remove or restrict access to sensitive information
2. Implement proper error handling (don't expose stack traces)
3. Review and remove debug information from production
4. Apply proper authentication and authorization
5. Use generic error messages for public-facing systems
6. Review server configurations and headers"""

        # Misconfigurations
        if "misconfiguration" in title_lower or "default" in title_lower:
            return """1. Change all default credentials immediately
2. Disable unnecessary services and features
3. Apply security hardening guidelines (CIS benchmarks)
4. Review and update security configurations
5. Implement regular security configuration audits
6. Use infrastructure-as-code for consistent configurations"""

        # SMB/Windows issues
        if "smb" in title_lower or tool == "enum4linux":
            return """1. Disable SMBv1 protocol (use SMBv2/v3 only)
2. Restrict anonymous access to SMB shares
3. Implement proper access controls on shares
4. Enable SMB signing and encryption
5. Apply latest Windows security patches
6. Use strong authentication mechanisms"""

        # DNS issues
        if "dns" in title_lower or tool == "dnsrecon":
            return """1. Restrict zone transfers to authorized servers only
2. Implement DNSSEC for data integrity
3. Use split-horizon DNS for internal/external separation
4. Apply rate limiting to prevent DNS amplification attacks
5. Monitor DNS logs for suspicious activity
6. Keep DNS software updated"""

        # Brute force / Weak credentials
        if (
            "brute" in title_lower
            or "weak password" in title_lower
            or tool in ["hydra", "medusa"]
        ):
            return """1. Enforce strong password policies
2. Implement account lockout mechanisms
3. Deploy multi-factor authentication (MFA)
4. Monitor and alert on failed login attempts
5. Use CAPTCHA for login forms
6. Implement rate limiting on authentication endpoints"""

        # Web vulnerabilities (generic)
        if tool in ["nuclei", "gobuster", "ffuf"]:
            return """1. Review and patch identified web vulnerabilities
2. Apply security updates to web server and applications
3. Implement Web Application Firewall (WAF)
4. Use security headers (CSP, X-Frame-Options, etc.)
5. Perform regular security testing
6. Follow OWASP Top 10 remediation guidance"""

        # Default by severity
        if severity == "critical":
            return """1. **IMMEDIATE ACTION REQUIRED** - Patch or mitigate this vulnerability within 24 hours
2. Isolate affected systems if immediate patching isn't possible
3. Implement monitoring for exploitation attempts
4. Review logs for signs of compromise
5. Notify security team and stakeholders
6. Plan for emergency patching and testing"""
        elif severity == "high":
            return """1. Prioritize remediation within 7 days
2. Apply vendor patches or security updates
3. Implement temporary mitigations if patches unavailable
4. Review and restrict access to affected systems
5. Enhance monitoring and logging
6. Document remediation efforts"""
        elif severity == "medium":
            return """1. Address within 30 days as part of regular patching cycle
2. Review and apply security best practices
3. Implement defense-in-depth controls
4. Update security configurations
5. Include in next maintenance window
6. Test thoroughly before production deployment"""
        else:  # low or info
            return """1. Address during regular maintenance windows
2. Review and document the finding
3. Implement security improvements as resources allow
4. Include in security hardening initiatives
5. Monitor for any changes in risk level
6. Consider as part of security posture improvement"""

    def ai_executive_summary(self, content: str, provider: str = "AI") -> str:
        """
        Render AI-generated executive summary.

        Args:
            content: AI-generated executive summary text
            provider: Name of AI provider (e.g., 'Claude', 'Ollama')

        Returns:
            str: Formatted markdown section
        """
        return f"""## AI-ENHANCED EXECUTIVE SUMMARY

*Generated by {provider}*

{content}

---"""

    def ai_remediation_plan(self, content: str, provider: str = "AI") -> str:
        """
        Render AI-generated remediation plan.

        Args:
            content: AI-generated remediation plan text
            provider: Name of AI provider (e.g., 'Claude', 'Ollama')

        Returns:
            str: Formatted markdown section
        """
        return f"""## AI-ENHANCED REMEDIATION PLAN

*Generated by {provider}*

{content}

---"""

    def ai_risk_rating(
        self, rating: str, justification: str, provider: str = "AI"
    ) -> str:
        """
        Render AI-generated risk rating.

        Args:
            rating: Overall risk rating (CRITICAL, HIGH, MODERATE, LOW)
            justification: Justification for the rating
            provider: Name of AI provider

        Returns:
            str: Formatted markdown section
        """
        emoji_map = {
            "CRITICAL": "🔴",
            "HIGH": "🟠",
            "MODERATE": "🟡",
            "LOW": "🟢",
            "UNKNOWN": "⚪",
        }
        emoji = emoji_map.get(rating.upper(), "⚪")

        return f"""### AI Risk Assessment

**Overall Risk Rating:** {emoji} **{rating.upper()}**

{justification}

*Assessment by {provider}*

---"""

    def ai_finding_enhancement(
        self,
        finding_id: int,
        business_impact: str,
        attack_scenario: str,
        risk_context: str,
        provider: str = "AI",
    ) -> str:
        """
        Render AI-enhanced finding context.

        Args:
            finding_id: ID of the finding being enhanced
            business_impact: AI-generated business impact text
            attack_scenario: AI-generated attack scenario
            risk_context: AI-generated risk context
            provider: Name of AI provider

        Returns:
            str: Formatted markdown for insertion into finding
        """
        sections = []

        if business_impact:
            sections.append(f"""**Business Impact:**
{business_impact}""")

        if attack_scenario:
            sections.append(f"""**Attack Scenario:**
{attack_scenario}""")

        if risk_context:
            sections.append(f"""**Risk Context:**
{risk_context}""")

        if not sections:
            return ""

        content = "\n\n".join(sections)
        return f"""
#### AI-Enhanced Analysis

{content}

*Analysis by {provider}*
"""

    # =========================================================================
    # Detection Coverage Report Methods
    # =========================================================================

    def detection_title_page(self, engagement: Dict, generated_at) -> str:
        """Generate title page for detection coverage report."""
        return f"""# DETECTION COVERAGE REPORT
## {engagement.get('name', 'Unknown Engagement')}

**Generated:** {generated_at.strftime('%B %d, %Y at %H:%M:%S')}
**Report Type:** SIEM Detection Validation

---"""

    def detection_executive_summary(self, data) -> str:
        """
        Generate executive summary for detection coverage.

        Args:
            data: DetectionReportData object
        """
        summary = data.summary
        coverage = summary.coverage_percent

        # Determine risk level based on coverage
        if coverage >= 75:
            risk_level = "LOW"
            risk_icon = "🟢"
            risk_msg = "Good detection coverage"
        elif coverage >= 50:
            risk_level = "MEDIUM"
            risk_icon = "🟡"
            risk_msg = "Detection gaps identified"
        elif coverage >= 25:
            risk_level = "HIGH"
            risk_icon = "🟠"
            risk_msg = "Significant detection gaps"
        else:
            risk_level = "CRITICAL"
            risk_icon = "🔴"
            risk_msg = "Critical detection blindspots"

        # Use generated executive summary if available
        exec_summary_text = getattr(data, "executive_summary", "") or ""

        return f"""## EXECUTIVE SUMMARY

**Engagement:** {data.engagement.get('name', 'Unknown')}
**SIEM Type:** {data.siem_type.upper()}
**Coverage Rate:** {coverage}%
**Risk Level:** {risk_icon} **{risk_level}**

{exec_summary_text if exec_summary_text else f"{risk_msg}. {summary.not_detected} attack{'s were' if summary.not_detected != 1 else ' was'} not detected by the SIEM, representing potential blindspots in security monitoring."}

### KEY METRICS

| Metric | Value |
|--------|-------|
| Total Attacks Executed | {summary.total_attacks} |
| Detected by SIEM | {summary.detected} ({round(summary.detected/summary.total_attacks*100, 1) if summary.total_attacks > 0 else 0}%) |
| Not Detected | {summary.not_detected} ({round(summary.not_detected/summary.total_attacks*100, 1) if summary.total_attacks > 0 else 0}%) |
| Partial Detection | {summary.partial} |
| Offline Tools | {summary.offline} |
| MITRE Techniques Tested | {len(data.mitre_coverage)} |
| Hosts Assessed | {len(data.per_host_analysis)} |

---"""

    def detection_coverage_overview(self, data) -> str:
        """Generate detection coverage overview section."""
        summary = data.summary

        section = """## DETECTION COVERAGE OVERVIEW

This section summarizes which penetration test attacks triggered SIEM alerts and which were missed.

### Coverage Breakdown

"""
        # Status breakdown
        statuses = [
            ("Detected", summary.detected, "Attacks that triggered SIEM alerts"),
            (
                "Not Detected",
                summary.not_detected,
                "Attacks that did NOT trigger alerts (gaps)",
            ),
            ("Partial", summary.partial, "Attacks with some but incomplete detection"),
            (
                "Offline",
                summary.offline,
                "Offline tools (no network detection expected)",
            ),
            ("Unknown", summary.unknown, "Validation errors or inconclusive results"),
        ]

        for status, count, desc in statuses:
            if count > 0:
                section += f"- **{status}:** {count} - {desc}\n"

        section += "\n---\n"
        return section

    def mitre_heatmap_section(self, data) -> str:
        """
        Generate MITRE ATT&CK heatmap section in Markdown.

        For HTML reports, this is replaced by mitre_heatmap_html().
        """
        section = """## MITRE ATT&CK COVERAGE

The following matrix shows which MITRE ATT&CK techniques were tested during the engagement and their detection status.

### Legend
- ✅ **Detected** - SIEM generated alerts for this technique
- ❌ **Not Detected** - No SIEM alerts (detection gap)
- ⚠️ **Partial** - Some attacks detected, others missed
- ⬜ **Not Tested** - Technique not exercised

### Technique Coverage

"""
        # Group by tactic
        tactics_data = {}
        for item in data.heatmap_data:
            tactic = item["tactic_name"]
            if tactic not in tactics_data:
                tactics_data[tactic] = []
            tactics_data[tactic].append(item)

        for tactic, techniques in tactics_data.items():
            section += f"#### {tactic}\n\n"

            for tech in techniques:
                status = tech["status"]
                icon = {
                    "detected": "✅",
                    "not_detected": "❌",
                    "partial": "⚠️",
                    "not_tested": "⬜",
                }.get(status, "⬜")

                rate = f" ({tech['detection_rate']}%)" if tech["tested"] > 0 else ""
                tools = ", ".join(tech["tools_used"]) if tech["tools_used"] else "N/A"

                section += f"- {icon} **{tech['technique_id']}** - {tech['technique_name']}{rate}\n"
                section += f"  - Tools: {tools}\n"

            section += "\n"

        section += "---\n"
        return section

    def detected_attacks_table(self, data) -> str:
        """Generate table of attacks that triggered SIEM alerts."""
        detected = [r for r in data.detection_results if r.status == "detected"]

        if not detected:
            return """## DETECTED ATTACKS

No attacks triggered SIEM alerts during this assessment.

---
"""

        section = f"""## DETECTED ATTACKS

The following {len(detected)} attack{'s' if len(detected) != 1 else ''} successfully triggered SIEM alerts:

| Attack Type | Target | Alerts | Rule IDs | Timestamp |
|-------------|--------|--------|----------|-----------|
"""

        for result in detected[:50]:  # Limit to 50
            attack_type = result.attack_type or "Unknown"
            target = getattr(result, "target_ip", "N/A") or "N/A"
            alerts = result.alerts_count
            rules = ", ".join(result.rule_ids[:3]) if result.rule_ids else "N/A"
            if len(result.rule_ids) > 3:
                rules += "..."
            timestamp = (
                result.checked_at.strftime("%Y-%m-%d %H:%M")
                if result.checked_at
                else "N/A"
            )

            section += (
                f"| {attack_type} | {target} | {alerts} | {rules} | {timestamp} |\n"
            )

        section += "\n---\n"
        return section

    def detection_gaps_section(self, data) -> str:
        """Generate detection gaps analysis - attacks NOT detected."""
        gaps = data.gaps

        if not gaps:
            return """## DETECTION GAPS

No detection gaps identified. All executed attacks triggered SIEM alerts.

---
"""

        section = f"""## DETECTION GAPS

**CRITICAL:** The following {len(gaps)} attack{'s' if len(gaps) != 1 else ''} did NOT trigger SIEM alerts.
These represent blindspots in security monitoring that should be addressed.

| Priority | Attack Type | Target | MITRE Technique | Recommendation |
|----------|-------------|--------|-----------------|----------------|
"""

        for idx, gap in enumerate(gaps[:30], 1):  # Limit to 30
            attack_type = gap.attack_type or "Unknown"
            target = getattr(gap, "target_ip", "N/A") or "N/A"

            # Get MITRE technique
            from souleyez.detection.mitre_mappings import map_tool_to_techniques

            techniques = map_tool_to_techniques(attack_type)
            mitre = techniques[0]["id"] if techniques else "N/A"

            # Priority based on attack type severity
            from souleyez.detection.attack_signatures import get_signature

            sig = get_signature(attack_type)
            severity = sig.get("severity", "medium")
            priority_map = {
                "critical": "🔴 Critical",
                "high": "🟠 High",
                "medium": "🟡 Medium",
                "low": "🟢 Low",
            }
            priority = priority_map.get(severity, "🟡 Medium")

            section += f"| {priority} | {attack_type} | {target} | {mitre} | Add detection rules |\n"

        section += "\n---\n"
        return section

    def severity_breakdown_section(self, data) -> str:
        """Generate alert severity breakdown section."""
        severity = getattr(data, "severity_breakdown", None)
        if not severity or severity.total == 0:
            return """## ALERT SEVERITY BREAKDOWN

No alerts were generated during this assessment.

---
"""
        section = f"""## ALERT SEVERITY BREAKDOWN

Distribution of {severity.total} alerts by severity level:

| Severity | Count | Percentage |
|----------|-------|------------|
"""
        for level, count in [
            ("Critical", severity.critical),
            ("High", severity.high),
            ("Medium", severity.medium),
            ("Low", severity.low),
            ("Info", severity.info),
        ]:
            if count > 0:
                pct = round(count / severity.total * 100, 1)
                icon = {
                    "Critical": "🔴",
                    "High": "🟠",
                    "Medium": "🟡",
                    "Low": "🟢",
                    "Info": "⚪",
                }.get(level, "⚪")
                section += f"| {icon} {level} | {count} | {pct}% |\n"

        section += "\n---\n"
        return section

    def top_rules_section(self, data) -> str:
        """Generate top triggered rules section."""
        top_rules = getattr(data, "top_rules", [])
        if not top_rules:
            return """## TOP TRIGGERED RULES

No rules were triggered during this assessment.

---
"""
        section = f"""## TOP TRIGGERED RULES

The following SIEM rules generated the most alerts:

| # | Rule ID | Rule Name | Count | Severity |
|---|---------|-----------|-------|----------|
"""
        for idx, rule in enumerate(top_rules[:10], 1):
            sev_icon = {
                "critical": "🔴",
                "crit": "🔴",
                "high": "🟠",
                "medium": "🟡",
                "med": "🟡",
                "low": "🟢",
                "info": "⚪",
            }.get(rule.severity.lower(), "⚪")
            rule_name = (
                rule.rule_name[:50] + "..."
                if len(rule.rule_name) > 50
                else rule.rule_name
            )
            section += f"| {idx} | {rule.rule_id} | {rule_name} | {rule.count} | {sev_icon} {rule.severity.capitalize()} |\n"

        section += "\n---\n"
        return section

    def sample_alerts_section(self, data) -> str:
        """Generate sample alerts section with actual alert content."""
        samples = getattr(data, "sample_alerts", [])
        if not samples:
            return """## SAMPLE ALERTS

No sample alerts available.

---
"""
        section = f"""## SAMPLE ALERTS

Representative alerts from the assessment (highest severity first):

"""
        for idx, alert in enumerate(samples[:5], 1):
            sev_icon = {
                "critical": "🔴",
                "crit": "🔴",
                "high": "🟠",
                "medium": "🟡",
                "med": "🟡",
                "low": "🟢",
                "info": "⚪",
            }.get(alert.severity.lower(), "⚪")

            section += f"""### Alert {idx}: {alert.rule_name}

**Rule ID:** {alert.rule_id}
**Severity:** {sev_icon} {alert.severity.upper()}
**Source Attack:** {alert.source}
**Timestamp:** {alert.timestamp}

"""
            if alert.description:
                section += f"**Description:** {alert.description}\n\n"

            if alert.raw_snippet:
                section += f"""**Raw Log Snippet:**
```
{alert.raw_snippet}
```

"""
        section += "---\n"
        return section

    def vulnerability_section(self, data) -> str:
        """Generate Wazuh vulnerability section for detection report."""
        vuln_data = getattr(data, "vulnerability_section", None)

        if not vuln_data or vuln_data.total_vulns == 0:
            return """## VULNERABILITY CONTEXT

No vulnerability data available from Wazuh. Ensure Wazuh vulnerability detection is enabled and synced.

---
"""
        section = f"""## VULNERABILITY CONTEXT

This section shows known vulnerabilities on the assessed hosts from Wazuh's vulnerability detection module.
Cross-referencing with attack targets reveals which vulnerable systems were tested.

### Overall Vulnerability Summary

| Severity | Count |
|----------|-------|
| 🔴 Critical | {vuln_data.critical_count} |
| 🟠 High | {vuln_data.high_count} |
| 🟡 Medium | {vuln_data.medium_count} |
| 🟢 Low | {vuln_data.low_count} |
| **Total** | **{vuln_data.total_vulns}** |

**Hosts with Vulnerabilities:** {vuln_data.hosts_with_vulns}

"""
        # Top CVEs section
        if vuln_data.top_cves:
            section += """### Top CVEs by Severity

| CVE ID | Name | Severity | CVSS | Package |
|--------|------|----------|------|---------|
"""
            for cve in vuln_data.top_cves[:10]:
                sev_icon = {
                    "critical": "🔴",
                    "high": "🟠",
                    "medium": "🟡",
                    "low": "🟢",
                }.get(cve.severity.lower(), "⚪")
                name = cve.name[:40] + "..." if len(cve.name) > 40 else cve.name
                pkg = cve.package_name or "N/A"
                section += f"| {cve.cve_id} | {name} | {sev_icon} {cve.severity} | {cve.cvss_score:.1f} | {pkg} |\n"
            section += "\n"

        # Per-host vulnerability breakdown (attacked hosts first)
        attacked_hosts = [h for h in vuln_data.host_summaries if h.was_attacked]
        other_hosts = [h for h in vuln_data.host_summaries if not h.was_attacked]

        if attacked_hosts:
            section += """### Attacked Hosts - Vulnerability Status

These hosts were targeted during the assessment and have known vulnerabilities:

| Host | Agent | Critical | High | Medium | Low | Total |
|------|-------|----------|------|--------|-----|-------|
"""
            for host in attacked_hosts[:10]:
                section += f"| {host.host_ip} | {host.agent_name or 'N/A'} | {host.critical} | {host.high} | {host.medium} | {host.low} | {host.total_vulns} |\n"
            section += "\n"

            # Show top vulns for each attacked host
            for host in attacked_hosts[:5]:
                if host.top_vulns:
                    section += f"**{host.host_ip}** - Top Vulnerabilities:\n"
                    for v in host.top_vulns[:3]:
                        sev_icon = {
                            "critical": "🔴",
                            "high": "🟠",
                            "medium": "🟡",
                            "low": "🟢",
                        }.get(v.severity.lower(), "⚪")
                        section += f"- {sev_icon} **{v.cve_id}** (CVSS {v.cvss_score:.1f}) - {v.name[:60]}\n"
                    section += "\n"

        if other_hosts:
            section += """### Other Monitored Hosts

| Host | Agent | Critical | High | Medium | Low | Total |
|------|-------|----------|------|--------|-----|-------|
"""
            for host in other_hosts[:10]:
                section += f"| {host.host_ip} | {host.agent_name or 'N/A'} | {host.critical} | {host.high} | {host.medium} | {host.low} | {host.total_vulns} |\n"
            section += "\n"

        section += "---\n"
        return section

    def rule_recommendations_section(self, data) -> str:
        """Generate SIEM rule recommendations section."""
        recs = data.rule_recommendations

        if not recs:
            return """## RULE RECOMMENDATIONS

No specific rule recommendations. Detection coverage is adequate.

---
"""

        section = f"""## RULE RECOMMENDATIONS

The following recommendations will help close detection gaps:

"""
        for idx, rec in enumerate(recs[:20], 1):
            priority_icon = {
                "critical": "🔴",
                "high": "🟠",
                "medium": "🟡",
                "low": "🟢",
            }.get(rec.priority, "🟡")

            section += f"""### {idx}. {rec.attack_type.upper()} Detection

**Priority:** {priority_icon} {rec.priority.upper()}
**Gap:** {rec.gap_description}
**MITRE Technique:** {rec.mitre_technique}
**Category:** {rec.rule_category.replace('_', ' ').title()}

**Detection Guidance:**
{rec.detection_guidance}

"""
            if rec.suggested_rule_ids:
                section += (
                    f"**Suggested Rule IDs:** {', '.join(rec.suggested_rule_ids)}\n\n"
                )

        section += "---\n"
        return section

    def per_host_detection_section(self, data) -> str:
        """Generate per-host detection coverage breakdown."""
        hosts = data.per_host_analysis

        if not hosts:
            return """## PER-HOST ANALYSIS

No host-specific detection data available.

---
"""

        section = """## PER-HOST DETECTION ANALYSIS

Detection coverage broken down by target host:

| Host | Attacks | Detected | Not Detected | Coverage |
|------|---------|----------|--------------|----------|
"""

        # Sort by coverage (lowest first to highlight problem areas)
        sorted_hosts = sorted(hosts.values(), key=lambda h: h.coverage_percent)

        for host in sorted_hosts[:20]:  # Limit to 20
            coverage_icon = (
                "🟢"
                if host.coverage_percent >= 75
                else "🟡" if host.coverage_percent >= 50 else "🔴"
            )
            section += f"| {host.host_ip} | {host.total_attacks} | {host.detected} | {host.not_detected} | {coverage_icon} {host.coverage_percent}% |\n"

        section += "\n---\n"
        return section


class HTMLFormatter(MarkdownFormatter):
    """Format report sections as HTML with CSS styling."""

    def html_header(self, title: str) -> str:
        """Generate HTML header with CSS."""
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - Penetration Test Report</title>
    <style>
        /* Base Typography & Layout */
        * {{
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.7;
            color: #2c3e50;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            font-size: 16px;
        }}
        
        .container {{
            background-color: #ffffff;
            padding: 50px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            border-radius: 8px;
            min-height: 100vh;
        }}
        
        /* Enhanced Typography */
        h1 {{
            font-size: 2.5em;
            color: #1a202c;
            border-bottom: 4px solid #3498db;
            padding-bottom: 15px;
            margin-top: 0;
            font-weight: 700;
            letter-spacing: -0.5px;
        }}
        
        h2 {{
            font-size: 2em;
            color: #2d3748;
            border-bottom: 3px solid #e74c3c;
            padding-bottom: 12px;
            margin-top: 50px;
            margin-bottom: 25px;
            font-weight: 600;
            letter-spacing: -0.3px;
        }}
        
        h3 {{
            font-size: 1.5em;
            color: #4a5568;
            margin-top: 30px;
            margin-bottom: 15px;
            font-weight: 600;
        }}
        
        h4 {{
            font-size: 1.2em;
            color: #718096;
            margin-top: 20px;
            margin-bottom: 10px;
            font-weight: 600;
        }}
        
        p {{
            margin-bottom: 1.2em;
            line-height: 1.8;
        }}
        
        strong {{
            font-weight: 600;
            color: #2d3748;
        }}
        
        /* Severity Colors */
        .severity-critical {{
            color: #dc3545;
            font-weight: 700;
        }}
        .severity-high {{
            color: #fd7e14;
            font-weight: 700;
        }}
        .severity-medium {{
            color: #f39c12;
            font-weight: 700;
        }}
        .severity-low {{
            color: #28a745;
            font-weight: 700;
        }}
        .severity-info {{
            color: #17a2b8;
            font-weight: 600;
        }}
        
        /* Tables */
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 25px 0;
            font-size: 0.95em;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            border-radius: 8px;
            overflow: hidden;
        }}
        
        th, td {{
            border: 1px solid #e2e8f0;
            padding: 14px 16px;
            text-align: left;
        }}
        
        th {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.85em;
            letter-spacing: 0.5px;
        }}
        
        tr:nth-child(even) {{
            background-color: #f7fafc;
        }}
        
        tr:hover {{
            background-color: #edf2f7;
            transition: background-color 0.2s ease;
        }}
        
        /* Finding Cards */
        .finding {{
            border-left: 5px solid #e74c3c;
            padding: 20px 25px;
            margin: 35px 0;
            background-color: #f8f9fa;
            border-radius: 0 8px 8px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }}
        
        /* Footer */
        .footer {{
            margin-top: 80px;
            padding-top: 30px;
            border-top: 3px solid #e2e8f0;
            text-align: center;
            color: #718096;
            font-size: 0.9em;
        }}
        
        hr {{
            border: none;
            border-top: 2px solid #e2e8f0;
            margin: 40px 0;
        }}
        
        /* Lists */
        ul, ol {{
            margin: 15px 0;
            padding-left: 30px;
        }}
        
        li {{
            margin-bottom: 8px;
            line-height: 1.6;
        }}
        
        /* Code Blocks */
        code {{
            background-color: #f1f5f9;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', Courier, monospace;
            font-size: 0.9em;
            color: #e74c3c;
        }}
        
        pre {{
            background-color: #1e293b;
            color: #e2e8f0;
            padding: 20px;
            border-radius: 8px;
            overflow-x: auto;
            font-size: 0.9em;
            line-height: 1.6;
        }}
        
        /* Executive Dashboard Styles */
        .dashboard {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 25px;
            margin: 35px 0;
        }}
        
        .metric-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }}
        
        .metric-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(102, 126, 234, 0.5);
        }}
        
        .metric-card.risk-critical {{
            background: linear-gradient(135deg, #dc3545 0%, #bd2130 100%);
            box-shadow: 0 6px 20px rgba(220, 53, 69, 0.4);
        }}
        .metric-card.risk-high {{
            background: linear-gradient(135deg, #fd7e14 0%, #e8590c 100%);
            box-shadow: 0 6px 20px rgba(253, 126, 20, 0.4);
        }}
        .metric-card.risk-medium {{
            background: linear-gradient(135deg, #ffc107 0%, #e0a800 100%);
            box-shadow: 0 6px 20px rgba(255, 193, 7, 0.4);
        }}
        .metric-card.risk-low {{
            background: linear-gradient(135deg, #28a745 0%, #218838 100%);
            box-shadow: 0 6px 20px rgba(40, 167, 69, 0.4);
        }}
        
        .metric-value {{
            font-size: 3em;
            font-weight: 800;
            margin: 15px 0;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }}
        
        .metric-label {{
            font-size: 0.95em;
            opacity: 0.95;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        /* Chart Container */
        .chart-container {{
            margin: 30px 0;
            padding: 30px;
            background: #ffffff;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.08);
            border: 1px solid #e2e8f0;
        }}
        
        .charts-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(450px, 1fr));
            gap: 35px;
            margin: 35px 0;
        }}
        
        /* Collapsible Findings */
        details {{
            margin: 25px 0;
            border: 2px solid #e2e8f0;
            border-radius: 8px;
            overflow: hidden;
            transition: all 0.3s ease;
        }}
        
        details:hover {{
            border-color: #cbd5e0;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }}
        
        summary {{
            padding: 20px 25px;
            background: linear-gradient(135deg, #f7fafc 0%, #edf2f7 100%);
            cursor: pointer;
            font-weight: 700;
            font-size: 1.2em;
            user-select: none;
            transition: all 0.2s ease;
        }}
        
        summary:hover {{
            background: linear-gradient(135deg, #edf2f7 0%, #e2e8f0 100%);
        }}
        
        details[open] summary {{
            border-bottom: 2px solid #cbd5e0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }}
        
        details .findings-content {{
            padding: 30px;
            background-color: #ffffff;
        }}
        
        /* Finding Cards */
        .finding-card {{
            margin-bottom: 30px;
            padding: 25px;
            background: #ffffff;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }}
        
        .finding-card h3 {{
            margin-top: 0;
            color: #2d3748;
        }}
        
        .finding-card p {{
            margin: 10px 0;
            line-height: 1.6;
        }}
        
        .finding-card code {{
            background-color: #667eea;
            color: white;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.85em;
            margin-right: 5px;
        }}
        
        .finding-card strong {{
            color: #2d3748;
            font-weight: 600;
        }}
        
        .finding-card hr {{
            margin: 20px 0;
            border-color: #e2e8f0;
        }}
        
        .severity-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .severity-count {{
            background-color: rgba(255,255,255,0.9);
            color: #2d3748;
            padding: 6px 18px;
            border-radius: 25px;
            font-size: 0.9em;
            font-weight: 600;
        }}
        
        details[open] .severity-count {{
            background-color: rgba(255,255,255,0.95);
        }}
        
        .collapse-controls {{
            margin: 25px 0;
            text-align: right;
        }}
        
        .btn {{
            padding: 12px 24px;
            margin-left: 12px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 0.95em;
            font-weight: 600;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            transition: all 0.3s ease;
            box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
        }}
        
        .btn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
        }}
        
        .btn:active {{
            transform: translateY(0);
        }}
        
        /* Responsive Design */
        @media (max-width: 768px) {{
            body {{
                padding: 10px;
                font-size: 14px;
            }}
            
            .container {{
                padding: 25px;
            }}
            
            h1 {{
                font-size: 2em;
            }}
            
            h2 {{
                font-size: 1.6em;
            }}
            
            .dashboard {{
                grid-template-columns: 1fr;
            }}
            
            .charts-grid {{
                grid-template-columns: 1fr;
            }}
            
            .metric-value {{
                font-size: 2.5em;
            }}
        }}
        
        /* Executive One-Pager Styles */
        .exec-one-pager {{
            background: linear-gradient(135deg, #1a1a2e 0%, #0f0f23 100%);
            color: white;
            padding: 40px;
            border-radius: 12px;
            margin-bottom: 40px;
            page-break-after: always;
        }}

        .exec-one-pager h1 {{
            color: #00d4ff;
            border-bottom: 3px solid #00d4ff;
            font-size: 2em;
            margin-top: 0;
            padding-bottom: 15px;
        }}

        .exec-hero {{
            display: grid;
            grid-template-columns: 1fr 2fr;
            gap: 30px;
            margin: 30px 0;
        }}

        .exec-risk-score {{
            text-align: center;
            padding: 30px;
            background: rgba(255,255,255,0.05);
            border-radius: 12px;
            border: 2px solid rgba(255,255,255,0.1);
        }}

        .exec-risk-score .score-value {{
            font-size: 5em;
            font-weight: 800;
            line-height: 1;
        }}

        .exec-risk-score .score-label {{
            font-size: 1.2em;
            margin-top: 10px;
            opacity: 0.9;
        }}

        .exec-risk-score.critical .score-value {{ color: #ff4757; }}
        .exec-risk-score.high .score-value {{ color: #ffa502; }}
        .exec-risk-score.medium .score-value {{ color: #ffc107; }}
        .exec-risk-score.low .score-value {{ color: #2ed573; }}

        .exec-key-stats {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 15px;
        }}

        .exec-stat-card {{
            background: rgba(255,255,255,0.05);
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #00d4ff;
        }}

        .exec-stat-card.critical {{ border-left-color: #ff4757; }}
        .exec-stat-card.high {{ border-left-color: #ffa502; }}
        .exec-stat-card.money {{ border-left-color: #2ed573; }}

        .exec-stat-value {{
            font-size: 2em;
            font-weight: 700;
            color: #00d4ff;
        }}

        .exec-stat-card.critical .exec-stat-value {{ color: #ff4757; }}
        .exec-stat-card.high .exec-stat-value {{ color: #ffa502; }}
        .exec-stat-card.money .exec-stat-value {{ color: #2ed573; }}

        .exec-stat-label {{
            font-size: 0.85em;
            opacity: 0.8;
            margin-top: 5px;
        }}

        .exec-top-findings {{
            margin-top: 30px;
        }}

        .exec-top-findings h3 {{
            color: #ff4757;
            font-size: 1.1em;
            margin-bottom: 15px;
            border: none;
        }}

        .exec-finding-row {{
            display: flex;
            align-items: center;
            padding: 12px 15px;
            background: rgba(255,255,255,0.03);
            border-radius: 6px;
            margin-bottom: 8px;
            border-left: 3px solid #ff4757;
        }}

        .exec-finding-row.high {{ border-left-color: #ffa502; }}

        .exec-finding-num {{
            background: #ff4757;
            color: white;
            width: 24px;
            height: 24px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.8em;
            font-weight: 700;
            margin-right: 12px;
        }}

        .exec-finding-row.high .exec-finding-num {{ background: #ffa502; }}

        .exec-finding-title {{
            flex: 1;
            font-weight: 500;
        }}

        .exec-finding-host {{
            color: #888;
            font-size: 0.85em;
        }}

        .exec-bottom-line {{
            margin-top: 30px;
            padding: 20px;
            background: linear-gradient(135deg, #ff4757 0%, #ff6b81 100%);
            border-radius: 8px;
            text-align: center;
        }}

        .exec-bottom-line.medium {{
            background: linear-gradient(135deg, #ffa502 0%, #ffc048 100%);
        }}

        .exec-bottom-line.low {{
            background: linear-gradient(135deg, #2ed573 0%, #7bed9f 100%);
            color: #1a1a2e;
        }}

        .exec-bottom-line p {{
            margin: 0;
            font-size: 1.1em;
            font-weight: 600;
        }}

        /* Risk Quadrant Styles */
        .risk-quadrant {{
            margin: 30px 0;
            padding: 25px;
            background: #f8f9fa;
            border-radius: 12px;
        }}

        .quadrant-grid {{
            display: grid;
            grid-template-columns: 30px 1fr 1fr;
            grid-template-rows: auto 150px 150px 30px;
            gap: 2px;
            background: #dee2e6;
            border-radius: 8px;
            overflow: hidden;
        }}

        .quadrant-label {{
            background: #f8f9fa;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.75em;
            font-weight: 600;
            color: #666;
        }}

        .quadrant-label.vertical {{
            writing-mode: vertical-rl;
            text-orientation: mixed;
            transform: rotate(180deg);
        }}

        .quadrant-cell {{
            background: white;
            padding: 15px;
            position: relative;
        }}

        .quadrant-cell.critical {{ background: #fff5f5; }}
        .quadrant-cell.high {{ background: #fff8f0; }}
        .quadrant-cell.medium {{ background: #fffef0; }}
        .quadrant-cell.low {{ background: #f0fff4; }}

        .quadrant-title {{
            font-size: 0.7em;
            font-weight: 700;
            text-transform: uppercase;
            color: #999;
            margin-bottom: 10px;
        }}

        .quadrant-cell.critical .quadrant-title {{ color: #dc3545; }}
        .quadrant-cell.high .quadrant-title {{ color: #fd7e14; }}

        .quadrant-findings {{
            display: flex;
            flex-wrap: wrap;
            gap: 5px;
        }}

        .quadrant-dot {{
            width: 28px;
            height: 28px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.7em;
            font-weight: 700;
            color: white;
            cursor: default;
        }}

        .quadrant-dot.critical {{ background: #dc3545; }}
        .quadrant-dot.high {{ background: #fd7e14; }}
        .quadrant-dot.medium {{ background: #ffc107; color: #333; }}
        .quadrant-dot.low {{ background: #28a745; }}

        /* Severity Badges */
        .severity-badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.75em;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        .severity-badge.critical {{
            background: #dc3545;
            color: white;
        }}

        .severity-badge.high {{
            background: #fd7e14;
            color: white;
        }}

        .severity-badge.medium {{
            background: #ffc107;
            color: #333;
        }}

        .severity-badge.low {{
            background: #28a745;
            color: white;
        }}

        .severity-badge.info {{
            background: #17a2b8;
            color: white;
        }}

        /* Remediation Timeline */
        .remediation-timeline {{
            margin: 30px 0;
            padding: 25px;
            background: #f8f9fa;
            border-radius: 12px;
        }}

        .timeline-bar {{
            display: flex;
            height: 40px;
            border-radius: 8px;
            overflow: hidden;
            margin: 20px 0;
        }}

        .timeline-segment {{
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: 600;
            font-size: 0.85em;
            transition: flex 0.3s ease;
        }}

        .timeline-segment.critical {{ background: #dc3545; }}
        .timeline-segment.high {{ background: #fd7e14; }}
        .timeline-segment.medium {{ background: #ffc107; color: #333; }}
        .timeline-segment.low {{ background: #28a745; }}

        .timeline-legend {{
            display: flex;
            justify-content: space-around;
            margin-top: 15px;
        }}

        .timeline-legend-item {{
            text-align: center;
        }}

        .timeline-legend-label {{
            font-size: 0.8em;
            color: #666;
        }}

        .timeline-legend-value {{
            font-size: 1.1em;
            font-weight: 700;
        }}

        /* Evidence in Findings */
        .finding-evidence {{
            margin-top: 15px;
            padding: 15px;
            background: #1e293b;
            border-radius: 8px;
            border-left: 3px solid #00d4ff;
        }}

        .finding-evidence-label {{
            color: #00d4ff;
            font-size: 0.8em;
            font-weight: 600;
            margin-bottom: 8px;
            text-transform: uppercase;
        }}

        .finding-evidence pre {{
            margin: 0;
            font-size: 0.85em;
            white-space: pre-wrap;
            word-break: break-all;
        }}

        /* Print Optimizations */
        @media print {{
            .exec-one-pager {{
                page-break-after: always;
                -webkit-print-color-adjust: exact;
                print-color-adjust: exact;
            }}

            .page-break {{
                page-break-before: always;
            }}

            .no-print {{
                display: none !important;
            }}

            .intel-hub, .exec-one-pager {{
                -webkit-print-color-adjust: exact;
                print-color-adjust: exact;
            }}
        }}

        /* Intelligence Hub Styles */
        .intel-hub {{
            margin: 35px 0;
            padding: 30px;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            border-radius: 12px;
            box-shadow: 0 6px 20px rgba(0,0,0,0.3);
        }}

        .intel-hub h2 {{
            color: #00d4ff;
            border-bottom: 2px solid #00d4ff;
            margin-top: 0;
            font-size: 1.4em;
            letter-spacing: 2px;
        }}

        .intel-hub-summary {{
            display: flex;
            flex-wrap: wrap;
            gap: 20px;
            margin-bottom: 25px;
            padding: 15px;
            background: rgba(0, 212, 255, 0.1);
            border-radius: 8px;
            border: 1px solid rgba(0, 212, 255, 0.3);
        }}

        .intel-stat {{
            color: #e2e8f0;
            font-size: 0.95em;
        }}

        .intel-stat-value {{
            color: #00d4ff;
            font-weight: 700;
        }}

        .top-target {{
            background: linear-gradient(135deg, #ff6b35 0%, #f7931e 100%);
            padding: 15px 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            color: white;
        }}

        .top-target-label {{
            font-size: 0.85em;
            opacity: 0.9;
            margin-bottom: 5px;
        }}

        .top-target-host {{
            font-size: 1.2em;
            font-weight: 700;
        }}

        .top-target-stats {{
            font-size: 0.9em;
            opacity: 0.95;
            margin-top: 5px;
        }}

        .intel-hub-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.9em;
        }}

        .intel-hub-table th {{
            background: rgba(0, 212, 255, 0.2);
            color: #00d4ff;
            padding: 12px 15px;
            text-align: left;
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.8em;
            letter-spacing: 1px;
            border-bottom: 2px solid rgba(0, 212, 255, 0.3);
        }}

        .intel-hub-table td {{
            padding: 12px 15px;
            color: #e2e8f0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }}

        .intel-hub-table tr:hover {{
            background: rgba(0, 212, 255, 0.1);
        }}

        .score-critical {{
            color: #ff4757;
            font-weight: 700;
        }}

        .score-high {{
            color: #ffa502;
            font-weight: 700;
        }}

        .score-medium {{
            color: #2ed573;
            font-weight: 600;
        }}

        .findings-critical {{
            color: #ff4757;
            font-weight: 700;
        }}

        .exploit-progress {{
            display: flex;
            align-items: center;
            gap: 8px;
        }}

        .progress-bar {{
            display: inline-block;
            font-family: monospace;
            font-size: 0.85em;
        }}

        .progress-filled {{
            color: #2ed573;
        }}

        .progress-empty {{
            color: #555;
        }}

        .exploit-ratio {{
            color: #a0a0a0;
            font-size: 0.85em;
        }}

        /* Mermaid Diagram Container */
        .mermaid-container {{
            margin: 30px 0;
            padding: 30px;
            background: #ffffff;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.08);
            border: 1px solid #e2e8f0;
            overflow-x: auto;
        }}
        
        .mermaid {{
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 300px;
        }}
        
        /* Print Styles */
        @media print {{
            body {{
                background: white;
                padding: 0;
            }}
            
            .container {{
                box-shadow: none;
                max-width: 100%;
                padding: 20px;
            }}
            
            .collapse-controls {{
                display: none;
            }}
            
            details {{
                border: 1px solid #ccc;
                page-break-inside: avoid;
            }}
            
            summary {{
                display: none;
            }}
            
            details .findings-content {{
                display: block !important;
                padding: 15px;
            }}
            
            .metric-card {{
                page-break-inside: avoid;
                box-shadow: none;
            }}
            
            .chart-container {{
                page-break-inside: avoid;
            }}
            
            h2 {{
                page-break-after: avoid;
            }}
            
            table {{
                page-break-inside: avoid;
            }}
            
            .mermaid-container {{
                page-break-inside: avoid;
            }}
        }}
    </style>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10.6.1/dist/mermaid.min.js"></script>
    <script>
        // Initialize Mermaid
        mermaid.initialize({{ 
            startOnLoad: true,
            theme: 'default',
            securityLevel: 'loose',
            flowchart: {{
                useMaxWidth: true,
                htmlLabels: true,
                curve: 'basis'
            }}
        }});
    </script>
</head>
<body>
<div class="container">
"""

    def executive_one_pager(
        self, metrics: Dict, findings: Dict, engagement: Dict
    ) -> str:
        """Generate executive one-pager - single page summary for executives."""
        risk_level = metrics.get("risk_level", "MEDIUM").lower()
        risk_score = metrics.get("risk_score", 50)

        # Get top findings
        critical = findings.get("critical", [])
        high = findings.get("high", [])
        top_findings = (critical + high)[:5]

        # Calculate estimated breach cost (rough estimate based on findings)
        critical_count = len(critical)
        high_count = len(high)
        # Base cost estimates: Critical = $500K avg, High = $100K avg
        estimated_cost = (critical_count * 500000) + (high_count * 100000)
        if estimated_cost >= 1000000:
            cost_display = f"${estimated_cost / 1000000:.1f}M"
        else:
            cost_display = f"${estimated_cost / 1000:.0f}K"

        html = f"""<div class="exec-one-pager">
<h1>SECURITY ASSESSMENT SUMMARY</h1>
<p style="opacity: 0.7; margin-top: -10px;">{engagement.get('name', 'Penetration Test')} | {engagement.get('created_at', '')[:10] if engagement.get('created_at') else 'N/A'}</p>

<div class="exec-hero">
    <div class="exec-risk-score {risk_level}">
        <div class="score-value">{risk_score}</div>
        <div class="score-label">RISK SCORE</div>
    </div>

    <div class="exec-key-stats">
        <div class="exec-stat-card critical">
            <div class="exec-stat-value">{critical_count}</div>
            <div class="exec-stat-label">Critical Findings</div>
        </div>
        <div class="exec-stat-card high">
            <div class="exec-stat-value">{high_count}</div>
            <div class="exec-stat-label">High Findings</div>
        </div>
        <div class="exec-stat-card">
            <div class="exec-stat-value">{metrics.get('total_hosts', 0)}</div>
            <div class="exec-stat-label">Hosts Tested</div>
        </div>
        <div class="exec-stat-card money">
            <div class="exec-stat-value">{cost_display}</div>
            <div class="exec-stat-label">Est. Breach Risk</div>
        </div>
    </div>
</div>
"""

        # Top findings section
        if top_findings:
            html += """<div class="exec-top-findings">
<h3>TOP SECURITY RISKS</h3>
"""
            for idx, finding in enumerate(top_findings, 1):
                severity = finding.get("severity", "high")
                sev_class = "high" if severity == "high" else ""
                title = finding.get("title", "Finding")[:50]
                host = finding.get("ip_address", finding.get("hostname", "Unknown"))

                html += f"""<div class="exec-finding-row {sev_class}">
    <div class="exec-finding-num">{idx}</div>
    <div class="exec-finding-title">{title}</div>
    <div class="exec-finding-host">{host}</div>
</div>
"""
            html += "</div>\n"

        # Bottom line recommendation
        if risk_level in ["critical", "high"]:
            bottom_class = ""
            bottom_msg = "IMMEDIATE ACTION REQUIRED: Critical vulnerabilities expose your organization to significant risk. Remediation should begin within 24-48 hours."
        elif risk_level == "medium":
            bottom_class = "medium"
            bottom_msg = "ACTION RECOMMENDED: Several security issues require attention within the next 1-2 weeks to maintain security posture."
        else:
            bottom_class = "low"
            bottom_msg = "GOOD STANDING: Minor issues identified. Continue regular security maintenance and monitoring."

        html += f"""<div class="exec-bottom-line {bottom_class}">
<p>{bottom_msg}</p>
</div>
</div>
"""
        return html

    def risk_quadrant(self, findings: Dict) -> str:
        """Generate risk quadrant showing Impact vs Exploitability."""
        all_findings = []
        for severity, items in findings.items():
            for f in items:
                f["_severity"] = severity
                all_findings.append(f)

        if not all_findings:
            return ""

        # Categorize findings into quadrants based on severity and exploitability
        # High Impact + Easy to Exploit = Critical (top-right)
        # High Impact + Hard to Exploit = High (top-left)
        # Low Impact + Easy to Exploit = Medium (bottom-right)
        # Low Impact + Hard to Exploit = Low (bottom-left)

        quadrants = {
            "critical": [],  # High impact, easy exploit
            "high": [],  # High impact, hard exploit
            "medium": [],  # Low impact, easy exploit
            "low": [],  # Low impact, hard exploit
        }

        for f in all_findings:
            sev = f.get("_severity", "info")
            if sev == "critical":
                quadrants["critical"].append(f)
            elif sev == "high":
                quadrants["high"].append(f)
            elif sev == "medium":
                quadrants["medium"].append(f)
            elif sev == "low":
                quadrants["low"].append(f)

        def render_dots(findings_list, severity, max_dots=12):
            dots = ""
            for i, f in enumerate(findings_list[:max_dots]):
                title = f.get("title", "Finding")[:20]
                dots += (
                    f'<div class="quadrant-dot {severity}" title="{title}">{i+1}</div>'
                )
            if len(findings_list) > max_dots:
                dots += f'<div class="quadrant-dot {severity}">+{len(findings_list) - max_dots}</div>'
            return dots

        html = """<div class="risk-quadrant">
<h3>Risk Assessment Matrix</h3>
<p style="color: #666; font-size: 0.9em;">Findings plotted by business impact vs. ease of exploitation</p>

<div class="quadrant-grid">
    <div class="quadrant-label"></div>
    <div class="quadrant-label">Hard to Exploit</div>
    <div class="quadrant-label">Easy to Exploit</div>

    <div class="quadrant-label vertical">High Impact</div>
    <div class="quadrant-cell high">
        <div class="quadrant-title">Monitor</div>
        <div class="quadrant-findings">
"""
        html += render_dots(quadrants["high"], "high")
        html += """        </div>
    </div>
    <div class="quadrant-cell critical">
        <div class="quadrant-title">Fix Now</div>
        <div class="quadrant-findings">
"""
        html += render_dots(quadrants["critical"], "critical")
        html += """        </div>
    </div>

    <div class="quadrant-label vertical">Low Impact</div>
    <div class="quadrant-cell low">
        <div class="quadrant-title">Accept Risk</div>
        <div class="quadrant-findings">
"""
        html += render_dots(quadrants["low"], "low")
        html += """        </div>
    </div>
    <div class="quadrant-cell medium">
        <div class="quadrant-title">Schedule Fix</div>
        <div class="quadrant-findings">
"""
        html += render_dots(quadrants["medium"], "medium")
        html += """        </div>
    </div>

    <div class="quadrant-label"></div>
    <div class="quadrant-label"></div>
    <div class="quadrant-label"></div>
</div>
</div>
"""
        return html

    def remediation_timeline(self, metrics: Dict) -> str:
        """Generate visual remediation timeline."""
        timeline = metrics.get("remediation_timeline", {})
        total_days = timeline.get("total_days", 30)

        critical_days = timeline.get("critical", 2)
        high_days = timeline.get("high", 7)
        medium_days = timeline.get("medium", 14)
        low_days = timeline.get("low", 7)

        # Calculate percentages
        if total_days > 0:
            critical_pct = (critical_days / total_days) * 100
            high_pct = (high_days / total_days) * 100
            medium_pct = (medium_days / total_days) * 100
            low_pct = (low_days / total_days) * 100
        else:
            critical_pct = high_pct = medium_pct = low_pct = 25

        html = f"""<div class="remediation-timeline">
<h3>Remediation Timeline</h3>
<p style="color: #666; font-size: 0.9em;">Estimated effort by severity - Total: {total_days:.0f} days</p>

<div class="timeline-bar">
"""
        if critical_pct > 0:
            html += f'    <div class="timeline-segment critical" style="flex: {critical_pct};">Critical</div>\n'
        if high_pct > 0:
            html += f'    <div class="timeline-segment high" style="flex: {high_pct};">High</div>\n'
        if medium_pct > 0:
            html += f'    <div class="timeline-segment medium" style="flex: {medium_pct};">Medium</div>\n'
        if low_pct > 0:
            html += f'    <div class="timeline-segment low" style="flex: {low_pct};">Low</div>\n'

        html += f"""</div>

<div class="timeline-legend">
    <div class="timeline-legend-item">
        <div class="timeline-legend-value" style="color: #dc3545;">{critical_days:.0f}d</div>
        <div class="timeline-legend-label">Critical (24-48h)</div>
    </div>
    <div class="timeline-legend-item">
        <div class="timeline-legend-value" style="color: #fd7e14;">{high_days:.0f}d</div>
        <div class="timeline-legend-label">High (1 week)</div>
    </div>
    <div class="timeline-legend-item">
        <div class="timeline-legend-value" style="color: #ffc107;">{medium_days:.0f}d</div>
        <div class="timeline-legend-label">Medium (2 weeks)</div>
    </div>
    <div class="timeline-legend-item">
        <div class="timeline-legend-value" style="color: #28a745;">{low_days:.0f}d</div>
        <div class="timeline-legend-label">Low (30+ days)</div>
    </div>
</div>
</div>
"""
        return html

    def executive_dashboard(self, metrics: Dict) -> str:
        """Generate executive dashboard with key metrics."""
        risk_class = f"risk-{metrics['risk_color']}"

        html = """<div id="executive-dashboard">
<h2>EXECUTIVE DASHBOARD</h2>

<div class="dashboard">
"""

        # Risk Score Card
        html += f"""    <div class="metric-card {risk_class}">
        <div class="metric-label">OVERALL RISK SCORE</div>
        <div class="metric-value">{metrics['risk_score']}/100</div>
        <div class="metric-label">{metrics['risk_level']}</div>
    </div>
"""

        # Total Findings Card
        html += f"""    <div class="metric-card">
        <div class="metric-label">TOTAL FINDINGS</div>
        <div class="metric-value">{metrics['total_findings']}</div>
        <div class="metric-label">{metrics['critical_findings']} Critical | {metrics['high_findings']} High</div>
    </div>
"""

        # Hosts Assessed Card
        html += f"""    <div class="metric-card">
        <div class="metric-label">HOSTS ASSESSED</div>
        <div class="metric-value">{metrics['total_hosts']}</div>
        <div class="metric-label">{metrics['vulnerable_hosts']} Vulnerable</div>
    </div>
"""

        # Exploitation Rate Card
        html += f"""    <div class="metric-card">
        <div class="metric-label">EXPLOITATION RATE</div>
        <div class="metric-value">{metrics['exploitation_rate']}%</div>
        <div class="metric-label">{metrics['exploited_services']}/{metrics['total_services']} Services</div>
    </div>
"""

        # Remediation Timeline Card
        timeline = metrics["remediation_timeline"]
        html += f"""    <div class="metric-card">
        <div class="metric-label">ESTIMATED REMEDIATION</div>
        <div class="metric-value">{timeline['weeks']}</div>
        <div class="metric-label">Weeks (~{timeline['total_days']} days)</div>
    </div>
"""

        # Credentials Found Card
        html += f"""    <div class="metric-card">
        <div class="metric-label">CREDENTIALS FOUND</div>
        <div class="metric-value">{metrics['credentials_found']}</div>
        <div class="metric-label">Valid Credentials</div>
    </div>
"""

        html += "</div>\n</div>\n\n---\n\n"
        return html

    def intelligence_hub_section(self, attack_surface: Dict) -> str:
        """Generate Intelligence Hub section with prioritized target table."""
        if not attack_surface:
            return ""

        overview = attack_surface.get("overview", {})
        hosts = attack_surface.get("hosts", [])

        if not hosts:
            return ""

        # Calculate gap count (services not exploited)
        total_services = overview.get("total_services", 0)
        exploited_services = overview.get("exploited_services", 0)
        gap_count = total_services - exploited_services

        html = """<div class="intel-hub">
<h2>INTELLIGENCE HUB</h2>

<div class="intel-hub-summary">
"""
        # Summary stats
        html += f'    <span class="intel-stat">Hosts: <span class="intel-stat-value">{overview.get("total_hosts", 0)}</span></span>\n'
        html += f'    <span class="intel-stat">Services: <span class="intel-stat-value">{total_services}</span></span>\n'
        html += f'    <span class="intel-stat">Exploited: <span class="intel-stat-value">{exploited_services}</span></span>\n'
        html += f'    <span class="intel-stat">Gaps: <span class="intel-stat-value">{gap_count}</span></span>\n'
        html += f'    <span class="intel-stat">Credentials: <span class="intel-stat-value">{overview.get("credentials_found", 0)}</span></span>\n'
        html += "</div>\n\n"

        # Top target callout
        if hosts:
            top = hosts[0]
            top_ip = top.get("host", "unknown")
            top_hostname = top.get("hostname", "")
            top_score = top.get("score", 0)
            top_services = top.get("services", [])
            top_exploited = sum(
                1 for s in top_services if s.get("status") == "exploited"
            )
            top_total_svc = len(top_services)
            top_critical = top.get("critical_findings", 0)
            top_findings = top.get("findings", 0)

            top_display = top_ip
            if top_hostname:
                top_display += f" ({top_hostname})"

            html += '<div class="top-target">\n'
            html += '    <div class="top-target-label">TOP TARGET</div>\n'
            html += f'    <div class="top-target-host">{top_display}</div>\n'
            html += f'    <div class="top-target-stats">Score: {top_score} pts | {top_exploited}/{top_total_svc} services exploited | '
            if top_critical > 0:
                html += f"{top_critical} critical, {top_findings - top_critical} high findings"
            else:
                html += f"{top_findings} findings"
            html += "</div>\n"
            html += "</div>\n\n"

        # Host table
        # Limit to top 10 hosts for readability
        max_hosts = 10
        display_hosts = hosts[:max_hosts]
        remaining_hosts = len(hosts) - max_hosts

        html += """<table class="intel-hub-table">
<thead>
    <tr>
        <th>#</th>
        <th>Host</th>
        <th>Score</th>
        <th>Services</th>
        <th>Findings</th>
        <th>Exploited</th>
    </tr>
</thead>
<tbody>
"""

        for idx, host in enumerate(display_hosts, 1):
            host_ip = host.get("host", "unknown")
            hostname = host.get("hostname", "")
            score = host.get("score", 0)
            services = host.get("services", [])
            service_count = len(services)
            findings = host.get("findings", 0)
            critical = host.get("critical_findings", 0)

            # Score color class
            if score >= 70:
                score_class = "score-critical"
            elif score >= 50:
                score_class = "score-high"
            else:
                score_class = "score-medium"

            # Host display
            host_display = host_ip
            if hostname:
                host_display += f"<br><small style='color: #888;'>{hostname}</small>"

            # Findings display
            if critical > 0:
                findings_display = f'<span class="findings-critical">{findings} ({critical} critical)</span>'
            else:
                findings_display = str(findings)

            # Exploitation progress
            exploited = sum(1 for s in services if s.get("status") == "exploited")
            progress_filled = min(
                8, int((exploited / service_count * 8) if service_count > 0 else 0)
            )
            progress_empty = 8 - progress_filled

            progress_bar = f'<span class="progress-filled">{"█" * progress_filled}</span><span class="progress-empty">{"░" * progress_empty}</span>'
            exploit_display = f'<div class="exploit-progress"><span class="progress-bar">{progress_bar}</span><span class="exploit-ratio">{exploited}/{service_count}</span></div>'

            html += f"""    <tr>
        <td>{idx}</td>
        <td>{host_display}</td>
        <td class="{score_class}">{score}</td>
        <td>{service_count}</td>
        <td>{findings_display}</td>
        <td>{exploit_display}</td>
    </tr>
"""

        html += "</tbody>\n</table>\n"

        # Show remaining hosts note if applicable
        if remaining_hosts > 0:
            html += f'\n<p style="color: #888; font-size: 0.9em; margin-top: 10px;">+ {remaining_hosts} additional host(s) not shown. See Appendix for complete list.</p>\n'

        html += """</div>

---

"""
        return html

    def compare_to_previous(
        self,
        current_metrics: Dict,
        previous_metrics: Dict,
        current_engagement: Dict,
        previous_engagement: Dict,
    ) -> str:
        """Generate comparison section showing improvement/regression from previous engagement.

        Args:
            current_metrics: Metrics from current engagement
            previous_metrics: Metrics from previous engagement
            current_engagement: Current engagement details
            previous_engagement: Previous engagement details
        """
        if not previous_metrics:
            return ""

        # Calculate deltas
        current_risk = current_metrics.get("risk_score", 0)
        prev_risk = previous_metrics.get("risk_score", 0)
        risk_delta = current_risk - prev_risk

        current_critical = current_metrics.get("severity_counts", {}).get("critical", 0)
        prev_critical = previous_metrics.get("severity_counts", {}).get("critical", 0)
        critical_delta = current_critical - prev_critical

        current_high = current_metrics.get("severity_counts", {}).get("high", 0)
        prev_high = previous_metrics.get("severity_counts", {}).get("high", 0)
        high_delta = current_high - prev_high

        current_total = current_metrics.get("total_findings", 0)
        prev_total = previous_metrics.get("total_findings", 0)
        total_delta = current_total - prev_total

        # Determine overall trend
        if risk_delta < -10:
            trend_icon = "📈"
            trend_text = "SIGNIFICANT IMPROVEMENT"
            trend_color = "#10b981"
        elif risk_delta < 0:
            trend_icon = "📊"
            trend_text = "IMPROVEMENT"
            trend_color = "#34d399"
        elif risk_delta > 10:
            trend_icon = "📉"
            trend_text = "REGRESSION"
            trend_color = "#ef4444"
        elif risk_delta > 0:
            trend_icon = "⚠️"
            trend_text = "SLIGHT REGRESSION"
            trend_color = "#f59e0b"
        else:
            trend_icon = "➡️"
            trend_text = "NO CHANGE"
            trend_color = "#6b7280"

        prev_date = previous_engagement.get("created_at", "Unknown")
        if hasattr(prev_date, "strftime"):
            prev_date = prev_date.strftime("%B %d, %Y")

        html = f"""<div class="compare-section" style="margin: 30px 0; padding: 25px; background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%); border-radius: 12px; border: 2px solid #0ea5e9;">

<h2 style="margin-top: 0; color: #0369a1;">📊 COMPARISON TO PREVIOUS ASSESSMENT</h2>

<p style="color: #64748b; margin-bottom: 20px;">Comparing to: <strong>{previous_engagement.get('name', 'Previous Engagement')}</strong> ({prev_date})</p>

<div style="display: flex; align-items: center; gap: 15px; margin-bottom: 25px; padding: 15px; background: white; border-radius: 8px;">
    <span style="font-size: 2em;">{trend_icon}</span>
    <div>
        <div style="font-size: 1.5em; font-weight: bold; color: {trend_color};">{trend_text}</div>
        <div style="color: #64748b;">Overall security posture since last assessment</div>
    </div>
</div>

<table style="width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden;">
    <thead>
        <tr style="background: #0369a1; color: white;">
            <th style="padding: 12px; text-align: left;">Metric</th>
            <th style="padding: 12px; text-align: center;">Previous</th>
            <th style="padding: 12px; text-align: center;">Current</th>
            <th style="padding: 12px; text-align: center;">Change</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td style="padding: 12px; border-bottom: 1px solid #e2e8f0;"><strong>Risk Score</strong></td>
            <td style="padding: 12px; text-align: center; border-bottom: 1px solid #e2e8f0;">{prev_risk}/100</td>
            <td style="padding: 12px; text-align: center; border-bottom: 1px solid #e2e8f0;">{current_risk}/100</td>
            <td style="padding: 12px; text-align: center; border-bottom: 1px solid #e2e8f0;">{self._format_delta(risk_delta, invert=True)}</td>
        </tr>
        <tr style="background: #fef2f2;">
            <td style="padding: 12px; border-bottom: 1px solid #e2e8f0;"><strong>Critical Findings</strong></td>
            <td style="padding: 12px; text-align: center; border-bottom: 1px solid #e2e8f0;">{prev_critical}</td>
            <td style="padding: 12px; text-align: center; border-bottom: 1px solid #e2e8f0;">{current_critical}</td>
            <td style="padding: 12px; text-align: center; border-bottom: 1px solid #e2e8f0;">{self._format_delta(critical_delta, invert=True)}</td>
        </tr>
        <tr>
            <td style="padding: 12px; border-bottom: 1px solid #e2e8f0;"><strong>High Findings</strong></td>
            <td style="padding: 12px; text-align: center; border-bottom: 1px solid #e2e8f0;">{prev_high}</td>
            <td style="padding: 12px; text-align: center; border-bottom: 1px solid #e2e8f0;">{current_high}</td>
            <td style="padding: 12px; text-align: center; border-bottom: 1px solid #e2e8f0;">{self._format_delta(high_delta, invert=True)}</td>
        </tr>
        <tr>
            <td style="padding: 12px;"><strong>Total Findings</strong></td>
            <td style="padding: 12px; text-align: center;">{prev_total}</td>
            <td style="padding: 12px; text-align: center;">{current_total}</td>
            <td style="padding: 12px; text-align: center;">{self._format_delta(total_delta, invert=True)}</td>
        </tr>
    </tbody>
</table>

"""

        # Add remediation progress note
        if risk_delta < 0:
            html += f"""
<div style="margin-top: 20px; padding: 15px; background: #dcfce7; border-radius: 8px; border-left: 4px solid #10b981;">
    <strong>✓ Remediation Progress:</strong> Risk score decreased by {abs(risk_delta)} points since the previous assessment.
</div>
"""
        elif risk_delta > 0:
            html += f"""
<div style="margin-top: 20px; padding: 15px; background: #fef2f2; border-radius: 8px; border-left: 4px solid #ef4444;">
    <strong>⚠ Attention Required:</strong> Risk score increased by {risk_delta} points since the previous assessment. Review new findings immediately.
</div>
"""

        html += """
</div>

---

"""
        return html

    def _format_delta(self, delta: int, invert: bool = False) -> str:
        """Format delta value with color and arrow.

        Args:
            delta: The change value
            invert: If True, negative is good (for risk scores, finding counts)
        """
        if delta == 0:
            return '<span style="color: #6b7280;">→ 0</span>'

        if invert:
            # For metrics where lower is better
            if delta < 0:
                return f'<span style="color: #10b981;">↓ {abs(delta)}</span>'
            else:
                return f'<span style="color: #ef4444;">↑ +{delta}</span>'
        else:
            # For metrics where higher is better
            if delta > 0:
                return f'<span style="color: #10b981;">↑ +{delta}</span>'
            else:
                return f'<span style="color: #ef4444;">↓ {abs(delta)}</span>'

    def charts_section(self, charts: Dict) -> str:
        """Generate charts section with Chart.js visualizations."""
        if not charts:
            return ""

        html = """<div id="charts-section">
<h2>VISUAL ANALYSIS</h2>

<div class="charts-grid">
"""

        # Phase 1 Charts
        # Severity Distribution Chart
        if "severity_distribution" in charts:
            html += """    <div class="chart-container">
        <canvas id="severityChart"></canvas>
    </div>
"""

        # Host Impact Chart
        if "host_impact" in charts:
            html += """    <div class="chart-container">
        <canvas id="hostChart"></canvas>
    </div>
"""

        # Exploitation Progress Chart
        if "exploitation_progress" in charts:
            html += """    <div class="chart-container">
        <canvas id="exploitationChart"></canvas>
    </div>
"""

        # Phase 2 Charts
        # Timeline Chart
        if "timeline" in charts:
            html += """    <div class="chart-container">
        <canvas id="timelineChart"></canvas>
    </div>
"""

        # Evidence by Phase Chart
        if "evidence_by_phase" in charts:
            html += """    <div class="chart-container">
        <canvas id="evidencePhaseChart"></canvas>
    </div>
"""

        # Service Exposure Chart
        if "service_exposure" in charts:
            html += """    <div class="chart-container">
        <canvas id="serviceExposureChart"></canvas>
    </div>
"""

        # Credentials by Service Chart
        if "credentials_by_service" in charts:
            html += """    <div class="chart-container">
        <canvas id="credentialsChart"></canvas>
    </div>
"""

        html += "</div>\n</div>\n\n---\n\n"

        # Add Chart.js initialization scripts
        html += "<script>\n"

        # Phase 1 Charts
        if "severity_distribution" in charts:
            html += f"""
const severityCtx = document.getElementById('severityChart');
if (severityCtx) {{
    new Chart(severityCtx, {charts['severity_distribution']});
}}
"""

        if "host_impact" in charts:
            html += f"""
const hostCtx = document.getElementById('hostChart');
if (hostCtx) {{
    new Chart(hostCtx, {charts['host_impact']});
}}
"""

        if "exploitation_progress" in charts:
            html += f"""
const exploitationCtx = document.getElementById('exploitationChart');
if (exploitationCtx) {{
    new Chart(exploitationCtx, {charts['exploitation_progress']});
}}
"""

        # Phase 2 Charts
        if "timeline" in charts:
            html += f"""
const timelineCtx = document.getElementById('timelineChart');
if (timelineCtx) {{
    new Chart(timelineCtx, {charts['timeline']});
}}
"""

        if "evidence_by_phase" in charts:
            html += f"""
const evidencePhaseCtx = document.getElementById('evidencePhaseChart');
if (evidencePhaseCtx) {{
    new Chart(evidencePhaseCtx, {charts['evidence_by_phase']});
}}
"""

        if "service_exposure" in charts:
            html += f"""
const serviceExposureCtx = document.getElementById('serviceExposureChart');
if (serviceExposureCtx) {{
    new Chart(serviceExposureCtx, {charts['service_exposure']});
}}
"""

        if "credentials_by_service" in charts:
            html += f"""
const credentialsCtx = document.getElementById('credentialsChart');
if (credentialsCtx) {{
    new Chart(credentialsCtx, {charts['credentials_by_service']});
}}
"""

        html += "</script>\n\n"
        return html

    def detailed_findings_collapsible(self, findings: Dict) -> str:
        """Generate detailed findings with collapsible sections by severity."""
        from souleyez.reporting.compliance_mappings import ComplianceMappings

        mapper = ComplianceMappings()

        section = """## DETAILED FINDINGS

<div class="collapse-controls">
    <button class="btn" onclick="expandAll()">Expand All</button>
    <button class="btn" onclick="collapseAll()">Collapse All</button>
</div>

"""

        severity_order = ["critical", "high", "medium", "low", "info"]
        emoji_map = {
            "critical": "🔴",
            "high": "🟠",
            "medium": "🟡",
            "low": "🟢",
            "info": "🔵",
        }

        finding_number = 1

        for severity in severity_order:
            if not findings.get(severity):
                continue

            count = len(findings[severity])
            severity_title = severity.upper()
            emoji = emoji_map.get(severity, "")

            # Create collapsible section
            # Auto-expand Critical and High findings for quick visibility
            open_attr = " open" if severity in ["critical", "high"] else ""
            section_id = f"findings-{severity}"
            section += f"""<details id="{section_id}"{open_attr}>
    <summary class="severity-{severity}">
        <span class="severity-header">
            <span>{emoji} {severity_title} SEVERITY FINDINGS</span>
            <span class="severity-count">{count} finding{"s" if count != 1 else ""}</span>
        </span>
    </summary>
    <div class="findings-content">

"""

            # Add each finding
            for finding in findings[severity]:
                severity_lower = finding.get("severity", severity).lower()

                # Use HTML formatting instead of markdown for proper rendering
                section += f"""<div class="finding-card">
<h3>Finding #{finding_number}: {finding['title']}</h3>

<p><span class="severity-badge {severity_lower}">{severity_lower.upper()}</span></p>
"""

                # Add compliance badges
                owasp_matches = mapper.map_finding_to_owasp(finding)
                cwe_matches = mapper.map_finding_to_cwe(finding)

                if owasp_matches or cwe_matches:
                    section += "<p><strong>Compliance:</strong> "
                    badges = []
                    for owasp_id in owasp_matches:
                        badges.append(f"<code>{owasp_id}</code>")
                    for cwe_id in cwe_matches:
                        badges.append(f"<code>{cwe_id}</code>")
                    section += " ".join(badges) + "</p>\n"

                if finding.get("cvss"):
                    section += (
                        f"<p><strong>CVSS Score:</strong> {finding['cvss']}</p>\n"
                    )
                if finding.get("cve"):
                    section += f"<p><strong>CVE:</strong> {finding['cve']}</p>\n"

                # Format affected host display
                affected_host = self._format_affected_host(finding)
                section += f"<p><strong>Affected Host:</strong> {affected_host}</p>\n"
                section += f"<p><strong>Tool:</strong> {finding['tool']}</p>\n"

                # Description
                if finding.get("description"):
                    desc = finding["description"].replace("\n", "<br>\n")
                    section += f"<p><strong>Description:</strong></p>\n<p>{desc}</p>\n"

                # Evidence (if available) - shows proof of vulnerability
                evidence_text = finding.get("evidence", "")
                if evidence_text and len(evidence_text.strip()) > 0:
                    # Escape HTML in evidence
                    safe_evidence = evidence_text.replace("<", "&lt;").replace(
                        ">", "&gt;"
                    )
                    section += f"""<div class="finding-evidence">
<div class="finding-evidence-label">Evidence / Proof</div>
<pre>{safe_evidence}</pre>
</div>
"""

                # Remediation - Add recommendations
                remediation_text = finding.get("remediation", "")

                # If no remediation provided, generate a basic one
                if not remediation_text:
                    remediation_text = self._generate_default_remediation(
                        finding, severity
                    )

                if remediation_text:
                    remediation_html = remediation_text.replace("\n", "<br>\n")
                    section += f"<p><strong>Remediation:</strong></p>\n<p>{remediation_html}</p>\n"

                section += "</div>\n<hr>\n\n"
                finding_number += 1

            section += "    </div>\n</details>\n\n"

        return section

    # =========================================================================
    # Detection Report HTML Methods
    # =========================================================================

    def mitre_heatmap_html(self, data) -> str:
        """
        Generate HTML MITRE ATT&CK heatmap with CSS grid styling.

        Args:
            data: DetectionReportData object

        Returns:
            HTML string with styled heatmap
        """
        if not data.heatmap_data:
            return "<p>No MITRE ATT&CK data available.</p>"

        # Group by tactic
        tactics_data = {}
        for item in data.heatmap_data:
            tactic = item["tactic_name"]
            if tactic not in tactics_data:
                tactics_data[tactic] = {
                    "id": item["tactic_id"],
                    "order": item["tactic_order"],
                    "techniques": [],
                }
            tactics_data[tactic]["techniques"].append(item)

        # Sort tactics by order
        sorted_tactics = sorted(tactics_data.items(), key=lambda x: x[1]["order"])

        html = """
<style>
.mitre-section {
    margin: 30px 0;
}

.mitre-heatmap {
    display: flex;
    flex-wrap: wrap;
    gap: 20px;
    margin: 20px 0;
}

.mitre-tactic {
    flex: 1;
    min-width: 200px;
    max-width: 300px;
    background: #f8f9fa;
    border-radius: 8px;
    overflow: hidden;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.mitre-tactic-header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 12px 15px;
    font-weight: 600;
    font-size: 14px;
}

.mitre-techniques {
    padding: 10px;
}

.mitre-technique {
    display: flex;
    align-items: center;
    padding: 8px 10px;
    margin: 5px 0;
    border-radius: 6px;
    font-size: 13px;
    transition: transform 0.1s;
}

.mitre-technique:hover {
    transform: translateX(3px);
}

.mitre-technique.detected {
    background: #d4edda;
    border-left: 4px solid #28a745;
}

.mitre-technique.not-detected {
    background: #f8d7da;
    border-left: 4px solid #dc3545;
}

.mitre-technique.partial {
    background: #fff3cd;
    border-left: 4px solid #ffc107;
}

.mitre-technique.not-tested {
    background: #e9ecef;
    border-left: 4px solid #6c757d;
    color: #6c757d;
}

.mitre-technique-id {
    font-weight: 600;
    min-width: 60px;
}

.mitre-technique-name {
    flex: 1;
    margin-left: 10px;
}

.mitre-technique-rate {
    font-size: 12px;
    font-weight: 600;
    padding: 2px 6px;
    border-radius: 10px;
    background: rgba(0,0,0,0.1);
}

.mitre-legend {
    display: flex;
    gap: 20px;
    flex-wrap: wrap;
    margin-bottom: 20px;
    padding: 15px;
    background: #f8f9fa;
    border-radius: 8px;
}

.mitre-legend-item {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 14px;
}

.mitre-legend-color {
    width: 20px;
    height: 20px;
    border-radius: 4px;
}

.mitre-legend-color.detected { background: #28a745; }
.mitre-legend-color.not-detected { background: #dc3545; }
.mitre-legend-color.partial { background: #ffc107; }
.mitre-legend-color.not-tested { background: #6c757d; }
</style>

<div class="mitre-section">
<h2>MITRE ATT&CK COVERAGE</h2>

<p>The following matrix shows which MITRE ATT&CK techniques were tested during the engagement and their detection status.</p>

<div class="mitre-legend">
    <div class="mitre-legend-item">
        <div class="mitre-legend-color detected"></div>
        <span>Detected</span>
    </div>
    <div class="mitre-legend-item">
        <div class="mitre-legend-color not-detected"></div>
        <span>Not Detected</span>
    </div>
    <div class="mitre-legend-item">
        <div class="mitre-legend-color partial"></div>
        <span>Partial</span>
    </div>
    <div class="mitre-legend-item">
        <div class="mitre-legend-color not-tested"></div>
        <span>Not Tested</span>
    </div>
</div>

<div class="mitre-heatmap">
"""

        for tactic_name, tactic_data in sorted_tactics:
            techniques = tactic_data["techniques"]
            if not techniques:
                continue

            html += f"""
<div class="mitre-tactic">
    <div class="mitre-tactic-header">{tactic_name}</div>
    <div class="mitre-techniques">
"""

            for tech in techniques:
                status_class = tech["status"].replace("_", "-")
                rate_html = ""
                if tech["tested"] > 0:
                    rate_html = f'<span class="mitre-technique-rate">{tech["detection_rate"]}%</span>'

                tools_title = (
                    ", ".join(tech["tools_used"]) if tech["tools_used"] else "N/A"
                )

                html += f"""
        <div class="mitre-technique {status_class}" title="Tools: {tools_title}">
            <span class="mitre-technique-id">{tech['technique_id']}</span>
            <span class="mitre-technique-name">{tech['technique_name']}</span>
            {rate_html}
        </div>
"""

            html += """
    </div>
</div>
"""

        html += """
</div>
</div>

<hr>
"""

        return html

    def detection_report_header(self, title: str) -> str:
        """Generate HTML header for detection coverage report."""
        base_header = self.html_header(title)

        # Add detection-specific CSS
        detection_css = """
<style>
/* Detection Report Specific Styles */
.detection-stat-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 20px;
    margin: 20px 0;
}

.detection-stat-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 20px;
    border-radius: 12px;
    text-align: center;
}

.detection-stat-card.detected {
    background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
}

.detection-stat-card.not-detected {
    background: linear-gradient(135deg, #dc3545 0%, #e74c3c 100%);
}

.detection-stat-card.coverage {
    background: linear-gradient(135deg, #17a2b8 0%, #138496 100%);
}

.detection-stat-value {
    font-size: 2.5em;
    font-weight: 700;
}

.detection-stat-label {
    font-size: 0.9em;
    opacity: 0.9;
    margin-top: 5px;
}

.gap-warning {
    background: #f8d7da;
    border: 1px solid #f5c6cb;
    border-left: 4px solid #dc3545;
    padding: 15px;
    border-radius: 8px;
    margin: 20px 0;
}

.gap-warning h4 {
    color: #721c24;
    margin: 0 0 10px 0;
}

.recommendation-card {
    background: #fff;
    border: 1px solid #e9ecef;
    border-radius: 8px;
    padding: 20px;
    margin: 15px 0;
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

.recommendation-card.critical {
    border-left: 4px solid #dc3545;
}

.recommendation-card.high {
    border-left: 4px solid #fd7e14;
}

.recommendation-card.medium {
    border-left: 4px solid #ffc107;
}

.recommendation-card.low {
    border-left: 4px solid #28a745;
}

.recommendation-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 15px;
}

.recommendation-priority {
    padding: 4px 10px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 600;
    text-transform: uppercase;
}

.recommendation-priority.critical { background: #dc3545; color: white; }
.recommendation-priority.high { background: #fd7e14; color: white; }
.recommendation-priority.medium { background: #ffc107; color: black; }
.recommendation-priority.low { background: #28a745; color: white; }
</style>
"""

        # Insert CSS before closing </head>
        return base_header.replace(
            "</style>\n</head>", "</style>\n" + detection_css + "</head>"
        )

    def html_footer(self) -> str:
        """Generate HTML footer."""
        return """</div>
<script>
// Expand/Collapse All functionality
function expandAll() {
    document.querySelectorAll('details').forEach(details => {
        details.open = true;
    });
}

function collapseAll() {
    document.querySelectorAll('details').forEach(details => {
        details.open = false;
    });
}

// Auto-expand Critical findings on load
window.addEventListener('DOMContentLoaded', () => {
    const criticalSection = document.getElementById('findings-critical');
    if (criticalSection) {
        criticalSection.open = true;
    }
});
</script>
</body>
</html>"""
