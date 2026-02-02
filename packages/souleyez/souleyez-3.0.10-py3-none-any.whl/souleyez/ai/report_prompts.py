"""
souleyez.ai.report_prompts - Prompt templates for AI report generation

These templates are designed to produce professional, actionable
penetration test report content.
"""

# System prompt for all report generation
REPORT_SYSTEM_PROMPT = """You are a senior cybersecurity consultant with 15+ years of experience
writing penetration test reports for Fortune 500 companies. Your reports are known for:
- Clear communication of technical risks to business stakeholders
- Actionable remediation guidance with realistic timelines
- Professional tone that balances urgency with constructive guidance
- Precise technical accuracy without unnecessary jargon

Always write in third person professional voice. Be specific and avoid generic statements."""


EXECUTIVE_SUMMARY_PROMPT = """Write an executive summary for a penetration test report based on the following data.

ENGAGEMENT DETAILS:
- Engagement Name: {engagement_name}
- Type: {engagement_type}
- Duration: {duration}
- Scope: {scope_summary}

FINDINGS SUMMARY:
- Total Findings: {total_findings}
- Critical: {critical_count}
- High: {high_count}
- Medium: {medium_count}
- Low: {low_count}
- Informational: {info_count}

ENVIRONMENT:
- Total Hosts Assessed: {total_hosts}
- Hosts with Critical/High Findings: {compromised_hosts}
- Credentials Discovered: {credentials_count}

TOP CRITICAL FINDINGS:
{top_findings}

Write a professional executive summary (300-400 words) that:
1. Opens with a one-sentence overall security posture assessment
2. Summarizes the most significant risks in business terms
3. Quantifies potential business impact (data breach, compliance, reputation)
4. Provides a clear recommended action timeline
5. Ends with a forward-looking statement about security improvement

Do NOT include technical jargon, CVE numbers, or exploit details.
Focus on BUSINESS IMPACT and RISK to the organization."""


FINDING_ENHANCEMENT_PROMPT = """Enhance this penetration test finding with business context.

FINDING DETAILS:
- Title: {title}
- Severity: {severity}
- Affected System: {host} ({hostname})
- Port/Service: {port} / {service}
- Tool Used: {tool}

TECHNICAL DESCRIPTION:
{description}

CVE/CWE: {cve}

EVIDENCE:
{evidence}

Provide the following sections (be specific to THIS finding, not generic):

BUSINESS IMPACT (2-3 sentences):
Explain how this vulnerability could affect the organization. Consider data confidentiality,
service availability, regulatory compliance, and reputation.

ATTACK SCENARIO (2-3 sentences):
Describe a realistic attack path an adversary could take to exploit this vulnerability.
Include the likely attacker profile (script kiddie, organized crime, nation-state).

RISK CONTEXT (1-2 sentences):
Note any industry-specific implications (PCI-DSS for payment data, HIPAA for healthcare, etc.)
or recent threat intelligence related to this vulnerability type.

Format your response with clear section headers."""


REMEDIATION_PLAN_PROMPT = """Create a prioritized remediation plan for this penetration test engagement.

FINDINGS SUMMARY BY SEVERITY:
{findings_summary}

ENVIRONMENT CONTEXT:
- Total Hosts: {total_hosts}
- Critical Findings: {critical_count}
- High Findings: {high_count}
- Medium Findings: {medium_count}
- Credentials Compromised: {creds_count}

TOP VULNERABILITIES:
{top_vulnerabilities}

Create a prioritized remediation plan with four phases:

## IMMEDIATE (24-48 hours)
Emergency actions for critical vulnerabilities that pose imminent risk.
For each item include: specific action, estimated effort, required skills.

## SHORT-TERM (1-2 weeks)
High-priority fixes and access control improvements.
For each item include: specific action, estimated effort, dependencies.

## MEDIUM-TERM (30 days)
Systematic security improvements and hardening.
For each item include: specific action, estimated effort, success criteria.

## ONGOING
Process and policy recommendations for sustained security improvement.

Be specific and actionable. Reference actual findings where appropriate.
Estimate effort in hours or days. Consider resource constraints of a typical IT team."""


COMPLIANCE_ANALYSIS_PROMPT = """Analyze the penetration test findings for compliance implications.

FINDINGS:
{findings_list}

DETECTED COMPLIANCE FRAMEWORKS:
{detected_frameworks}

For each applicable compliance framework, provide:
1. Relevant control failures identified
2. Potential audit findings
3. Recommended remediation priority

Focus on: PCI-DSS, HIPAA, SOC 2, NIST 800-53, ISO 27001 as applicable.
Be specific about which findings map to which controls."""


# Shorter prompts for specific sections
RISK_RATING_PROMPT = """Based on these findings, provide a single-sentence overall risk rating:
{findings_summary}

Choose from: CRITICAL (immediate breach risk), HIGH (significant vulnerabilities),
MODERATE (important gaps), LOW (minor issues only).

Format: "RATING: [rating] - [one sentence justification]" """


ATTACK_CHAIN_PROMPT = """Based on these findings, describe the most likely attack chain an adversary could use:

FINDINGS:
{findings}

CREDENTIALS DISCOVERED:
{credentials}

Describe the attack chain in 3-5 steps, from initial access to objective (data theft,
ransomware deployment, etc.). Be specific about which findings enable each step."""
