"""Strategy registry — maps license category to a concrete strategy."""

from __future__ import annotations

import logging

from analyzer.extractors.function_extractor import FunctionExtractor
from analyzer.strategies.base import AnalysisStrategy
from analyzer.strategies.copyleft import CopyleftStrategy
from analyzer.strategies.permissive import PermissiveStrategy
from analyzer.transformers.rust_rewriter import RustRewriter

logger = logging.getLogger(__name__)


def strategy_for(
    license_category: str,
    *,
    function_extractor: FunctionExtractor,
    rust_rewriter: RustRewriter,
    function_threshold: int = 2,
) -> AnalysisStrategy:
    """Return the right strategy for *license_category*.

    Falls back to PermissiveStrategy for unknown categories.
    """
    if license_category == "copyleft":
        return CopyleftStrategy(
            function_extractor=function_extractor,
            rust_rewriter=rust_rewriter,
            function_threshold=function_threshold,
        )

    if license_category != "permissive":
        logger.warning(
            "Unknown license category %r — defaulting to permissive strategy",
            license_category,
        )

    return PermissiveStrategy(function_extractor=function_extractor)
