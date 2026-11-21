"""build_llm picks the adapter from settings; the stub answers from its fixture file."""

import asyncio
from pathlib import Path

import pytest
from pydantic import BaseModel, ValidationError

from meritum_core.shared.llm import (
    LlmPort,
    LlmSettings,
    Prompt,
    ProviderUnavailableError,
    build_llm,
)

PROMPT = Prompt(instructions="Wypisz twierdzenia.", data=("Sejm przyjął ustawę.",))


def test_stub_returns_the_fixture_without_provider_keys(
    stub_fixtures: Path, claim_list: type[BaseModel], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("MERITUM_LLM_PROVIDER", "stub")
    monkeypatch.setenv("MERITUM_LLM_STUB_FIXTURES", str(stub_fixtures))
    result = asyncio.run(build_llm(LlmSettings()).complete(PROMPT, claim_list))
    assert result.output == claim_list.model_validate(
        {"claims": ["Sejm przyjął ustawę."]}
    )
    usage = result.usage
    assert (usage.provider, usage.input_tokens, usage.output_tokens) == ("stub", 0, 0)


def test_stub_without_a_fixture_for_the_type_fails_as_provider_unavailable(
    claim_list: type[BaseModel],
) -> None:
    llm = build_llm(LlmSettings(provider="stub"))
    with pytest.raises(ProviderUnavailableError, match="ClaimList"):
        asyncio.run(llm.complete(PROMPT, claim_list))


def test_stub_with_an_invalid_fixture_fails_as_provider_unavailable(
    tmp_path: Path, claim_list: type[BaseModel]
) -> None:
    path = tmp_path / "bad.json"
    path.write_text('{"ClaimList": {"claims": 3}}', encoding="utf-8")
    llm = build_llm(LlmSettings(provider="stub", stub_fixtures=path))
    with pytest.raises(ProviderUnavailableError, match="invalid"):
        asyncio.run(llm.complete(PROMPT, claim_list))


def test_default_provider_is_the_stub(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MERITUM_LLM_PROVIDER", raising=False)
    settings = LlmSettings()
    assert settings.provider == "stub"
    assert type(build_llm(settings)).__name__ == "StubLlm"


def test_factory_builds_vertex_from_settings(vertex_settings: LlmSettings) -> None:
    llm = build_llm(vertex_settings)
    assert isinstance(llm, LlmPort)
    assert type(llm).__name__ == "VertexLlm"


@pytest.mark.parametrize(
    "overrides",
    [
        {"model": None},
        {"region": None},
        {"region": "us-central1"},
        {"region": "europe-west2"},  # London: Europe, not the EU
        {"region": "europe-west6"},  # Zurich
    ],
)
def test_vertex_needs_a_pinned_model_and_an_eu_region(
    vertex_settings: LlmSettings, overrides: dict[str, object]
) -> None:
    with pytest.raises(ValidationError):
        LlmSettings.model_validate(vertex_settings.model_dump() | overrides)


def test_eu_multi_region_is_accepted(vertex_settings: LlmSettings) -> None:
    settings = LlmSettings.model_validate(
        vertex_settings.model_dump() | {"region": "eu"}
    )
    assert settings.region == "eu"


def test_stub_fixture_file_that_is_not_an_object_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "list.json"
    path.write_text('["ClaimList"]', encoding="utf-8")
    with pytest.raises(ValidationError):
        build_llm(LlmSettings(provider="stub", stub_fixtures=path))
