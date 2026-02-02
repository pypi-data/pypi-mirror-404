#!/usr/bin/env python3
"""
souleyez.ai.recommender - AI-powered attack path recommendations

Uses LLM (via Ollama or Claude) to analyze engagement data and suggest
the next most promising penetration testing step.
"""

import logging
import re
from typing import Any, Dict, List, Optional

from .context_builder import ContextBuilder
from .llm_factory import LLMFactory
from .ollama_service import OllamaService

logger = logging.getLogger(__name__)


class AttackRecommender:
    """
    Generate AI-powered attack path recommendations.

    Analyzes current engagement state and suggests the single best
    next action to take, using local LLM inference.
    """

    PROMPT_TEMPLATE = """You are an expert penetration tester analyzing an engagement and suggesting the next most promising attack step.

{context}

Based on this engagement data, suggest the SINGLE BEST next attack step to take.

Respond in EXACTLY this format:
ACTION: [specific action to take]
TARGET: [host/service to target]
RATIONALE: [why this is the best next step]
EXPECTED: [what we hope to achieve]
RISK: [low/medium/high]

Consider:
- High-value targets (domain controllers, databases, web servers)
- Available credentials to test
- Known vulnerabilities and CVEs
- Services that commonly have weak configurations
- Lateral movement opportunities
- Information gathering that could lead to further access

Be specific and actionable. Focus on practical pentesting methodology.
If no hosts are discovered yet, suggest reconnaissance actions.
"""

    def __init__(self, provider=None):
        """
        Initialize recommender.

        Args:
            provider: Optional LLM provider instance (from LLMFactory)
        """
        self.provider = provider or LLMFactory.get_available_provider()
        self.context_builder = ContextBuilder()

        # For backward compatibility, also set ollama attribute if using OllamaProvider
        if hasattr(self.provider, "service"):
            self.ollama = self.provider.service
        else:
            self.ollama = None

    def suggest_next_step(
        self, engagement_id: int, target_host_ids: Optional[list] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Suggest the next best attack step for an engagement.

        Args:
            engagement_id: Engagement to analyze
            target_host_ids: Optional list of specific host IDs to target

        Returns:
            dict: Recommendation with keys:
                - action: Specific action to take
                - target: Host/service to target
                - rationale: Why this is the best step
                - expected_outcome: What we hope to achieve
                - risk_level: low/medium/high
            None: If recommendation fails
        """
        # Check provider availability
        if not self.provider or not self.provider.is_available():
            logger.error("Cannot generate recommendation: AI provider not available")
            return {
                "error": "AI provider not available. Configure Ollama or Claude in Settings → AI Settings.",
                "action": None,
                "target": None,
                "rationale": None,
                "expected_outcome": None,
                "risk_level": None,
            }

        # Build context from engagement data (with optional host filtering)
        try:
            context = self.context_builder.build_context(
                engagement_id, target_host_ids=target_host_ids
            )
        except Exception as e:
            logger.error(f"Failed to build context: {e}")
            return {
                "error": f"Failed to load engagement data: {e}",
                "action": None,
                "target": None,
                "rationale": None,
                "expected_outcome": None,
                "risk_level": None,
            }

        # Build prompt with state awareness
        state_summary = self.context_builder.get_state_summary(
            engagement_id, target_host_ids=target_host_ids
        )

        # Add targeting note if specific hosts selected
        targeting_note = ""
        if target_host_ids:
            targeting_note = f"\nNOTE: Only target the {len(target_host_ids)} selected host(s) listed above. Do not suggest actions against other hosts.\n"

        prompt = f"""You are an expert penetration tester analyzing an engagement and suggesting the next most promising attack step.

{state_summary}

{context}{targeting_note}

IMPORTANT: Analyze the current state above carefully:
- If credentials are marked as VALID, they've been tested successfully - don't suggest retesting them
- If hosts are marked as COMPROMISED, we already have access - suggest next steps from that point
- If access_level is shown, continue from that privilege level
- Focus on UNTESTED credentials and unexplored attack paths
- If a service scan (nmap) was already completed, don't suggest running it again

TOOL SELECTION GUIDELINES:
- For HTTP/HTTPS services: Use "HTTP enumeration" (gobuster), NOT nmap
- For web directory discovery: Use "directory enumeration" 
- For SMB shares: Use "enumerate SMB shares" (enum4linux/smbmap)
- For SQL databases: Use "test database credentials" or "enumerate database"
- For SSH/FTP/RDP: Use "test [service] credentials" if credentials available
- For unknown ports: Use "port scan" (nmap)
- Don't suggest nmap service scans if services are already identified

Based on this engagement data, suggest the SINGLE BEST next attack step to take.

Respond in EXACTLY this format:
ACTION: [specific action to take]
TARGET: [host/service to target]
RATIONALE: [why this is the best next step given current state]
EXPECTED: [what we hope to achieve]
RISK: [low/medium/high]

Consider:
- High-value targets (domain controllers, databases, web servers)
- Available UNTESTED credentials
- Known vulnerabilities and CVEs
- Services that commonly have weak configurations
- Lateral movement opportunities from compromised hosts
- Privilege escalation if we have user-level access

Be specific and actionable. Focus on practical pentesting methodology.
Continue from current state - don't restart from scratch."""

        # Generate recommendation
        provider_type = getattr(self.provider, "provider_type", "unknown")
        logger.info(
            f"Generating recommendation for engagement {engagement_id} using {provider_type}"
        )
        try:
            response = self.provider.generate(
                prompt=prompt, max_tokens=2000, temperature=0.7
            )
            if not response:
                logger.error("LLM returned empty response")
                return {
                    "error": "LLM generation failed (empty response). Check AI provider configuration.",
                    "action": None,
                    "target": None,
                    "rationale": None,
                    "expected_outcome": None,
                    "risk_level": None,
                }
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            return {
                "error": f"LLM generation failed: {e}",
                "action": None,
                "target": None,
                "rationale": None,
                "expected_outcome": None,
                "risk_level": None,
            }

        # Parse response
        try:
            recommendation = self._parse_response(response)
            logger.info(
                f"Generated recommendation: {recommendation.get('action', 'unknown')}"
            )
            return recommendation
        except Exception as e:
            logger.error(f"Failed to parse LLM response: {e}")
            logger.debug(f"Raw response: {response}")
            return {
                "error": f"Failed to parse LLM response: {e}",
                "action": None,
                "target": None,
                "rationale": None,
                "expected_outcome": None,
                "risk_level": None,
                "raw_response": response,
            }

    def _parse_response(self, response: str) -> Dict[str, Any]:
        """
        Parse LLM response into structured recommendation.

        Expected format:
            ACTION: [text]
            TARGET: [text]
            RATIONALE: [text]
            EXPECTED: [text]
            RISK: [low/medium/high]

        Args:
            response: Raw LLM response text

        Returns:
            dict: Parsed recommendation

        Raises:
            ValueError: If response format is invalid
        """
        # Extract fields using regex
        action_match = re.search(
            r"ACTION:\s*(.+?)(?=\n[A-Z]+:|$)", response, re.DOTALL | re.IGNORECASE
        )
        target_match = re.search(
            r"TARGET:\s*(.+?)(?=\n[A-Z]+:|$)", response, re.DOTALL | re.IGNORECASE
        )
        rationale_match = re.search(
            r"RATIONALE:\s*(.+?)(?=\n[A-Z]+:|$)", response, re.DOTALL | re.IGNORECASE
        )
        expected_match = re.search(
            r"EXPECTED:\s*(.+?)(?=\n[A-Z]+:|$)", response, re.DOTALL | re.IGNORECASE
        )
        risk_match = re.search(
            r"RISK:\s*(.+?)(?=\n[A-Z]+:|$)", response, re.DOTALL | re.IGNORECASE
        )

        # Validate all fields present
        if not all(
            [action_match, target_match, rationale_match, expected_match, risk_match]
        ):
            missing = []
            if not action_match:
                missing.append("ACTION")
            if not target_match:
                missing.append("TARGET")
            if not rationale_match:
                missing.append("RATIONALE")
            if not expected_match:
                missing.append("EXPECTED")
            if not risk_match:
                missing.append("RISK")
            raise ValueError(f"Missing required fields: {', '.join(missing)}")

        # Extract and clean values
        action = action_match.group(1).strip()
        target = target_match.group(1).strip()
        rationale = rationale_match.group(1).strip()
        expected = expected_match.group(1).strip()

        # Extract risk level (grab only first word, handle multi-line responses)
        risk_text = risk_match.group(1).strip()
        risk = risk_text.split()[0].lower() if risk_text else "medium"

        # Validate risk level
        if risk not in ["low", "medium", "high"]:
            logger.warning(f"Invalid risk level '{risk}', defaulting to 'medium'")
            risk = "medium"

        return {
            "error": None,
            "action": action,
            "target": target,
            "rationale": rationale,
            "expected_outcome": expected,
            "risk_level": risk,
        }

    def generate_chain(
        self, engagement_id: int, num_steps: int = 5
    ) -> Optional[Dict[str, Any]]:
        """
        Generate a multi-step attack chain.

        Args:
            engagement_id: ID of engagement to analyze
            num_steps: Number of steps to generate

        Returns:
            dict: Chain with list of steps, or error dict if failed
        """
        # Check provider availability
        if not self.provider or not self.provider.is_available():
            logger.error("Cannot generate chain: AI provider not available")
            return {
                "error": "AI provider not available. Configure Ollama or Claude in Settings → AI Settings.",
                "steps": [],
            }

        # Build context from engagement data
        try:
            context = self.context_builder.build_context(engagement_id)
        except Exception as e:
            logger.error(f"Failed to build context: {e}")
            return {"error": f"Failed to load engagement data: {e}", "steps": []}

        # Create multi-step prompt
        prompt = self._build_chain_prompt(context, num_steps, engagement_id)

        # Get AI response
        provider_type = getattr(self.provider, "provider_type", "unknown")
        logger.info(
            f"Generating {num_steps}-step chain for engagement {engagement_id} using {provider_type}"
        )
        try:
            response = self.provider.generate(
                prompt=prompt, max_tokens=3000, temperature=0.7
            )
            if not response:
                logger.error("LLM returned empty response")
                return {"error": "LLM generation failed (empty response)", "steps": []}
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            return {"error": f"LLM generation failed: {e}", "steps": []}

        # Parse multi-step response
        try:
            steps = self._parse_chain_response(response)
            logger.info(f"Generated {len(steps)}-step attack chain")

            # DEBUG: Log if we got empty steps
            if not steps:
                logger.warning(
                    f"Parsed 0 steps from response. Raw response:\n{response}"
                )

            return {
                "error": None,
                "engagement_id": engagement_id,
                "num_steps": len(steps),
                "steps": steps,
            }
        except Exception as e:
            logger.error(f"Failed to parse chain response: {e}")
            logger.debug(f"Raw response: {response}")
            return {
                "error": f"Failed to parse chain response: {e}",
                "steps": [],
                "raw_response": response,
            }

    def _build_chain_prompt(
        self, context: str, num_steps: int, engagement_id: int
    ) -> str:
        """Build prompt for multi-step attack chain with state awareness."""

        # Get current state summary
        state_summary = self.context_builder.get_state_summary(engagement_id)

        return f"""You are an expert penetration tester. Analyze this engagement and create a {num_steps}-step attack chain.

{state_summary}

ENGAGEMENT DATA:
{context}

IMPORTANT: Analyze the current state above carefully:
- If credentials are marked as VALID, they've been tested successfully - skip retesting them
- If hosts are marked as COMPROMISED, we already have access - plan next steps from that point
- If access_level is shown, continue from that privilege level
- Focus on UNTESTED credentials and unexplored attack paths

Generate exactly {num_steps} sequential attack steps. Each step should build on previous steps AND current engagement state.

FORMAT for each step:
STEP N:
ACTION: [specific action to take]
TARGET: [target system/service]
RATIONALE: [why this step makes sense now, considering current state]
EXPECTED: [expected outcome]
RISK: [LOW/MEDIUM/HIGH]
DEPENDENCIES: [which previous steps must complete first, or "None"]

PROGRESSION LOGIC:
1. If no access yet: Test known credentials first (lowest risk)
2. If credentials validated but no shell: Exploit services with valid creds
3. If user access gained: Enumerate and find privilege escalation
4. If root/admin access: Establish persistence, search for lateral movement
5. If multiple systems: Plan lateral movement between hosts

Be specific and actionable. Think like a professional pentester. Continue from current state, don't restart from scratch."""

    def _parse_chain_response(self, response: str) -> List[Dict[str, str]]:
        """Parse AI response into list of steps."""
        steps = []

        # DEBUG: Log the response we're trying to parse
        logger.debug(f"Parsing chain response: {response[:200]}...")

        # Split by "STEP N:" pattern (handle both with and without leading newline)
        step_blocks = re.split(r"STEP \d+:", response)

        logger.debug(f"Split into {len(step_blocks)} blocks")

        for i, block in enumerate(
            step_blocks[1:], 1
        ):  # Skip first block (before first STEP)
            step = {
                "step_number": i,
                "action": self._extract_field(block, "ACTION"),
                "target": self._extract_field(block, "TARGET"),
                "rationale": self._extract_field(block, "RATIONALE"),
                "expected": self._extract_field(block, "EXPECTED"),
                "risk": self._extract_risk_field(block),
                "dependencies": self._extract_field(block, "DEPENDENCIES"),
            }
            steps.append(step)

        return steps

    def _extract_field(self, text: str, field_name: str) -> str:
        """Extract a field value from text block."""
        pattern = rf"{field_name}:\s*(.+?)(?=\n[A-Z]+:|$)"
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return "Unknown"

    def _extract_risk_field(self, text: str) -> str:
        """Extract and validate risk field (handles multi-line responses)."""
        risk_text = self._extract_field(text, "RISK")
        risk = (
            risk_text.split()[0].upper()
            if risk_text and risk_text != "Unknown"
            else "MEDIUM"
        )

        # Validate risk level
        if risk not in ["LOW", "MEDIUM", "HIGH"]:
            logger.warning(f"Invalid risk level '{risk}', defaulting to 'MEDIUM'")
            risk = "MEDIUM"

        return risk

    def suggest_multiple_paths(
        self, engagement_id: int, num_paths: int = 3
    ) -> Dict[str, Any]:
        """
        Generate multiple alternative attack paths and rank them.

        Args:
            engagement_id: Engagement to analyze
            num_paths: Number of alternative paths to generate (default: 3)

        Returns:
            dict with:
                - paths: List of ranked paths with scores
                - engagement_id: Engagement ID
                - error: Error message if failed
        """
        # Check provider availability
        if not self.provider or not self.provider.is_available():
            logger.error("Cannot generate paths: AI provider not available")
            return {
                "error": "AI provider not available. Configure Ollama or Claude in Settings → AI Settings.",
                "paths": [],
            }

        # Build context
        try:
            context = self.context_builder.build_context(engagement_id)
        except Exception as e:
            logger.error(f"Failed to build context: {e}")
            return {"error": f"Failed to load engagement data: {e}", "paths": []}

        # Build multi-path prompt
        prompt = self._build_multi_path_prompt(context, num_paths)

        # Generate recommendations
        provider_type = getattr(self.provider, "provider_type", "unknown")
        logger.info(
            f"Generating {num_paths} alternative paths for engagement {engagement_id} using {provider_type}"
        )
        try:
            response = self.provider.generate(
                prompt=prompt, max_tokens=2500, temperature=0.7
            )
            if not response:
                logger.error("LLM returned empty response")
                return {
                    "error": "AI generation failed. Check provider configuration.",
                    "paths": [],
                }
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            return {"error": f"LLM generation failed: {e}", "paths": []}

        # Parse response
        try:
            paths = self._parse_multi_path_response(response)
            logger.info(f"Generated {len(paths)} alternative paths")

            # Score and rank paths
            from .path_scorer import PathScorer

            scorer = PathScorer()

            # Get engagement data for scoring
            engagement_data = self._get_engagement_data(engagement_id)
            ranked_paths = scorer.rank_paths(paths, engagement_data)

            return {
                "error": None,
                "engagement_id": engagement_id,
                "paths": ranked_paths,
            }
        except Exception as e:
            logger.error(f"Failed to parse/score paths: {e}")
            return {
                "error": f"Failed to process paths: {e}",
                "paths": [],
                "raw_response": response,
            }

    def _build_multi_path_prompt(self, context: str, num_paths: int) -> str:
        """Build prompt for generating multiple alternative paths."""
        return f"""You are an expert penetration tester. Analyze this engagement and suggest {num_paths} DIFFERENT attack paths.

ENGAGEMENT DATA:
{context}

Generate exactly {num_paths} alternative attack approaches. Each should be DISTINCT and viable.

FORMAT for each path:
PATH N:
ACTION: [specific action to take]
TARGET: [target system/service]
RATIONALE: [why this approach makes sense]
EXPECTED: [expected outcome]
RISK: [LOW/MEDIUM/HIGH]

Focus on diversity - each path should use different techniques:
- Path 1: Credential-based approach (if credentials available)
- Path 2: Vulnerability exploitation (if vulns found)
- Path 3: Service enumeration and exploitation
- Path 4+: Alternative techniques (lateral movement, privilege escalation, etc.)

Be specific and actionable. Think like a professional pentester considering multiple options."""

    def _parse_multi_path_response(self, response: str) -> List[Dict[str, str]]:
        """Parse AI response into list of alternative paths."""
        import re

        paths = []

        # Split by "PATH N:" pattern
        path_blocks = re.split(r"PATH \d+:", response)

        for i, block in enumerate(path_blocks[1:], 1):  # Skip first block
            path = {
                "action": self._extract_field(block, "ACTION"),
                "target": self._extract_field(block, "TARGET"),
                "rationale": self._extract_field(block, "RATIONALE"),
                "expected": self._extract_field(block, "EXPECTED"),
                "risk_level": self._extract_risk_field(block),
            }
            paths.append(path)

        return paths

    def _get_engagement_data(self, engagement_id: int) -> Dict[str, Any]:
        """Get engagement data for scoring."""
        from ..storage.credentials import CredentialsManager
        from ..storage.engagements import EngagementManager
        from ..storage.findings import FindingsManager
        from ..storage.hosts import HostManager

        em = EngagementManager()
        hm = HostManager()
        cm = CredentialsManager()
        fm = FindingsManager()

        return {
            "engagement": em.get_by_id(engagement_id),
            "hosts": hm.list_hosts(engagement_id),
            "credentials": cm.list_credentials(engagement_id),
            "findings": fm.list_findings(engagement_id),
        }
