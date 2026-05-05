"""Unit tests for analysis strategies (LlamaIndex-based)."""

import pytest

from analyzer.extractors.function_extractor import FunctionLLMExtractor
from analyzer.models import FunctionList, FunctionSignature
from analyzer.strategies.copyleft import CopyleftStrategy
from analyzer.strategies.permissive import PermissiveStrategy
from analyzer.strategies.registry import strategy_for
from analyzer.transformers.rust_rewriter import RustLLMRewriter


class TestPermissiveStrategy:
    @pytest.mark.asyncio
    async def test_always_extracts_functions(self, fake_llm, sample_permissive):
        """Test that PermissiveStrategy always extracts function signatures regardless of count."""
        fake_llm.enqueue(
            FunctionList(
                functions=[
                    FunctionSignature(name="greet", num_args=1),
                    FunctionSignature(name="add", num_args=2),
                    FunctionSignature(name="multiply", num_args=3),
                ]
            )
        )
        strategy = PermissiveStrategy(function_extractor=FunctionLLMExtractor(fake_llm))
        result = await strategy.analyse(sample_permissive, "sample.py")

        assert result.functions is not None
        assert len(result.functions.functions) == 3
        assert result.rust_rewrite is None


class TestCopyleftStrategy:
    def _get_strategy(self, fake_llm, threshold=2):
        return CopyleftStrategy(
            function_extractor=FunctionLLMExtractor(fake_llm),
            rust_rewriter=RustLLMRewriter(fake_llm),
            function_threshold=threshold,
        )

    @pytest.mark.asyncio
    async def test_many_functions_extracts(self, fake_llm, sample_copyleft_many):
        """When function count > threshold, extract signatures."""
        fake_llm.enqueue(
            FunctionList(
                functions=[
                    FunctionSignature(name="alpha", num_args=0),
                    FunctionSignature(name="beta", num_args=1),
                    FunctionSignature(name="gamma", num_args=2),
                ]
            )
        )
        strategy = self._get_strategy(fake_llm, threshold=2)
        result = await strategy.analyse(sample_copyleft_many, "many.py")

        assert result.functions is not None
        assert len(result.functions.functions) == 3
        assert result.rust_rewrite is None

    @pytest.mark.asyncio
    async def test_few_functions_rewrites_rust(self, fake_llm, sample_copyleft_few):
        """When function count <= threshold, rewrite to Rust."""
        fake_llm.enqueue('fn only_one() {\n    println!("I am alone");\n}')
        strategy = self._get_strategy(fake_llm, threshold=2)
        result = await strategy.analyse(sample_copyleft_few, "few.py")

        assert result.rust_rewrite is not None
        assert "fn only_one" in result.rust_rewrite.rust_code
        assert result.functions is None


class TestRegistry:
    @pytest.mark.parametrize(
        "category, expected_class",
        [
            ("permissive", PermissiveStrategy),
            ("copyleft", CopyleftStrategy),
            ("unknown_val", PermissiveStrategy),
        ],
    )
    def test_registry_resolution(self, fake_llm, category, expected_class):
        """Verify that the registry resolves the correct strategy for each category."""
        s = strategy_for(
            category,
            function_extractor=FunctionLLMExtractor(fake_llm),
            rust_rewriter=RustLLMRewriter(fake_llm),
        )
        assert isinstance(s, expected_class)
