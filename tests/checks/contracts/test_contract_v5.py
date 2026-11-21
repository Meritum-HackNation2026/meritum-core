"""Contract v5: a CheckRequest carries the browser session id (US-BEZ-05, US-BEZ-06)."""

from collections.abc import Callable

import pytest
from pydantic import ValidationError
from tests.checks.contracts.samples import EXAMPLES

from meritum_core.checks import contracts as c

SESSION = "s_12345678"


def request(**fields: object) -> Callable[[], c.CheckRequest]:
    return lambda: c.CheckRequest.model_validate({"text": "Tekst testowy."} | fields)


MUST_REJECT: dict[str, Callable[[], object]] = {
    "session id shorter than a CheckRecord allows": request(
        channel="extension", session_id="s_1234"
    ),
    "session id longer than a CheckRecord allows": request(
        channel="web", session_id="s" * 65
    ),
    "Discord request with a session id": lambda: c.CheckRequest.model_validate(
        EXAMPLES["CheckRequest.discord"] | {"session_id": SESSION}
    ),
}


@pytest.mark.parametrize("label", sorted(MUST_REJECT))
def test_contract_rejects(label: str) -> None:
    with pytest.raises(ValidationError):
        MUST_REJECT[label]()


@pytest.mark.parametrize("channel", ["web", "extension"])
def test_browser_request_validates_with_and_without_session_id(channel: str) -> None:
    assert request(channel=channel, session_id=SESSION)().session_id == SESSION
    assert request(channel=channel)().session_id is None


def test_request_session_id_fits_the_record() -> None:
    record = EXAMPLES["CheckRecord"] | {
        "session_id": request(channel="extension", session_id=SESSION)().session_id
    }
    assert c.CheckRecord.model_validate(record).session_id == SESSION
