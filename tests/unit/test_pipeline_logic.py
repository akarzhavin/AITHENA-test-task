"""Unit tests for AnalysisPipeline."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest

from analyzer.models import AnalysisResult, LicenseCategory, LicenseInfo
from analyzer.pipeline import AnalysisPipeline
from analyzer.strategies.base import StrategyOutput

if TYPE_CHECKING:
    pass


class MockWriter:
    """Mock writer that tracks what was written and simulates existing files."""

    def __init__(self, existing_files: set[str] | None = None) -> None:
        self.existing_files = existing_files or set()
        self.written: list[str] = []

    async def write(self, result: AnalysisResult) -> None:
        self.written.append(result.file)

    def exists(self, filename: str) -> bool:
        return filename in self.existing_files


@pytest.fixture
def mock_deps() -> dict[str, Any]:
    """Provides mock extractor and strategy resolver."""

    class MockExtractor:
        async def extract(self, source: str) -> LicenseInfo:
            return LicenseInfo(
                copyright_holder="X",
                license_name="MIT",
                category=LicenseCategory.PERMISSIVE,
            )

    class MockStrategy:
        async def analyse(self, source: str, name: str) -> StrategyOutput:
            return StrategyOutput(total_functions=0)

    return {
        "extractor": MockExtractor(),
        "strategy_resolver": lambda _: MockStrategy(),
    }


@pytest.fixture
def test_data(tmp_path: Path) -> Path:
    """Creates a temporary data directory with two sample files."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "file1.py").write_text("code1")
    (data_dir / "file2.py").write_text("code2")
    return data_dir


@pytest.mark.asyncio
async def test_pipeline_idempotency(test_data: Path, mock_deps: dict[str, Any]) -> None:
    """Verify that by default the pipeline skips files with existing results."""
    writer = MockWriter(existing_files={"file1.py"})
    pipeline = AnalysisPipeline(
        data_dir=test_data,
        writer=writer,
        license_extractor=mock_deps["extractor"],
        resolve_strategy=mock_deps["strategy_resolver"],
    )

    results = await pipeline.run()

    assert len(results) == 1
    assert results[0].file == "file2.py"
    assert writer.written == ["file2.py"]


@pytest.mark.asyncio
async def test_pipeline_force_rewrite(test_data: Path, mock_deps: dict[str, Any]) -> None:
    """Verify that force_rewrite=True overrides idempotency checks."""
    writer = MockWriter(existing_files={"file1.py", "file2.py"})
    pipeline = AnalysisPipeline(
        data_dir=test_data,
        writer=writer,
        license_extractor=mock_deps["extractor"],
        resolve_strategy=mock_deps["strategy_resolver"],
        force_rewrite=True,
    )

    results = await pipeline.run()

    assert len(results) == 2
    assert "file1.py" in writer.written
    assert "file2.py" in writer.written


@pytest.mark.asyncio
async def test_pipeline_error_isolation(test_data: Path, mock_deps: dict[str, Any]) -> None:
    """Verify that an error in one file doesn't crash the whole pipeline."""

    class CrashingExtractor:
        async def extract(self, source: str) -> LicenseInfo:
            if "code1" in source:
                raise RuntimeError("Boom")
            return LicenseInfo(
                copyright_holder="X",
                license_name="MIT",
                category=LicenseCategory.PERMISSIVE,
            )

    pipeline = AnalysisPipeline(
        data_dir=test_data,
        writer=MockWriter(),
        license_extractor=CrashingExtractor(),  # type: ignore[arg-type]
        resolve_strategy=mock_deps["strategy_resolver"],
    )

    results = await pipeline.run()

    # file1.py failed, but file2.py should be processed
    assert len(results) == 1
    assert results[0].file == "file2.py"
