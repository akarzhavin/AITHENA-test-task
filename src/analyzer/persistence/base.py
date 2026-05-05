"""ResultWriter protocol — the contract for all output backends."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from analyzer.models import AnalysisResult


@runtime_checkable
class ResultWriter(Protocol):
    """Any persistence backend must implement this."""

    async def write(self, result: AnalysisResult) -> None:
        """Persist a single analysis result."""
        ...
