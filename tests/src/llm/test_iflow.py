"""Tests for iFlow provider."""

import pytest
from unittest.mock import MagicMock, patch
from llm_mindmap.llm.iflow import IFlowProvider


class TestIFlowProvider:
    """Test IFlowProvider class."""

    @pytest.fixture
    def provider(self):
        """Create iFlow provider with test config."""
        return IFlowProvider(
            model="gpt-4o-mini",
            api_key="test-key",
            base_url="https://test.api",
        )

    def test_initialization(self, provider):
        """Test provider initialization."""
        assert provider.model == "gpt-4o-mini"
        assert provider.api_key == "test-key"
        assert provider.base_url == "https://test.api"

    def test_initialization_with_connection_config(self):
        """Test initialization with connection config dict."""
        provider = IFlowProvider(
            model="gpt-4o",
            **{
                "api_key": "test-key",
                "base_url": "https://custom.api",
                "timeout": 30,
            }
        )

        assert provider.model == "gpt-4o"
        assert provider.api_key == "test-key"
        assert provider.base_url == "https://custom.api"
        assert provider.timeout == 30

    @patch("llm_mindmap.llm.iflow.httpx.Client")
    def test_get_response(self, mock_client_class, provider):
        """Test get_response method."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Test response"}}]
        }
        mock_response.raise_for_status = MagicMock()
        
        mock_client = MagicMock()
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client

        result = provider.get_response(
            [{"role": "user", "content": "Hello"}],
            temperature=0.5,
        )

        assert result == "Test response"
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert "messages" in call_args[1]["json"]
        assert call_args[1]["json"]["temperature"] == 0.5

    @patch("llm_mindmap.llm.iflow.httpx.Client")
    def test_get_response_invalid_api_response(self, mock_client_class, provider):
        """Test get_response with invalid API response."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"invalid": "response"}
        mock_response.raise_for_status = MagicMock()
        
        mock_client = MagicMock()
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client

        with pytest.raises(ValueError) as exc_info:
            provider.get_response([{"role": "user", "content": "Hello"}])

        assert "Invalid API response" in str(exc_info.value)

    @patch("llm_mindmap.llm.iflow.httpx.Client")
    def test_get_tools_response_without_tools(self, mock_client_class, provider):
        """Test get_tools_response without tool calls."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Response text"}}]
        }
        mock_response.raise_for_status = MagicMock()
        
        mock_client = MagicMock()
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client

        result = provider.get_tools_response(
            [{"role": "user", "content": "Hello"}],
            tools=[{"type": "function", "function": {"name": "test"}}],
        )

        assert result["text"] == "Response text"
        assert result["func_names"] == []
        assert result["arguments"] == []

    @patch("llm_mindmap.llm.iflow.httpx.Client")
    def test_get_tools_response_with_tools(self, mock_client_class, provider):
        """Test get_tools_response with tool calls."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": "Response text",
                    "tool_calls": [{
                        "id": "call_123",
                        "type": "function",
                        "function": {
                            "name": "test_function",
                            "arguments": '{"param": "value"}'
                        }
                    }]
                }
            }]
        }
        mock_response.raise_for_status = MagicMock()
        
        mock_client = MagicMock()
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client

        result = provider.get_tools_response(
            [{"role": "user", "content": "Hello"}],
            tools=[{"type": "function", "function": {"name": "test"}}],
        )

        assert result["text"] == "Response text"
        assert result["func_names"] == ["test_function"]
        assert result["arguments"] == [{"param": "value"}]
        assert len(result["tool_calls"]) == 1

    @patch("llm_mindmap.llm.iflow.httpx.Client")
    def test_get_stream_response(self, mock_client_class, provider):
        """Test get_stream_response method."""
        mock_stream_response = MagicMock()
        mock_stream_response.iter_lines.return_value = [
            b'{"choices":[{"delta":{"content":"Hello"}}]}',
            b'{"choices":[{"delta":{"content":" world"}}]}',
        ]
        mock_stream_response.raise_for_status = MagicMock()
        
        mock_response = MagicMock()
        mock_response.__enter__ = MagicMock(return_value=mock_stream_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        
        mock_client = MagicMock()
        mock_client.stream.return_value = mock_response
        mock_client_class.return_value = mock_client

        chunks = list(provider.get_stream_response([{"role": "user", "content": "Hello"}]))

        assert chunks == ["Hello", " world"]

    @patch("llm_mindmap.llm.iflow.httpx.Client")
    def test_http_error_handling(self, mock_client_class, provider):
        """Test HTTP error handling."""
        import httpx
        
        mock_client = MagicMock()
        mock_client.post.side_effect = httpx.HTTPStatusError(
            "Error",
            request=MagicMock(),
            response=MagicMock(status_code=500)
        )
        mock_client_class.return_value = mock_client

        with pytest.raises(httpx.HTTPStatusError):
            provider.get_response([{"role": "user", "content": "Hello"}])