"""
Unit tests for souleyez.ai.ollama_service

Tests all methods of OllamaService class with mocked Ollama client
to avoid real network calls during testing.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from souleyez.ai.ollama_service import OllamaService


@pytest.fixture(autouse=True)
def mock_host_validation():
    """Mock host validation to allow all hosts during testing."""
    with patch("souleyez.core.network_utils.is_valid_ollama_host") as mock:
        mock.return_value = (True, "localhost")
        yield mock


class TestOllamaServiceInitialization:
    """Test OllamaService initialization."""

    @patch("souleyez.config.get")
    def test_init_with_default_endpoint(self, mock_config_get):
        """Test initialization with default endpoint."""

        # Mock config to return defaults
        def config_side_effect(key, default=None):
            if key == "ai.ollama_url":
                return OllamaService.DEFAULT_ENDPOINT
            elif key == "ai.ollama_model":
                return OllamaService.DEFAULT_MODEL
            return default

        mock_config_get.side_effect = config_side_effect

        service = OllamaService()
        assert service.endpoint == OllamaService.DEFAULT_ENDPOINT
        assert service.client is not None
        assert service._connected is False
        assert service._model_available is False

    def test_init_with_custom_endpoint(self):
        """Test initialization with custom endpoint."""
        custom_endpoint = "http://custom-host:12345"
        service = OllamaService(endpoint=custom_endpoint)
        assert service.endpoint == custom_endpoint
        assert service.client is not None


class TestOllamaServiceConnection:
    """Test connection checking functionality."""

    @patch("souleyez.ai.ollama_service.Client")
    def test_check_connection_success(self, mock_client_class):
        """Test successful connection to Ollama."""
        # Setup mock
        mock_client = Mock()
        mock_response = MagicMock()
        mock_response.models = []
        mock_client.list.return_value = mock_response
        mock_client_class.return_value = mock_client

        service = OllamaService()
        service.client = mock_client

        # Test
        result = service.check_connection()

        assert result is True
        assert service._connected is True
        mock_client.list.assert_called_once()

    @patch("souleyez.ai.ollama_service.Client")
    def test_check_connection_failure(self, mock_client_class):
        """Test failed connection to Ollama (not running)."""
        # Setup mock to raise exception
        mock_client = Mock()
        mock_client.list.side_effect = Exception("Connection refused")
        mock_client_class.return_value = mock_client

        service = OllamaService()
        service.client = mock_client

        # Test
        result = service.check_connection()

        assert result is False
        assert service._connected is False


class TestOllamaServiceModelChecking:
    """Test model availability checking."""

    @patch("souleyez.ai.ollama_service.Client")
    def test_check_model_exists(self, mock_client_class):
        """Test checking for model that exists."""
        # Setup mock
        mock_client = Mock()
        mock_model1 = MagicMock()
        mock_model1.model = "llama3.1:latest"
        mock_model2 = MagicMock()
        mock_model2.model = "codellama:latest"
        mock_response = MagicMock()
        mock_response.models = [mock_model1, mock_model2]
        mock_client.list.return_value = mock_response
        mock_client_class.return_value = mock_client

        service = OllamaService()
        service.client = mock_client
        service._connected = True

        # Test
        result = service.check_model("llama3.1")

        assert result is True
        assert service._model_available is True

    @patch("souleyez.ai.ollama_service.Client")
    def test_check_model_not_exists(self, mock_client_class):
        """Test checking for model that doesn't exist."""
        # Setup mock
        mock_client = Mock()
        mock_model = MagicMock()
        mock_model.model = "codellama:latest"
        mock_response = MagicMock()
        mock_response.models = [mock_model]
        mock_client.list.return_value = mock_response
        mock_client_class.return_value = mock_client

        service = OllamaService()
        service.client = mock_client
        service._connected = True

        # Test
        result = service.check_model("llama3.1")

        assert result is False
        assert service._model_available is False

    @patch("souleyez.ai.ollama_service.Client")
    def test_check_model_connection_failed(self, mock_client_class):
        """Test checking model when not connected."""
        # Setup mock
        mock_client = Mock()
        mock_client.list.side_effect = Exception("Not connected")
        mock_client_class.return_value = mock_client

        service = OllamaService()
        service.client = mock_client
        service._connected = False

        # Test
        result = service.check_model("llama3.1")

        assert result is False

    @patch("souleyez.config.get")
    @patch("souleyez.ai.ollama_service.Client")
    def test_check_model_default_model(self, mock_client_class, mock_config_get):
        """Test checking default model when no model specified."""

        # Mock config to return appropriate values for each key
        def config_side_effect(key, default=None):
            if key == "ai.ollama_url":
                return OllamaService.DEFAULT_ENDPOINT
            elif key == "ai.ollama_model":
                return OllamaService.DEFAULT_MODEL
            return default

        mock_config_get.side_effect = config_side_effect

        # Setup mock
        mock_client = Mock()
        mock_model = MagicMock()
        mock_model.model = OllamaService.DEFAULT_MODEL
        mock_response = MagicMock()
        mock_response.models = [mock_model]
        mock_client.list.return_value = mock_response
        mock_client_class.return_value = mock_client

        service = OllamaService()
        service.client = mock_client
        service._connected = True

        # Test (no model specified, should use default)
        result = service.check_model()

        assert result is True


