"""Weight of a gold chunk on the claim date: validity for acts, freshness otherwise.

Features:
    US-ZRD-05, F-12
"""

from datetime import date

from meritum_core.corpus.fusion import freshness_weight
from meritum_core.corpus.ready.constants import (
    ACT_IN_WINDOW_WEIGHT,
    ACT_OUT_OF_WINDOW_WEIGHT,
)
from meritum_core.corpus.ready.models import DocumentKind, GoldHit


def gold_weight(hit: GoldHit, claim_date: date) -> float:
    """Multiplier of a gold hit's fused score.

    An act counts by whether it was in force on the claim date, not by its age:
    the Constitution is not stale. Other documents keep the bronze freshness.
    The builder's base weight (low for title-only stubs) multiplies both.

    Args:
        hit: The hit with its kind, validity window and base weight.
        claim_date: The date the claim is about.

    Returns:
        The weight in (0, 1].

    Features:
        US-ZRD-05, F-12
    """
    if hit.kind in {DocumentKind.ACT, DocumentKind.CONSOLIDATED_TEXT}:
        started = hit.valid_from is None or hit.valid_from <= claim_date
        not_ended = hit.valid_to is None or claim_date <= hit.valid_to
        in_window = started and not_ended
        validity = ACT_IN_WINDOW_WEIGHT if in_window else ACT_OUT_OF_WINDOW_WEIGHT
        return hit.weight * validity
    return hit.weight * freshness_weight(hit.published_on, claim_date)
