"""Function signature extraction via LLM (LlamaIndex structured prediction)."""

from __future__ import annotations

import ast
import logging
from typing import Protocol, runtime_checkable

from analyzer.llm.protocol import LLMClient
from analyzer.models import FunctionList, FunctionSignature
from analyzer.prompts import FUNCTION_EXTRACTION_PROMPT

logger = logging.getLogger(__name__)


@runtime_checkable
class FunctionExtractor(Protocol):
    """Protocol for function extraction."""

    async def extract(self, source_code: str) -> FunctionList: ...


class FunctionLLMExtractor:
    """Extracts function signatures from source code using LlamaIndex structured prediction."""

    def __init__(self, llm: LLMClient) -> None:
        self._llm = llm

    async def extract(self, source_code: str) -> FunctionList:
        return await self._llm.astructured_predict(
            FunctionList,
            FUNCTION_EXTRACTION_PROMPT,
            source_code=source_code,
        )


class SmartFunctionExtractor:
    """Tries to extract using AST (fast, free, deterministic), falls back to LLM."""

    def __init__(self, fallback: FunctionExtractor) -> None:
        self._fallback = fallback

    async def extract(self, source_code: str) -> FunctionList:
        try:
            tree = ast.parse(source_code)
            functions = []
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Count arguments
                    args = node.args.args
                    num_args = len(args)

                    # Exclude 'self' or 'cls' for methods
                    if num_args > 0 and args[0].arg in ("self", "cls"):
                        num_args -= 1

                    functions.append(FunctionSignature(name=node.name, num_args=num_args))

            logger.info("  [SmartExtractor] Extracted %d functions via AST", len(functions))
            return FunctionList(functions=functions)

        except SyntaxError:
            logger.info(
                "  [SmartExtractor] AST parsing failed (likely JS/TS). Falling back to LLM."
            )
            return await self._fallback.extract(source_code)
