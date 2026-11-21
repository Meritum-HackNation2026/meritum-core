"""Contract v4: transcript, channel user id, failure and limitation codes, match basis,
what would change the verdict and ClaimReview ratings as premises (ADR-34, ADR-35)."""

from collections.abc import Callable
from typing import Any

import pytest
from pydantic import ValidationError
from tests.checks.contracts.samples import (
    CACHED,
    CASE,
    CATALOG,
    CLAIM,
    DONE,
    EXAMPLES,
    PREMISES,
    REFUTING,
    SUPPORTING,
    result,
)

from meritum_core.checks import contracts as c

FAILURE: dict[str, Any] = EXAMPLES["CheckResult.failure"]
REVIEWED: dict[str, Any] = EXAMPLES["CheckResult.claim_review"]
REVIEW_CLAIM: dict[str, Any] = REVIEWED["claims"][0]
REVIEW: dict[str, Any] = REVIEW_CLAIM["claim_review_premises"][0]
INCIDENT: dict[str, Any] = REVIEW_CLAIM["incident"]
OTHER_REVIEW = REVIEW | {"publisher": "Inny fact-checker", "publisher_id": "inny-fc"}
REVIEW_PREMISES = REVIEW_CLAIM["strength"]["premises"]


def request(**fields: object) -> Callable[[], object]:
    return lambda: c.CheckRequest.model_validate({"text": "Tekst testowy."} | fields)


def reviewed(**changes: object) -> Callable[[], object]:
    return lambda: c.CheckResult.model_validate(
        REVIEWED | {"claims": [REVIEW_CLAIM | changes]}
    )


def without(data: dict[str, Any], key: str) -> dict[str, Any]:
    return {k: v for k, v in data.items() if k != key}


MUST_REJECT: dict[str, Callable[[], object]] = {
    "web request with a channel user id": request(channel="web", channel_user_id="1"),
    "extension request with a channel user id": request(
        channel="extension", channel_user_id="1"
    ),
    "technical failure without a failure code": lambda: c.CheckResult.model_validate(
        without(FAILURE, "failure_code")
    ),
    "finished check with a failure code": lambda: c.CheckResult.model_validate(
        DONE | {"failure_code": "provider_unavailable"}
    ),
    "failure code naming a provider": lambda: c.CheckResult.model_validate(
        FAILURE | {"failure_code": "vertex_quota"}
    ),
    "unknown limitation code": lambda: c.CheckResult.model_validate(
        DONE | {"limitation_codes": ["corpus_missing"]}
    ),
    "claim without a claim date": lambda: c.CheckResult.model_validate(
        DONE | {"claims": [without(CLAIM, "claim_date")]}
    ),
    "claim without the origin of its date": lambda: c.CheckResult.model_validate(
        DONE | {"claims": [without(CLAIM, "claim_date_source")]}
    ),
    "unknown code of what would change the verdict": result(
        would_change_verdict=["needs_luck"]
    ),
    "content match on the domain only": reviewed(
        incident=INCIDENT | {"match_basis": ["domain"]}
    ),
    "content match without the date": reviewed(
        incident=INCIDENT | {"match_basis": ["title", "topic"]}
    ),
    "domain match without the domain in its basis": reviewed(
        incident=INCIDENT | {"matched_on": "domain", "match_basis": ["title", "topic"]}
    ),
    "incident match without a basis": reviewed(incident=INCIDENT | {"match_basis": []}),
    "rating of a publisher outside IFCN and EFCSN": reviewed(
        claim_review_premises=[REVIEW | {"signatory_of": []}]
    ),
    "rating with a network other than IFCN or EFCSN": reviewed(
        claim_review_premises=[REVIEW | {"signatory_of": ["gfcn"]}]
    ),
    "two ratings of one fact-checker counted as two sources": reviewed(
        claim_review_premises=[REVIEW, REVIEW | {"title": "Druga ocena (fikstura)"}],
        strength={
            "level": "moderate",
            "premises": REVIEW_PREMISES | {"independent_sources": 2},
        },
    ),
    "insufficient evidence carrying a rating without a conflict": reviewed(
        verdict="insufficient_evidence", strength=None, unresolved="Brak danych."
    ),
    "high-risk case classified by a model": lambda: c.ModeratorCase.model_validate(
        CASE | {"high_risk_classified_by": "model"}
    ),
    "transcript over the length limit": lambda: c.CachedResult.model_validate(
        CACHED | {"transcript": "a" * 4001}
    ),
}

MUST_ACCEPT: dict[str, Callable[[], object]] = {
    "Discord request with a channel user id": request(
        channel="discord", channel_user_id="100000000000000001"
    ),
    "SMS request with a phone number": request(
        channel="sms", channel_user_id="+48500000000"
    ),
    "finished check limited by the fact-check index": lambda: (
        c.CheckResult.model_validate(
            DONE | {"limitation_codes": ["fact_check_unavailable"]}
        )
    ),
    "domain match on the domain and topic": reviewed(
        incident=INCIDENT | {"matched_on": "domain", "match_basis": ["domain", "topic"]}
    ),
    "citation and a rating from two publishers, one primary: strong": result(
        citations=[REFUTING],
        claim_review_premises=[REVIEW],
        strength={
            "level": "strong",
            "premises": PREMISES | {"independent_sources": 2},
        },
    ),
    "supporting citation against a refuting rating: insufficient evidence": result(
        verdict="insufficient_evidence",
        unresolved="Źródło i fact-checker się nie zgadzają.",
        citations=[SUPPORTING],
        claim_review_premises=[REVIEW],
        strength=None,
    ),
    "two fact-checkers' ratings: moderate": reviewed(
        claim_review_premises=[REVIEW, OTHER_REVIEW],
        strength={
            "level": "moderate",
            "premises": REVIEW_PREMISES | {"independent_sources": 2},
        },
    ),
    "case classified by keywords": lambda: c.ModeratorCase.model_validate(
        CASE | {"high_risk_classified_by": "keywords"}
    ),
    "catalogue entry of an IFCN signatory": lambda: c.CatalogEntry.model_validate(
        CATALOG | {"signatory_of": ["ifcn"]}
    ),
    "cached result with a transcript and limitation codes": lambda: (
        c.CachedResult.model_validate(
            CACHED
            | {
                "transcript": "Nagranie testowe.",
                "limitation_codes": ["fact_check_unavailable"],
            }
        )
    ),
}


@pytest.mark.parametrize("label", sorted(MUST_REJECT))
def test_v4_rule_rejects(label: str) -> None:
    with pytest.raises(ValidationError):
        MUST_REJECT[label]()


@pytest.mark.parametrize("label", sorted(MUST_ACCEPT))
def test_v4_rule_accepts(label: str) -> None:
    MUST_ACCEPT[label]()


def test_claim_review_premise_needs_no_fragment() -> None:
    claim = c.CheckResult.model_validate(REVIEWED).claims[0]
    assert claim.verdict == "false"
    assert not claim.citations
    assert claim.claim_review_premises[0].rating == "Fałsz"


def test_domain_alone_never_makes_a_content_match() -> None:
    assert c.REQUIRED_MATCH_BASIS["content"] == {"title", "topic", "date"}
    assert c.REQUIRED_MATCH_BASIS["domain"] == {"domain", "topic"}
