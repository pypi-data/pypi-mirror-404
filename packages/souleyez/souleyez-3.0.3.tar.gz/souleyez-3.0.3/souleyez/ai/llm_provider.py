"""
souleyez.ai.llm_provider - Abstract LLM provider interface

This module defines the abstract base class for LLM providers,
enabling support for multiple backends (Ollama, Claude, etc.)
"""

import logging
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class LLMProviderType(Enum):
    """Supported LLM provider types."""

    OLLAMA = "ollama"
    CLAUDE = "claude"


class LLMProvider(ABC):
    """
    Abstract base class for LLM providers.

    All LLM integrations (Ollama, Claude, etc.) must implement this interface
    to ensure consistent behavior across the application.
    """

    @property
    @abstractmethod
    def provider_type(self) -> LLMProviderType:
        """Return the provider type."""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Return the model name being used."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if the provider is configured and accessible.

        Returns:
            bool: True if provider is ready to generate, False otherwise
        """
        pass

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.3,
    ) -> Optional[str]:
        """
        Generate text from a prompt.

        Args:
            prompt: The user prompt to send to the LLM
            system_prompt: Optional system prompt for context/instructions
            max_tokens: Maximum tokens in the response
            temperature: Creativity setting (0.0 = deterministic, 1.0 = creative)

        Returns:
            str: Generated text, or None if generation failed
        """
        pass

    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """
        Get comprehensive status of the provider.

        Returns:
            dict: Status information including connection state, model info, errors
        """
        pass

    def generate_with_fallback(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.3,
        fallback: Optional[str] = None,
    ) -> str:
        """
        Generate text with a fallback value if generation fails.

        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt
            max_tokens: Maximum tokens in response
            temperature: Creativity setting
            fallback: Value to return if generation fails

        Returns:
            str: Generated text or fallback value
        """
        result = self.generate(prompt, system_prompt, max_tokens, temperature)
        if result is None:
            logger.warning(f"LLM generation failed, using fallback")
            return fallback or ""
        return result
