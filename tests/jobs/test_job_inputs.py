from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from meritum_core.checks import CheckRequest
from meritum_core.jobs.constants import CONTRACT_VERSION
from meritum_core.jobs.contracts import (
    CHECK,
    DELETE_SUBJECT,
    ESCALATE_CLAIM,
    READINESS,
    WORKFLOWS,
    CheckInput,
    DeleteSubjectInput,
    EscalateClaimInput,
    ReadinessReport,
)

HASH = "a" * 64
NOW = datetime(2026, 11, 21, tzinfo=UTC)


def _discord(**identity: str) -> CheckInput:
    request = CheckRequest(channel="discord", text="Polska przyjęła euro.")
    return CheckInput(request=request, received_at=NOW, **identity)


def test_contract_version_is_4_and_every_workflow_is_listed() -> None:
    assert CONTRACT_VERSION == 4
    assert {s.name for s in WORKFLOWS} == {
        "ping",
        "check",
        "escalate_claim",
        "delete_subject",
        "readiness",
        "eval_run",
    }
    assert {CHECK, ESCALATE_CLAIM, DELETE_SUBJECT, READINESS} <= set(WORKFLOWS)


def test_check_input_keeps_text_without_personal_data_unchanged() -> None:
    text = "Rząd podniósł VAT na chleb do 23% w 2025 roku."
    request = CheckRequest(channel="web", text=text)
    payload = CheckInput(request=request, session_id="session-1", received_at=NOW)
    dumped = payload.model_dump(mode="json")
    assert dumped["request"]["text"] == text
    assert dumped["contract_version"] == CONTRACT_VERSION
    assert CheckInput.model_validate(dumped) == payload


def test_check_input_on_discord_carries_the_hash_as_session() -> None:
    payload = _discord(session_id=HASH, channel_user_hash=HASH)
    assert payload.channel_user_hash == HASH


def test_check_input_rejects_a_raw_channel_user_id() -> None:
    raw = "123456789012345678"
    with pytest.raises(ValidationError):
        _discord(session_id=raw, channel_user_hash=raw)
    with pytest.raises(ValidationError):
        _discord(session_id=raw, channel_user_hash=HASH)
    with pytest.raises(ValidationError):
        _discord(session_id=HASH, channel_user_hash=HASH, user_id=raw)


def test_check_input_rejects_a_request_still_carrying_the_raw_id() -> None:
    request = CheckRequest(
        channel="sms", text="Polska przyjęła euro.", channel_user_id="+48500000000"
    )
    with pytest.raises(ValidationError, match="raw channel user id"):
        CheckInput(
            request=request, session_id=HASH, channel_user_hash=HASH, received_at=NOW
        )


def test_check_input_rejects_an_unknown_field_for_the_raw_id() -> None:
    with pytest.raises(ValidationError):
        CheckInput.model_validate(
            {
                "request": {"channel": "discord", "text": "Polska przyjęła euro."},
                "session_id": HASH,
                "channel_user_hash": HASH,
                "channel_user_id": "123456789012345678",
                "received_at": NOW.isoformat(),
            }
        )


def test_check_input_needs_the_hash_only_on_sessionless_channels() -> None:
    with pytest.raises(ValidationError):
        _discord(session_id="session-1")
    request = CheckRequest(channel="web", text="Polska przyjęła euro.")
    with pytest.raises(ValidationError):
        CheckInput(
            request=request,
            session_id=HASH,
            channel_user_hash=HASH,
            received_at=NOW,
        )


def test_check_input_needs_a_session_or_a_user() -> None:
    request = CheckRequest(channel="web", text="Polska przyjęła euro.")
    with pytest.raises(ValidationError):
        CheckInput(request=request, received_at=NOW)
    signed_in = CheckInput(request=request, user_id="user-0001", received_at=NOW)
    assert signed_in.user_id == "user-0001"


@pytest.mark.parametrize("reason", ["recommended_clicked", "cache_hit"])
def test_escalation_without_dispute_has_no_justification(reason: str) -> None:
    payload = EscalateClaimInput.model_validate(
        {
            "check_id": "c1",
            "claim_index": 0,
            "reason": reason,
        }
    )
    assert payload.justification_masked is None
    with pytest.raises(ValidationError):
        EscalateClaimInput.model_validate(
            {
                "check_id": "c1",
                "claim_index": 0,
                "reason": reason,
                "justification_masked": "Źródło jest nieaktualne.",
            }
        )


def test_user_dispute_may_come_without_a_justification() -> None:
    bare = EscalateClaimInput(check_id="c1", claim_index=0, reason="user_dispute")
    assert bare.justification_masked is None
    payload = EscalateClaimInput(
        check_id="c1",
        claim_index=1,
        reason="user_dispute",
        justification_masked="Źródło jest nieaktualne.",
    )
    assert (payload.claim_index, payload.justification_masked) == (
        1,
        "Źródło jest nieaktualne.",
    )


def test_user_dispute_rejects_an_empty_justification() -> None:
    with pytest.raises(ValidationError):
        EscalateClaimInput(
            check_id="c1", claim_index=0, reason="user_dispute", justification_masked=""
        )


def test_escalation_rejects_a_negative_claim_index() -> None:
    with pytest.raises(ValidationError):
        EscalateClaimInput(check_id="c1", claim_index=-1, reason="cache_hit")


def test_delete_subject_by_channel_user_takes_only_the_hash() -> None:
    assert DeleteSubjectInput(kind="channel_user_hash", value=HASH).value == HASH
    with pytest.raises(ValidationError):
        DeleteSubjectInput(kind="channel_user_hash", value="123456789012345678")
    by_session = DeleteSubjectInput(kind="session_id", value="session-1")
    assert by_session.value == "session-1"


def test_readiness_report_lists_what_is_missing() -> None:
    report = ReadinessReport(
        missing_env=["MERITUM_LLM_PROVIDER"],
        unavailable_providers=["vertex"],
        checked_at=NOW,
    )
    assert report.model_dump(mode="json")["missing_env"] == ["MERITUM_LLM_PROVIDER"]


def test_check_input_rejects_a_request_session_id_other_than_its_own() -> None:
    request = CheckRequest(channel="web", text="Tekst testowy.", session_id="session-1")
    with pytest.raises(ValidationError, match="session id"):
        CheckInput(request=request, session_id="session-2", received_at=NOW)
    with pytest.raises(ValidationError, match="session id"):
        CheckInput(request=request, user_id="user-0001", received_at=NOW)
    same = CheckInput(request=request, session_id="session-1", received_at=NOW)
    assert same.request.session_id == same.session_id
