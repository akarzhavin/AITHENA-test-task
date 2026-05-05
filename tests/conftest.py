"""Shared test fixtures and fake LLM client (LlamaIndex-compatible)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, TypeVar

import pytest
from llama_index.core.prompts import ChatPromptTemplate, PromptTemplate
from pydantic import BaseModel

from analyzer.models import (
    LicenseCategory,
    LicenseInfo,
)

T = TypeVar("T", bound=BaseModel)


# ---------------------------------------------------------------------------
# Fake LLM client for deterministic testing
# ---------------------------------------------------------------------------


class FakeLLMClient:
    """A controllable fake that satisfies the LLMClient protocol.

    Supports three response modes matching the real client:
    - ``astructured_predict`` → returns pre-enqueued Pydantic model instances
    - ``apredict``            → returns pre-enqueued plain strings from template
    - ``acomplete``           → returns pre-enqueued plain strings
    """

    def __init__(self, responses: list[Any] | None = None) -> None:
        self._responses: list[Any] = list(responses or [])
        self._call_index = 0
        self.prompts: list[str] = []  # spy on what was sent

    def enqueue(self, *responses: Any) -> None:
        """Add responses to the queue (Pydantic models or strings)."""
        self._responses.extend(responses)

    def _next(self) -> Any:
        if self._call_index >= len(self._responses):
            raise RuntimeError("FakeLLMClient: no more responses queued")
        resp = self._responses[self._call_index]
        self._call_index += 1
        return resp

    async def astructured_predict(
        self,
        output_cls: type[T],
        prompt: PromptTemplate | ChatPromptTemplate,
        **prompt_kwargs,
    ) -> T:
        """Return the next queued Pydantic model instance."""
        formatted = prompt.format(**prompt_kwargs)
        self.prompts.append(formatted)
        resp = self._next()
        if isinstance(resp, output_cls):
            return resp
        # Allow dicts for convenience — auto-validate into the output class
        if isinstance(resp, dict):
            return output_cls.model_validate(resp)
        raise TypeError(
            f"FakeLLMClient: expected {output_cls.__name__} or dict, got {type(resp).__name__}"
        )

    async def apredict(
        self,
        prompt: PromptTemplate | ChatPromptTemplate,
        **prompt_kwargs,
    ) -> str:
        """Return the next queued string."""
        formatted = prompt.format(**prompt_kwargs)
        self.prompts.append(formatted)
        resp = self._next()
        if isinstance(resp, str):
            return resp
        raise TypeError(f"FakeLLMClient: expected str for apredict, got {type(resp).__name__}")

    async def acomplete(self, prompt: str) -> str:
        """Return the next queued string."""
        self.prompts.append(prompt)
        resp = self._next()
        if isinstance(resp, str):
            return resp
        raise TypeError(f"FakeLLMClient: expected str for acomplete, got {type(resp).__name__}")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def fake_llm() -> FakeLLMClient:
    return FakeLLMClient()


@pytest.fixture
def fixtures_dir() -> Path:
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_permissive(fixtures_dir: Path) -> str:
    return (fixtures_dir / "sample_permissive.py").read_text()


@pytest.fixture
def sample_copyleft_few(fixtures_dir: Path) -> str:
    return (fixtures_dir / "sample_copyleft_few.py").read_text()


@pytest.fixture
def sample_copyleft_many(fixtures_dir: Path) -> str:
    return (fixtures_dir / "sample_copyleft_many.py").read_text()


@pytest.fixture
def permissive_license_info() -> LicenseInfo:
    return LicenseInfo(
        copyright_holder="Test Author",
        license_name="MIT",
        category=LicenseCategory.PERMISSIVE,
    )


@pytest.fixture
def copyleft_license_info() -> LicenseInfo:
    return LicenseInfo(
        copyright_holder="Test Author",
        license_name="GPL-3.0",
        category=LicenseCategory.COPYLEFT,
    )
