#!/usr/bin/env python3
"""
souleyez.ai.chain_advisor - AI-powered tool chain recommendations

Uses LLM to analyze scan results and suggest additional tools to run,
complementing the static rule-based chaining system.
"""

import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from .llm_factory import LLMFactory

logger = logging.getLogger(__name__)


class ChainAdvisorMode(Enum):
    """AI chain recommendation modes."""

    OFF = "off"  # No AI involvement
    SUGGEST = "suggest"  # Show recommendations, don't auto-queue
    AUTO = "auto"  # Auto-queue AI recommendations


@dataclass
class AIChainRecommendation:
    """Single tool recommendation from LLM."""

    tool: str
    target: str
    args: List[str] = field(default_factory=list)
    priority: int = 5  # 1-10
    rationale: str = ""
    confidence: float = 0.7  # 0.0-1.0
    expected_outcome: str = ""
    risk_level: str = "medium"  # low/medium/high


@dataclass
class AIChainAnalysis:
    """Complete AI analysis of scan results."""

    recommendations: List[AIChainRecommendation]
    summary: str = ""
    static_rules_applied: List[str] = field(default_factory=list)
    analysis_time_ms: int = 0
    provider: str = ""
    error: Optional[str] = None


# Available tools for recommendations (must match actual plugins in souleyez/plugins/)
AVAILABLE_TOOLS = {
    "nmap": "Network scanning, service detection, OS fingerprinting",
    "nuclei": "Vulnerability scanning with templates (CVEs, misconfigs)",
    "nikto": "Web server vulnerability scanner",
    "gobuster": "Directory/file brute-forcing",
    "ffuf": "Web fuzzing (parameters, directories)",
    "sqlmap": "SQL injection detection and exploitation",
    "wpscan": "WordPress vulnerability scanner",
    "hydra": "Brute-force password cracking",
    "enum4linux": "SMB/NetBIOS enumeration",
    "smbmap": "SMB share enumeration",
    "crackmapexec": "Windows/AD enumeration and exploitation",
    "dnsrecon": "DNS enumeration and zone transfers",
    "theharvester": "OSINT - emails, subdomains, IPs",
    "dalfox": "XSS vulnerability scanner",
    "searchsploit": "Exploit database search",
    "bloodhound": "Active Directory attack path mapping",
}


