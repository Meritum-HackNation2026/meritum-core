"""The masking gate: Sensitive Data Protection on recorded replies, the null gate."""

import asyncio
import json
import logging
from collections.abc import Callable
from pathlib import Path

import httpx2
import pytest
from google.oauth2.credentials import Credentials
from pydantic import ValidationError

from meritum_core.security import (
    MaskedText,
    NullPiiGate,
    PiiGatePort,
    PiiGateSettings,
    build_pii_gate,
    mask_personal_data,
)

FIXTURES = Path(__file__).parent / "fixtures"
TEXT = "Mieszkam przy ul. Marszałkowskiej 12/4, 00-590 Warszawa i widziałem, że szczepionki zawierają chipy."
DEIDENTIFY = (
    "https://dlp.europe-central2.rep.googleapis.com/v2/projects/meritum-test"
    "/locations/europe-central2/content:deidentify"
)

type Sent = list[httpx2.Request]
type GateFactory = Callable[[Callable[[httpx2.Request], httpx2.Response]], PiiGatePort]


@pytest.fixture
def sent() -> Sent:
    return []


@pytest.fixture
def sdp_gate(sent: Sent) -> GateFactory:
    """Build Sensitive Data Protection through the factory with a fake HTTP handler."""

    def build(handler: Callable[[httpx2.Request], httpx2.Response]) -> PiiGatePort:
        def record(request: httpx2.Request) -> httpx2.Response:
            sent.append(request)
            return handler(request)

        client = httpx2.AsyncClient(transport=httpx2.MockTransport(record))
        token = Credentials(token="recorded")  # ruff: ignore[hardcoded-password-func-arg]  # fake token, no network
        settings = PiiGateSettings(gate="sdp", project="meritum-test")
        return build_pii_gate(settings, credentials=token, http_client=client)

    return build


def reply(name: str, status: int = 200) -> Callable[[httpx2.Request], httpx2.Response]:
    content = (FIXTURES / name).read_bytes()
    return lambda _request: httpx2.Response(status, content=content)


def test_address_is_masked_on_the_eu_regional_endpoint(
    sdp_gate: GateFactory, sent: Sent
) -> None:
    gate = sdp_gate(reply("dlp-address.json"))
    result = asyncio.run(mask_personal_data(TEXT, gate))
    assert result == MaskedText(
        text="Mieszkam przy [adres] i widziałem, że szczepionki zawierają chipy.",
        replaced=1,
    )
    [request] = sent
    assert str(request.url) == DEIDENTIFY
    assert request.headers["authorization"] == "Bearer recorded"
    body = json.loads(request.content)
    assert body["item"] == {"value": TEXT}
    assert body["inspectConfig"]["minLikelihood"] == "LIKELY"
    inspected = {t["name"] for t in body["inspectConfig"]["infoTypes"]}
    assert {"STREET_ADDRESS", "POLAND_PESEL_NUMBER"} <= inspected
    assert "PERSON_NAME" not in inspected
    transformations = body["deidentifyConfig"]["infoTypeTransformations"]
    replaced = {
        t["infoTypes"][0]["name"]: t["primitiveTransformation"]["replaceConfig"][
            "newValue"
        ]["stringValue"]
        for t in transformations["transformations"]
    }
    assert replaced["STREET_ADDRESS"] == "[adres]"
    assert set(replaced) == inspected


def test_patterns_mask_what_the_gate_left(sdp_gate: GateFactory) -> None:
    reply_json = {
        "item": {"value": "Mieszkam przy [adres]. Dzwoń 601 234 567"},
        "overview": {
            "transformationSummaries": [
                {"results": [{"count": "1", "code": "SUCCESS"}]}
            ]
        },
    }
    gate = sdp_gate(lambda _request: httpx2.Response(200, json=reply_json))
    result = asyncio.run(mask_personal_data(TEXT, gate))
    assert result == MaskedText(
        text="Mieszkam przy [adres]. Dzwoń [telefon]", replaced=2
    )


@pytest.mark.parametrize(
    "handler",
    [
        reply("dlp-unavailable.json", status=503),
        reply("dlp-partial-error.json"),
        lambda _request: httpx2.Response(200, content=b"<html>"),
        lambda _request: (_ for _ in ()).throw(httpx2.ConnectError("down")),
    ],
    ids=["http-503", "transformation-error", "not-json", "unreachable"],
)
def test_failing_gate_is_skipped_and_patterns_still_mask(
    sdp_gate: GateFactory,
    handler: Callable[[httpx2.Request], httpx2.Response],
    caplog: pytest.LogCaptureFixture,
) -> None:
    gate = sdp_gate(handler)
    text = f"{TEXT} Dzwoń: 601 234 567."
    with caplog.at_level(logging.WARNING):
        result = asyncio.run(mask_personal_data(text, gate))
    assert result == MaskedText(text=f"{TEXT} Dzwoń: [telefon].", replaced=1)
    assert "skipped" in caplog.text
    assert "Marszałkowskiej" not in caplog.text
    assert "601 234 567" not in caplog.text


def test_default_settings_build_the_null_gate_that_logs_the_skip(
    caplog: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("MERITUM_PII_GATE", raising=False)
    gate = build_pii_gate(PiiGateSettings())
    assert isinstance(gate, NullPiiGate)
    with caplog.at_level(logging.INFO):
        result = asyncio.run(gate.mask(TEXT))
    assert result == MaskedText(text=TEXT, replaced=0)
    assert "skipped" in caplog.text
    assert TEXT not in caplog.text


def test_environment_picks_sensitive_data_protection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MERITUM_PII_GATE", "sdp")
    monkeypatch.setenv("MERITUM_PII_PROJECT", "meritum-test")
    monkeypatch.setenv("MERITUM_PII_LOCATION", "europe-west3")
    settings = PiiGateSettings()
    gate = build_pii_gate(settings, credentials=Credentials(token="x"))  # ruff: ignore[hardcoded-password-func-arg]  # fake token
    assert not isinstance(gate, NullPiiGate)
    assert isinstance(gate, PiiGatePort)
    assert settings.location == "europe-west3"


def test_sdp_needs_a_project() -> None:
    with pytest.raises(ValidationError, match="PROJECT"):
        PiiGateSettings(gate="sdp")


@pytest.mark.parametrize(
    "location", ["global", "us-central1", "europe-west2", "europe"]
)
def test_location_outside_the_eu_is_refused(location: str) -> None:
    with pytest.raises(ValidationError, match="EU region"):
        PiiGateSettings(gate="sdp", project="meritum-test", location=location)


def test_location_is_not_checked_without_the_gate() -> None:
    assert PiiGateSettings(location="us-central1").gate == "none"


class _ReplacingGate:
    """A gate that masks one known address, like DLP would."""

    def __init__(self, address: str) -> None:
        self.address = address

    async def mask(self, text: str) -> MaskedText:
        masked = text.replace(self.address, "[adres]")
        return MaskedText(text=masked, replaced=text.count(self.address))


def test_masking_twice_with_a_gate_changes_nothing() -> None:
    gate = _ReplacingGate("ul. Marszałkowskiej 12/4, 00-590 Warszawa")
    once = asyncio.run(mask_personal_data(f"{TEXT} tel. 601 234 567", gate))
    twice = asyncio.run(mask_personal_data(once.text, gate))
    assert twice == MaskedText(text=once.text, replaced=0)
