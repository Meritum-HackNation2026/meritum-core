"""Reciprocal rank fusion of several rankings, weighted by freshness.

Features:
    US-ZRD-05, F-12, ADR-04
"""

import math
from collections.abc import Sequence
from datetime import date

from meritum_core.corpus.constants import (
    FRESHNESS_FLOOR,
    FRESHNESS_HALF_LIFE_DAYS,
    RRF_K,
)
from meritum_core.corpus.models import Passage


def freshness_weight(published_on: date | None, claim_date: date) -> float:
    """Weight in [FRESHNESS_FLOOR, 1] that halves its bonus every half-life.

    Age counts from the claim date, not from today (US-ZRD-05); a passage
    published after the claim date counts as brand new.

    Args:
        published_on: Publication date, None when unknown (gets the floor).
        claim_date: The date the claim is about.

    Returns:
        The multiplier for the passage's fused score.

    Features:
        US-ZRD-05, F-12, ADR-04
    """
    if published_on is None:
        return FRESHNESS_FLOOR
    age_days = max((claim_date - published_on).days, 0)
    decay = math.exp2(-age_days / FRESHNESS_HALF_LIFE_DAYS)
    return FRESHNESS_FLOOR + (1 - FRESHNESS_FLOOR) * decay


def fuse_rankings(
    rankings: Sequence[Sequence[Passage]], *, claim_date: date, limit: int
) -> list[Passage]:
    """Merge rankings into one list scored by RRF times freshness.

    Args:
        rankings: Each ranking's passages, best first (vector, full text, typos).
        claim_date: The date the claim is about.
        limit: Most passages to return.

    Returns:
        Distinct passages, best first, each with its ``score``; ties by id.

    Features:
        US-ZRD-05, F-12, ADR-04
    """
    rrf: dict[str, float] = {}
    passages: dict[str, Passage] = {}
    for ranking in rankings:
        for rank, passage in enumerate(ranking, start=1):
            passages.setdefault(passage.passage_id, passage)
            rrf[passage.passage_id] = rrf.get(passage.passage_id, 0.0) + 1 / (
                RRF_K + rank
            )
    fused = [
        passage.model_copy(
            update={
                "score": rrf[pid] * freshness_weight(passage.published_on, claim_date)
            }
        )
        for pid, passage in passages.items()
    ]
    fused.sort(key=lambda p: (-p.score, p.passage_id))
    return fused[:limit]
