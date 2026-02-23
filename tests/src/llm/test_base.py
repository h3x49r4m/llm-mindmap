"""Tests for LLM base module."""

import pytest

from llm_mindmap.llm.base import LLMConfig, LLMEngine


class TestLLMConfig:
    """Test LLMConfig configuration model."""

    def test_valid_config(self):
        """Test creating a valid LLMConfig."""
        config = LLMConfig(
            provider="openrouter",
            model="anthropic/claude-3.5-sonnet",
            connection_config={"api_key": "test-key"},
            temperature=0.0,
            timeout=60,
        )

        assert config.provider == "openrouter"
        assert config.model == "anthropic/claude-3.5-sonnet"
        assert config.connection_config == {"api_key": "test-key"}
        assert config.temperature == 0.0
        assert config.timeout == 60

    def test_provider_validation_valid(self):
        """Test provider validation with valid providers."""
        for provider in ["openrouter", "iflow"]:
            config = LLMConfig(provider=provider, model="test-model")
            assert config.provider == provider

    def test_provider_validation_invalid(self):
        """Test provider validation rejects invalid providers."""
        with pytest.raises(ValueError) as exc_info:
            LLMConfig(provider="invalid", model="test-model")

        assert "Unsupported provider" in str(exc_info.value)

    def test_provider_case_insensitive(self):
        """Test provider validation is case-insensitive."""
        config = LLMConfig(provider="OPENROUTER", model="test-model")
        assert config.provider == "openrouter"

    def test_temperature_bounds(self):
        """Test temperature bounds validation."""
        # Valid range
        LLMConfig(provider="openrouter", model="test", temperature=0.0)
        LLMConfig(provider="openrouter", model="test", temperature=1.0)
        LLMConfig(provider="openrouter", model="test", temperature=2.0)

        # Invalid: negative
        with pytest.raises(ValueError):
            LLMConfig(provider="openrouter", model="test", temperature=-0.1)

        # Invalid: too high
        with pytest.raises(ValueError):
            LLMConfig(provider="openrouter", model="test", temperature=2.1)

    def test_timeout_bounds(self):
        """Test timeout bounds validation."""
        # Valid
        LLMConfig(provider="openrouter", model="test", timeout=1)
        LLMConfig(provider="openrouter", model="test", timeout=60)

        # Invalid: too low
        with pytest.raises(ValueError):
            LLMConfig(provider="openrouter", model="test", timeout=0)

    def test_get_llm_kwargs(self):
        """Test get_llm_kwargs filters out reserved keys."""
        config = LLMConfig(
            provider="openrouter",
            model="test-model",
            connection_config={"api_key": "test"},
            temperature=0.5,
            timeout=30,
        )

        kwargs = config.get_llm_kwargs()

        assert "model" not in kwargs
        assert "provider" not in kwargs
        assert "connection_config" not in kwargs
        assert kwargs["temperature"] == 0.5
        assert kwargs["timeout"] == 30


class TestLLMEngine:
    """Test LLMEngine provider loading."""

    def test_parse_model_with_provider(self):
        """Test parsing model string with provider prefix."""
        engine = LLMEngine(model="openrouter::anthropic/claude-3.5-sonnet")

        assert engine.provider_name == "openrouter"
        assert engine.model_name == "anthropic/claude-3.5-sonnet"

    def test_parse_model_without_provider(self):
        """Test parsing model string without provider prefix."""
        engine = LLMEngine(model="anthropic/claude-3.5-sonnet")

        assert engine.provider_name == "openrouter"  # Default
        assert engine.model_name == "anthropic/claude-3.5-sonnet"

    def test_parse_model_from_env(self):
        """Test parsing model from environment variable."""
        import os

        os.environ["LLM_MINDMAP_DEFAULT_MODEL"] = "iflow::test-model"

        engine = LLMEngine()

        assert engine.provider_name == "iflow"
        assert engine.model_name == "test-model"

        del os.environ["LLM_MINDMAP_DEFAULT_MODEL"]

    def test_connection_config_passed_to_provider(self):
        """Test connection config is passed to provider."""
        engine = LLMEngine(
            model="openrouter::test-model",
            api_key="test-key",
            base_url="https://test.example.com",
        )

        assert engine.provider.connection_config == {
            "api_key": "test-key",
            "base_url": "https://test.example.com",
        }

    def test_invalid_provider_raises_error(self):
        """Test invalid provider raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            LLMEngine(model="invalid::test-model")

        assert "Unsupported provider" in str(exc_info.value)