class TestOllamaServiceModelPulling:
    """Test model downloading functionality."""

    @patch("souleyez.ai.ollama_service.Client")
    def test_pull_model_success(self, mock_client_class):
        """Test successful model pull."""
        # Setup mock
        mock_client = Mock()
        mock_client.pull.return_value = None
        mock_client_class.return_value = mock_client

        service = OllamaService()
        service.client = mock_client
        service._connected = True

        # Test
        result = service.pull_model("llama3.1")

        assert result is True
        assert service._model_available is True
        mock_client.pull.assert_called_once_with("llama3.1")

    @patch("souleyez.ai.ollama_service.Client")
    def test_pull_model_failure(self, mock_client_class):
        """Test failed model pull (network error)."""
        # Setup mock
        mock_client = Mock()
        mock_client.pull.side_effect = Exception("Network error")
        mock_client_class.return_value = mock_client

        service = OllamaService()
        service.client = mock_client
        service._connected = True

        # Test
        result = service.pull_model("llama3.1")

        assert result is False

    @patch("souleyez.ai.ollama_service.Client")
    def test_pull_model_not_connected(self, mock_client_class):
        """Test pulling model when not connected."""
        # Setup mock
        mock_client = Mock()
        mock_client.list.side_effect = Exception("Not connected")
        mock_client_class.return_value = mock_client

        service = OllamaService()
        service.client = mock_client
        service._connected = False

        # Test
        result = service.pull_model("llama3.1")

        assert result is False
        mock_client.pull.assert_not_called()

    @patch("souleyez.config.get")
    @patch("souleyez.ai.ollama_service.Client")
    def test_pull_model_default(self, mock_client_class, mock_config_get):
        """Test pulling default model when no model specified."""

        # Mock config to return appropriate values for each key
        def config_side_effect(key, default=None):
            if key == "ai.ollama_url":
                return OllamaService.DEFAULT_ENDPOINT
            elif key == "ai.ollama_model":
                return OllamaService.DEFAULT_MODEL
            return default

        mock_config_get.side_effect = config_side_effect

        # Setup mock
        mock_client = Mock()
        mock_client.pull.return_value = None
        mock_client_class.return_value = mock_client

        service = OllamaService()
        service.client = mock_client
        service._connected = True

        # Test (no model specified)
        result = service.pull_model()

        assert result is True
        mock_client.pull.assert_called_once_with(OllamaService.DEFAULT_MODEL)


