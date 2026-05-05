"""Copyleft-license strategy — extracts functions OR rewrites to Rust."""

from __future__ import annotations

import logging

from analyzer.extractors.function_extractor import FunctionExtractor
from analyzer.strategies.base import StrategyOutput
from analyzer.transformers.rust_rewriter import RustRewriter

logger = logging.getLogger(__name__)

# Default threshold from task: "if number of functions > 2"
DEFAULT_FUNCTION_THRESHOLD = 2


class CopyleftStrategy:
    """For copyleft licenses: branch on function count.

    - > threshold → extract function signatures
    - ≤ threshold → rewrite the file to Rust
    """

    def __init__(
        self,
        function_extractor: FunctionExtractor,
        rust_rewriter: RustRewriter,
        function_threshold: int = DEFAULT_FUNCTION_THRESHOLD,
    ) -> None:
        self._function_extractor = function_extractor
        self._rust_rewriter = rust_rewriter
        self._function_threshold = function_threshold

    async def analyse(self, source_code: str, filename: str) -> StrategyOutput:
        # We use the extractor to get an accurate count
        # (handles multiple languages via LLM fallback)
        functions = await self._function_extractor.extract(source_code)
        num_functions = functions.effective_count

        logger.info(
            "  [copyleft] %s has %d functions (threshold=%d)",
            filename,
            num_functions,
            self._function_threshold,
        )

        if num_functions > self._function_threshold:
            return StrategyOutput(total_functions=num_functions, functions=functions)

        # Few functions -> Rewrite to Rust
        rust = await self._rust_rewriter.rewrite(source_code, filename)
        return StrategyOutput(total_functions=num_functions, rust_rewrite=rust)
