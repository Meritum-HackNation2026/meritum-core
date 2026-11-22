"""Fuses gold rankings and merges them with the bronze result of the same search.

Features:
    US-KOR-02, US-ZRD-05, F-12
"""

from collections.abc import Collection, Sequence
from datetime import date

from meritum_core.corpus.constants import RRF_K
from meritum_core.corpus.models import Passage
from meritum_core.corpus.ready.constants import GOLD_ID_PREFIX
from meritum_core.corpus.ready.models import GoldHit
from meritum_core.corpus.ready.weighting import gold_weight


def fuse_gold(
    rankings: Sequence[Sequence[GoldHit]], *, claim_date: date
) -> list[Passage]:
    """RRF of the gold rankings times ``gold_weight``, as passages, best first.

    Args:
        rankings: Each ranking's hits, best first (vector, full text).
        claim_date: The date the claim is about.

    Returns:
        Distinct passages with ``passage_id`` ``gold:<chunk_id>``; ties by id.

    Features:
        US-KOR-02, US-ZRD-05, F-12
    """
    rrf: dict[str, float] = {}
    hits: dict[str, GoldHit] = {}
    for ranking in rankings:
        for rank, hit in enumerate(ranking, start=1):
            hits.setdefault(hit.chunk_id, hit)
            rrf[hit.chunk_id] = rrf.get(hit.chunk_id, 0.0) + 1 / (RRF_K + rank)
    fused = [
        Passage(
            passage_id=GOLD_ID_PREFIX + cid,
            source_id=hit.source_id,
            text=hit.text,
            published_on=hit.published_on,
            fetched_at=hit.fetched_at,
            score=rrf[cid] * gold_weight(hit, claim_date),
        )
        for cid, hit in hits.items()
    ]
    fused.sort(key=lambda p: (-p.score, p.passage_id))
    return fused


def merge_with_bronze(
    gold: Sequence[Passage],
    bronze: Sequence[Passage],
    *,
    covered: Collection[str],
    limit: int,
) -> list[Passage]:
    """Gold replaces bronze for the documents it covers; the rest stays.

    The two lists are scored differently, so they are merged by rank (RRF of
    the two lists); a passage keeps the score of its own list.

    Args:
        gold: Fused gold passages, best first.
        bronze: The unchanged bronze result, best first.
        covered: Source ids that have gold chunks in this snapshot.
        limit: Most passages to return.

    Returns:
        At most ``limit`` passages, best first.

    Features:
        US-KOR-02, US-ZRD-05, F-12
    """
    kept = [p for p in bronze if p.source_id not in covered]
    ranked: dict[str, tuple[float, Passage]] = {}
    for ranking in (gold, kept):
        for rank, passage in enumerate(ranking, start=1):
            old, _ = ranked.get(passage.passage_id, (0.0, passage))
            ranked[passage.passage_id] = (old + 1 / (RRF_K + rank), passage)
    order = sorted(
        ranked.values(), key=lambda r: (-r[0], _bronze_first(r[1]), r[1].passage_id)
    )
    return [passage for _, passage in order[:limit]]


def _bronze_first(passage: Passage) -> bool:
    # On a tie gold goes first: False sorts before True.
    return not passage.passage_id.startswith(GOLD_ID_PREFIX)
