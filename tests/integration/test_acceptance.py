from __future__ import annotations

import json
import re
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from analyzer.extractors.function_extractor import (
    FunctionLLMExtractor,
    SmartFunctionExtractor,
)
from analyzer.extractors.license_extractor import (
    LicenseLLMExtractor,
    SmartLicenseExtractor,
)
from analyzer.extractors.license_registry import SPDX_CATEGORY_MAP
from analyzer.models import (
    FunctionList,
    FunctionSignature,
    LicenseCategory,
    LicenseInfo,
)
from analyzer.persistence.json_writer import JSONResultWriter
from analyzer.pipeline import AnalysisPipeline
from analyzer.strategies.registry import strategy_for
from analyzer.transformers.rust_rewriter import RustLLMRewriter

if TYPE_CHECKING:
    from tests.conftest import FakeLLMClient


@pytest.mark.asyncio
async def test_acceptance_golden_files(fake_llm: FakeLLMClient, tmp_path: Path) -> None:
    """
    Acceptance test: Runs the pipeline on the real 'data' directory
    and verifies that the results match the 'output' directory.
    """
    project_root = Path(__file__).parent.parent.parent
    fixtures_dir = project_root / "tests" / "fixtures" / "acceptance"
    data_dir = fixtures_dir / "data"
    golden_dir = fixtures_dir / "output"
    test_output_dir = tmp_path / "output"

    # 1. Prepare
    data_files = sorted(p for p in data_dir.iterdir() if p.is_file())
    _prepare_mock_responses(fake_llm, data_files, golden_dir)

    # 2. Setup & Run
    pipeline = _build_pipeline(fake_llm, data_dir, test_output_dir)
    await pipeline.run()

    # 3. Verify
    _verify_results(test_output_dir, golden_dir)


def _prepare_mock_responses(
    fake_llm: FakeLLMClient, data_files: list[Path], golden_dir: Path
) -> None:
    """Fills FakeLLMClient with data from existing golden files."""
    for data_file in data_files:
        stem = data_file.stem
        json_path = golden_dir / f"{stem}_analysis.json"

        if not json_path.exists():
            continue

        with open(json_path) as f:
            golden_data = json.load(f)

        # Check if we need to enqueue LicenseInfo
        # SmartLicenseExtractor bypasses LLM ONLY if both SPDX and Copyright are found
        source = data_file.read_text(encoding="utf-8")
        head = "\n".join(source.splitlines()[:50])
        spdx_pattern = re.compile(r"SPDX-License-Identifier:\s*([A-Za-z0-9\.\-\+]+)", re.IGNORECASE)
        copy_pattern = re.compile(
            r"Copyright\s+(?:\([cC]\)\s+)?(?:[0-9]{4}\s+)?(.+)", re.IGNORECASE
        )

        spdx_match = spdx_pattern.search(head)
        copy_match = copy_pattern.search(head)

        needs_license_llm = True
        if spdx_match and copy_match:
            license_id = spdx_match.group(1).strip().upper()
            if license_id in SPDX_CATEGORY_MAP:
                needs_license_llm = False

        if needs_license_llm:
            fake_llm.enqueue(
                LicenseInfo(
                    copyright_holder=golden_data["license_info"]["copyright_holder"],
                    license_name=golden_data["license_info"]["license_name"],
                    category=LicenseCategory(golden_data["license_info"]["category"]),
                )
            )

        # Determine if we need to mock function extraction or rust rewrite
        _enqueue_strategy_responses(fake_llm, data_file, golden_data, golden_dir)


def _enqueue_strategy_responses(
    fake_llm: FakeLLMClient, data_file: Path, golden_data: dict, golden_dir: Path
) -> None:
    """Enqueues additional responses if the strategy requires LLM calls."""
    is_python = data_file.suffix == ".py"
    is_copyleft = golden_data["license_info"]["category"] == "copyleft"
    count = golden_data.get("total_functions_in_file", 0)

    # ALL strategies now call function_extractor.extract() to get the count.
    # We only need to enqueue if it triggers an LLM call (non-python or specific fallback).
    if not is_python or data_file.stem in ("3", "18", "19"):
        if "extracted_functions" in golden_data:
            functions = [
                FunctionSignature(**fn) for fn in golden_data["extracted_functions"]
            ]
        else:
            # For Rust rewrite cases, we might not have the list in golden,
            # but we need the count to be correct for strategy branching.
            functions = [
                FunctionSignature(name=f"stub_{i}", num_args=0)
                for i in range(count)
            ]

        fake_llm.enqueue(FunctionList(functions=functions, total_count=len(functions)))

    # Handle Rust rewrite for copyleft <= 2
    if is_copyleft and count <= 2:
        rs_path = golden_dir / f"{data_file.stem}.rs"
        if rs_path.exists():
            fake_llm.enqueue(rs_path.read_text())


def _build_pipeline(llm: FakeLLMClient, data_dir: Path, output_dir: Path) -> AnalysisPipeline:
    """Wires up the pipeline with all dependencies."""
    license_extractor = SmartLicenseExtractor(fallback=LicenseLLMExtractor(llm))
    function_extractor = SmartFunctionExtractor(fallback=FunctionLLMExtractor(llm))
    rust_rewriter = RustLLMRewriter(llm)

    def resolve_strategy(license_type: str):
        return strategy_for(
            license_type,
            function_extractor=function_extractor,
            rust_rewriter=rust_rewriter,
        )

    return AnalysisPipeline(
        data_dir=data_dir,
        license_extractor=license_extractor,
        resolve_strategy=resolve_strategy,
        writer=JSONResultWriter(output_dir=output_dir),
    )


def _verify_results(test_output_dir: Path, golden_dir: Path) -> None:
    """Compares each file in test_output_dir against golden_dir."""
    for golden_file in golden_dir.iterdir():
        test_file = test_output_dir / golden_file.name

        if golden_file.suffix == ".json":
            _compare_json(test_file, golden_file)
        elif golden_file.suffix == ".rs":
            _compare_text(test_file, golden_file)


def _compare_json(test_file: Path, golden_file: Path) -> None:
    assert test_file.exists(), f"Missing output for {golden_file.name}"

    golden = json.loads(golden_file.read_text())
    test = json.loads(test_file.read_text())

    assert test["file"] == golden["file"]
    assert test["license_info"] == golden["license_info"]
    assert test.get("total_functions_in_file") == golden.get("total_functions_in_file")

    if "extracted_functions" in golden:
        assert test["extracted_functions"] == golden["extracted_functions"]


def _compare_text(test_file: Path, golden_file: Path) -> None:
    assert test_file.exists(), f"Missing Rust rewrite for {golden_file.name}"
    assert test_file.read_text().strip() == golden_file.read_text().strip()
