"""Decorator to add resilience (retries) to any LLMClient."""

from __future__ import annotations

import logging
from typing import Any, TypeVar

from llama_index.core.prompts import ChatPromptTemplate, PromptTemplate
from pydantic import BaseModel

from analyzer.llm.protocol import LLMClient

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class ResilientLLMClient:
    """Wraps an LLMClient and adds automatic retries for all operations."""

    def __init__(self, base_client: LLMClient, max_retries: int = 2) -> None:
        self._base_client = base_client
        self._max_retries = max_retries

    async def astructured_predict(
        self,
        output_cls: type[T],
        prompt: PromptTemplate | ChatPromptTemplate,
        **prompt_kwargs: Any,
    ) -> T:
        """Retry structured prediction on failure."""
        for attempt in range(self._max_retries + 1):
            try:
                return await self._base_client.astructured_predict(
                    output_cls,
                    prompt,
                    **prompt_kwargs,
                )
            except Exception as e:
                if attempt == self._max_retries:
                    logger.error(f"Final attempt failed for structured prediction: {e}")
                    raise
                logger.warning(f"LLM attempt {attempt + 1} failed: {e}. Retrying...")

        raise RuntimeError("Unreachable")

    async def apredict(
        self,
        prompt: PromptTemplate | ChatPromptTemplate,
        **prompt_kwargs: Any,
    ) -> str:
        """Retry plain-text prediction on failure."""
        for attempt in range(self._max_retries + 1):
            try:
                return await self._base_client.apredict(
                    prompt,
                    **prompt_kwargs,
                )
            except Exception as e:
                if attempt == self._max_retries:
                    logger.error(f"Final attempt failed for apredict: {e}")
                    raise
                logger.warning(f"LLM attempt {attempt + 1} failed: {e}. Retrying...")

        raise RuntimeError("Unreachable")

    async def acomplete(self, prompt: str) -> str:
        """Retry plain-text completion on failure."""
        for attempt in range(self._max_retries + 1):
            try:
                return await self._base_client.acomplete(prompt)
            except Exception as e:
                if attempt == self._max_retries:
                    logger.error(f"Final attempt failed for acomplete: {e}")
                    raise
                logger.warning(f"LLM attempt {attempt + 1} failed: {e}. Retrying...")

        raise RuntimeError("Unreachable")
