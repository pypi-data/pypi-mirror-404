"""Unit tests for model API integrations."""

import pytest
from unittest.mock import MagicMock, patch

from rotalabs_probe.integrations.base import ModelAPI, ModelResponse
from rotalabs_probe.integrations.anthropic_api import AnthropicModelAPI
from rotalabs_probe.integrations.openai_api import OpenAIModelAPI


class TestModelResponse:
    """Test ModelResponse dataclass."""

    def test_response_creation_minimal(self) -> None:
        """Test creating a response with minimal parameters."""
        response = ModelResponse(text="Hello", model="test-model")
        assert response.text == "Hello"
        assert response.model == "test-model"
        assert response.usage == {}
        assert response.latency_ms == 0.0

    def test_response_creation_full(self) -> None:
        """Test creating a response with all parameters."""
        response = ModelResponse(
            text="Hello world",
            model="gpt-4",
            usage={"prompt_tokens": 10, "completion_tokens": 5},
            latency_ms=150.5,
            metadata={"finish_reason": "stop"},
        )
        assert response.text == "Hello world"
        assert response.usage["prompt_tokens"] == 10
        assert response.latency_ms == 150.5
        assert response.metadata["finish_reason"] == "stop"


class TestModelAPIProtocol:
    """Test ModelAPI protocol compliance."""

    def test_protocol_check(self) -> None:
        """Test that protocol checking works."""
        # Create a mock that implements the protocol
        mock_api = MagicMock()
        mock_api.generate.return_value = "response"
        mock_api.generate_with_perturbation.return_value = "perturbed"

        # Should be able to call methods
        assert mock_api.generate("test") == "response"
        assert mock_api.generate_with_perturbation("test", 0.1) == "perturbed"


class TestAnthropicModelAPI:
    """Test AnthropicModelAPI implementation."""

    def test_init_without_key_raises(self) -> None:
        """Test that initialization without API key raises."""
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValueError, match="API key required"):
                AnthropicModelAPI()

    def test_init_with_key(self) -> None:
        """Test initialization with API key."""
        api = AnthropicModelAPI(api_key="test-key")
        assert api.model == "claude-sonnet-4-20250514"
        assert api.max_tokens == 1024
        assert api.temperature == 0.7

    def test_init_custom_params(self) -> None:
        """Test initialization with custom parameters."""
        api = AnthropicModelAPI(
            model="claude-3-opus-20240229",
            max_tokens=2048,
            temperature=0.5,
            api_key="test-key",
        )
        assert api.model == "claude-3-opus-20240229"
        assert api.max_tokens == 2048
        assert api.temperature == 0.5

    def test_get_model_info(self) -> None:
        """Test get_model_info returns expected data."""
        api = AnthropicModelAPI(api_key="test-key")
        info = api.get_model_info()

        assert info["provider"] == "anthropic"
        assert info["model"] == "claude-sonnet-4-20250514"
        assert "capabilities" in info

    def test_perturb_prompt(self) -> None:
        """Test prompt perturbation."""
        api = AnthropicModelAPI(api_key="test-key")

        # At high noise level, prompt should be modified
        original = "What is 2+2?"
        perturbed = api._perturb_prompt(original, noise_level=1.0)

        # Due to randomness, we can't check exact output
        # but we can verify it returns a string
        assert isinstance(perturbed, str)

    @patch("rotalabs_probe.integrations.anthropic_api.AnthropicModelAPI._get_client")
    def test_generate_calls_api(self, mock_get_client: MagicMock) -> None:
        """Test that generate calls the API correctly."""
        # Setup mock
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Test response")]
        mock_client.messages.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        api = AnthropicModelAPI(api_key="test-key")
        result = api.generate("Hello")

        assert result == "Test response"
        mock_client.messages.create.assert_called_once()


class TestOpenAIModelAPI:
    """Test OpenAIModelAPI implementation."""

    def test_init_without_key_raises(self) -> None:
        """Test that initialization without API key raises."""
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValueError, match="API key required"):
                OpenAIModelAPI()

    def test_init_with_key(self) -> None:
        """Test initialization with API key."""
        api = OpenAIModelAPI(api_key="test-key")
        assert api.model == "gpt-4"
        assert api.max_tokens == 1024
        assert api.temperature == 0.7

    def test_init_custom_params(self) -> None:
        """Test initialization with custom parameters."""
        api = OpenAIModelAPI(
            model="gpt-4-turbo",
            max_tokens=4096,
            temperature=0.3,
            api_key="test-key",
        )
        assert api.model == "gpt-4-turbo"
        assert api.max_tokens == 4096
        assert api.temperature == 0.3

    def test_get_model_info(self) -> None:
        """Test get_model_info returns expected data."""
        api = OpenAIModelAPI(api_key="test-key")
        info = api.get_model_info()

        assert info["provider"] == "openai"
        assert info["model"] == "gpt-4"
        assert "capabilities" in info

    def test_perturb_prompt(self) -> None:
        """Test prompt perturbation."""
        api = OpenAIModelAPI(api_key="test-key")

        original = "What is 2+2?"
        perturbed = api._perturb_prompt(original, noise_level=1.0)

        assert isinstance(perturbed, str)

    @patch("rotalabs_probe.integrations.openai_api.OpenAIModelAPI._get_client")
    def test_generate_calls_api(self, mock_get_client: MagicMock) -> None:
        """Test that generate calls the API correctly."""
        # Setup mock
        mock_client = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.content = "Test response"
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        api = OpenAIModelAPI(api_key="test-key")
        result = api.generate("Hello")

        assert result == "Test response"
        mock_client.chat.completions.create.assert_called_once()

    @patch("rotalabs_probe.integrations.openai_api.OpenAIModelAPI._get_client")
    def test_generate_batch(self, mock_get_client: MagicMock) -> None:
        """Test batch generation."""
        mock_client = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.content = "Response"
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        api = OpenAIModelAPI(api_key="test-key")
        results = api.generate_batch(["Q1", "Q2", "Q3"])

        assert len(results) == 3
        assert all(r == "Response" for r in results)
