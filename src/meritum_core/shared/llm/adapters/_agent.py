"""Base of the Pydantic AI adapters: one agent run, errors and usage mapped.

Features:
    US-WDR-02, US-OBS-02, F-30, ADR-11, ADR-12
"""

from google.auth.exceptions import GoogleAuthError
from pydantic import BaseModel
from pydantic_ai import Agent, DeferredToolRequests
from pydantic_ai.agent import AgentRunResult
from pydantic_ai.exceptions import ModelAPIError, UnexpectedModelBehavior
from pydantic_ai.models import Model
from pydantic_ai.settings import ModelSettings
from pydantic_ai.tools import ToolDefinition
from pydantic_ai.toolsets import ExternalToolset

from meritum_core.shared.llm.constants import OUTPUT_RETRIES
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

from ._pricing import cost_usd


class AgentLlm:
    """LlmPort on a Pydantic AI model; subclasses build the model.

    Subclasses may override ``_processed_in`` and ``_cost`` when the provider
    reports where it ran the call and what it cost.

    Args:
        model: The provider's Pydantic AI model.
        settings: Model settings (thinking effort, temperature where accepted).
        provider: Provider name reported in usage.
        region: Where the provider processes the data, reported in usage.

    Features:
        US-WDR-02, US-OBS-02, F-30, ADR-11, ADR-12
    """

    def __init__(
        self,
        model: Model,
        settings: ModelSettings,
        *,
        provider: LlmProvider,
        region: str,
    ) -> None:
        self._model = model
        self._settings = settings
        self._provider = provider
        self._region = region

    async def complete[T: BaseModel](
        self, prompt: Prompt, output: type[T]
    ) -> LlmResult[T]:
        """Ask the model with instructions as system text and data as user parts.

        Args:
            prompt: Instructions and data, kept apart.
            output: The model the answer must validate against.

        Returns:
            The validated answer, token usage and cost.

        Raises:
            ProviderUnavailableError: The provider failed or refused the
                credentials after the configured retries, or the answer did not
                validate after ``OUTPUT_RETRIES`` re-asks.
        """
        agent = Agent(
            self._model,
            output_type=output,
            instructions=prompt.instructions,
            retries=OUTPUT_RETRIES,
            model_settings=self._settings,
        )
        try:
            result = await agent.run(list(prompt.data))
        except (ModelAPIError, UnexpectedModelBehavior, GoogleAuthError) as exc:
            raise ProviderUnavailableError(self._failed()) from exc
        return LlmResult[T](output=result.output, usage=self._usage(result))

    async def complete_with_tools[T: BaseModel](
        self, prompt: Prompt, output: type[T], tools: tuple[Tool, ...]
    ) -> LlmToolResult[T]:
        """Ask the model with external tools; the run stops at the first tool calls.

        Args:
            prompt: Instructions and data, kept apart.
            output: The model the final answer must validate against.
            tools: Tools the model may call; the caller runs them.

        Returns:
            The answer, or the calls with no answer, and the usage.

        Raises:
            ProviderUnavailableError: As in ``complete``.
        """
        toolset = ExternalToolset(
            [
                ToolDefinition(
                    name=t.name,
                    description=t.description,
                    parameters_json_schema=t.parameters,
                )
                for t in tools
            ]
        )
        agent = Agent(
            self._model,
            output_type=[output, DeferredToolRequests],
            toolsets=[toolset],
            instructions=prompt.instructions,
            retries=OUTPUT_RETRIES,
            model_settings=self._settings,
        )
        try:
            result = await agent.run(list(prompt.data))
        except (ModelAPIError, UnexpectedModelBehavior, GoogleAuthError) as exc:
            raise ProviderUnavailableError(self._failed()) from exc
        usage = self._usage(result)
        if not isinstance(result.output, DeferredToolRequests):
            return LlmToolResult[T](output=result.output, usage=usage)
        calls = tuple(
            ToolCall(id=c.tool_call_id, name=c.tool_name, args=c.args_as_dict())
            for c in result.output.calls
        )
        return LlmToolResult[T](output=None, calls=calls, usage=usage)

    def _failed(self) -> str:
        return f"{self._provider} {self._model.model_name} failed after retries"

    def _usage(self, result: AgentRunResult[object]) -> LlmUsage:
        usage = result.usage
        return LlmUsage(
            provider=self._provider,
            model=self._model.model_name,
            region=self._processed_in(result),
            input_tokens=usage.input_tokens,
            output_tokens=usage.output_tokens,
            cost_usd=self._cost(result),
        )

    def _processed_in(
        self,
        result: AgentRunResult[object],  # ruff: ignore[unused-method-argument]  # used by overrides
    ) -> str:
        return self._region

    def _cost(self, result: AgentRunResult[object]) -> float:
        usage = result.usage
        return cost_usd(self._model.model_name, usage.input_tokens, usage.output_tokens)
