"""LLMClient protocol — the contract every LLM backend must satisfy.

The extractors and transformers depend on this abstraction.
"""

from __future__ import annotations

from typing import Protocol, TypeVar, runtime_checkable

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


@runtime_checkable
class LLMClient(Protocol):
    """Minimal interface for LLM interactions."""

    async def astructured_predict(
        self,
        output_cls: type[T],
        messages: list[dict[str, str]],
        **prompt_kwargs,
    ) -> T:
        """Return a Pydantic model instance from structured LLM output."""
        ...

    async def apredict(
        self,
        messages: list[dict[str, str]],
        **prompt_kwargs,
    ) -> str:
        """Return a plain-text completion from a list of messages with placeholders."""
        ...

    async def acomplete(self, prompt: str) -> str:
        """Send a plain-text prompt and return the model's text response."""
        ...
