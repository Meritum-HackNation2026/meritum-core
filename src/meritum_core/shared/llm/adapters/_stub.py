"""Stub LLM: deterministic answers from a fixture, no keys and no network.

Features:
    US-WDR-02, F-30, ADR-11
"""

from collections.abc import Mapping

from pydantic import BaseModel, JsonValue, TypeAdapter, ValidationError

from meritum_core.shared.llm.constants import STUB_REGION
from meritum_core.shared.llm.errors import ProviderUnavailableError
from meritum_core.shared.llm.ports import (
    LlmResult,
    LlmToolResult,
    LlmUsage,
    Prompt,
    Tool,
    ToolCall,
)
from meritum_core.shared.llm.settings import LlmProvider


class StubLlm:
    """Answers each output model with its fixture, whatever the prompt.

    For ``complete_with_tools``, ``<Name>.tool_calls`` holds rounds of calls: each
    call returns the next round, then the ``<Name>`` answer once they run out.

    Args:
        fixtures: Answer per output model class name, as JSON.

    Features:
        US-WDR-02, F-30, ADR-11
    """

    def __init__(self, fixtures: Mapping[str, JsonValue]) -> None:
        self._fixtures = dict(fixtures)
        self._rounds: dict[str, int] = {}

    async def complete[T: BaseModel](
        self,
        prompt: Prompt,  # ruff: ignore[unused-method-argument]  # the stub answers by output type only
        output: type[T],
    ) -> LlmResult[T]:
        """Return the fixture for ``output`` with zero token usage.

        Args:
            prompt: Ignored.
            output: The model to validate the fixture against.

        Returns:
            The fixture as ``output``.

        Raises:
            ProviderUnavailableError: No valid fixture for ``output``.
        """
        name = output.__name__
        if name not in self._fixtures:
            msg = f"stub has no fixture for {name}"
            raise ProviderUnavailableError(msg)
        try:
            answer = output.model_validate(self._fixtures[name])
        except ValidationError as exc:
            msg = f"stub fixture for {name} is invalid"
            raise ProviderUnavailableError(msg) from exc
        return LlmResult[T](output=answer, usage=_usage())

    async def complete_with_tools[T: BaseModel](
        self, prompt: Prompt, output: type[T], tools: tuple[Tool, ...]
    ) -> LlmToolResult[T]:
        """Return the next scripted round of calls, or the answer when none is left.

        Args:
            prompt: Ignored.
            output: The model the final answer validates against.
            tools: The tools offered; a scripted call to another one fails.

        Returns:
            The round's calls, or the ``output`` fixture.

        Raises:
            ProviderUnavailableError: An invalid fixture, no answer fixture,
                or a call to a tool that was not offered.
        """
        key = f"{output.__name__}.tool_calls"
        index = self._rounds.get(key, 0)
        try:
            rounds = TypeAdapter(list[tuple[ToolCall, ...]]).validate_python(
                self._fixtures.get(key, [])
            )
        except ValidationError as exc:
            msg = f"stub fixture for {key} is invalid"
            raise ProviderUnavailableError(msg) from exc
        if index >= len(rounds):
            answer = await self.complete(prompt, output)
            return LlmToolResult[T](output=answer.output, usage=_usage())
        offered = {t.name for t in tools}
        if unknown := [c.name for c in rounds[index] if c.name not in offered]:
            msg = f"stub calls tools it was not given: {', '.join(unknown)}"
            raise ProviderUnavailableError(msg)
        self._rounds[key] = index + 1
        return LlmToolResult[T](output=None, calls=rounds[index], usage=_usage())


def _usage() -> LlmUsage:
    return LlmUsage(
        provider=LlmProvider.STUB,
        model=LlmProvider.STUB,
        region=STUB_REGION,
        input_tokens=0,
        output_tokens=0,
        cost_usd=0.0,
    )
