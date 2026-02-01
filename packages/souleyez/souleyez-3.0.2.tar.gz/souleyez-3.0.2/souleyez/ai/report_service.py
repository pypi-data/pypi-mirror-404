"""
souleyez.ai.report_service - AI-powered report generation service

Provides methods for generating AI-enhanced report sections using
configured LLM providers (Claude or Ollama).
"""

import concurrent.futures
import logging
import re
from typing import Any, Dict, List, Optional

from .llm_factory import LLMFactory
from .llm_provider import LLMProvider
from .report_context import ReportContextBuilder
from .report_prompts import (
    ATTACK_CHAIN_PROMPT,
    EXECUTIVE_SUMMARY_PROMPT,
    FINDING_ENHANCEMENT_PROMPT,
    REMEDIATION_PLAN_PROMPT,
    REPORT_SYSTEM_PROMPT,
    RISK_RATING_PROMPT,
)

logger = logging.getLogger(__name__)

# Default timeout for AI operations (in seconds)
AI_TIMEOUT_SECONDS = 120  # 2 minutes per AI call


def _run_with_timeout(func, timeout_seconds: int = AI_TIMEOUT_SECONDS):
    """
    Run a function with a timeout.

    Args:
        func: Callable to execute
        timeout_seconds: Maximum time to wait

    Returns:
        Result of func() or None if timeout/error
    """
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(func)
        try:
            return future.result(timeout=timeout_seconds)
        except concurrent.futures.TimeoutError:
            logger.warning(f"AI operation timed out after {timeout_seconds}s")
            return None
        except Exception as e:
            logger.error(f"AI operation failed: {e}")
            return None


