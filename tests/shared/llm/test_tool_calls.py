"""Port contract for tool calls: definitions in, calls out, on stub and recorded replies."""

import asyncio
import json
from collections.abc import Callable

import httpx2
import pytest
from pydantic import BaseModel, JsonValue, TypeAdapter

from meritum_core.shared.llm import (
    LlmPort,
    LlmSettings,
    Prompt,
    ProviderUnavailableError,
    Tool,
    ToolCall,
)
from meritum_core.shared.llm.adapters import StubLlm

from .conftest import ANSWER

PROMPT = Prompt(instructions="Sprawdź twierdzenie.", data=("Sejm przyjął ustawę.",))
SEARCH = Tool(
    name="search_corpus",
    description="Szukaj w korpusie źródeł.",
    parameters={
        "type": "object",
        "properties": {"query": {"type": "string"}},
        "required": ["query"],
    },
)
CALL = ToolCall(
    id="call_search_1",
    name="search_corpus",
    args={"query": "ustawa o ochronie zwierząt"},
)


def _json(fixtures: object) -> dict[str, JsonValue]:
    return TypeAdapter(dict[str, JsonValue]).validate_python(fixtures)


type Sent = list[httpx2.Request]
type RecordedFactory = Callable[[LlmSettings, str, int], tuple[LlmPort, Sent]]


def test_stub_returns_scripted_tool_calls_then_the_answer(
    claim_list: type[BaseModel],
) -> None:
    fixtures = _json(
        {
            "ClaimList": ANSWER,
            "ClaimList.tool_calls": [[CALL.model_dump(mode="json")]],
        }
    )
    llm = StubLlm(fixtures)
    first = asyncio.run(llm.complete_with_tools(PROMPT, claim_list, (SEARCH,)))
    assert (first.output, first.calls) == (None, (CALL,))
    second = asyncio.run(llm.complete_with_tools(PROMPT, claim_list, (SEARCH,)))
    assert second.output == claim_list.model_validate(ANSWER)
    assert second.calls == ()
    assert second.usage.provider == "stub"


def test_stub_refuses_a_call_to_a_tool_it_was_not_given(
    claim_list: type[BaseModel],
) -> None:
    fixtures = _json({"ClaimList.tool_calls": [[CALL.model_dump(mode="json")]]})
    llm = StubLlm(fixtures)
    with pytest.raises(ProviderUnavailableError, match="search_corpus"):
        asyncio.run(llm.complete_with_tools(PROMPT, claim_list, ()))


def test_openrouter_sends_the_tool_and_returns_its_call(
    recorded_llm: RecordedFactory,
    claim_list: type[BaseModel],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-test")  # fake key, no network
    settings = LlmSettings(
        provider="openrouter", model="openai/gpt-6.1-terra", region="global", retries=1
    )
    llm, sent = recorded_llm(settings, "openrouter-terra-tool", 200)
    result = asyncio.run(llm.complete_with_tools(PROMPT, claim_list, (SEARCH,)))
    assert (result.output, result.calls) == (None, (CALL,))
    assert result.usage.cost_usd == pytest.approx(0.000238)
    tools = {t["function"]["name"]: t for t in json.loads(sent[0].content)["tools"]}
    assert tools["search_corpus"]["function"]["parameters"]["required"] == ["query"]


def test_vertex_returns_the_final_answer_when_no_tool_is_called(
    recorded_vertex: Callable[[LlmSettings, int], tuple[LlmPort, Sent]],
    vertex_settings: LlmSettings,
    claim_list: type[BaseModel],
) -> None:
    llm, sent = recorded_vertex(vertex_settings, 200)
    result = asyncio.run(llm.complete_with_tools(PROMPT, claim_list, (SEARCH,)))
    assert result.output == claim_list.model_validate(ANSWER)
    assert result.calls == ()
    declared = json.loads(sent[0].content)["tools"][0]["functionDeclarations"]
    assert "search_corpus" in {d["name"] for d in declared}
