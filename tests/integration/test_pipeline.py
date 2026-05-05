"""Integration tests for the analysis pipeline (OpenAI-based)."""

import json

import pytest

from analyzer.extractors.function_extractor import FunctionLLMExtractor
from analyzer.extractors.license_extractor import LicenseLLMExtractor
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


@pytest.mark.asyncio
async def test_full_pipeline_with_fixtures(fake_llm, fixtures_dir, tmp_path):
    """Run the pipeline against the test fixtures directory and verify output."""

    # --- Enqueue LLM responses in the order the pipeline will call them ---

    # File 1: sample_copyleft_few.py (1 function → ≤ threshold → Rust rewrite)
    fake_llm.enqueue(
        # License extraction (astructured_predict)
        LicenseInfo(
            copyright_holder="Test Author",
            license_name="GPL-3.0",
            category=LicenseCategory.COPYLEFT,
        ),
        # Function extraction (now mandatory to get the count)
        FunctionList(functions=[FunctionSignature(name="only_one", num_args=0)]),
        # Rust rewrite via acomplete (only_one function, ≤ 2 threshold)
        'fn only_one() {\n    println!("I am alone");\n}',
    )

    # File 2: sample_copyleft_many.py (3 functions → > threshold → extract)
    fake_llm.enqueue(
        # License extraction (astructured_predict)
        LicenseInfo(
            copyright_holder="Test Author",
            license_name="GPL-3.0",
            category=LicenseCategory.COPYLEFT,
        ),
        # Function extraction (astructured_predict)
        FunctionList(
            functions=[
                FunctionSignature(name="alpha", num_args=0),
                FunctionSignature(name="beta", num_args=1),
                FunctionSignature(name="gamma", num_args=2),
            ]
        ),
    )

    # File 3: sample_permissive.py (permissive → always extract functions)
    fake_llm.enqueue(
        # License extraction (astructured_predict)
        LicenseInfo(
            copyright_holder="Test Author",
            license_name="MIT",
            category=LicenseCategory.PERMISSIVE,
        ),
        # Function extraction (astructured_predict)
        FunctionList(
            functions=[
                FunctionSignature(name="greet", num_args=1),
                FunctionSignature(name="add", num_args=2),
                FunctionSignature(name="multiply", num_args=3),
            ]
        ),
    )

    # --- Wire up the pipeline ---
    license_extractor = LicenseLLMExtractor(fake_llm)
    function_extractor = FunctionLLMExtractor(fake_llm)
    rust_rewriter = RustLLMRewriter(fake_llm)

    def resolve_strategy(license_type: str):
        return strategy_for(
            license_type,
            function_extractor=function_extractor,
            rust_rewriter=rust_rewriter,
        )

    output_dir = tmp_path / "output"
    writer = JSONResultWriter(output_dir=output_dir)

    pipeline = AnalysisPipeline(
        data_dir=fixtures_dir,
        license_extractor=license_extractor,
        resolve_strategy=resolve_strategy,
        writer=writer,
    )

    # --- Run ---
    results = await pipeline.run()

    # --- Assert ---
    assert len(results) == 3

    # Check output files exist
    assert (output_dir / "sample_copyleft_few_analysis.json").exists()
    assert (output_dir / "sample_copyleft_few.rs").exists()  # Rust rewrite
    assert (output_dir / "sample_copyleft_many_analysis.json").exists()
    assert (output_dir / "sample_permissive_analysis.json").exists()

    # Verify copyleft-few got Rust rewrite
    few_data = json.loads((output_dir / "sample_copyleft_few_analysis.json").read_text())
    assert "rust_rewrite" not in few_data
    assert "extracted_functions" not in few_data

    # Verify copyleft-many got function extraction
    many_data = json.loads((output_dir / "sample_copyleft_many_analysis.json").read_text())
    assert len(many_data["extracted_functions"]) == 3
    assert "rust_rewrite" not in many_data

    # Verify permissive got function extraction
    perm_data = json.loads((output_dir / "sample_permissive_analysis.json").read_text())
    assert len(perm_data["extracted_functions"]) == 3
    assert "rust_rewrite" not in perm_data
