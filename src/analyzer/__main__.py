"""Composition root — wires all dependencies and runs the pipeline."""

import asyncio
import sys

from analyzer.config import Settings
from analyzer.extractors.function_extractor import (
    FunctionLLMExtractor,
    SmartFunctionExtractor,
)
from analyzer.extractors.license_extractor import LicenseLLMExtractor
from analyzer.llm.factory import build_llm_client
from analyzer.persistence.json_writer import JSONResultWriter
from analyzer.pipeline import AnalysisPipeline
from analyzer.strategies.registry import strategy_for
from analyzer.transformers.rust_rewriter import RustLLMRewriter


async def main() -> None:
    settings = Settings()  # type: ignore[call-arg]

    llm = build_llm_client(settings)

    license_extractor = LicenseLLMExtractor(llm)
    # Wrap LLM extractor inside the smart AST-based extractor
    function_extractor = SmartFunctionExtractor(fallback=FunctionLLMExtractor(llm))
    rust_rewriter = RustLLMRewriter(llm)

    def resolve_strategy(license_type: str):
        return strategy_for(
            license_type,
            function_extractor=function_extractor,
            rust_rewriter=rust_rewriter,
        )

    writer = JSONResultWriter(output_dir=settings.output_dir)

    pipeline = AnalysisPipeline(
        data_dir=settings.data_dir,
        license_extractor=license_extractor,
        resolve_strategy=resolve_strategy,
        writer=writer,
    )

    await pipeline.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(130)
