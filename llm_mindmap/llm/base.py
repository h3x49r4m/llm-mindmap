"""Base LLM configuration and provider abstraction."""

from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from logging import Logger, getLogger
from pathlib import Path
from typing import Any, Generator

from pydantic import BaseModel, Field, field_validator

logger: Logger = getLogger(__name__)


def load_llm_config(config_path: str | Path = ".local/llms.json") -> dict[str, Any]:
    """Load LLM configuration from JSON file.

    Args:
        config_path: Path to the configuration file

    Returns:
        Dictionary containing LLM configuration
    """
    path = Path(config_path)
    if path.exists():
        try:
            with open(path) as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to load LLM config from {config_path}: {e}")
    return {}


class LLMConfig(BaseModel):
    """Configuration for LLM models."""

    model: str
    provider: str
    connection_config: dict = Field(
        default_factory=dict,
        description="Connection configuration for the LLM provider (API keys, base URLs, etc.)",
    )
    temperature: float | None = Field(
        default=0.0,
        description="Sampling temperature (0.0 to 2.0). Lower values make output more deterministic.",
        ge=0.0,
        le=2.0,
    )
    response_format: dict = Field(
        default={"type": "text"},
        description="Response format (e.g., {'type': 'json_object'} for JSON mode)",
    )
    timeout: int = Field(
        default=60,
        description="Timeout for LLM requests in seconds",
        ge=1,
    )

    @field_validator("provider")
    @classmethod
    def validate_provider(cls, v: str) -> str:
        """Validate provider is supported."""
        supported_providers = {"openrouter", "iflow"}
        provider = v.lower()
        if provider not in supported_providers:
            raise ValueError(
                f"Unsupported provider '{v}'. Supported providers: {supported_providers}"
            )
        return provider

    def get_llm_kwargs(
        self,
        remove_max_tokens: bool = False,
        remove_timeout: bool = False,
    ) -> dict[str, Any]:
        """Get LLM kwargs excluding model, provider, and connection_config.

        Args:
            remove_max_tokens: If True, exclude max_tokens from the result
            remove_timeout: If True, exclude timeout from the result

        Returns:
            Dictionary of LLM kwargs
        """
        exclude = {"model", "provider", "connection_config"}
        if remove_max_tokens:
            exclude.add("max_tokens")
        if remove_timeout:
            exclude.add("timeout")

        config_dict = self.model_dump(exclude=exclude)
        return {k: v for k, v in config_dict.items() if v is not None}


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    def __init__(self, model: str, **connection_config):
        """Initialize the LLM provider.

        Args:
            model: The model identifier (e.g., 'anthropic/claude-3.5-sonnet')
            **connection_config: Connection configuration (API keys, base URLs, etc.)
        """
        self.model = model
        self.connection_config = connection_config

    @abstractmethod
    def get_response(self, chat_history: list[dict[str, str]], **kwargs) -> str:
        """Get a response from the LLM model.

        Args:
            chat_history: List of messages with 'role' and 'content' keys
            **kwargs: Additional arguments for the LLM call

        Returns:
            The LLM response as a string
        """
        pass

    @abstractmethod
    def get_tools_response(
        self,
        chat_history: list[dict[str, str]],
        tools: list[dict],
        **kwargs,
    ) -> dict[str, Any]:
        """Get a response from the LLM model with tool calling.

        Args:
            chat_history: List of messages with 'role' and 'content' keys
            tools: List of tool definitions
            **kwargs: Additional arguments for the LLM call

        Returns:
            Dictionary with tool call results or text response
        """
        pass

    @abstractmethod
    def get_stream_response(
        self, chat_history: list[dict[str, str]], **kwargs
    ) -> Generator[str, None, None]:
        """Get a streaming response from the LLM model.

        Args:
            chat_history: List of messages with 'role' and 'content' keys
            **kwargs: Additional arguments for the LLM call

        Yields:
            Streaming response chunks
        """
        pass


class LLMEngine:
    """Main engine for LLM interactions.

    Loads and manages LLM providers based on configuration.
    """

    def __init__(self, model: str | None = None, **connection_config):
        """Initialize the LLM engine.

        Args:
            model: Model identifier in format 'provider::model' or just 'model'
            **connection_config: Connection configuration (API keys, base URLs, etc.)
        """
        if model is None:
            llm_config = load_llm_config()
            default_provider = llm_config.get("default_provider", "iflow")
            model = os.getenv("LLM_MINDMAP_DEFAULT_MODEL", f"{default_provider}::gpt-4o-mini")

        self.provider_name, self.model_name = self._parse_model(model)
        self.provider = self._load_provider(**connection_config)

    def _parse_model(self, model: str) -> tuple[str, str]:
        """Parse model string into provider and model name.

        Args:
            model: Model identifier (e.g., 'openrouter::anthropic/claude-3.5-sonnet')

        Returns:
            Tuple of (provider, model_name)

        Raises:
            ValueError: If model format is invalid
        """
        if "::" in model:
            provider, model_name = model.split("::", 1)
        else:
            # Use default provider from config
            llm_config = load_llm_config()
            provider = llm_config.get("default_provider", "iflow")
            model_name = model

        config = LLMConfig(provider=provider, model=model_name)
        return config.provider, model_name

    def _load_provider(self, **connection_config) -> LLMProvider:
        """Load the appropriate provider.

        Args:
            **connection_config: Connection configuration

        Returns:
            Initialized LLMProvider instance

        Raises:
            ValueError: If provider is not supported
        """
        llm_config = load_llm_config()
        provider_config = llm_config.get("providers", {}).get(self.provider_name, {})

        # Merge connection_config with provider config from file
        merged_config = {**provider_config, **connection_config}

        if self.provider_name == "openrouter":
            from llm_mindmap.llm.openrouter import OpenRouterProvider

            return OpenRouterProvider(
                model=self.model_name, **merged_config
            )
        elif self.provider_name == "iflow":
            from llm_mindmap.llm.iflow import IFlowProvider

            return IFlowProvider(model=self.model_name, **merged_config)
        else:
            raise ValueError(f"Unsupported provider: {self.provider_name}")

    def get_response(self, chat_history: list[dict[str, str]], **kwargs) -> str:
        """Get a response from the LLM.

        Args:
            chat_history: List of messages with 'role' and 'content' keys
            **kwargs: Additional arguments for the LLM call

        Returns:
            The LLM response as a string
        """
        return self.provider.get_response(chat_history, **kwargs)

    def get_tools_response(
        self, chat_history: list[dict[str, str]], tools: list[dict], **kwargs
    ) -> dict[str, Any]:
        """Get a response from the LLM with tool calling.

        Args:
            chat_history: List of messages with 'role' and 'content' keys
            tools: List of tool definitions
            **kwargs: Additional arguments for the LLM call

        Returns:
            Dictionary with tool call results or text response
        """
        return self.provider.get_tools_response(chat_history, tools, **kwargs)

    def get_stream_response(
        self, chat_history: list[dict[str, str]], **kwargs
    ) -> Generator[str, None, None]:
        """Get a streaming response from the LLM.

        Args:
            chat_history: List of messages with 'role' and 'content' keys
            **kwargs: Additional arguments for the LLM call

        Yields:
            Streaming response chunks
        """
        return self.provider.get_stream_response(chat_history, **kwargs)