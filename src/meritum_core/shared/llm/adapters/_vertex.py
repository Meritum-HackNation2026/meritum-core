"""Vertex AI adapter: Pydantic AI over Google Cloud, temperature 0, pinned model.

Features:
    US-WDR-02, F-30, ADR-11, ADR-14, ADR-19
"""

from google.auth.credentials import Credentials
from google.genai.types import HttpRetryOptions
from httpx2 import AsyncClient
from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.exceptions import ModelAPIError, UnexpectedModelBehavior
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google_cloud import GoogleCloudProvider
from pydantic_ai.settings import ModelSettings

from meritum_core.shared.llm.constants import TEMPERATURE
from meritum_core.shared.llm.errors import ProviderUnavailableError
from meritum_core.shared.llm.ports import LlmResult, LlmUsage, Prompt
from meritum_core.shared.llm.settings import LlmProvider, LlmSettings


class VertexLlm:
    """LlmPort on a Vertex AI model named only in settings.

    Args:
        settings: Validated vertex settings (model and EU region are set).
        credentials: Google credentials; Application Default Credentials when None.
        http_client: HTTP client to use; tests pass one with a recorded reply.

    Features:
        US-WDR-02, F-30, ADR-11, ADR-14, ADR-19
    """

    def __init__(
        self,
        settings: LlmSettings,
        *,
        credentials: Credentials | None = None,
        http_client: AsyncClient | None = None,
    ) -> None:
        self._model_name = str(settings.model)
        self._region = str(settings.region)
        self._retries = settings.retries
        provider = GoogleCloudProvider(
            project=settings.project,
            location=self._region,
            credentials=credentials,
            http_client=http_client,
            retry_options=HttpRetryOptions(attempts=settings.retries),
        )
        self._model = GoogleModel(
            self._model_name,
            provider=provider,
            settings=ModelSettings(temperature=TEMPERATURE),
        )

    async def complete[T: BaseModel](
        self, prompt: Prompt, output: type[T]
    ) -> LlmResult[T]:
        """Ask the model with instructions as system text and data as user parts.

        Args:
            prompt: Instructions and data, kept apart.
            output: The model the answer must validate against.

        Returns:
            The validated answer and token usage.

        Raises:
            ProviderUnavailableError: The provider failed, or the answer did not
                validate, after the configured retries.
        """
        agent = Agent(
            self._model,
            output_type=output,
            instructions=prompt.instructions,
            retries=self._retries - 1,  # settings count attempts, Pydantic AI retries
        )
        try:
            result = await agent.run(list(prompt.data))
        except (ModelAPIError, UnexpectedModelBehavior) as exc:
            msg = f"{LlmProvider.VERTEX} {self._model_name} failed after retries"
            raise ProviderUnavailableError(msg) from exc
        usage = result.usage
        return LlmResult[T](
            output=result.output,
            usage=LlmUsage(
                provider=LlmProvider.VERTEX,
                model=self._model_name,
                region=self._region,
                input_tokens=usage.input_tokens,
                output_tokens=usage.output_tokens,
            ),
        )
