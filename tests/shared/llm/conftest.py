"""Shared fixtures for the LLM port tests: an output model and a recorded Vertex reply."""

import json
from collections.abc import Callable
from pathlib import Path

import httpx2
import pytest
from google.oauth2.credentials import Credentials
from pydantic import BaseModel

from meritum_core.shared.llm import LlmSettings
from meritum_core.shared.llm.adapters import VertexLlm

ANSWER = {"claims": ["Sejm przyjął ustawę."]}
RECORDED_REPLY = {
    "candidates": [
        {
            "content": {
                "role": "model",
                "parts": [{"functionCall": {"name": "final_result", "args": ANSWER}}],
            },
            "finishReason": "STOP",
        }
    ],
    "usageMetadata": {
        "promptTokenCount": 42,
        "candidatesTokenCount": 7,
        "totalTokenCount": 49,
    },
}
UNAVAILABLE = {
    "error": {"code": 503, "message": "unavailable", "status": "UNAVAILABLE"}
}

type Sent = list[httpx2.Request]
type VertexFactory = Callable[[LlmSettings, int], tuple[VertexLlm, Sent]]


class ClaimList(BaseModel):
    """Stand-in for the claim extraction output; the real one lives in `checks`."""

    claims: list[str]


@pytest.fixture
def claim_list() -> type[ClaimList]:
    return ClaimList


@pytest.fixture
def vertex_settings() -> LlmSettings:
    return LlmSettings(
        provider="vertex",
        model="gemini-2.5-flash-001",
        region="europe-west4",
        project="meritum-test",
        retries=1,
    )


@pytest.fixture
def stub_fixtures(tmp_path: Path) -> Path:
    path = tmp_path / "llm-stub.json"
    path.write_text(json.dumps({"ClaimList": ANSWER}), encoding="utf-8")
    return path


@pytest.fixture
def recorded_vertex() -> VertexFactory:
    """Build a VertexLlm whose HTTP calls get the recorded reply, or an error status."""

    def build(settings: LlmSettings, status: int) -> tuple[VertexLlm, Sent]:
        sent: Sent = []

        def reply(request: httpx2.Request) -> httpx2.Response:
            sent.append(request)
            body = RECORDED_REPLY if status == httpx2.codes.OK else UNAVAILABLE
            return httpx2.Response(status, json=body)

        client = httpx2.AsyncClient(transport=httpx2.MockTransport(reply), timeout=60)
        token = Credentials(token="recorded")  # ruff: ignore[hardcoded-password-func-arg]  # fake token, no network
        return VertexLlm(settings, credentials=token, http_client=client), sent

    return build
