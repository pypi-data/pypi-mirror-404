"""
souleyez.ai.ollama_service - Ollama LLM integration for local AI inference

This module provides the connection and management layer for Ollama,
enabling SoulEyez to generate AI-powered attack path recommendations
without sending sensitive engagement data to the cloud.
"""

import logging
from typing import Any, Dict, Optional

# Ollama is optional - not available in Ubuntu repos
try:
    import ollama
    from ollama import Client

    OLLAMA_AVAILABLE = True
except ImportError:
    ollama = None
    Client = None
    OLLAMA_AVAILABLE = False

logger = logging.getLogger(__name__)


class OllamaService:
    """
    Service for managing Ollama connections and LLM inference.

    Handles connection management, model verification, and basic
    inference capabilities for local LLM operations.

    Supports automatic failback from remote to localhost when remote is unreachable.
    """

    DEFAULT_ENDPOINT = "http://localhost:11434"
    DEFAULT_MODEL = "llama3.1:8b"  # 8B parameter model for good quality reasoning
    CONNECTION_TIMEOUT = 30  # seconds

    def __init__(
        self,
        endpoint: Optional[str] = None,
        model: Optional[str] = None,
        allow_failback: bool = True,
    ):
        """
        Initialize Ollama service.

        Args:
            endpoint: Custom Ollama endpoint URL (default: read from config or localhost:11434)
            model: Model to use (default: read from config, fallback to DEFAULT_MODEL)
            allow_failback: If True, failback to localhost when remote unreachable

        Raises:
            ValueError: If endpoint is not localhost or VM host gateway
        """
        from souleyez.config import get

        # Read endpoint from config if not provided
        if endpoint is None:
            endpoint = get("ai.ollama_url", self.DEFAULT_ENDPOINT)

        self._original_endpoint = endpoint
        self._failback_used = False
        self._allow_failback = allow_failback
        self._ollama_mode = get("ai.ollama_mode", "local")

        # Security: Validate endpoint is localhost or VM host gateway
        from souleyez.core.network_utils import is_valid_ollama_host

        is_valid, reason = is_valid_ollama_host(endpoint)
        if not is_valid:
            logger.error(f"Ollama endpoint blocked: {reason}")
            raise ValueError(f"Ollama endpoint not allowed: {reason}")

        self.endpoint = endpoint
        self._connected = False
        self._model_available = False
        self._host_type = reason  # 'localhost' or 'local network'

        # Check if ollama package is available
        if not OLLAMA_AVAILABLE:
            logger.warning("Ollama package not installed. AI features disabled.")
            self.client = None
        else:
            self.client = Client(host=self.endpoint)

        # Read model from config if not provided
        if model is None:
            model = get("ai.ollama_model", self.DEFAULT_MODEL)

        self.model = model

    @property
    def failback_used(self) -> bool:
        """Returns True if failback to localhost was used."""
        return self._failback_used

    def _try_failback_to_localhost(self) -> bool:
        """
        Attempt to failback to localhost if remote connection failed.

        Returns:
            True if failback succeeded, False otherwise
        """
        if not self._allow_failback:
            return False

        # Only failback if we're in remote mode and not already on localhost
        if self._ollama_mode != "remote":
            return False

        if self.endpoint == self.DEFAULT_ENDPOINT:
            return False

        logger.warning(
            f"Remote Ollama at {self._original_endpoint} unreachable, "
            f"falling back to localhost"
        )

        # Try localhost
        try:
            self.endpoint = self.DEFAULT_ENDPOINT
            if OLLAMA_AVAILABLE:
                self.client = Client(host=self.endpoint)
                # Test connection
                self.client.list()
                self._connected = True
                self._failback_used = True
                self._host_type = "localhost (failback)"
                logger.info("Successfully connected to localhost Ollama (failback)")
                return True
        except Exception as e:
            logger.warning(f"Localhost failback also failed: {e}")
            # Restore original endpoint
            self.endpoint = self._original_endpoint
            if OLLAMA_AVAILABLE:
                self.client = Client(host=self.endpoint)

        return False

    def check_connection(self) -> bool:
        """
        Check if Ollama is running and accessible.

        If remote mode and connection fails, attempts failback to localhost.

        Returns:
            bool: True if connection successful, False otherwise
        """
        if not OLLAMA_AVAILABLE or self.client is None:
            return False

        try:
            # Try to list models - this will fail if Ollama isn't running
            self.client.list()
            self._connected = True
            logger.info(f"Successfully connected to Ollama at {self.endpoint}")
            return True
        except Exception as e:
            self._connected = False
            logger.warning(f"Failed to connect to Ollama at {self.endpoint}: {e}")

            # Try failback to localhost if in remote mode
            if self._try_failback_to_localhost():
                return True

            return False

    def check_model(self, model_name: Optional[str] = None) -> bool:
        """
        Check if specified model is available locally.

        Args:
            model_name: Model to check (default: configured model)

        Returns:
            bool: True if model exists, False otherwise
        """
        model_name = model_name or self.model

        if not self._connected and not self.check_connection():
            return False

        try:
            models = self.client.list()
            available_models = [m.model for m in models.models]

            # Check for exact match or partial match (e.g., "llama3.1:latest")
            self._model_available = any(model_name in m for m in available_models)

            if self._model_available:
                logger.info(f"Model '{model_name}' is available")
            else:
                logger.warning(
                    f"Model '{model_name}' not found. Available: {available_models}"
                )

            return self._model_available
        except Exception as e:
            logger.error(f"Error checking model: {e}")
            return False

    def pull_model(self, model_name: Optional[str] = None) -> bool:
        """
        Pull/download a model from Ollama registry.

        Args:
            model_name: Model to pull (default: configured model)

        Returns:
            bool: True if pull successful, False otherwise
        """
        model_name = model_name or self.model

        if not self._connected and not self.check_connection():
            logger.error("Cannot pull model: Ollama not connected")
            return False

        try:
            logger.info(f"Pulling model '{model_name}' (this may take a while)...")
            self.client.pull(model_name)
            logger.info(f"Successfully pulled model '{model_name}'")
            self._model_available = True
            return True
        except Exception as e:
            logger.error(f"Failed to pull model: {e}")
            return False

    def generate(
        self, prompt: str, model_name: Optional[str] = None, timeout: int = 120
    ) -> Optional[str]:
        """
        Generate a response from the LLM.

        Args:
            prompt: Input prompt for the LLM
            model_name: Model to use (default: configured model)
            timeout: Timeout in seconds (default: 120)

        Returns:
            str: Generated response, or None if failed
        """
        model_name = model_name or self.model

        if not self._connected and not self.check_connection():
            logger.error("Cannot generate: Ollama not connected")
            return None

        if not self._model_available and not self.check_model(model_name):
            logger.error(f"Cannot generate: Model '{model_name}' not available")
            return None

        try:
            import concurrent.futures

            # Use thread-based timeout instead of signals
            # Signals can interrupt unrelated code (like click.prompt) causing crashes
            def _do_generate():
                return self.client.generate(model=model_name, prompt=prompt)

            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(_do_generate)
                try:
                    response = future.result(timeout=timeout)
                    return response.get("response", "")
                except concurrent.futures.TimeoutError:
                    logger.error(f"Generation timed out after {timeout}s")
                    return None
                except Exception as e:
                    logger.error(f"Generation error: {e}")
                    return None
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            return None

    def get_status(self) -> Dict[str, Any]:
        """
        Get comprehensive status of Ollama service.

        Returns:
            dict: Status information including connection, models, etc.
        """
        status = {
            "endpoint": self.endpoint,
            "original_endpoint": self._original_endpoint,
            "mode": self._ollama_mode,
            "failback_used": self._failback_used,
            "connected": False,
            "models": [],
            "default_model": self.DEFAULT_MODEL,
            "configured_model": self.model,
            "model_available": False,
            "error": None,
        }

        # Check connection
        if not self.check_connection():
            status["error"] = "Cannot connect to Ollama. Is it running?"
            return status

        status["connected"] = True
        status["endpoint"] = self.endpoint  # Update in case failback changed it
        status["failback_used"] = self._failback_used

        # Get available models
        try:
            models_response = self.client.list()
            status["models"] = [m.model for m in models_response.models]
        except Exception as e:
            status["error"] = f"Error listing models: {e}"
            return status

        # Check if default model is available
        status["model_available"] = self.check_model()

        return status
