"""License extraction via LLM and SPDX identifiers."""

from __future__ import annotations

import logging
import re
from typing import Protocol, runtime_checkable

from analyzer.llm.protocol import LLMClient
from analyzer.models import LicenseCategory, LicenseInfo
from analyzer.extractors.license_registry import SPDX_CATEGORY_MAP
from analyzer.prompts import LICENSE_EXTRACTION_PROMPT

logger = logging.getLogger(__name__)


# Patterns and templates for fast extraction
SPDX_PATTERN = re.compile(r"SPDX-License-Identifier:\s*([A-Za-z0-9\.\-\+]+)", re.IGNORECASE)
COPYRIGHT_PATTERN = re.compile(r"Copyright\s+(?:\([cC]\)\s+)?(?:[0-9]{4}\s+)?(.+)", re.IGNORECASE)
MICRO_SNIPPET_TEMPLATE = "// SPDX-License-Identifier: {license_id}\n// Copyright: {copyright}"


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


class SmartLicenseExtractor:
    """Tries to extract license via SPDX identifiers (fast), falls back to LLM."""

    def __init__(self, fallback: LicenseExtractor, max_lines: int = 50) -> None:
        self._fallback = fallback
        self._max_lines = max_lines

    async def extract(self, source_code: str) -> LicenseInfo:
        head = "\n".join(source_code.splitlines()[: self._max_lines])

        spdx_match = SPDX_PATTERN.search(head)
        copy_match = COPYRIGHT_PATTERN.search(head)

        # We only use the fast path if both license AND author are found.
        # Otherwise, fall back to LLM, as the author might be hidden deeper in the file.
        if spdx_match and copy_match:
            license_id = spdx_match.group(1).strip()
            copyright = copy_match.group(1).split("*/")[0].strip()

            # Normalize for dictionary lookup (e.g. mit -> MIT)
            if cat := SPDX_CATEGORY_MAP.get(license_id.upper()):
                return LicenseInfo(
                    copyright_holder=copyright, license_name=license_id, category=cat
                )

            # If license is rare, use micro-snippet to save tokens
            return await self._fallback.extract(
                MICRO_SNIPPET_TEMPLATE.format(license_id=license_id, copyright=copyright)
            )

        return await self._fallback.extract(source_code)
