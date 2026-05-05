"""Rust rewriting via LLM — lives in transformers/ (not extractors/).

Uses plain acomplete (not structured predict) because the output is raw
Rust source code, not a structured Pydantic model.
"""

from __future__ import annotations

import logging
from typing import Protocol, runtime_checkable

from analyzer.llm.protocol import LLMClient
from analyzer.models import RustRewrite
from analyzer.prompts import RUST_REWRITE_PROMPT

logger = logging.getLogger(__name__)


@runtime_checkable
class RustRewriter(Protocol):
    """Protocol for Rust code generation."""

    async def rewrite(self, source_code: str, filename: str) -> RustRewrite: ...


class RustLLMRewriter:
    """Rewrites source code into Rust using an LLM."""

    def __init__(self, llm: LLMClient) -> None:
        self._llm = llm

    async def rewrite(self, source_code: str, filename: str) -> RustRewrite:
        prompt = RUST_REWRITE_PROMPT.format(source_code=source_code)
        rust_code = await self._llm.acomplete(prompt)
        return RustRewrite(rust_code=rust_code.strip(), source_file=filename)
