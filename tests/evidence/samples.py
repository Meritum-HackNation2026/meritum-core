"""Citation and fact-checker rating builders for the evidence tests."""

import json
from datetime import date
from pathlib import Path
from typing import Any

from meritum_core.checks.contracts import (
    Citation,
    ClaimReviewPremise,
    SourceTier,
    Stance,
    Validity,
)

EXAMPLES: dict[str, Any] = json.loads(
    (Path(__file__).parents[2] / "contracts" / "examples.json").read_text("utf-8")
)
CLAIM: dict[str, Any] = EXAMPLES["CheckResult.done"]["claims"][0]
SOURCE: dict[str, Any] = CLAIM["citations"][0]["source"]
REVIEW: dict[str, Any] = EXAMPLES["CheckResult.claim_review"]["claims"][0][
    "claim_review_premises"
][0]
CLAIM_DATE = date(2026, 11, 21)


def cite(  # ruff: ignore[too-many-arguments]  # test builder: every argument is one field of the citation
    stance: Stance,
    publisher_id: str,
    tier: SourceTier = "secondary",
    *,
    published_at: str = "2026-11-10T00:00:00+01:00",
    validity: Validity = "expires",
    page: str = "a",
) -> Citation:
    """A citation of one page of ``publisher_id`` with the given stance."""
    source = SOURCE | {
        "id": f"{publisher_id}-{page}",
        "publisher_id": publisher_id,
        "tier": tier,
        "url": f"https://{publisher_id}.example.pl/{page}",
        "published_at": published_at,
    }
    return Citation.model_validate(
        {
            "source": source,
            "fragment": f"Fragment strony {page} wydawcy {publisher_id} (testowy).",
            "stance": stance,
            "validity": validity,
        }
    )


def review(stance: Stance, publisher_id: str) -> ClaimReviewPremise:
    """A fact-checker's ClaimReview rating with the given stance."""
    return ClaimReviewPremise.model_validate(
        REVIEW | {"publisher_id": publisher_id, "stance": stance}
    )
