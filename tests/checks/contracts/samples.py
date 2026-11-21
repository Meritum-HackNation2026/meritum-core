"""Shared samples for the check contract tests, built from contracts/examples.json.

Ported from design-system/contracts/export_schema.py (the self-check of the
former working copy).
"""

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

from meritum_core.checks import contracts as c

EXAMPLES: dict[str, Any] = {
    k: v
    for k, v in json.loads(
        (Path(__file__).parents[3] / "contracts" / "examples.json").read_text("utf-8")
    ).items()
    if not k.startswith("$")
}
DONE: dict[str, Any] = EXAMPLES["CheckResult.done"]
CLAIM: dict[str, Any] = DONE["claims"][0]
PREMISES: dict[str, Any] = CLAIM["strength"]["premises"]
REFUTING: dict[str, Any] = CLAIM["citations"][0]
SUPPORTING = REFUTING | {
    "stance": "supports",
    "fragment": "Prezydent może sprawować urząd przez trzy kadencje (fragment testowy).",
}
SAME_PUBLISHER = REFUTING | {
    "fragment": "Prezydent Rzeczypospolitej jest wybierany przez Naród w wyborach powszechnych."
}
OTHER_SOURCE: dict[str, Any] = REFUTING["source"] | {
    "id": "other-01",
    "publisher": "Inny wydawca",
    "publisher_id": "inny-wydawca",
    "domain": "inny.example.pl",
    "kind": "fact_check",
    "tier": "secondary",
}
SECONDARY_REFUTING = REFUTING | {
    "source": OTHER_SOURCE,
    "fragment": "Ponowny wybór możliwy jest tylko raz (fragment testowy).",
}
CONTEXT_OTHER = SECONDARY_REFUTING | {"stance": "context"}
EXPIRING = REFUTING | {"validity": "expires"}
EXPIRING_PREMISES = PREMISES | {"validity": "expires"}
STALE: dict[str, Any] = {
    "level": "weak",
    "premises": EXPIRING_PREMISES | {"newest_source_age_hours": 900 * 24},
}
SHORT_LIVED: dict[str, Any] = {
    "level": "weak",
    "premises": EXPIRING_PREMISES
    | {"newest_source_age_hours": 48, "max_age_hours": 24},
}
CATALOG: dict[str, Any] = EXAMPLES["CatalogEntry"]
CACHED: dict[str, Any] = EXAMPLES["CachedResult"]
RECORD: dict[str, Any] = EXAMPLES["CheckRecord"]
CASE: dict[str, Any] = EXAMPLES["ModeratorCase"]
NOTE: dict[str, Any] = EXAMPLES["Notification"]
HASH = "a" * 64
SUPERSEDED_SUPPORTING = SUPPORTING | {"validity": "superseded"}
NEWER_SOURCE: dict[str, Any] = REFUTING["source"] | {
    "id": "isap-newer",
    "published_at": "2025-01-01T00:00:00+01:00",
}
NEWER_REFUTING = REFUTING | {
    "source": NEWER_SOURCE,
    "fragment": "Nowszy dokument urzędowy obala to twierdzenie (fragment testowy).",
}
NEWER_CONTEXT = NEWER_REFUTING | {"stance": "context"}


def with_claim(**changes: object) -> dict[str, object]:
    return DONE | {"claims": [CLAIM | changes]}


def result(**changes: object) -> Callable[[], object]:
    return lambda: c.CheckResult.model_validate(with_claim(**changes))


def stale(**changes: object) -> Callable[[], object]:
    return result(citations=[EXPIRING], **changes)


def lasting(validity: str, **changes: object) -> Callable[[], object]:
    return result(
        citations=[REFUTING | {"validity": validity}],
        strength={
            "level": "moderate",
            "premises": STALE["premises"] | {"validity": validity},
        },
        **changes,
    )


def premises(**changes: object) -> c.Premises:
    return c.Premises.model_validate(EXPIRING_PREMISES | changes)