class ChainAdvisor:
    """AI-powered chain recommendation engine."""

    SYSTEM_PROMPT = """You are an expert penetration testing advisor analyzing tool output
and recommending the most effective next steps. You understand the souleyez tool ecosystem
and can recommend specific tools with arguments.

Your recommendations should:
- Be actionable and specific
- Prioritize high-value targets and critical findings
- Avoid redundant scans (don't repeat what's already been done)
- Consider the engagement context and discovered information
- Focus on practical pentesting methodology"""

    ANALYSIS_TEMPLATE = """Analyze the following scan results and recommend additional tools to run.

COMPLETED TOOL: {tool}
TARGET: {target}

PARSED RESULTS:
{results_summary}

ALREADY QUEUED BY RULES:
{static_commands}

AVAILABLE TOOLS:
{available_tools}

Based on these results, recommend 0-5 ADDITIONAL tools that would provide value beyond
what's already queued. Only suggest tools that make sense given the findings.

For EACH recommendation, respond in EXACTLY this format:
TOOL: [tool_name from available tools]
TARGET: [specific target - IP, URL, or host]
ARGS: [command arguments, comma-separated]
PRIORITY: [1-10, higher = more important]
RATIONALE: [brief explanation why this tool should run]
CONFIDENCE: [0.0-1.0, how confident in this recommendation]
EXPECTED: [what you expect to find]
RISK: [low/medium/high]
---

If no additional tools are needed, respond with:
NO_RECOMMENDATIONS: The static rules have adequately covered the next steps.

Guidelines:
- Don't recommend nmap if services are already identified
- Don't recommend the same tool that just ran
- Prioritize CVE checks for identified vulnerable versions
- Consider credential testing if usernames/passwords discovered
- Focus on high-value services (databases, admin panels, etc.)
"""

    def __init__(
        self, provider=None, mode: ChainAdvisorMode = ChainAdvisorMode.SUGGEST
    ):
        """
        Initialize chain advisor.

        Args:
            provider: Optional LLM provider instance (from LLMFactory)
            mode: Chain advisor mode (off/suggest/auto)
        """
        self.provider = provider
        self.mode = mode
        self._provider_initialized = False

    def _ensure_provider(self):
        """Lazy-load provider on first use."""
        if not self._provider_initialized:
            if self.provider is None:
                self.provider = LLMFactory.get_available_provider()
            self._provider_initialized = True

    def is_available(self) -> bool:
        """Check if AI chain analysis is available."""
        if self.mode == ChainAdvisorMode.OFF:
            return False
        self._ensure_provider()
        return self.provider is not None and self.provider.is_available()

    def analyze_results(
        self,
        tool: str,
        target: str,
        parse_results: Dict[str, Any],
        static_commands: List[Dict[str, Any]],
        engagement_id: Optional[int] = None,
    ) -> AIChainAnalysis:
        """
        Analyze scan results and recommend next tools.

        Args:
            tool: Tool that just completed
            target: Target that was scanned
            parse_results: Parsed output from the tool
            static_commands: Commands already queued by static rules
            engagement_id: Current engagement ID (optional)

        Returns:
            AIChainAnalysis with recommendations, or error if failed
        """
        import time

        start_time = time.time()

        # Check mode
        if self.mode == ChainAdvisorMode.OFF:
            return AIChainAnalysis(
                recommendations=[], error="AI chain analysis is disabled"
            )

        # Ensure provider is available
        self._ensure_provider()
        if not self.provider or not self.provider.is_available():
            logger.debug("AI provider not available for chain analysis")
            return AIChainAnalysis(
                recommendations=[], error="AI provider not available"
            )

        # Build prompt
        prompt = self._build_analysis_prompt(
            tool, target, parse_results, static_commands
        )

        # Generate recommendations
        try:
            response = self.provider.generate(
                prompt=prompt,
                system_prompt=self.SYSTEM_PROMPT,
                max_tokens=2000,
                temperature=0.3,  # Lower for consistent tool recommendations
            )

            if not response:
                logger.warning("AI returned empty chain analysis")
                return AIChainAnalysis(
                    recommendations=[], error="Empty response from AI provider"
                )

            # Parse recommendations
            recommendations = self._parse_recommendations(response)

            # Filter out low-confidence recommendations
            min_confidence = 0.6
            recommendations = [
                r for r in recommendations if r.confidence >= min_confidence
            ]

            # Filter duplicates with static commands
            recommendations = self._filter_duplicates(recommendations, static_commands)

            elapsed_ms = int((time.time() - start_time) * 1000)
            provider_name = getattr(self.provider, "provider_type", "unknown")

            return AIChainAnalysis(
                recommendations=recommendations,
                summary=f"AI suggested {len(recommendations)} additional tools",
                static_rules_applied=[
                    cmd.get("description", "") for cmd in static_commands
                ],
                analysis_time_ms=elapsed_ms,
                provider=str(provider_name),
            )

        except Exception as e:
            logger.error(f"AI chain analysis failed: {e}")
            return AIChainAnalysis(recommendations=[], error=str(e))

    def _build_analysis_prompt(
        self,
        tool: str,
        target: str,
        parse_results: Dict[str, Any],
        static_commands: List[Dict[str, Any]],
    ) -> str:
        """Build LLM prompt for chain analysis."""
        # Format results summary
        results_lines = []

        # Add hosts
        hosts = parse_results.get("hosts", [])
        if hosts:
            results_lines.append(f"Hosts discovered: {len(hosts)}")
            for host in hosts[:5]:  # Limit to first 5
                ip = host.get("ip", "unknown")
                os_name = host.get("os", "unknown")
                results_lines.append(f"  - {ip} (OS: {os_name})")

        # Add services
        services = parse_results.get("services", [])
        if services:
            results_lines.append(f"\nServices found: {len(services)}")
            for svc in services[:10]:  # Limit to first 10
                ip = svc.get("ip", target)
                port = svc.get("port", "?")
                name = svc.get("service_name", svc.get("service", "unknown"))
                product = svc.get("product", "")
                version = svc.get("version", "")
                ver_str = f" {product} {version}".strip() if product or version else ""
                results_lines.append(f"  - {ip}:{port} - {name}{ver_str}")

        # Add findings
        findings = parse_results.get("findings", [])
        if findings:
            results_lines.append(f"\nFindings: {len(findings)}")
            for finding in findings[:5]:  # Limit to first 5
                title = finding.get("title", "unknown")
                severity = finding.get("severity", "info")
                results_lines.append(f"  - [{severity.upper()}] {title}")

        # Add credentials
        credentials = parse_results.get("credentials", [])
        if credentials:
            results_lines.append(f"\nCredentials found: {len(credentials)}")

        results_summary = (
            "\n".join(results_lines)
            if results_lines
            else "No structured results parsed."
        )

        # Format static commands
        static_lines = []
        for cmd in static_commands:
            tool_name = cmd.get("tool", "unknown")
            desc = cmd.get("description", "")
            static_lines.append(f"  - {tool_name}: {desc}")
        static_summary = "\n".join(static_lines) if static_lines else "  (none)"

        # Format available tools
        tools_lines = []
        for tool_name, desc in AVAILABLE_TOOLS.items():
            tools_lines.append(f"  - {tool_name}: {desc}")
        tools_summary = "\n".join(tools_lines)

        return self.ANALYSIS_TEMPLATE.format(
            tool=tool,
            target=target,
            results_summary=results_summary,
            static_commands=static_summary,
            available_tools=tools_summary,
        )

    def _parse_recommendations(self, response: str) -> List[AIChainRecommendation]:
        """Parse LLM response into structured recommendations."""
        recommendations = []

        # Check for no recommendations response
        if "NO_RECOMMENDATIONS" in response.upper():
            return []

        # Split by separator
        sections = response.split("---")

        for section in sections:
            section = section.strip()
            if not section:
                continue

            try:
                rec = self._parse_single_recommendation(section)
                if rec:
                    recommendations.append(rec)
            except Exception as e:
                logger.debug(f"Failed to parse recommendation section: {e}")
                continue

        return recommendations

    def _parse_single_recommendation(
        self, section: str
    ) -> Optional[AIChainRecommendation]:
        """Parse a single recommendation section."""
        # Extract fields
        tool_match = re.search(r"TOOL:\s*(.+?)(?=\n|$)", section, re.IGNORECASE)
        target_match = re.search(r"TARGET:\s*(.+?)(?=\n|$)", section, re.IGNORECASE)
        args_match = re.search(r"ARGS:\s*(.+?)(?=\n|$)", section, re.IGNORECASE)
        priority_match = re.search(r"PRIORITY:\s*(\d+)", section, re.IGNORECASE)
        rationale_match = re.search(
            r"RATIONALE:\s*(.+?)(?=\n[A-Z]+:|$)", section, re.DOTALL | re.IGNORECASE
        )
        confidence_match = re.search(r"CONFIDENCE:\s*([\d.]+)", section, re.IGNORECASE)
        expected_match = re.search(
            r"EXPECTED:\s*(.+?)(?=\n[A-Z]+:|$)", section, re.DOTALL | re.IGNORECASE
        )
        risk_match = re.search(r"RISK:\s*(\w+)", section, re.IGNORECASE)

        # Require at least tool and target
        if not tool_match or not target_match:
            return None

        tool = tool_match.group(1).strip().lower()
        target = target_match.group(1).strip()

        # Validate tool is in available list
        if tool not in AVAILABLE_TOOLS:
            logger.debug(f"AI recommended unknown tool: {tool}")
            return None

        # Parse args
        args = []
        if args_match:
            args_str = args_match.group(1).strip()
            if args_str and args_str.lower() not in ["none", "n/a", "-"]:
                # Split by comma or space
                args = [a.strip() for a in re.split(r"[,\s]+", args_str) if a.strip()]

        # Parse priority (default 5)
        priority = 5
        if priority_match:
            try:
                priority = min(10, max(1, int(priority_match.group(1))))
            except ValueError:
                pass

        # Parse confidence (default 0.7)
        confidence = 0.7
        if confidence_match:
            try:
                confidence = min(1.0, max(0.0, float(confidence_match.group(1))))
            except ValueError:
                pass

        # Parse rationale
        rationale = ""
        if rationale_match:
            rationale = rationale_match.group(1).strip()

        # Parse expected
        expected = ""
        if expected_match:
            expected = expected_match.group(1).strip()

        # Parse risk
        risk = "medium"
        if risk_match:
            risk = risk_match.group(1).strip().lower()
            if risk not in ["low", "medium", "high"]:
                risk = "medium"

        return AIChainRecommendation(
            tool=tool,
            target=target,
            args=args,
            priority=priority,
            rationale=rationale,
            confidence=confidence,
            expected_outcome=expected,
            risk_level=risk,
        )

    def _filter_duplicates(
        self,
        recommendations: List[AIChainRecommendation],
        static_commands: List[Dict[str, Any]],
    ) -> List[AIChainRecommendation]:
        """Remove AI recommendations that duplicate static rules."""
        # Build set of (tool, target) pairs from static commands
        static_pairs = set()
        for cmd in static_commands:
            tool = cmd.get("tool", "").lower()
            target = cmd.get("target", "").lower()
            static_pairs.add((tool, target))

        # Filter recommendations
        filtered = []
        for rec in recommendations:
            pair = (rec.tool.lower(), rec.target.lower())
            if pair not in static_pairs:
                filtered.append(rec)
            else:
                logger.debug(
                    f"Filtered duplicate AI recommendation: {rec.tool} -> {rec.target}"
                )

        return filtered

    def to_chain_commands(
        self, recommendations: List[AIChainRecommendation], context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Convert AI recommendations to chain command format.

        Args:
            recommendations: List of AIChainRecommendation
            context: Chain context (for target resolution)

        Returns:
            List of command dicts compatible with chain execution
        """
        commands = []
        for rec in recommendations:
            cmd = {
                "tool": rec.tool,
                "target": rec.target,
                "args": rec.args,
                "priority": rec.priority,
                "description": f"[AI] {rec.rationale[:100]}",
                "source": "ai_advisor",
                "confidence": rec.confidence,
                "risk_level": rec.risk_level,
            }
            commands.append(cmd)

        # Sort by priority (highest first)
        commands.sort(key=lambda c: c["priority"], reverse=True)
        return commands
