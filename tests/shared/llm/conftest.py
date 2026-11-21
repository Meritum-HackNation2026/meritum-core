"""Shared fixtures for the LLM port tests: an output model and recorded replies."""

import json
from collections.abc import Callable
from pathlib import Path

import httpx2
import pytest
from google.oauth2.credentials import Credentials
from pydantic import BaseModel, TypeAdapter

from meritum_core.shared.llm import LlmPort, LlmSettings, build_llm

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

RECORDINGS = Path(__file__).parent / "recordings"

type Sent = list[httpx2.Request]
type VertexFactory = Callable[[LlmSettings, int], tuple[LlmPort, Sent]]
type RecordedFactory = Callable[[LlmSettings, str, int], tuple[LlmPort, Sent]]


def recording(name: str) -> dict[str, object]:
    """A real reply body recorded from the provider (thoughts and ids shortened)."""
    text = (RECORDINGS / f"{name}.json").read_text(encoding="utf-8")
    return TypeAdapter(dict[str, object]).validate_json(text)


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
    """Build Vertex through the factory; its HTTP calls get the recorded reply or an error."""

    def build(settings: LlmSettings, status: int) -> tuple[LlmPort, Sent]:
        sent: Sent = []

        def reply(request: httpx2.Request) -> httpx2.Response:
            sent.append(request)
            body = RECORDED_REPLY if status == httpx2.codes.OK else UNAVAILABLE
            return httpx2.Response(status, json=body)

        client = httpx2.AsyncClient(transport=httpx2.MockTransport(reply), timeout=60)
        token = Credentials(token="recorded")  # ruff: ignore[hardcoded-password-func-arg]  # fake token, no network
        return build_llm(settings, credentials=token, http_client=client), sent

    return build


@pytest.fixture
def recorded_llm() -> RecordedFactory:
    """Build any adapter through the factory; HTTP calls get a recorded reply.

    The reply is ``recordings/<name>.json`` with status 200, or a 503 error body.
    """

    def build(settings: LlmSettings, name: str, status: int) -> tuple[LlmPort, Sent]:
        sent: Sent = []
        body = recording(name) if status == httpx2.codes.OK else UNAVAILABLE

        def reply(request: httpx2.Request) -> httpx2.Response:
            sent.append(request)
            return httpx2.Response(status, json=body)

        client = httpx2.AsyncClient(transport=httpx2.MockTransport(reply), timeout=60)
        token = Credentials(token="recorded")  # ruff: ignore[hardcoded-password-func-arg]  # fake token, no network
        return build_llm(settings, credentials=token, http_client=client), sent

    return build
