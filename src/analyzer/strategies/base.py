"""AnalysisStrategy protocol and shared output model."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from pydantic import BaseModel

from analyzer.models import FunctionList, RustRewrite


class StrategyOutput(BaseModel):
    """What a strategy returns — data only, no side effects."""

    total_functions: int | None = None
    functions: FunctionList | None = None
    rust_rewrite: RustRewrite | None = None


@runtime_checkable
class AnalysisStrategy(Protocol):
    """Every strategy must implement this."""

    async def analyse(self, source_code: str, filename: str) -> StrategyOutput:
        """Analyse *source_code* and return structured data."""
        ...
