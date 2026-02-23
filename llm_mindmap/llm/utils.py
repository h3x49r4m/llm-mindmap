"""Concurrent execution utilities for LLM operations."""

from __future__ import annotations

import asyncio
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from logging import Logger, getLogger
from typing import Any, Callable

from tqdm import tqdm

from llm_mindmap.llm.base import LLMEngine

logger: Logger = getLogger(__name__)


def run_parallel_prompts(
    llm_engine: LLMEngine,
    prompts: list[str],
    system_prompt: str,
    max_workers: int = 30,
    processing_callbacks: list[Callable[[str], str]] | None = None,
    **kwargs,
) -> list[str]:
    """Run LLM prompts concurrently using threads.

    Args:
        llm_engine: The LLM engine with a synchronous get_response method
        prompts: List of prompts to run concurrently
        system_prompt: The system prompt
        max_workers: Maximum number of threads
        processing_callbacks: Optional callback functions to apply to responses
        **kwargs: Additional arguments for get_response

    Returns:
        List of responses in the same order as prompts

    Raises:
        ValueError: If prompts list is empty
    """
    if not prompts:
        raise ValueError("Prompts list cannot be empty")

    def fetch(idx: int, prompt: str) -> tuple[int, str]:
        """Fetch response for a single prompt with retry logic.

        Args:
            idx: Index of the prompt
            prompt: The prompt text

        Returns:
            Tuple of (index, response)
        """
        chat_history = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ]

        retry_delay = 1
        max_retries = 5
        last_exception = None

        for attempt in range(max_retries):
            try:
                response = llm_engine.get_response(chat_history, **kwargs)

                if processing_callbacks is not None:
                    for func in processing_callbacks:
                        response = func(response)

                return idx, response

            except Exception as e:
                last_exception = e
                logger.warning(
                    f"Attempt {attempt + 1}/{max_retries} failed for prompt {idx}: {e}"
                )
                time.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, 60)

        logger.error(
            f"Failed to get response for prompt {idx} after {max_retries} attempts: {last_exception}"
        )
        return idx, ""

    results = ["" for _ in prompts]

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(fetch, idx, prompt)
            for idx, prompt in enumerate(prompts)
        ]

        for future in tqdm(
            as_completed(futures),
            total=len(prompts),
            desc="Processing prompts...",
        ):
            idx, result = future.result()
            results[idx] = result

    return results


async def run_concurrent_prompts(
    llm_engine: LLMEngine,
    prompts: list[str],
    system_prompt: str,
    max_workers: int = 30,
    processing_callbacks: list[Callable[[str], str]] | None = None,
    **kwargs,
) -> list[str]:
    """Run LLM prompts concurrently using asyncio.

    Args:
        llm_engine: The LLM engine with a synchronous get_response method
        prompts: List of prompts to run concurrently
        system_prompt: The system prompt
        max_workers: Maximum number of concurrent tasks
        processing_callbacks: Optional callback functions to apply to responses
        **kwargs: Additional arguments for get_response

    Returns:
        List of responses in the same order as prompts

    Raises:
        ValueError: If prompts list is empty
    """
    if not prompts:
        raise ValueError("Prompts list cannot be empty")

    semaphore = asyncio.Semaphore(max_workers)

    async def fetch(idx: int, prompt: str) -> tuple[int, str]:
        """Fetch response for a single prompt with retry logic.

        Args:
            idx: Index of the prompt
            prompt: The prompt text

        Returns:
            Tuple of (index, response)
        """
        chat_history = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ]

        retry_delay = 1
        max_retries = 5
        last_exception = None

        async with semaphore:
            for attempt in range(max_retries):
                try:
                    response = llm_engine.get_response(chat_history, **kwargs)

                    if processing_callbacks is not None:
                        for func in processing_callbacks:
                            response = func(response)

                    return idx, response

                except Exception as e:
                    last_exception = e
                    logger.warning(
                        f"Attempt {attempt + 1}/{max_retries} failed for prompt {idx}: {e}"
                    )
                    await asyncio.sleep(retry_delay)
                    retry_delay = min(retry_delay * 2, 60)

            logger.error(
                f"Failed to get response for prompt {idx} after {max_retries} attempts: {last_exception}"
            )
            return idx, ""

    tasks = [fetch(idx, prompt) for idx, prompt in enumerate(prompts)]
    results = ["" for _ in prompts]

    with tqdm(total=len(prompts), desc="Processing prompts...") as pbar:
        for future in asyncio.as_completed(tasks):
            idx, result = await future
            results[idx] = result
            pbar.update(1)

    return results