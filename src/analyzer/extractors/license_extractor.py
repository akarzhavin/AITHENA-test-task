"""License extraction via LLM (LlamaIndex structured prediction)."""

from __future__ import annotations

import logging
from typing import Protocol, runtime_checkable

from analyzer.llm.protocol import LLMClient
from analyzer.models import LicenseInfo
from analyzer.prompts import LICENSE_EXTRACTION_PROMPT

logger = logging.getLogger(__name__)


@runtime_checkable
class LicenseExtractor(Protocol):
    """Protocol for license extraction."""

    async def extract(self, source_code: str) -> LicenseInfo: ...


class LicenseLLMExtractor:
    """Extracts license metadata from source code using LlamaIndex structured prediction."""

    def __init__(self, llm: LLMClient) -> None:
        self._llm = llm

    async def extract(self, source_code: str) -> LicenseInfo:
        return await self._llm.astructured_predict(
            LicenseInfo,
            LICENSE_EXTRACTION_PROMPT,
            source_code=source_code,
        )
