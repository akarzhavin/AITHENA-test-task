import logging
from typing import Any, TypeVar

from pydantic import BaseModel
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from analyzer.llm.protocol import LLMClient

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class ResilientLLMClient:
    """Wraps an LLMClient and adds automatic retries with exponential backoff using Tenacity."""

    def __init__(self, base_client: LLMClient, max_retries: int = 2, wait_strategy=None) -> None:
        self._base_client = base_client
        self._retrier = AsyncRetrying(
            stop=stop_after_attempt(max_retries + 1),
            wait=wait_strategy or wait_exponential(multiplier=1, min=2, max=10),
            retry=retry_if_exception_type(Exception),
            before_sleep=self._log_retry,
            reraise=True,
        )

    def _log_retry(self, retry_state) -> None:
        logger.warning(
            f"LLM attempt {retry_state.attempt_number} failed: {retry_state.outcome.exception()}. "
            f"Retrying in {retry_state.next_action.sleep}s..."
        )

    async def astructured_predict(
        self,
        output_cls: type[T],
        messages: list[dict[str, str]],
        **prompt_kwargs: Any,
    ) -> T:
        """Retry structured prediction on failure."""
        async for attempt in self._retrier:
            with attempt:
                return await self._base_client.astructured_predict(
                    output_cls,
                    messages,
                    **prompt_kwargs,
                )
        raise RuntimeError("Unreachable")

    async def apredict(
        self,
        messages: list[dict[str, str]],
        **prompt_kwargs: Any,
    ) -> str:
        """Retry plain-text prediction on failure."""
        async for attempt in self._retrier:
            with attempt:
                return await self._base_client.apredict(
                    messages,
                    **prompt_kwargs,
                )
        raise RuntimeError("Unreachable")

    async def acomplete(self, prompt: str) -> str:
        """Retry plain-text completion on failure."""
        async for attempt in self._retrier:
            with attempt:
                return await self._base_client.acomplete(prompt)
        raise RuntimeError("Unreachable")
