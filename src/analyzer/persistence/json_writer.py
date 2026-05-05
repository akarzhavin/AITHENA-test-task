"""JSON file writer — persists AnalysisResult as .json files."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from analyzer.models import AnalysisResult

logger = logging.getLogger(__name__)


class JSONResultWriter:
    """Writes each AnalysisResult as a JSON file in *output_dir*.

    Also writes Rust rewrites as separate .rs files alongside the JSON.
    """

    def __init__(self, output_dir: Path) -> None:
        self._output_dir = output_dir

    async def write(self, result: AnalysisResult) -> None:
        self._output_dir.mkdir(parents=True, exist_ok=True)

        # Write main JSON
        stem = Path(result.file).stem
        json_path = self._output_dir / f"{stem}_analysis.json"
        json_path.write_text(
            json.dumps(result.model_dump(exclude_none=True), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        logger.info("  Wrote %s", json_path)

        # Write Rust file separately if present
        if result.rust_rewrite:
            rs_path = self._output_dir / f"{stem}.rs"
            rs_path.write_text(result.rust_rewrite.rust_code, encoding="utf-8")
            logger.info("  Wrote %s", rs_path)
