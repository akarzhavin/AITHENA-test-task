"""Unit tests for extractors (LlamaIndex-based)."""

import pytest

from analyzer.extractors.function_extractor import (
    FunctionLLMExtractor,
    SmartFunctionExtractor,
)
from analyzer.extractors.license_extractor import (
    LicenseLLMExtractor,
    SmartLicenseExtractor,
)
from analyzer.models import (
    FunctionList,
    FunctionSignature,
    LicenseCategory,
    LicenseInfo,
)


class TestLicenseExtractor:
    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "category, name",
        [(LicenseCategory.PERMISSIVE, "MIT"), (LicenseCategory.COPYLEFT, "GPL-3.0")],
    )
    async def test_extracts_categories(self, fake_llm, category, name):
        """Test that LLM extractor correctly identifies various license categories."""
        fake_llm.enqueue(LicenseInfo(copyright_holder="Alice", license_name=name, category=category))
        extractor = LicenseLLMExtractor(fake_llm)
        info = await extractor.extract(f"# {name} License\n# Copyright Alice")

        assert info.license_name == name
        assert info.category == category

    @pytest.mark.asyncio
    async def test_unknown_category(self, fake_llm):
        """Test that unknown licenses are correctly categorized as UNKNOWN."""
        fake_llm.enqueue(LicenseInfo(copyright_holder="Eve", license_name="Custom", category=LicenseCategory.UNKNOWN))
        extractor = LicenseLLMExtractor(fake_llm)
        info = await extractor.extract("Proprietary stuff")
        assert info.category == LicenseCategory.UNKNOWN


class TestFunctionExtractor:
    @pytest.mark.asyncio
    async def test_extracts_functions(self, fake_llm):
        """Test that LLM extractor parses multiple function signatures."""
        fake_llm.enqueue(
            FunctionList(
                functions=[
                    FunctionSignature(name="foo", num_args=0),
                    FunctionSignature(name="bar", num_args=2),
                ]
            )
        )
        extractor = FunctionLLMExtractor(fake_llm)
        result = await extractor.extract("def foo(): ...")
        assert len(result.functions) == 2
        assert result.functions[1].name == "bar"


class TestSmartFunctionExtractor:
    @pytest.mark.asyncio
    async def test_valid_python_uses_ast(self, fake_llm):
        """Test that valid Python code is parsed via AST, bypassing the LLM."""
        extractor = SmartFunctionExtractor(FunctionLLMExtractor(fake_llm))
        code = "def foo(a, b): pass\ndef bar(x): pass"
        result = await extractor.extract(code)

        assert len(result.functions) == 2
        assert result.functions[0].name == "foo"
        assert len(fake_llm.prompts) == 0

    @pytest.mark.asyncio
    async def test_invalid_python_falls_back_to_llm(self, fake_llm):
        """Test that non-Python code triggers a fallback to the LLM extractor."""
        fake_llm.enqueue(FunctionList(functions=[FunctionSignature(name="js_func", num_args=1)]))
        extractor = SmartFunctionExtractor(FunctionLLMExtractor(fake_llm))

        result = await extractor.extract("function js_func(x) { console.log(x); }")
        assert result.functions[0].name == "js_func"
        assert len(fake_llm.prompts) == 1


class TestSmartLicenseExtractor:
    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "code, expected_license, expected_category",
        [
            ("// SPDX-License-Identifier: MIT\n// Copyright John", "MIT", LicenseCategory.PERMISSIVE),
            ("// spdx-license-identifier: mit\n// Copyright Alice", "mit", LicenseCategory.PERMISSIVE),
            ("// SPDX-License-Identifier: Apache-2.0\n// Copyright Bob", "Apache-2.0", LicenseCategory.PERMISSIVE),
        ],
    )
    async def test_fast_track_matches(self, fake_llm, code, expected_license, expected_category):
        """Test that known SPDX tags bypass the LLM completely (case-insensitive)."""
        extractor = SmartLicenseExtractor(LicenseLLMExtractor(fake_llm))
        result = await extractor.extract(code)

        assert result.license_name == expected_license
        assert result.category == expected_category
        assert len(fake_llm.prompts) == 0

    @pytest.mark.asyncio
    async def test_unknown_spdx_calls_llm_with_micro_snippet(self, fake_llm):
        """Test that unknown SPDX IDs use a micro-snippet fallback to save tokens."""
        fake_llm.enqueue(LicenseInfo(copyright_holder="Bob", license_name="MPL-2.0", category=LicenseCategory.COPYLEFT))
        extractor = SmartLicenseExtractor(LicenseLLMExtractor(fake_llm))

        code = "// SPDX-License-Identifier: MPL-2.0\n// Copyright Bob\n" + "x" * 1000
        result = await extractor.extract(code)

        assert result.category == LicenseCategory.COPYLEFT
        assert len(fake_llm.prompts) == 1
        assert "x" * 1000 not in fake_llm.prompts[0]
        assert "MPL-2.0" in fake_llm.prompts[0]

    @pytest.mark.asyncio
    async def test_license_found_but_author_missing_calls_full_llm(self, fake_llm):
        """Test that missing author info triggers a full-file LLM search (safety fallback)."""
        fake_llm.enqueue(LicenseInfo(copyright_holder="Deep Author", license_name="MIT", category=LicenseCategory.PERMISSIVE))
        extractor = SmartLicenseExtractor(LicenseLLMExtractor(fake_llm))

        code = "// SPDX-License-Identifier: MIT\n" + "\n" * 60 + "// Copyright Deep Author"
        result = await extractor.extract(code)

        assert result.copyright_holder == "Deep Author"
        assert len(fake_llm.prompts) == 1
        assert "Deep Author" in fake_llm.prompts[0]  # Verify full code was sent
