"""The RerankerPort contract, shipped so worker/031 runs it on its own adapters.

A test calls ``reranker_contract_violations(adapter)`` and expects an empty list.

Features:
    US-KOR-02, US-SPR-04, F-12, ADR-35
"""

from datetime import UTC, date, datetime

from meritum_core.corpus.models import Passage
from meritum_core.corpus.rerank.models import RankedPassage
from meritum_core.corpus.rerank.ports import RerankerPort


def _passages() -> list[Passage]:
    texts = (
        "Sanepid stwierdził, że woda z krakowskich wodociągów spełnia normy.",
        "Ceny biletów komunikacji miejskiej w Krakowie wzrosną od stycznia.",
        "Wodociągi Miasta Krakowa: woda w kranach jest zdatna do picia.",
        "Prognoza pogody na weekend w Małopolsce.",
        "Komunikat o przerwie w dostawie wody na Podgórzu.",
    )
    fetched = datetime(2026, 11, 21, tzinfo=UTC)
    return [
        Passage(
            passage_id=f"c{i}",
            source_id=f"src-c{i}",
            text=text,
            published_on=date(2026, 11, 1),
            fetched_at=fetched,
            score=(len(texts) - i) / 100,
        )
        for i, text in enumerate(texts)
    ]


def _shape_violations(
    ranked: list[RankedPassage], passages: list[Passage], limit: int
) -> list[str]:
    given = {p.passage_id: p for p in passages}
    ids = [r.passage.passage_id for r in ranked]
    relevance = [r.relevance for r in ranked]
    checks = {
        f"returned {len(ranked)} passages for limit {limit}": len(ranked) <= limit,
        "returned a passage it was not given": all(
            given.get(r.passage.passage_id) == r.passage for r in ranked
        ),
        "returned a passage twice": len(set(ids)) == len(ids),
        "relevance is not non-increasing": relevance == sorted(relevance, reverse=True),
        "returned nothing for non-empty passages": bool(ranked),
    }
    return [message for message, holds in checks.items() if not holds]


async def _rejects_zero_limit(
    reranker: RerankerPort, claim: str, passages: list[Passage]
) -> bool:
    try:
        await reranker.rerank(claim, passages, limit=0)
    except ValueError:
        return True
    return False


async def reranker_contract_violations(reranker: RerankerPort) -> list[str]:
    """Run the port contract on ``reranker`` and describe every broken rule.

    Calls the reranker with five Polish passages, with none, and with limit 0.

    Args:
        reranker: The adapter under test.

    Returns:
        One message per broken rule; empty when the adapter meets the contract.

    Features:
        US-KOR-02, US-SPR-04, F-12, ADR-35
    """
    claim = "Woda z wodociągów w Krakowie nie nadaje się do picia"
    limit = 3  # below the five passages, so a reranker that ignores it shows
    passages = _passages()
    ranked = await reranker.rerank(claim, passages, limit=limit)
    violations = _shape_violations(ranked, passages, limit)
    if await reranker.rerank(claim, [], limit=limit):
        violations.append("returned passages for no passages")
    if not await _rejects_zero_limit(reranker, claim, passages):
        violations.append("accepted limit 0")
    return violations
