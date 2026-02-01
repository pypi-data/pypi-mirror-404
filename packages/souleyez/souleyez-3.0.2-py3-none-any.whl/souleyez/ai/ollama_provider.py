"""
souleyez.ai.ollama_provider - Ollama LLM provider implementation

Wraps the existing OllamaService to implement the LLMProvider interface.
"""

import logging
from typing import Any, Dict, Optional

from .llm_provider import LLMProvider, LLMProviderType
from .ollama_service import OLLAMA_AVAILABLE, OllamaService

logger = logging.getLogger(__name__)


class OllamaProvider(LLMProvider):
    """
    Ollama LLM provider - wraps existing OllamaService.

    This provider runs LLMs locally via Ollama, keeping all data on-premise.
    No API key required, but Ollama must be installed and running.
    """

    def __init__(self, model: Optional[str] = None, endpoint: Optional[str] = None):
        """
        Initialize Ollama provider.

        Args:
            model: Model name to use (default: from config or llama3.1:8b)
            endpoint: Ollama API endpoint (default: localhost:11434)
        """
        self._service = OllamaService(endpoint=endpoint, model=model)
        self._model = model or self._service.model

    @property
    def provider_type(self) -> LLMProviderType:
        """Return the provider type."""
        return LLMProviderType.OLLAMA

    @property
    def model_name(self) -> str:
        """Return the model name being used."""
        return self._model

    def is_available(self) -> bool:
        """
        Check if Ollama is running and model is available.

        Returns:
            bool: True if ready to generate, False otherwise
        """
        if not OLLAMA_AVAILABLE:
            logger.debug("Ollama package not installed")
            return False

        if not self._service.check_connection():
            logger.debug("Ollama service not running")
            return False

        if not self._service.check_model():
            logger.debug(f"Model {self._model} not available")
            return False

        return True

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.3,
    ) -> Optional[str]:
        """
        Generate text using Ollama.

        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt (prepended to prompt)
            max_tokens: Maximum tokens (not directly supported, using timeout)
            temperature: Creativity setting (not directly used by OllamaService)

        Returns:
            str: Generated text, or None if failed
        """
        if not self.is_available():
            logger.error("Ollama provider not available")
            return None

        # Combine system prompt and user prompt
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"

        # Calculate timeout based on max_tokens (rough estimate)
        # ~50 tokens/second for typical models
        timeout = max(60, max_tokens // 30)

        return self._service.generate(full_prompt, timeout=timeout)

    def get_status(self) -> Dict[str, Any]:
        """
        Get Ollama service status.

        Returns:
            dict: Status including connection, models, availability
        """
        status = self._service.get_status()
        status["provider_type"] = self.provider_type.value
        status["provider"] = "Ollama"
        status["provider_name"] = "Ollama (Local)"
        return status
