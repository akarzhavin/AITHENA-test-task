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
        fake_llm.enqueue(
            FunctionList(
                functions=[
                    FunctionSignature(name="greet", num_args=1),
                    FunctionSignature(name="add", num_args=2),
                    FunctionSignature(name="multiply", num_args=3),
                ]
            )
        )
        extractor = FunctionLLMExtractor(fake_llm)
        strategy = PermissiveStrategy(function_extractor=extractor)

        result = await strategy.analyse(sample_permissive, "sample.py")

        assert result.functions is not None
        assert len(result.functions.functions) == 3
        assert result.rust_rewrite is None


class TestCopyleftStrategy:
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
        extractor = FunctionLLMExtractor(fake_llm)
        rewriter = RustLLMRewriter(fake_llm)
        strategy = CopyleftStrategy(
            function_extractor=extractor,
            rust_rewriter=rewriter,
            function_threshold=2,
        )

        result = await strategy.analyse(sample_copyleft_many, "many.py")

        assert result.functions is not None
        assert len(result.functions.functions) == 3
        assert result.rust_rewrite is None

    @pytest.mark.asyncio
    async def test_few_functions_rewrites_rust(self, fake_llm, sample_copyleft_few):
        """When function count ≤ threshold, rewrite to Rust."""
        fake_llm.enqueue('fn only_one() {\n    println!("I am alone");\n}')
        extractor = FunctionLLMExtractor(fake_llm)
        rewriter = RustLLMRewriter(fake_llm)
        strategy = CopyleftStrategy(
            function_extractor=extractor,
            rust_rewriter=rewriter,
            function_threshold=2,
        )

        result = await strategy.analyse(sample_copyleft_few, "few.py")

        assert result.rust_rewrite is not None
        assert "fn only_one" in result.rust_rewrite.rust_code
        assert result.functions is None


class TestRegistry:
    def test_permissive_returns_permissive_strategy(self, fake_llm):
        extractor = FunctionLLMExtractor(fake_llm)
        rewriter = RustLLMRewriter(fake_llm)
        s = strategy_for(
            "permissive",
            function_extractor=extractor,
            rust_rewriter=rewriter,
        )
        assert isinstance(s, PermissiveStrategy)

    def test_copyleft_returns_copyleft_strategy(self, fake_llm):
        extractor = FunctionLLMExtractor(fake_llm)
        rewriter = RustLLMRewriter(fake_llm)
        s = strategy_for(
            "copyleft",
            function_extractor=extractor,
            rust_rewriter=rewriter,
        )
        assert isinstance(s, CopyleftStrategy)

    def test_unknown_defaults_to_permissive(self, fake_llm):
        extractor = FunctionLLMExtractor(fake_llm)
        rewriter = RustLLMRewriter(fake_llm)
        s = strategy_for(
            "banana",
            function_extractor=extractor,
            rust_rewriter=rewriter,
        )
        assert isinstance(s, PermissiveStrategy)
