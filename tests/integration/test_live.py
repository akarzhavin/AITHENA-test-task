"""Live acceptance tests — requires real LLM access.

This module orchestrates full-scale integration tests using the real OpenAI API.
It automatically discovers all fixture files and verifies that the pipeline
produces valid results, comparing them against 'golden' expectations where appropriate.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest

from analyzer.config import Settings
from analyzer.extractors.function_extractor import (
    FunctionLLMExtractor,
    SmartFunctionExtractor,
)
from analyzer.extractors.license_extractor import (
    LicenseLLMExtractor,
    SmartLicenseExtractor,
)
from analyzer.llm.factory import build_llm_client
from analyzer.persistence.json_writer import JSONResultWriter
from analyzer.pipeline import AnalysisPipeline
from analyzer.strategies.registry import strategy_for
from analyzer.transformers.rust_rewriter import RustLLMRewriter

if TYPE_CHECKING:
    from analyzer.llm.protocol import LLMClient

# --- Constants & Path Discovery --------------------------------------------

BASE_DIR = Path(__file__).parent.parent.parent
DATA_DIR = BASE_DIR / "tests" / "fixtures" / "acceptance" / "data"
GOLDEN_DIR = BASE_DIR / "tests" / "fixtures" / "acceptance" / "output"

# Exclude hidden files (like .DS_Store)
ALL_FIXTURES = sorted(
    [f.name for f in DATA_DIR.iterdir() if f.is_file() and not f.name.startswith(".")]
)

logger = logging.getLogger(__name__)


# --- Helper Structures -----------------------------------------------------


@dataclass
class AnalysisContext:
    """Encapsulates the environment for a single test run."""

    data_dir: Path
    output_dir: Path
    source_file: str

    @property
    def source_path(self) -> Path:
        return self.data_dir / self.source_file

    @property
    def result_path(self) -> Path:
        return self.output_dir / f"{Path(self.source_file).stem}_analysis.json"

    @property
    def rust_path(self) -> Path:
        return self.output_dir / f"{Path(self.source_file).stem}.rs"


# --- Fixtures --------------------------------------------------------------


@pytest.fixture(scope="module")
def live_settings() -> Settings:
    """Load settings and verify API availability."""
    try:
        settings = Settings()  # type: ignore[call-arg]
        key = settings.openai_api_key
        if not key or key.startswith("sk-YOUR") or key == "sk-...":
            pytest.skip("Skipping live test: Valid OPENAI_API_KEY not found in environment.")
        return settings
    except Exception as e:
        pytest.skip(f"Could not initialize settings for live test: {e}")


@pytest.fixture(scope="module")
def live_llm(live_settings: Settings) -> LLMClient:
    """Initialize the real, resilient LLM client."""
    return build_llm_client(live_settings)


@pytest.fixture
def pipeline_builder(live_llm: LLMClient):
    """Factory for pre-configured AnalysisPipelines."""

    def _build(data_dir: Path, output_dir: Path) -> AnalysisPipeline:
        # Dependency injection for the full stack
        llm_license = LicenseLLMExtractor(live_llm)
        llm_function = FunctionLLMExtractor(live_llm)

        license_ext = SmartLicenseExtractor(fallback=llm_license)
        function_ext = SmartFunctionExtractor(fallback=llm_function)
        rust_rewriter = RustLLMRewriter(live_llm)

        def strategy_resolver(category: str):
            return strategy_for(
                category,
                function_extractor=function_ext,
                rust_rewriter=rust_rewriter,
            )

        return AnalysisPipeline(
            data_dir=data_dir,
            license_extractor=license_ext,
            resolve_strategy=strategy_resolver,
            writer=JSONResultWriter(output_dir=output_dir),
        )

    return _build


# --- Core Test Logic -------------------------------------------------------


@pytest.mark.live
@pytest.mark.asyncio
@pytest.mark.parametrize("source_name", ALL_FIXTURES)
async def test_live_pipeline_full_cycle(
    source_name: str,
    tmp_path: Path,
    pipeline_builder,
) -> None:
    """
    End-to-End verification on fixture files using real OpenAI models.

    Verifies:
    1. Pipeline completion without crashes.
    2. Correct license categorization.
    3. Deterministic function counting for Python.
    4. Existence and basic validity of Rust rewrites for copyleft code.
    """
    # 1. Setup Context
    ctx = AnalysisContext(
        data_dir=tmp_path / "data",
        output_dir=tmp_path / "output",
        source_file=source_name,
    )
    ctx.data_dir.mkdir()

    # Copy source to isolated data dir
    ctx.source_path.write_text((DATA_DIR / source_name).read_text(encoding="utf-8"))

    # 2. Execution
    pipeline = pipeline_builder(ctx.data_dir, ctx.output_dir)
    await pipeline.run()

    # 3. Verification
    _verify_output_exists(ctx)

    with open(ctx.result_path) as f:
        data = json.load(f)
        _verify_against_golden(ctx, data)
        _verify_rust_integrity(ctx, data)


# --- Verification Helpers --------------------------------------------------


def _verify_output_exists(ctx: AnalysisContext) -> None:
    assert ctx.result_path.exists(), f"Pipeline failed to generate {ctx.result_path.name}"


def _verify_against_golden(ctx: AnalysisContext, actual: dict[str, Any]) -> None:
    """Compare categorical and deterministic fields against golden files."""
    golden_path = GOLDEN_DIR / ctx.result_path.name
    if not golden_path.exists():
        logger.warning("No golden file found for %s, skipping deep comparison.", ctx.source_file)
        return

    with open(golden_path) as f:
        golden = json.load(f)

    # 1. License Category (Must match exactly)
    expected_cat = golden["license_info"]["category"]
    actual_cat = actual["license_info"]["category"]
    assert actual_cat == expected_cat, (
        f"[{ctx.source_file}] License mismatch: expected {expected_cat}, got {actual_cat}"
    )

    # 2. Function Count (Strict for Python, flexible for others)
    if ctx.source_file.endswith(".py") and "total_functions_in_file" in golden:
        expected_cnt = golden["total_functions_in_file"]
        actual_cnt = actual.get("total_functions_in_file")
        assert actual_cnt == expected_cnt, (
            f"[{ctx.source_file}] Function count mismatch: "
            f"expected {expected_cnt}, got {actual_cnt}"
        )


def _verify_rust_integrity(ctx: AnalysisContext, actual: dict[str, Any]) -> None:
    """Ensure Rust rewrite occurs only when expected and is non-empty."""
    if not ctx.rust_path.exists():
        return

    rust_code = ctx.rust_path.read_text(encoding="utf-8").strip()
    assert len(rust_code) > 20, f"Rust rewrite for {ctx.source_file} seems suspiciously short."

    # Logic check: Rewrite should only happen for copyleft with <= 2 functions
    assert actual["license_info"]["category"] == "copyleft"
    assert actual.get("total_functions_in_file", 0) <= 2
