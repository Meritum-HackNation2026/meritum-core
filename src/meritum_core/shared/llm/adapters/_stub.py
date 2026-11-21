"""Stub LLM: deterministic answers from a fixture, no keys and no network.

Features:
    US-WDR-02, F-30, ADR-11
"""

from collections.abc import Mapping

from pydantic import BaseModel, JsonValue, ValidationError

from meritum_core.shared.llm.constants import STUB_REGION
from meritum_core.shared.llm.errors import ProviderUnavailableError
from meritum_core.shared.llm.ports import LlmResult, LlmUsage, Prompt
from meritum_core.shared.llm.settings import LlmProvider


class StubLlm:
    """Answers each output model with its fixture, whatever the prompt.

    Args:
        fixtures: Answer per output model class name, as JSON.

    Features:
        US-WDR-02, F-30, ADR-11
    """

    def __init__(self, fixtures: Mapping[str, JsonValue]) -> None:
        self._fixtures = dict(fixtures)

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
        usage = LlmUsage(
            provider=LlmProvider.STUB,
            model=LlmProvider.STUB,
            region=STUB_REGION,
            input_tokens=0,
            output_tokens=0,
            cost_usd=0.0,
        )
        return LlmResult[T](output=answer, usage=usage)
