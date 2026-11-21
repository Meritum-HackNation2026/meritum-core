"""The LLM port: structured output with token usage, prompt data kept apart.

Features:
    US-WDR-02, F-30, ADR-11
"""

from typing import Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field


class Prompt(BaseModel):
    """What the model gets: instructions apart from the data they work on.

    User and source text goes only in ``data``; adapters send it as user content,
    never mixed into the instructions (ADR-12).

    Attributes:
        instructions: The task, written by Meritum; sent as the system instruction.
        data: User or source text, each item a separate user part, treated as data.

    Features:
        US-WDR-02, F-30, ADR-11, ADR-12
    """

    model_config = ConfigDict(frozen=True)

    instructions: str = Field(min_length=1)
    data: tuple[str, ...] = ()


class LlmUsage(BaseModel):
    """One call's provider, model, region and tokens, for ``ModelUsage``.

    Attributes:
        provider: The provider name from settings (``vertex``, ``stub``).
        model: The pinned model version that answered.
        region: Where the data was processed.
        input_tokens: Prompt tokens.
        output_tokens: Answer tokens.

    Features:
        US-WDR-02, F-30, ADR-11, ADR-14
    """

    model_config = ConfigDict(frozen=True)

    provider: str
    model: str
    region: str
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)


class LlmResult[T: BaseModel](BaseModel):
    """The validated answer with the usage of the call that produced it.

    Attributes:
        output: The answer, validated against the requested model.
        usage: Provider, model, region and tokens of the call.

    Features:
        US-WDR-02, F-30, ADR-11
    """

    model_config = ConfigDict(frozen=True)

    output: T
    usage: LlmUsage


@runtime_checkable
class LlmPort(Protocol):
    """Structured-output language model; every workflow step calls models through it.

    Features:
        US-WDR-02, F-30, ADR-11, ADR-19
    """

    async def complete[T: BaseModel](
        self, prompt: Prompt, output: type[T]
    ) -> LlmResult[T]:
        """Return the model's answer parsed into ``output``, with token usage.

        Args:
            prompt: Instructions and data, kept apart.
            output: Pydantic model the answer must validate against.

        Returns:
            The validated answer and the call's usage.

        Raises:
            ProviderUnavailableError: The provider failed after retries.
        """
        ...
