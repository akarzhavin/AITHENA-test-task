"""Unit tests for ResilientLLMClient decorator."""

import pytest
from llama_index.core.prompts import PromptTemplate

from analyzer.llm.resilient_client import ResilientLLMClient
from analyzer.models import LicenseCategory, LicenseInfo


class ActionableFake:
    """A fake LLM client that performs a sequence of pre-defined actions."""

    def __init__(self, actions):
        self.actions = list(actions)
        self.calls = 0

    async def _perform(self, default_value):
        self.calls += 1
        action = self.actions.pop(0)
        if isinstance(action, Exception):
            raise action
        return action or default_value

    async def astructured_predict(self, *args, **kwargs):
        return await self._perform(
            LicenseInfo(copyright_holder="X", license_name="Y", category=LicenseCategory.PERMISSIVE)
        )

    async def acomplete(self, *args, **kwargs):
        return await self._perform("ok")

    async def apredict(self, *args, **kwargs):
        return await self._perform("ok")


class TestResilientLLMClient:
    @pytest.mark.asyncio
    async def test_success_on_first_attempt(self):
        """Test that it returns result immediately if base client succeeds."""
        fake = ActionableFake([None])
        client = ResilientLLMClient(fake, max_retries=2)

        await client.acomplete("test")
        assert fake.calls == 1

    @pytest.mark.asyncio
    async def test_retry_on_transient_failure(self):
        """Test that it retries and eventually succeeds if failures are transient."""
        fake = ActionableFake([RuntimeError("Fail"), "Success"])
        client = ResilientLLMClient(fake, max_retries=2)

        result = await client.acomplete("test")
        assert result == "Success"
        assert fake.calls == 2

    @pytest.mark.asyncio
    async def test_exhausts_retries_and_raises(self):
        """Test that it raises the last error after all retries are exhausted."""
        fake = ActionableFake([RuntimeError("E1"), RuntimeError("E2"), RuntimeError("E3")])
        client = ResilientLLMClient(fake, max_retries=2)

        with pytest.raises(RuntimeError, match="E3"):
            await client.acomplete("test")
        assert fake.calls == 3

    @pytest.mark.asyncio
    async def test_structured_predict_retries(self):
        """Test that structured prediction also supports retries."""
        expected = LicenseInfo(
            copyright_holder="Alice", license_name="MIT", category=LicenseCategory.PERMISSIVE
        )
        fake = ActionableFake([RuntimeError("Fail"), expected])
        client = ResilientLLMClient(fake, max_retries=2)

        result = await client.astructured_predict(LicenseInfo, PromptTemplate("test"))
        assert result == expected
        assert fake.calls == 2
