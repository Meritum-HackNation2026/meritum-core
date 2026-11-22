"""Contract v12: expired evidence never conflicts with fresh evidence.

Features:
    US-ZRD-05, US-ZRD-10, ADR-25
"""

from typing import get_args

import pytest
from pydantic import ValidationError
from tests.evidence.samples import CLAIM, CLAIM_DATE, cite

from meritum_core.checks import contracts as c

OLD = "2020-01-01T00:00:00+01:00"


def _insufficient(citations: list[c.Citation]) -> c.ClaimResult:
    return c.ClaimResult.model_validate(
        CLAIM
        | {
            "claim_date": CLAIM_DATE,
            "verdict": "insufficient_evidence",
            "citations": citations,
            "strength": None,
            "unresolved": "Źródła podają sprzeczne informacje.",
        }
    )


def test_expired_evidence_next_to_a_fresh_refutation_is_not_a_conflict() -> None:
    citations = [cite("supports", "kprm", "primary", published_at=OLD)]
    citations.append(cite("refutes", "demagog"))
    with pytest.raises(ValidationError, match="credible sources conflict"):
        _insufficient(citations)


NON_EXPIRING = [v for v in get_args(c.Validity) if v not in {"expires", "superseded"}]


@pytest.mark.parametrize("validity", NON_EXPIRING)
def test_old_evidence_that_does_not_expire_still_conflicts(
    validity: c.Validity,
) -> None:
    old = cite("supports", "kprm", "primary", published_at=OLD, validity=validity)
    claim = _insufficient([old, cite("refutes", "demagog")])
    assert claim.verdict == "insufficient_evidence"