class TestOllamaServiceGeneration:
    """Test LLM inference functionality."""

    @patch("souleyez.ai.ollama_service.Client")
    def test_generate_success(self, mock_client_class):
        """Test successful LLM generation."""
        # Setup mock
        mock_client = Mock()
        mock_client.generate.return_value = {
            "response": "This is a test response from the LLM"
        }
        mock_client_class.return_value = mock_client

        service = OllamaService()
        service.client = mock_client
        service._connected = True
        service._model_available = True

        # Test
        result = service.generate("Test prompt", "llama3.1")

        assert result == "This is a test response from the LLM"
        mock_client.generate.assert_called_once_with(
            model="llama3.1", prompt="Test prompt"
        )

    @patch("souleyez.ai.ollama_service.Client")
    def test_generate_not_connected(self, mock_client_class):
        """Test generation when not connected."""
        # Setup mock
        mock_client = Mock()
        mock_client.list.side_effect = Exception("Not connected")
        mock_client_class.return_value = mock_client

        service = OllamaService()
        service.client = mock_client
        service._connected = False

        # Test
        result = service.generate("Test prompt")

        assert result is None
        mock_client.generate.assert_not_called()

    @patch("souleyez.ai.ollama_service.Client")
    def test_generate_model_not_available(self, mock_client_class):
        """Test generation when model not available."""
        # Setup mock
        mock_client = Mock()
        mock_response = MagicMock()
        mock_response.models = []
        mock_client.list.return_value = mock_response
        mock_client_class.return_value = mock_client

        service = OllamaService()
        service.client = mock_client
        service._connected = True
        service._model_available = False

        # Test
        result = service.generate("Test prompt", "llama3.1")

        assert result is None
        mock_client.generate.assert_not_called()

    @patch("souleyez.ai.ollama_service.Client")
    def test_generate_inference_failure(self, mock_client_class):
        """Test generation when inference fails."""
        # Setup mock
        mock_client = Mock()
        mock_client.generate.side_effect = Exception("Inference timeout")
        mock_client_class.return_value = mock_client

        service = OllamaService()
        service.client = mock_client
        service._connected = True
        service._model_available = True

        # Test
        result = service.generate("Test prompt")

        assert result is None

    @patch("souleyez.ai.ollama_service.Client")
    def test_generate_empty_response(self, mock_client_class):
        """Test generation with empty response."""
        # Setup mock
        mock_client = Mock()
        mock_client.generate.return_value = {"response": ""}
        mock_client_class.return_value = mock_client

        service = OllamaService()
        service.client = mock_client
        service._connected = True
        service._model_available = True

        # Test
        result = service.generate("Test prompt")

        assert result == ""

    @patch("souleyez.config.get")
    @patch("souleyez.ai.ollama_service.Client")
    def test_generate_default_model(self, mock_client_class, mock_config_get):
        """Test generation with default model."""

        # Mock config to return appropriate values for each key
        def config_side_effect(key, default=None):
            if key == "ai.ollama_url":
                return OllamaService.DEFAULT_ENDPOINT
            elif key == "ai.ollama_model":
                return OllamaService.DEFAULT_MODEL
            return default

        mock_config_get.side_effect = config_side_effect

        # Setup mock
        mock_client = Mock()
        mock_client.generate.return_value = {"response": "Test"}
        mock_client_class.return_value = mock_client

        service = OllamaService()
        service.client = mock_client
        service._connected = True
        service._model_available = True

        # Test (no model specified)
        result = service.generate("Test prompt")

        assert result == "Test"
        mock_client.generate.assert_called_once_with(
            model=OllamaService.DEFAULT_MODEL, prompt="Test prompt"
        )


class TestOllamaServiceStatus:
    """Test status reporting functionality."""

    @patch("souleyez.config.get")
    @patch("souleyez.ai.ollama_service.Client")
    def test_get_status_connected_with_models(self, mock_client_class, mock_config_get):
        """Test status when connected with models available."""

        # Mock config to return appropriate values for each key
        def config_side_effect(key, default=None):
            if key == "ai.ollama_url":
                return OllamaService.DEFAULT_ENDPOINT
            elif key == "ai.ollama_model":
                return OllamaService.DEFAULT_MODEL
            return default

        mock_config_get.side_effect = config_side_effect

        # Setup mock
        mock_client = Mock()
        mock_model1 = MagicMock()
        mock_model1.model = (
            OllamaService.DEFAULT_MODEL
        )  # Must include DEFAULT_MODEL for model_available=True
        mock_model2 = MagicMock()
        mock_model2.model = "codellama:latest"
        mock_response = MagicMock()
        mock_response.models = [mock_model1, mock_model2]
        mock_client.list.return_value = mock_response
        mock_client_class.return_value = mock_client

        service = OllamaService()
        service.client = mock_client

        # Test
        status = service.get_status()

        assert status["connected"] is True
        assert status["endpoint"] == OllamaService.DEFAULT_ENDPOINT
        assert len(status["models"]) == 2
        assert OllamaService.DEFAULT_MODEL in status["models"]
        assert status["default_model"] == OllamaService.DEFAULT_MODEL
        assert status["model_available"] is True
        assert status["error"] is None

    @patch("souleyez.ai.ollama_service.Client")
    def test_get_status_not_connected(self, mock_client_class):
        """Test status when not connected."""
        # Setup mock
        mock_client = Mock()
        mock_client.list.side_effect = Exception("Connection refused")
        mock_client_class.return_value = mock_client

        service = OllamaService()
        service.client = mock_client

        # Test
        status = service.get_status()

        assert status["connected"] is False
        assert status["models"] == []
        assert status["model_available"] is False
        assert "Cannot connect" in status["error"]

    @patch("souleyez.ai.ollama_service.Client")
    def test_get_status_connected_no_models(self, mock_client_class):
        """Test status when connected but no models available."""
        # Setup mock
        mock_client = Mock()
        mock_response = MagicMock()
        mock_response.models = []
        mock_client.list.return_value = mock_response
        mock_client_class.return_value = mock_client

        service = OllamaService()
        service.client = mock_client

        # Test
        status = service.get_status()

        assert status["connected"] is True
        assert status["models"] == []
        assert status["model_available"] is False
        assert status["error"] is None

    @patch("souleyez.ai.ollama_service.Client")
    def test_get_status_list_models_error(self, mock_client_class):
        """Test status when listing models fails."""
        # Setup mock - connection succeeds but list fails
        mock_client = Mock()
        call_count = [0]

        def list_side_effect():
            call_count[0] += 1
            if call_count[0] == 1:
                # First call (check_connection) succeeds
                mock_response = MagicMock()
                mock_response.models = []
                return mock_response
            else:
                # Second call (get models in get_status) fails
                raise Exception("Permission denied")

        mock_client.list.side_effect = list_side_effect
        mock_client_class.return_value = mock_client

        service = OllamaService()
        service.client = mock_client

        # Test
        status = service.get_status()

        assert status["connected"] is True
        assert "Error listing models" in status["error"]


