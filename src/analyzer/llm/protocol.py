"""LLMClient protocol — the contract every LLM backend must satisfy.

Mirrors the subset of llama_index LLM API we actually use, so extractors
and transformers depend on an abstraction, not on LlamaIndex directly.
"""

from __future__ import annotations

from typing import Protocol, TypeVar, runtime_checkable

from llama_index.core.prompts import PromptTemplate
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


@runtime_checkable
class LLMClient(Protocol):
    """Minimal interface for LLM interactions."""

    async def astructured_predict(
        self,
        output_cls: type[T],
        prompt: PromptTemplate,
        **prompt_kwargs,
    ) -> T:
        """Return a Pydantic model instance from structured LLM output."""
        ...

    async def acomplete(self, prompt: str) -> str:
        """Send a plain-text prompt and return the model's text response."""
        ...
