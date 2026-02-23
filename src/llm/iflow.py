"""iFlow LLM provider implementation."""

from __future__ import annotations

from json import loads
from logging import Logger, getLogger
from typing import Any, Generator

from llm_mindmap.llm.base import LLMProvider

logger: Logger = getLogger(__name__)


class IFlowProvider(LLMProvider):
    """iFlow provider implementation using llm-clients-python."""

    def __init__(self, model: str, **connection_config):
        """Initialize the iFlow provider.

        Args:
            model: The model identifier (e.g., 'claude-3.5-sonnet')
            **connection_config: Connection configuration (api_key, base_url, etc.)
        """
        super().__init__(model, **connection_config)
        self._client = None
        self._configure_client()

    def _configure_client(self) -> None:
        """Configure the iFlow client.

        Uses llm-clients-python iFlow client.
        """
        try:
            from llm_clients_python.iflow import IFlowClient

            self._client = IFlowClient(**self.connection_config)
        except ImportError as e:
            raise ImportError(
                "llm-clients-python package is required for iFlow provider. "
                "Install it with: pip install llm-clients-python"
            ) from e

    def get_response(self, chat_history: list[dict[str, str]], **kwargs) -> str:
        """Get a response from iFlow.

        Args:
            chat_history: List of messages with 'role' and 'content' keys
            **kwargs: Additional arguments (temperature, max_tokens, etc.)

        Returns:
            The LLM response as a string

        Raises:
            RuntimeError: If client is not initialized
            ValueError: If response is invalid
        """
        if self._client is None:
            raise RuntimeError("iFlow client is not initialized")

        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=chat_history,
                **kwargs,
            )

            if not response or not response.choices:
                raise ValueError("Invalid response from iFlow")

            return response.choices[0].message.content or ""

        except Exception as e:
            logger.error(f"iFlow API error: {e}")
            raise

    def get_tools_response(
        self,
        chat_history: list[dict[str, str]],
        tools: list[dict],
        **kwargs,
    ) -> dict[str, Any]:
        """Get a response from iFlow with tool calling.

        Args:
            chat_history: List of messages with 'role' and 'content' keys
            tools: List of tool definitions
            **kwargs: Additional arguments

        Returns:
            Dictionary with:
                - tool_calls: List of tool calls (if any)
                - text: Text response (if no tool calls)
                - func_names: List of function names (if tool calls)
                - arguments: List of function arguments (if tool calls)

        Raises:
            RuntimeError: If client is not initialized
            ValueError: If response is invalid
        """
        if self._client is None:
            raise RuntimeError("iFlow client is not initialized")

        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=chat_history,
                tools=tools,
                tool_choice="auto",
                **kwargs,
            )

            if not response or not response.choices:
                raise ValueError("Invalid response from iFlow")

            message = response.choices[0].message

            if message.tool_calls:
                tool_calls_data = []
                func_names = []
                arguments_list = []

                for tool_call in message.tool_calls:
                    tool_calls_data.append(tool_call)
                    func_names.append(tool_call.function.name)
                    arguments_list.append(loads(tool_call.function.arguments))

                return {
                    "tool_calls": tool_calls_data,
                    "func_names": func_names,
                    "arguments": arguments_list,
                    "text": None,
                }
            else:
                return {
                    "tool_calls": None,
                    "func_names": [],
                    "arguments": [],
                    "text": message.content or "",
                }

        except Exception as e:
            logger.error(f"iFlow tool calling error: {e}")
            raise

    def get_stream_response(
        self, chat_history: list[dict[str, str]], **kwargs
    ) -> Generator[str, None, None]:
        """Get a streaming response from iFlow.

        Args:
            chat_history: List of messages with 'role' and 'content' keys
            **kwargs: Additional arguments

        Yields:
            Streaming response chunks

        Raises:
            RuntimeError: If client is not initialized
        """
        if self._client is None:
            raise RuntimeError("iFlow client is not initialized")

        try:
            stream = self._client.chat.completions.create(
                model=self.model,
                messages=chat_history,
                stream=True,
                **kwargs,
            )

            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            logger.error(f"iFlow streaming error: {e}")
            raise