class TestOllamaServiceEdgeCases:
    """Test edge cases and error conditions."""

    @patch("souleyez.ai.ollama_service.Client")
    def test_multiple_connection_checks(self, mock_client_class):
        """Test that connection state is cached properly."""
        # Setup mock
        mock_client = Mock()
        mock_response = MagicMock()
        mock_response.models = []
        mock_client.list.return_value = mock_response
        mock_client_class.return_value = mock_client

        service = OllamaService()
        service.client = mock_client

        # Test multiple checks
        result1 = service.check_connection()
        result2 = service.check_connection()

        assert result1 is True
        assert result2 is True
        # Should be called twice (no caching)
        assert mock_client.list.call_count == 2

    @patch("souleyez.ai.ollama_service.Client")
    def test_check_model_auto_connects(self, mock_client_class):
        """Test that check_model auto-connects if not connected."""
        # Setup mock
        mock_client = Mock()
        mock_model = MagicMock()
        mock_model.model = "llama3.1:latest"
        mock_response = MagicMock()
        mock_response.models = [mock_model]
        mock_client.list.return_value = mock_response
        mock_client_class.return_value = mock_client

        service = OllamaService()
        service.client = mock_client
        service._connected = False

        # Test - should auto-connect
        result = service.check_model("llama3.1")

        assert result is True
        assert service._connected is True

    @patch("souleyez.ai.ollama_service.Client")
    def test_generate_auto_checks_model(self, mock_client_class):
        """Test that generate auto-checks model availability."""
        # Setup mock
        mock_client = Mock()
        mock_model = MagicMock()
        mock_model.model = "llama3.1:latest"
        mock_response = MagicMock()
        mock_response.models = [mock_model]
        mock_client.list.return_value = mock_response
        mock_client.generate.return_value = {"response": "Test"}
        mock_client_class.return_value = mock_client

        service = OllamaService()
        service.client = mock_client
        service._connected = True
        service._model_available = False

        # Test - should auto-check model
        result = service.generate("Test prompt", "llama3.1")

        assert result == "Test"
        assert service._model_available is True

    @patch("souleyez.ai.ollama_service.Client")
    def test_check_model_exception_handling(self, mock_client_class):
        """Test exception handling in check_model."""
        # Setup mock - connection works but list raises exception
        mock_client = Mock()
        call_count = [0]

        def list_side_effect():
            call_count[0] += 1
            if call_count[0] == 1:
                # First call (check_connection) succeeds
                mock_response = MagicMock()
                mock_response.models = []
                return mock_response
            else:
                # Second call raises exception
                raise Exception("Unexpected error")

        mock_client.list.side_effect = list_side_effect
        mock_client_class.return_value = mock_client

        service = OllamaService()
        service.client = mock_client

        # Test - should handle exception gracefully
        result = service.check_model("llama3.1")

        assert result is False


class TestOllamaHostValidation:
    """Test host validation security feature."""

    def test_init_rejects_invalid_host(self, mock_host_validation):
        """Test that initialization rejects non-localhost/gateway hosts."""
        # Override the autouse fixture to reject
        mock_host_validation.return_value = (False, "Only localhost allowed")

        with pytest.raises(ValueError) as exc_info:
            OllamaService(endpoint="http://evil-server:11434")

        assert "Ollama endpoint not allowed" in str(exc_info.value)

    def test_init_accepts_localhost(self, mock_host_validation):
        """Test that localhost is always accepted."""
        mock_host_validation.return_value = (True, "localhost")

        service = OllamaService(endpoint="http://localhost:11434")

        assert service.endpoint == "http://localhost:11434"
        assert service._host_type == "localhost"

    def test_init_accepts_local_network(self, mock_host_validation):
        """Test that local network IPs are accepted."""
        mock_host_validation.return_value = (True, "local network")

        service = OllamaService(endpoint="http://10.0.0.28:11434")

        assert service.endpoint == "http://10.0.0.28:11434"
        assert service._host_type == "local network"

    def test_host_type_stored(self, mock_host_validation):
        """Test that host type is stored for display purposes."""
        mock_host_validation.return_value = (True, "local network")

        service = OllamaService(endpoint="http://192.168.1.1:11434")

        assert hasattr(service, "_host_type")
        assert service._host_type == "local network"
