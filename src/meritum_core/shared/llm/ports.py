"""The LLM port: structured output with token usage, prompt data kept apart.

Features:
    US-WDR-02, F-30, ADR-11
"""

from typing import Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field, JsonValue


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
    """One call's provider, model, region, tokens and cost, for ``ModelUsage``.

    The fields match ``ModelUsage``, so ``ModelUsage(**usage.model_dump())`` works.

    Attributes:
        provider: Provider name from settings (``openrouter``, ``vertex``, ``stub``).
        model: The model ID from settings (``MERITUM_LLM_MODEL``).
        region: Where the data was processed.
        input_tokens: Prompt tokens.
        output_tokens: Answer tokens, thinking included.
        cost_usd: The call's cost in US dollars; 0 when the provider is free (stub).

    Features:
        US-WDR-02, US-OBS-02, F-30, ADR-11, ADR-14
    """

    model_config = ConfigDict(frozen=True)

    provider: str
    model: str
    region: str
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    cost_usd: float = Field(default=0.0, ge=0)


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


class Tool(BaseModel):
    """A tool the model may call; the caller runs it, never the adapter.

    Attributes:
        name: Tool name the model calls it by.
        description: What the tool does, written by Meritum.
        parameters: JSON Schema of the arguments (an ``object`` schema).

    Features:
        US-WDR-02, F-30, ADR-11
    """

    model_config = ConfigDict(frozen=True)

    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    parameters: dict[str, JsonValue]


class ToolCall(BaseModel):
    """One call the model asked for, to be run by the caller.

    Attributes:
        id: The provider's call ID, to tie the result to the call.
        name: The called tool's name.
        args: Arguments as the model sent them; validate before use.

    Features:
        US-WDR-02, F-30, ADR-11
    """

    model_config = ConfigDict(frozen=True)

    id: str
    name: str
    args: dict[str, JsonValue]


class LlmToolResult[T: BaseModel](BaseModel):
    """Either the final answer or the tool calls the model wants first.

    Exactly one is set: ``output`` when ``calls`` is empty, ``None`` otherwise.

    Attributes:
        output: The validated answer, or None when the model called tools.
        calls: Tool calls to run; their results go back as ``Prompt.data``.
        usage: Provider, model, region and tokens of the call.

    Features:
        US-WDR-02, F-30, ADR-11
    """

    model_config = ConfigDict(frozen=True)

    output: T | None
    calls: tuple[ToolCall, ...] = ()
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

    async def complete_with_tools[T: BaseModel](
        self, prompt: Prompt, output: type[T], tools: tuple[Tool, ...]
    ) -> LlmToolResult[T]:
        """Return the answer as ``output``, or the tool calls the model asks for.

        The caller runs the calls and asks again with their results in
        ``prompt.data`` (tool output is data, ADR-12).

        Args:
            prompt: Instructions and data, kept apart.
            output: Pydantic model the final answer must validate against.
            tools: Tools the model may call.

        Returns:
            The answer or the calls, with the call's usage.

        Raises:
            ProviderUnavailableError: The provider failed after retries.
        """
        ...
