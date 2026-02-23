"""Tests for iFlow provider."""

import pytest
from unittest.mock import MagicMock, patch

from llm_mindmap.llm.iflow import IFlowProvider


class TestIFlowProvider:
    """Test iFlow provider implementation."""

    @pytest.fixture
    def provider(self):
        """Create an iFlow provider for testing."""
        return IFlowProvider(
            model="claude-3.5-sonnet",
            api_key="test-key",
            base_url="https://iflow.example.com/api/v1",
        )

    def test_initialization(self, provider):
        """Test provider initialization."""
        assert provider.model == "claude-3.5-sonnet"
        assert provider.connection_config == {
            "api_key": "test-key",
            "base_url": "https://iflow.example.com/api/v1",
        }

    def test_initialization_without_client(self, provider):
        """Test client is configured during initialization."""
        assert provider._client is not None

    def test_missing_llm_clients_python_raises_error(self):
        """Test missing llm-clients-python raises ImportError."""
        with patch("llm_mindmap.llm.iflow.IFlowClient", side_effect=ImportError):
            with pytest.raises(ImportError) as exc_info:
                IFlowProvider(
                    model="test-model",
                    api_key="test-key",
                )

            assert "llm-clients-python" in str(exc_info.value)

    def test_get_response(self, provider):
        """Test get_response method."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Test response"

        with patch.object(provider._client, "chat") as mock_chat:
            mock_chat.completions.create.return_value = mock_response

            result = provider.get_response(
                chat_history=[{"role": "user", "content": "Hello"}],
                temperature=0.5,
            )

            assert result == "Test response"
            mock_chat.completions.create.assert_called_once()

    def test_get_response_empty_content(self, provider):
        """Test get_response with empty content."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = None

        with patch.object(provider._client, "chat") as mock_chat:
            mock_chat.completions.create.return_value = mock_response

            result = provider.get_response(
                chat_history=[{"role": "user", "content": "Hello"}],
            )

            assert result == ""

    def test_get_response_invalid_response(self, provider):
        """Test get_response with invalid response."""
        mock_response = MagicMock()
        mock_response.choices = []

        with patch.object(provider._client, "chat") as mock_chat:
            mock_chat.completions.create.return_value = mock_response

            with pytest.raises(ValueError) as exc_info:
                provider.get_response(
                    chat_history=[{"role": "user", "content": "Hello"}],
                )

            assert "Invalid response" in str(exc_info.value)

    def test_get_response_without_client(self):
        """Test get_response without initialized client."""
        provider = IFlowProvider.__new__(IFlowProvider)
        provider.model = "test-model"
        provider.connection_config = {}
        provider._client = None

        with pytest.raises(RuntimeError) as exc_info:
            provider.get_response(
                chat_history=[{"role": "user", "content": "Hello"}],
            )

        assert "not initialized" in str(exc_info.value)

    def test_get_tools_response_with_tool_calls(self, provider):
        """Test get_tools_response with tool calls."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]

        mock_tool_call = MagicMock()
        mock_tool_call.function.name = "test_function"
        mock_tool_call.function.arguments = '{"arg1": "value1"}'

        mock_response.choices[0].message.tool_calls = [mock_tool_call]
        mock_response.choices[0].message.content = None

        with patch.object(provider._client, "chat") as mock_chat:
            mock_chat.completions.create.return_value = mock_response

            result = provider.get_tools_response(
                chat_history=[{"role": "user", "content": "Hello"}],
                tools=[{"name": "test_function", "description": "Test"}],
            )

            assert result["tool_calls"] is not None
            assert len(result["func_names"]) == 1
            assert result["func_names"][0] == "test_function"
            assert len(result["arguments"]) == 1
            assert result["arguments"][0] == {"arg1": "value1"}
            assert result["text"] is None

    def test_get_tools_response_without_tool_calls(self, provider):
        """Test get_tools_response without tool calls."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.tool_calls = None
        mock_response.choices[0].message.content = "Text response"

        with patch.object(provider._client, "chat") as mock_chat:
            mock_chat.completions.create.return_value = mock_response

            result = provider.get_tools_response(
                chat_history=[{"role": "user", "content": "Hello"}],
                tools=[{"name": "test_function", "description": "Test"}],
            )

            assert result["tool_calls"] is None
            assert result["func_names"] == []
            assert result["arguments"] == []
            assert result["text"] == "Text response"

    def test_get_stream_response(self, provider):
        """Test get_stream_response method."""
        chunks = ["Hello", " ", "world", "!"]

        mock_stream = MagicMock()
        for i, chunk_text in enumerate(chunks):
            mock_chunk = MagicMock()
            mock_chunk.choices = [MagicMock()]
            mock_chunk.choices[0].delta.content = chunk_text
            mock_stream.__iter__.return_value = [mock_chunk]

        with patch.object(provider._client, "chat") as mock_chat:
            mock_chat.completions.create.return_value = mock_stream

            result = list(provider.get_stream_response(
                chat_history=[{"role": "user", "content": "Hello"}],
            ))

            assert result == chunks