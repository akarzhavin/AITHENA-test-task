"""OpenAI implementation of LLMClient using the native SDK."""

from __future__ import annotations

import logging
import string
from typing import Any, TypeVar

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam
from pydantic import BaseModel

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class OpenAIClient:
    """Wrapper around the native OpenAI AsyncOpenAI client.

    Implements the LLMClient protocol.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ) -> None:
        self._client = AsyncOpenAI(api_key=api_key)
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens

    async def astructured_predict(
        self,
        output_cls: type[T],
        messages: list[dict[str, str]],
        **prompt_kwargs: Any,
    ) -> T:
        """Structured prediction — returns a validated Pydantic instance."""
        formatted_messages = self._format_messages(messages, **prompt_kwargs)

        logger.debug(f"Calling astructured_predict with model {self._model}")

        completion = await self._client.chat.completions.parse(
            model=self._model,
            messages=formatted_messages,
            response_format=output_cls,
            temperature=self._temperature,
            max_tokens=self._max_tokens,
        )

        message = completion.choices[0].message

        # Handle explicit refusal (safety policy)
        if message.refusal:
            logger.warning(f"Model refused to answer: {message.refusal}")
            raise ValueError(f"Model refused: {message.refusal}")

        if message.parsed is None:
            raise ValueError("Failed to parse structured output from OpenAI response")

        return message.parsed

    async def apredict(
        self,
        messages: list[dict[str, str]],
        **prompt_kwargs: Any,
    ) -> str:
        """Plain-text prediction from message list with formatting."""
        formatted_messages = self._format_messages(messages, **prompt_kwargs)

        logger.debug(f"Calling apredict with model {self._model}")

        response = await self._client.chat.completions.create(
            model=self._model,
            messages=formatted_messages,
            temperature=self._temperature,
            max_tokens=self._max_tokens,
        )
        return response.choices[0].message.content or ""

    async def acomplete(self, prompt: str) -> str:
        """Plain-text completion."""
        logger.debug(f"Calling acomplete with model {self._model}")

        response = await self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": "user", "content": prompt}],
            temperature=self._temperature,
            max_tokens=self._max_tokens,
        )
        return response.choices[0].message.content or ""

    def _format_messages(
        self, messages: list[dict[str, str]], **kwargs: Any
    ) -> list[ChatCompletionMessageParam]:
        """Safely formats messages using string.Template to avoid curly brace conflicts."""
        if not kwargs:
            return messages  # type: ignore[return-value]

        formatted: list[ChatCompletionMessageParam] = []
        for m in messages:
            # Use Template so that curly braces {} in code/JSON inside the prompt
            # don't cause an error
            template = string.Template(m["content"])
            # safe_substitute leaves $var as is if the variable is not provided
            content = template.safe_substitute(**kwargs)
            # We use Any for the message dict to bypass complex TypedDict checks for roles
            msg: Any = {"role": m["role"], "content": content}
            formatted.append(msg)
        return formatted