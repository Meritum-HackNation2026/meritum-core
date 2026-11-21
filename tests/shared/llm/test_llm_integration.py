"""Real provider call: local only (`uv run pytest -m integration`), never in CI.

Set MERITUM_LLM_PROVIDER (vertex or openrouter) and the other
MERITUM_LLM_* settings; Vertex AI needs Application Default Credentials and
OpenRouter needs OPENROUTER_API_KEY in the environment.
"""

import asyncio
import os

import httpx2
import pytest
from pydantic import BaseModel

from meritum_core.shared.llm import LlmResult, LlmSettings, Prompt, build_llm

TIMEOUT_SECONDS = 120


async def _ask[T: BaseModel](settings: LlmSettings, output: type[T]) -> LlmResult[T]:
    prompt = Prompt(
        instructions="Wypisz twierdzenia z tekstu jako listę zdań.",
        data=("Sejm przyjął ustawę o ochronie zwierząt.",),
    )
    async with httpx2.AsyncClient(
        timeout=TIMEOUT_SECONDS
    ) as client:  # closed: no leaked sockets
        return await build_llm(settings, http_client=client).complete(prompt, output)


@pytest.mark.integration
def test_real_provider_answers_with_structured_output_usage_and_cost(
    claim_list: type[BaseModel],
) -> None:
    if os.environ.get("MERITUM_LLM_PROVIDER", "stub") == "stub":
        pytest.skip("set MERITUM_LLM_PROVIDER and the MERITUM_LLM_* settings")
    settings = LlmSettings()
    result = asyncio.run(_ask(settings, claim_list))
    assert isinstance(result.output, claim_list)
    usage = result.usage
    assert (usage.provider, usage.model) == (settings.provider, settings.model)
    assert usage.region.startswith(settings.region)  # OpenRouter adds the upstream
    assert usage.input_tokens > 0
    assert usage.cost_usd > 0
