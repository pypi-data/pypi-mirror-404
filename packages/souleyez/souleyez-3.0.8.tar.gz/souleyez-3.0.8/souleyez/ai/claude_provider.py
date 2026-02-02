"""
souleyez.ai.claude_provider - Anthropic Claude API provider implementation

Provides Claude LLM integration for high-quality AI report generation.
Requires API key stored securely via CryptoManager.
"""

import logging
from typing import Any, Dict, Optional

from .llm_provider import LLMProvider, LLMProviderType

logger = logging.getLogger(__name__)

# Check if anthropic package is available
try:
    import anthropic

    ANTHROPIC_AVAILABLE = True
except ImportError:
    anthropic = None
    ANTHROPIC_AVAILABLE = False


class ClaudeProvider(LLMProvider):
    """
    Anthropic Claude API provider.

    Provides high-quality LLM capabilities via the Claude API.
    API key is stored encrypted in config via CryptoManager.
    """

    DEFAULT_MODEL = "claude-sonnet-4-20250514"

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize Claude provider.

        Args:
            api_key: Claude API key (default: from encrypted config)
            model: Model to use (default: from config or claude-sonnet-4-20250514)
        """
        self._api_key = api_key
        self._model = model or self._load_model()
        self._client = None

    def _load_api_key(self) -> Optional[str]:
        """Load API key from encrypted config."""
        if self._api_key:
            return self._api_key

        from souleyez.config import get
        from souleyez.storage.crypto import get_crypto_manager

        encrypted_key = get("ai.claude_api_key")
        if not encrypted_key:
            logger.debug("No Claude API key configured")
            return None

        try:
            crypto = get_crypto_manager()
            if crypto.is_unlocked():
                decrypted = crypto.decrypt(encrypted_key)
                return decrypted
            else:
                logger.warning("Crypto manager locked, cannot decrypt API key")
                return None
        except Exception as e:
            logger.error(f"Failed to decrypt Claude API key: {e}")
            return None

    def _load_model(self) -> str:
        """Load model from config."""
        from souleyez.config import get

        return get("ai.claude_model", self.DEFAULT_MODEL)

    def _get_client(self):
        """Get or create Anthropic client."""
        if self._client is not None:
            return self._client

        api_key = self._load_api_key()
        if not api_key:
            return None

        if not ANTHROPIC_AVAILABLE:
            logger.error(
                "anthropic package not installed. Install with: pip install anthropic"
            )
            return None

        try:
            self._client = anthropic.Anthropic(api_key=api_key)
            return self._client
        except Exception as e:
            logger.error(f"Failed to create Anthropic client: {e}")
            return None

    @property
    def provider_type(self) -> LLMProviderType:
        """Return the provider type."""
        return LLMProviderType.CLAUDE

    @property
    def model_name(self) -> str:
        """Return the model name being used."""
        return self._model

    def is_available(self) -> bool:
        """
        Check if Claude API is configured and accessible.

        Returns:
            bool: True if ready to generate, False otherwise
        """
        if not ANTHROPIC_AVAILABLE:
            logger.debug("anthropic package not installed")
            return False

        api_key = self._load_api_key()
        if not api_key:
            logger.debug("No Claude API key available")
            return False

        # Try to create client
        client = self._get_client()
        return client is not None

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.3,
    ) -> Optional[str]:
        """
        Generate text using Claude API.

        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt for context
            max_tokens: Maximum tokens in response
            temperature: Creativity setting (0.0 - 1.0)

        Returns:
            str: Generated text, or None if failed
        """
        client = self._get_client()
        if client is None:
            logger.error("Claude client not available")
            return None

        try:
            # Build messages
            messages = [{"role": "user", "content": prompt}]

            # Create message with optional system prompt
            kwargs = {
                "model": self._model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": messages,
            }

            if system_prompt:
                kwargs["system"] = system_prompt

            response = client.messages.create(**kwargs)

            # Extract text from response
            if response.content and len(response.content) > 0:
                return response.content[0].text

            logger.warning("Empty response from Claude")
            return None

        except anthropic.APIConnectionError as e:
            logger.error(f"Claude API connection error: {e}")
            return None
        except anthropic.RateLimitError as e:
            logger.error(f"Claude API rate limit exceeded: {e}")
            return None
        except anthropic.APIStatusError as e:
            logger.error(f"Claude API error: {e.status_code} - {e.message}")
            return None
        except Exception as e:
            logger.error(f"Claude generation failed: {e}")
            return None

    def get_status(self) -> Dict[str, Any]:
        """
        Get Claude provider status.

        Returns:
            dict: Status including API key status, model, availability
        """
        api_key = self._load_api_key()
        has_key = api_key is not None

        status = {
            "provider_type": self.provider_type.value,
            "provider": "Claude",
            "provider_name": "Claude (Anthropic)",
            "model": self._model,
            "api_key_configured": has_key,
            "package_installed": ANTHROPIC_AVAILABLE,
            "connected": False,
            "error": None,
        }

        if not ANTHROPIC_AVAILABLE:
            status["error"] = "anthropic package not installed"
            return status

        if not has_key:
            status["error"] = "No API key configured"
            return status

        # Test connection
        try:
            client = self._get_client()
            if client:
                status["connected"] = True
            else:
                status["error"] = "Failed to create client"
        except Exception as e:
            status["error"] = str(e)

        return status


def set_claude_api_key(api_key: str) -> bool:
    """
    Securely store Claude API key in encrypted config.

    Args:
        api_key: The Claude API key to store

    Returns:
        bool: True if stored successfully, False otherwise
    """
    from souleyez.config import read_config, write_config
    from souleyez.storage.crypto import get_crypto_manager

    crypto = get_crypto_manager()
    if not crypto.is_unlocked():
        logger.error("Vault must be unlocked to store API key")
        return False

    try:
        encrypted_key = crypto.encrypt(api_key)
        if not encrypted_key:
            logger.error("Failed to encrypt API key")
            return False

        cfg = read_config()
        if "ai" not in cfg:
            cfg["ai"] = {}
        cfg["ai"]["claude_api_key"] = encrypted_key
        write_config(cfg)

        logger.info("Claude API key stored successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to store Claude API key: {e}")
        return False


def clear_claude_api_key() -> bool:
    """
    Remove Claude API key from config.

    Returns:
        bool: True if removed successfully, False otherwise
    """
    from souleyez.config import read_config, write_config

    try:
        cfg = read_config()
        if "ai" in cfg and "claude_api_key" in cfg["ai"]:
            del cfg["ai"]["claude_api_key"]
            write_config(cfg)
            logger.info("Claude API key removed")
        return True
    except Exception as e:
        logger.error(f"Failed to remove Claude API key: {e}")
        return False
