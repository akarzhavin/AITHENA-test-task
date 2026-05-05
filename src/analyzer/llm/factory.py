"""Factory to build an LLMClient from application Settings."""

from __future__ import annotations

from analyzer.config import Settings
from analyzer.llm.openai_client import OpenAIClient
from analyzer.llm.protocol import LLMClient


def build_llm_client(settings: Settings) -> LLMClient:
    """Construct the appropriate LLM client from config."""
    return OpenAIClient(
        api_key=settings.openai_api_key,
        model=settings.openai_model,
        temperature=settings.openai_temperature,
        max_tokens=settings.openai_max_tokens,
    )