class AIReportService:
    """
    Service for generating AI-enhanced report sections.

    Uses configured LLM provider (Claude or Ollama) to generate
    executive summaries, enhanced finding descriptions, and
    remediation plans.
    """

    def __init__(self, provider: Optional[LLMProvider] = None):
        """
        Initialize AI report service.

        Args:
            provider: Specific LLM provider to use (default: from factory)
        """
        self._provider = provider
        self._context_builder = ReportContextBuilder()

    @property
    def provider(self) -> Optional[LLMProvider]:
        """Get the LLM provider, initializing from factory if needed."""
        if self._provider is None:
            self._provider = LLMFactory.get_available_provider()
        return self._provider

    def is_available(self) -> bool:
        """Check if AI report generation is available."""
        return self.provider is not None and self.provider.is_available()

    def get_provider_info(self) -> Dict[str, Any]:
        """Get information about the current provider."""
        if not self.provider:
            return {"available": False, "error": "No provider configured"}
        return self.provider.get_status()

    def generate_executive_summary(
        self, engagement_id: int, max_tokens: int = 1500
    ) -> Optional[str]:
        """
        Generate AI-powered executive summary.

        Args:
            engagement_id: Engagement to generate summary for
            max_tokens: Maximum tokens in response

        Returns:
            str: Generated executive summary, or None if failed
        """
        if not self.is_available():
            logger.warning("AI provider not available for executive summary")
            return None

        try:
            context = self._context_builder.build_executive_context(engagement_id)
            if not context:
                logger.error("Failed to build executive context")
                return None

            prompt = EXECUTIVE_SUMMARY_PROMPT.format(**context)

            def _generate():
                return self.provider.generate(
                    prompt=prompt,
                    system_prompt=REPORT_SYSTEM_PROMPT,
                    max_tokens=max_tokens,
                    temperature=0.3,
                )

            result = _run_with_timeout(_generate)

            if result:
                logger.info(
                    f"Generated executive summary for engagement {engagement_id}"
                )
            return result

        except Exception as e:
            logger.error(f"Failed to generate executive summary: {e}")
            return None

    def enhance_finding(
        self, finding: Dict[str, Any], max_tokens: int = 800
    ) -> Optional[Dict[str, str]]:
        """
        Enhance a single finding with business context.

        Args:
            finding: Finding dict from FindingsManager
            max_tokens: Maximum tokens in response

        Returns:
            dict: Enhanced sections {business_impact, attack_scenario, risk_context}
                  or None if failed
        """
        if not self.is_available():
            logger.warning("AI provider not available for finding enhancement")
            return None

        try:
            context = self._context_builder.build_finding_context(finding)
            prompt = FINDING_ENHANCEMENT_PROMPT.format(**context)

            def _generate():
                return self.provider.generate(
                    prompt=prompt,
                    system_prompt=REPORT_SYSTEM_PROMPT,
                    max_tokens=max_tokens,
                    temperature=0.3,
                )

            result = _run_with_timeout(_generate)

            if result:
                return self._parse_finding_enhancement(result)
            return None

        except Exception as e:
            logger.error(f"Failed to enhance finding: {e}")
            return None

    def generate_remediation_plan(
        self, engagement_id: int, max_tokens: int = 2500
    ) -> Optional[str]:
        """
        Generate prioritized remediation plan.

        Args:
            engagement_id: Engagement to generate plan for
            max_tokens: Maximum tokens in response

        Returns:
            str: Generated remediation plan, or None if failed
        """
        if not self.is_available():
            logger.warning("AI provider not available for remediation plan")
            return None

        try:
            context = self._context_builder.build_remediation_context(engagement_id)
            if not context:
                logger.error("Failed to build remediation context")
                return None

            prompt = REMEDIATION_PLAN_PROMPT.format(**context)

            def _generate():
                return self.provider.generate(
                    prompt=prompt,
                    system_prompt=REPORT_SYSTEM_PROMPT,
                    max_tokens=max_tokens,
                    temperature=0.3,
                )

            result = _run_with_timeout(_generate)

            if result:
                logger.info(
                    f"Generated remediation plan for engagement {engagement_id}"
                )
            return result

        except Exception as e:
            logger.error(f"Failed to generate remediation plan: {e}")
            return None

    def generate_risk_rating(self, engagement_id: int) -> Optional[Dict[str, str]]:
        """
        Generate overall risk rating.

        Args:
            engagement_id: Engagement to rate

        Returns:
            dict: {rating: str, justification: str} or None if failed
        """
        if not self.is_available():
            return None

        try:
            context = self._context_builder.build_executive_context(engagement_id)
            findings_summary = f"""
Critical: {context.get('critical_count', 0)}
High: {context.get('high_count', 0)}
Medium: {context.get('medium_count', 0)}
Low: {context.get('low_count', 0)}
Hosts: {context.get('total_hosts', 0)}
Credentials Compromised: {context.get('credentials_count', 0)}
"""
            prompt = RISK_RATING_PROMPT.format(findings_summary=findings_summary)

            def _generate():
                return self.provider.generate(
                    prompt=prompt,
                    system_prompt=REPORT_SYSTEM_PROMPT,
                    max_tokens=200,
                    temperature=0.2,
                )

            result = _run_with_timeout(_generate)

            if result:
                return self._parse_risk_rating(result)
            return None

        except Exception as e:
            logger.error(f"Failed to generate risk rating: {e}")
            return None

    def generate_all_content(
        self, engagement_id: int, enhance_findings: bool = True, max_findings: int = 10
    ) -> Dict[str, Any]:
        """
        Generate all AI content for a report.

        Args:
            engagement_id: Engagement to generate content for
            enhance_findings: Whether to enhance individual findings
            max_findings: Maximum findings to enhance (for cost control)

        Returns:
            dict: All generated content
        """
        from souleyez.storage.findings import FindingsManager

        content = {
            "executive_summary": None,
            "remediation_plan": None,
            "risk_rating": None,
            "enhanced_findings": {},
            "provider": None,
            "errors": [],
        }

        if not self.is_available():
            content["errors"].append("AI provider not available")
            return content

        content["provider"] = self.provider.provider_type.value

        # Generate executive summary
        try:
            content["executive_summary"] = self.generate_executive_summary(
                engagement_id
            )
        except Exception as e:
            content["errors"].append(f"Executive summary: {e}")

        # Generate remediation plan
        try:
            content["remediation_plan"] = self.generate_remediation_plan(engagement_id)
        except Exception as e:
            content["errors"].append(f"Remediation plan: {e}")

        # Generate risk rating
        try:
            content["risk_rating"] = self.generate_risk_rating(engagement_id)
        except Exception as e:
            content["errors"].append(f"Risk rating: {e}")

        # Enhance individual findings (top critical/high only)
        if enhance_findings:
            try:
                fm = FindingsManager()
                findings = fm.list_findings(engagement_id)

                # Sort by severity and take top N
                severity_order = {
                    "critical": 0,
                    "high": 1,
                    "medium": 2,
                    "low": 3,
                    "info": 4,
                }
                priority_findings = sorted(
                    [
                        f
                        for f in findings
                        if f.get("severity", "").lower() in ["critical", "high"]
                    ],
                    key=lambda f: severity_order.get(
                        f.get("severity", "info").lower(), 4
                    ),
                )[:max_findings]

                for finding in priority_findings:
                    try:
                        enhanced = self.enhance_finding(finding)
                        if enhanced:
                            content["enhanced_findings"][finding["id"]] = enhanced
                    except Exception as e:
                        logger.warning(
                            f"Failed to enhance finding {finding.get('id')}: {e}"
                        )

            except Exception as e:
                content["errors"].append(f"Finding enhancement: {e}")

        return content

    def _parse_finding_enhancement(self, response: str) -> Dict[str, str]:
        """Parse LLM response into structured finding enhancement."""
        result = {"business_impact": "", "attack_scenario": "", "risk_context": ""}

        # Try to extract sections
        sections = {
            "business_impact": r"BUSINESS IMPACT[:\s]*(.+?)(?=ATTACK SCENARIO|RISK CONTEXT|$)",
            "attack_scenario": r"ATTACK SCENARIO[:\s]*(.+?)(?=RISK CONTEXT|BUSINESS IMPACT|$)",
            "risk_context": r"RISK CONTEXT[:\s]*(.+?)(?=BUSINESS IMPACT|ATTACK SCENARIO|$)",
        }

        for key, pattern in sections.items():
            match = re.search(pattern, response, re.IGNORECASE | re.DOTALL)
            if match:
                result[key] = match.group(1).strip()

        # If parsing failed, use the whole response as business impact
        if not any(result.values()):
            result["business_impact"] = response.strip()

        return result

    def _parse_risk_rating(self, response: str) -> Dict[str, str]:
        """Parse risk rating response."""
        result = {"rating": "UNKNOWN", "justification": response}

        # Look for rating pattern
        match = re.search(
            r"RATING:\s*(CRITICAL|HIGH|MODERATE|LOW)\s*[-–]\s*(.+)",
            response,
            re.IGNORECASE,
        )
        if match:
            result["rating"] = match.group(1).upper()
            result["justification"] = match.group(2).strip()

        return result

    def estimate_tokens(self, engagement_id: int) -> Dict[str, int]:
        """
        Estimate token usage for full AI enhancement.

        Args:
            engagement_id: Engagement to estimate for

        Returns:
            dict: Estimated token counts
        """
        from souleyez.storage.findings import FindingsManager

        context = self._context_builder.build_executive_context(engagement_id)
        fm = FindingsManager()
        findings = fm.list_findings(engagement_id)

        # Rough estimates
        executive_input = len(EXECUTIVE_SUMMARY_PROMPT.format(**context)) // 4
        executive_output = 400

        remediation_ctx = self._context_builder.build_remediation_context(engagement_id)
        remediation_input = len(REMEDIATION_PLAN_PROMPT.format(**remediation_ctx)) // 4
        remediation_output = 800

        critical_high = len(
            [
                f
                for f in findings
                if f.get("severity", "").lower() in ["critical", "high"]
            ]
        )
        findings_input = critical_high * 300
        findings_output = critical_high * 200

        return {
            "executive_summary": executive_input + executive_output,
            "remediation_plan": remediation_input + remediation_output,
            "findings_enhancement": findings_input + findings_output,
            "total_estimated": (
                executive_input
                + executive_output
                + remediation_input
                + remediation_output
                + findings_input
                + findings_output
            ),
            "findings_to_enhance": min(critical_high, 10),
        }
