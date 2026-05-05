"""Permissive-license strategy — always extracts functions."""

from __future__ import annotations

import logging

from analyzer.extractors.function_extractor import FunctionExtractor
from analyzer.strategies.base import StrategyOutput

logger = logging.getLogger(__name__)


class PermissiveStrategy:
    """For permissive licenses: extract function signatures."""

    def __init__(self, function_extractor: FunctionExtractor) -> None:
        self._function_extractor = function_extractor

    async def analyse(self, source_code: str, filename: str) -> StrategyOutput:
        functions = await self._function_extractor.extract(source_code)
        num_functions = functions.effective_count
        logger.info("  [permissive] %s has %d functions", filename, num_functions)

        return StrategyOutput(total_functions=num_functions, functions=functions)
