"""OpenRouter LLM provider implementation."""

import json
from logging import Logger, getLogger
from typing import Any

import httpx

from llm_mindmap.llm.base import LLMProvider

logger: Logger = getLogger(__name__)


class OpenRouterProvider(LLMProvider):
    """OpenRouter LLM provider using httpx for HTTP requests."""

    def __init__(self, model: str, api_key: str | None = None, base_url: str | None = None, **connection_config):
        """Initialize OpenRouter provider.

        Args:
            model: Model name (e.g., "anthropic/claude-3.5-sonnet")
            api_key: OpenRouter API key (defaults to OPENROUTER_API_KEY env var)
            base_url: Base URL for OpenRouter API (defaults to https://openrouter.ai/api/v1)
            **connection_config: Additional connection parameters
        """
        super().__init__(model, **connection_config)
        
        self.api_key = api_key or connection_config.get("api_key")
        self.base_url = base_url or connection_config.get("base_url", "https://openrouter.ai/api/v1")
        self.timeout = connection_config.get("timeout", 60)
        
        self._client = httpx.Client(
            timeout=self.timeout,
            headers={"Authorization": f"Bearer {self.api_key}"} if self.api_key else {},
        )

    def get_response(self, chat_history: list[dict[str, str]], **kwargs) -> str:
        """Get response from OpenRouter LLM.

        Args:
            chat_history: List of chat messages
            **kwargs: Additional parameters (temperature, max_tokens, etc.)

        Returns:
            LLM response text

        Raises:
            ValueError: If API response is invalid
        """
        url = f"{self.base_url}/chat/completions"
        
        payload = {
            "model": self.model,
            "messages": chat_history,
            **kwargs
        }
        
        response = self._client.post(url, json=payload)
        response.raise_for_status()
        
        data = response.json()
        
        if "choices" not in data or not data["choices"]:
            raise ValueError(f"Invalid API response: {data}")
        
        return data["choices"][0]["message"]["content"]

    def get_tools_response(
        self,
        chat_history: list[dict[str, str]],
        tools: list[dict],
        **kwargs,
    ) -> dict[str, list[dict] | str]:
        """Get response with tool calling from OpenRouter.

        Args:
            chat_history: List of chat messages
            tools: List of tool definitions
            **kwargs: Additional parameters

        Returns:
            Dictionary with func_names, arguments, text, and tool_calls
        """
        url = f"{self.base_url}/chat/completions"
        
        payload = {
            "model": self.model,
            "messages": chat_history,
            "tools": tools,
            **kwargs
        }
        
        response = self._client.post(url, json=payload)
        response.raise_for_status()
        
        data = response.json()
        
        if "choices" not in data or not data["choices"]:
            raise ValueError(f"Invalid API response: {data}")
        
        message = data["choices"][0]["message"]
        
        output = {
            "func_names": [],
            "arguments": [],
            "text": message.get("content", ""),
            "tool_calls": [],
        }
        
        if message.get("tool_calls"):
            output["tool_calls"] = message["tool_calls"]
            output["func_names"] = [tool["function"]["name"] for tool in message["tool_calls"]]
            output["arguments"] = [
                json.loads(tool["function"]["arguments"])
                for tool in message["tool_calls"]
            ]
        
        return output

    def get_stream_response(self, chat_history: list[dict[str, str]], **kwargs):
        """Get streaming response from OpenRouter.

        Args:
            chat_history: List of chat messages
            **kwargs: Additional parameters

        Yields:
            Response chunks as they arrive
        """
        url = f"{self.base_url}/chat/completions"
        
        payload = {
            "model": self.model,
            "messages": chat_history,
            "stream": True,
            **kwargs
        }
        
        with self._client.stream("POST", url, json=payload) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if line.strip():
                    data = json.loads(line)
                    if "choices" in data and data["choices"]:
                        delta = data["choices"][0].get("delta", {})
                        if "content" in delta:
                            yield delta["content"]