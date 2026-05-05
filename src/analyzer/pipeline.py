"""Orchestration layer — calls strategy → gets data → writes via persistence."""

from __future__ import annotations

import logging
from collections.abc import Callable
from pathlib import Path

from analyzer.extractors.license_extractor import LicenseExtractor
from analyzer.models import AnalysisResult
from analyzer.persistence.base import ResultWriter
from analyzer.strategies.base import AnalysisStrategy

logger = logging.getLogger(__name__)


class AnalysisPipeline:
    """Processes every file in *data_dir* through the analysis flow."""

    def __init__(
        self,
        data_dir: Path,
        license_extractor: LicenseExtractor,
        resolve_strategy: Callable[[str], AnalysisStrategy],
        writer: ResultWriter,
    ) -> None:
        self._data_dir = data_dir
        self._license_extractor = license_extractor
        self._resolve_strategy = resolve_strategy
        self._writer = writer

    async def run(self) -> list[AnalysisResult]:
        """Analyse all files and return the collected results."""
        results: list[AnalysisResult] = []

        files = sorted(self._data_dir.iterdir())
        if not files:
            logger.warning("No files found in %s", self._data_dir)
            return results

        for path in files:
            if path.is_dir():
                continue
            logger.info("Processing %s", path.name)
            result = await self._process_file(path)
            results.append(result)

        return results

    async def _process_file(self, path: Path) -> AnalysisResult:
        source = path.read_text(encoding="utf-8")

        # 1. Extract license
        license_info = await self._license_extractor.extract(source)
        logger.info("  License: %s (%s)", license_info.license_name, license_info.category.value)

        # 2. Pick strategy based on license category
        strategy = self._resolve_strategy(license_info.category.value)

        # 3. Run strategy — returns data only
        strategy_output = await strategy.analyse(source, path.name)

        # 4. Assemble final result
        result = AnalysisResult(
            file=path.name,
            license_info=license_info,
            total_functions_in_file=strategy_output.total_functions,
            extracted_functions=(
                strategy_output.functions.functions if strategy_output.functions else None
            ),
            rust_rewrite=strategy_output.rust_rewrite,
        )

        # 5. Persist
        await self._writer.write(result)

        return result
