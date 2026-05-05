"""OpenAI implementation of LLMClient via LlamaIndex."""

from __future__ import annotations

import logging
from typing import TypeVar

from llama_index.core.prompts import PromptTemplate
from llama_index.llms.openai import OpenAI
from pydantic import BaseModel

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class OpenAIClient:
    """Thin wrapper around the LlamaIndex OpenAI LLM.

    Exposes exactly the two methods our protocol requires:
    ``astructured_predict`` and ``acomplete``.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ) -> None:
        self._llm = OpenAI(
            api_key=api_key,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    async def astructured_predict(
        self,
        output_cls: type[T],
        prompt: PromptTemplate,
        **prompt_kwargs,
    ) -> T:
        """Structured prediction — returns a validated Pydantic instance."""
        return await self._llm.astructured_predict(
            output_cls,
            prompt,
            **prompt_kwargs,
        )

    async def acomplete(self, prompt: str) -> str:
        """Plain-text completion."""
        response = await self._llm.acomplete(prompt)
        return response.text
