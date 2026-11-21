"""Real Vertex AI call: local only (`uv run pytest -m integration`), never in CI.

Needs Application Default Credentials and MERITUM_LLM_PROVIDER=vertex,
MERITUM_LLM_MODEL, MERITUM_LLM_REGION (and MERITUM_LLM_PROJECT) in the environment.
"""

import asyncio

import pytest
from pydantic import BaseModel

from meritum_core.shared.llm import LlmSettings, Prompt, build_llm


@pytest.mark.integration
def test_real_vertex_answers_with_structured_output_and_usage(
    claim_list: type[BaseModel],
) -> None:
    settings = LlmSettings()
    if settings.provider != "vertex":
        pytest.skip("set MERITUM_LLM_PROVIDER=vertex and the MERITUM_LLM_* settings")
    prompt = Prompt(
        instructions="Wypisz twierdzenia z tekstu jako listę zdań.",
        data=("Sejm przyjął ustawę o ochronie zwierząt.",),
    )
    result = asyncio.run(build_llm(settings).complete(prompt, claim_list))
    assert isinstance(result.output, claim_list)
    assert result.usage.model == settings.model
    assert result.usage.input_tokens > 0
