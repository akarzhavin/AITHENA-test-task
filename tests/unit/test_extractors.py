"""Unit tests for extractors (LlamaIndex-based)."""

import pytest

from analyzer.extractors.function_extractor import (
    FunctionLLMExtractor,
    SmartFunctionExtractor,
)
from analyzer.extractors.license_extractor import LicenseLLMExtractor
from analyzer.models import (
    FunctionList,
    FunctionSignature,
    LicenseCategory,
    LicenseInfo,
)


class TestLicenseExtractor:
    @pytest.mark.asyncio
    async def test_extracts_permissive(self, fake_llm):
        fake_llm.enqueue(
            LicenseInfo(
                copyright_holder="Alice",
                license_name="MIT",
                category=LicenseCategory.PERMISSIVE,
            )
        )
        extractor = LicenseLLMExtractor(fake_llm)
        info = await extractor.extract("# MIT License\n# Copyright Alice")

        assert info.copyright_holder == "Alice"
        assert info.license_name == "MIT"
        assert info.category == LicenseCategory.PERMISSIVE

    @pytest.mark.asyncio
    async def test_extracts_copyleft(self, fake_llm):
        fake_llm.enqueue(
            LicenseInfo(
                copyright_holder="Bob",
                license_name="GPL-3.0",
                category=LicenseCategory.COPYLEFT,
            )
        )
        extractor = LicenseLLMExtractor(fake_llm)
        info = await extractor.extract("# GPL License\n# Copyright Bob")

        assert info.category == LicenseCategory.COPYLEFT

    @pytest.mark.asyncio
    async def test_unknown_category(self, fake_llm):
        fake_llm.enqueue(
            LicenseInfo(
                copyright_holder="Eve",
                license_name="Proprietary",
                category=LicenseCategory.UNKNOWN,
            )
        )
        extractor = LicenseLLMExtractor(fake_llm)
        info = await extractor.extract("# Some license")

        assert info.category == LicenseCategory.UNKNOWN


class TestFunctionExtractor:
    @pytest.mark.asyncio
    async def test_extracts_functions(self, fake_llm):
        fake_llm.enqueue(
            FunctionList(
                functions=[
                    FunctionSignature(name="foo", num_args=0),
                    FunctionSignature(name="bar", num_args=2),
                ]
            )
        )
        extractor = FunctionLLMExtractor(fake_llm)
        result = await extractor.extract("def foo(): ...\ndef bar(a, b): ...")

        assert len(result.functions) == 2
        assert result.functions[0].name == "foo"
        assert result.functions[1].num_args == 2

    @pytest.mark.asyncio
    async def test_empty_functions(self, fake_llm):
        fake_llm.enqueue(FunctionList(functions=[]))
        extractor = FunctionLLMExtractor(fake_llm)
        result = await extractor.extract("x = 1")

        assert len(result.functions) == 0


class TestSmartFunctionExtractor:
    @pytest.mark.asyncio
    async def test_valid_python_uses_ast(self, fake_llm):
        llm_fallback = FunctionLLMExtractor(fake_llm)
        extractor = SmartFunctionExtractor(llm_fallback)

        # Valid Python code — shouldn't call the LLM at all
        code = "def alpha(a, b): pass\n\ndef beta(c): pass\n"
        result = await extractor.extract(code)

        assert len(result.functions) == 2
        assert result.functions[0].name == "alpha"
        assert result.functions[0].num_args == 2
        assert result.functions[1].name == "beta"
        assert result.functions[1].num_args == 1

        # Verify LLM was NOT called
        assert len(fake_llm.prompts) == 0

    @pytest.mark.asyncio
    async def test_invalid_python_falls_back_to_llm(self, fake_llm):
        fake_llm.enqueue(FunctionList(functions=[FunctionSignature(name="js_func", num_args=1)]))
        llm_fallback = FunctionLLMExtractor(fake_llm)
        extractor = SmartFunctionExtractor(llm_fallback)

        # Invalid Python code (JS) — should trigger SyntaxError and fallback
        code = "function js_func(x) { console.log(x); }"
        result = await extractor.extract(code)

        assert len(result.functions) == 1
        assert result.functions[0].name == "js_func"

        # Verify LLM WAS called
        assert len(fake_llm.prompts) == 1
