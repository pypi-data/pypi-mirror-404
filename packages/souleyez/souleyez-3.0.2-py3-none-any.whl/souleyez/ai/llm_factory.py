"""
souleyez.ai.llm_factory - Factory for creating LLM providers

This module provides a factory pattern for creating LLM providers
based on user configuration.
"""

import logging
from typing import Optional

from .llm_provider import LLMProvider, LLMProviderType

logger = logging.getLogger(__name__)


class LLMFactory:
    """
    Factory for creating LLM providers based on configuration.

    Supports automatic provider selection based on config and
    fallback to alternative providers if primary is unavailable.
    """

    @staticmethod
    def get_provider(provider_type: Optional[LLMProviderType] = None) -> LLMProvider:
        """
        Get LLM provider of specified type.

        Args:
            provider_type: Provider type to create (default: from config)

        Returns:
            LLMProvider: Instance of the requested provider
        """
        from souleyez.config import get

        if provider_type is None:
            # Read from config
            provider_str = get("ai.provider", "ollama")
            try:
                provider_type = LLMProviderType(provider_str)
            except ValueError:
                logger.warning(
                    f"Unknown provider '{provider_str}', defaulting to ollama"
                )
                provider_type = LLMProviderType.OLLAMA

        if provider_type == LLMProviderType.CLAUDE:
            from .claude_provider import ClaudeProvider

            model = get("ai.claude_model")
            return ClaudeProvider(model=model)
        else:
            from .ollama_provider import OllamaProvider

            model = get("ai.ollama_model") or get("settings.ollama_model")
            return OllamaProvider(model=model)

    @staticmethod
    def get_available_provider() -> Optional[LLMProvider]:
        """
        Get first available provider, preferring configured one.

        Tries the configured provider first, then falls back to alternatives.

        Returns:
            LLMProvider: First available provider, or None if none available
        """
        # Try configured provider first
        configured = LLMFactory.get_provider()
        if configured.is_available():
            logger.debug(f"Using configured provider: {configured.provider_type.value}")
            return configured

        # Determine fallback type
        if configured.provider_type == LLMProviderType.CLAUDE:
            fallback_type = LLMProviderType.OLLAMA
        else:
            fallback_type = LLMProviderType.CLAUDE

        # Try fallback
        try:
            fallback = LLMFactory.get_provider(fallback_type)
            if fallback.is_available():
                logger.info(
                    f"Primary provider {configured.provider_type.value} unavailable, "
                    f"using fallback: {fallback_type.value}"
                )
                return fallback
        except Exception as e:
            logger.debug(f"Fallback provider {fallback_type.value} failed: {e}")

        logger.warning("No LLM providers available")
        return None

    @staticmethod
    def get_all_providers() -> dict:
        """
        Get status of all supported providers.

        Returns:
            dict: Status information for each provider type
        """
        from souleyez.config import get

        results = {}

        # Check Ollama
        try:
            from .ollama_provider import OllamaProvider

            ollama = OllamaProvider()
            results["ollama"] = {
                "available": ollama.is_available(),
                "status": ollama.get_status(),
                "configured": get("ai.provider", "ollama") == "ollama",
            }
        except Exception as e:
            results["ollama"] = {
                "available": False,
                "error": str(e),
                "configured": get("ai.provider", "ollama") == "ollama",
            }

        # Check Claude
        try:
            from .claude_provider import ClaudeProvider

            claude = ClaudeProvider()
            results["claude"] = {
                "available": claude.is_available(),
                "status": claude.get_status(),
                "configured": get("ai.provider", "ollama") == "claude",
            }
        except Exception as e:
            results["claude"] = {
                "available": False,
                "error": str(e),
                "configured": get("ai.provider", "ollama") == "claude",
            }

        return results
