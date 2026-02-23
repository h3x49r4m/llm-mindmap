"""Tests for LLM utilities."""

import pytest
from unittest.mock import MagicMock, patch
from typing import Generator

from llm_mindmap.llm.utils import run_parallel_prompts, run_concurrent_prompts


class TestRunParallelPrompts:
    """Test run_parallel_prompts function."""

    @pytest.fixture
    def mock_llm_engine(self):
        """Create a mock LLM engine."""
        engine = MagicMock()
        engine.get_response.return_value = "Response"
        return engine

    def test_empty_prompts_raises_error(self, mock_llm_engine):
        """Test empty prompts list raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            run_parallel_prompts(
                mock_llm_engine,
                [],
                "System prompt",
            )

        assert "cannot be empty" in str(exc_info.value)

    def test_single_prompt(self, mock_llm_engine):
        """Test processing a single prompt."""
        prompts = ["Test prompt"]
        result = run_parallel_prompts(
            mock_llm_engine,
            prompts,
            "System prompt",
            max_workers=1,
        )

        assert len(result) == 1
        assert result[0] == "Response"
        mock_llm_engine.get_response.assert_called_once()

    def test_multiple_prompts(self, mock_llm_engine):
        """Test processing multiple prompts."""
        prompts = ["Prompt 1", "Prompt 2", "Prompt 3"]
        result = run_parallel_prompts(
            mock_llm_engine,
            prompts,
            "System prompt",
            max_workers=2,
        )

        assert len(result) == 3
        assert all(r == "Response" for r in result)
        assert mock_llm_engine.get_response.call_count == 3

    def test_order_preservation(self, mock_llm_engine):
        """Test that response order matches prompt order."""
        prompts = ["Prompt 1", "Prompt 2", "Prompt 3"]

        counter = [0]

        def side_effect(chat_history):
            counter[0] += 1
            return f"Response {counter[0]}"

        mock_llm_engine.get_response.side_effect = side_effect

        result = run_parallel_prompts(
            mock_llm_engine,
            prompts,
            "System prompt",
            max_workers=3,
        )

        assert result == ["Response 1", "Response 2", "Response 3"]

    def test_processing_callbacks(self, mock_llm_engine):
        """Test processing callbacks are applied."""
        prompts = ["Test prompt"]

        def uppercase(response):
            return response.upper()

        def add_exclamation(response):
            return response + "!"

        result = run_parallel_prompts(
            mock_llm_engine,
            prompts,
            "System prompt",
            processing_callbacks=[uppercase, add_exclamation],
        )

        assert result[0] == "RESPONSE!"

    def test_retry_logic_on_failure(self, mock_llm_engine):
        """Test retry logic when LLM calls fail."""
        prompts = ["Test prompt"]

        attempt_count = [0]

        def side_effect(chat_history):
            attempt_count[0] += 1
            if attempt_count[0] < 3:
                raise Exception("Temporary failure")
            return "Success"

        mock_llm_engine.get_response.side_effect = side_effect

        result = run_parallel_prompts(
            mock_llm_engine,
            prompts,
            "System prompt",
            max_workers=1,
        )

        assert result[0] == "Success"
        assert attempt_count[0] == 3

    def test_max_retries_exceeded(self, mock_llm_engine):
        """Test empty string returned after max retries."""
        prompts = ["Test prompt"]

        mock_llm_engine.get_response.side_effect = Exception("Persistent failure")

        result = run_parallel_prompts(
            mock_llm_engine,
            prompts,
            "System prompt",
            max_workers=1,
        )

        assert result[0] == ""

    def test_chat_history_format(self, mock_llm_engine):
        """Test chat history is formatted correctly."""
        prompts = ["Test prompt"]

        run_parallel_prompts(
            mock_llm_engine,
            prompts,
            "System prompt",
            max_workers=1,
        )

        call_args = mock_llm_engine.get_response.call_args
        chat_history = call_args[0][0]

        assert len(chat_history) == 2
        assert chat_history[0] == {"role": "system", "content": "System prompt"}
        assert chat_history[1] == {"role": "user", "content": "Test prompt"}


class TestRunConcurrentPrompts:
    """Test run_concurrent_prompts function."""

    @pytest.fixture
    def mock_llm_engine(self):
        """Create a mock LLM engine."""
        engine = MagicMock()
        engine.get_response.return_value = "Response"
        return engine

    @pytest.mark.asyncio
    async def test_empty_prompts_raises_error(self, mock_llm_engine):
        """Test empty prompts list raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            await run_concurrent_prompts(
                mock_llm_engine,
                [],
                "System prompt",
            )

        assert "cannot be empty" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_single_prompt(self, mock_llm_engine):
        """Test processing a single prompt."""
        prompts = ["Test prompt"]
        result = await run_concurrent_prompts(
            mock_llm_engine,
            prompts,
            "System prompt",
            max_workers=1,
        )

        assert len(result) == 1
        assert result[0] == "Response"
        mock_llm_engine.get_response.assert_called_once()

    @pytest.mark.asyncio
    async def test_multiple_prompts(self, mock_llm_engine):
        """Test processing multiple prompts."""
        prompts = ["Prompt 1", "Prompt 2", "Prompt 3"]
        result = await run_concurrent_prompts(
            mock_llm_engine,
            prompts,
            "System prompt",
            max_workers=2,
        )

        assert len(result) == 3
        assert all(r == "Response" for r in result)
        assert mock_llm_engine.get_response.call_count == 3

    @pytest.mark.asyncio
    async def test_order_preservation(self, mock_llm_engine):
        """Test that response order matches prompt order."""
        prompts = ["Prompt 1", "Prompt 2", "Prompt 3"]

        counter = [0]

        def side_effect(chat_history):
            counter[0] += 1
            return f"Response {counter[0]}"

        mock_llm_engine.get_response.side_effect = side_effect

        result = await run_concurrent_prompts(
            mock_llm_engine,
            prompts,
            "System prompt",
            max_workers=3,
        )

        assert result == ["Response 1", "Response 2", "Response 3"]

    @pytest.mark.asyncio
    async def test_processing_callbacks(self, mock_llm_engine):
        """Test processing callbacks are applied."""
        prompts = ["Test prompt"]

        def uppercase(response):
            return response.upper()

        def add_exclamation(response):
            return response + "!"

        result = await run_concurrent_prompts(
            mock_llm_engine,
            prompts,
            "System prompt",
            processing_callbacks=[uppercase, add_exclamation],
        )

        assert result[0] == "RESPONSE!"

    @pytest.mark.asyncio
    async def test_retry_logic_on_failure(self, mock_llm_engine):
        """Test retry logic when LLM calls fail."""
        prompts = ["Test prompt"]

        attempt_count = [0]

        def side_effect(chat_history):
            attempt_count[0] += 1
            if attempt_count[0] < 3:
                raise Exception("Temporary failure")
            return "Success"

        mock_llm_engine.get_response.side_effect = side_effect

        result = await run_concurrent_prompts(
            mock_llm_engine,
            prompts,
            "System prompt",
            max_workers=1,
        )

        assert result[0] == "Success"
        assert attempt_count[0] == 3

    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self, mock_llm_engine):
        """Test empty string returned after max retries."""
        prompts = ["Test prompt"]

        mock_llm_engine.get_response.side_effect = Exception("Persistent failure")

        result = await run_concurrent_prompts(
            mock_llm_engine,
            prompts,
            "System prompt",
            max_workers=1,
        )

        assert result[0] == ""

    @pytest.mark.asyncio
    async def test_semaphore_limits_concurrency(self, mock_llm_engine):
        """Test semaphore limits concurrent operations."""
        prompts = ["Prompt 1", "Prompt 2", "Prompt 3", "Prompt 4", "Prompt 5"]

        concurrent_count = [0]
        max_concurrent = [0]

        def side_effect(chat_history):
            concurrent_count[0] += 1
            max_concurrent[0] = max(max_concurrent[0], concurrent_count[0])
            time.sleep(0.01)
            concurrent_count[0] -= 1
            return "Response"

        mock_llm_engine.get_response.side_effect = side_effect

        import time

        await run_concurrent_prompts(
            mock_llm_engine,
            prompts,
            "System prompt",
            max_workers=2,
        )

        assert max_concurrent[0] <= 2