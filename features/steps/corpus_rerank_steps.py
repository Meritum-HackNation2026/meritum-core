"""Steps for the reranker scenarios of features/corpus.feature (fake and null gate)."""

import asyncio
import logging
from datetime import UTC, date, datetime
from typing import override

from behave import given, then, when
from behave.runner import Context

from meritum_core.corpus import Passage
from meritum_core.corpus.rerank import RERANK_TOP_K, NullReranker
from meritum_core.corpus.rerank.fakes import FakeReranker

CLAIM = "Woda w Krakowie nie nadaje się do picia"
HYBRID_COUNT = 20


class _Records(logging.Handler):
    def __init__(self) -> None:
        super().__init__(logging.INFO)
        self.messages: list[str] = []

    @override
    def emit(self, record: logging.LogRecord) -> None:
        self.messages.append(record.getMessage())


def _hybrid_passages() -> list[Passage]:
    """Twenty passages best first by fused score, as the hybrid search returns them.

    Returns:
        The passages, best first.
    """
    fetched = datetime(2026, 11, 21, tzinfo=UTC)
    return [
        Passage(
            passage_id=f"p{i}",
            source_id=f"src-{i}",
            text=f"Fragment {i} o jakości wody",
            published_on=date(2026, 11, 1),
            fetched_at=fetched,
            score=(HYBRID_COUNT - i) / 100,
        )
        for i in range(HYBRID_COUNT)
    ]


@given("20 fragmentów z wyszukiwania hybrydowego dla jednego twierdzenia")
def given_hybrid_passages(context: Context) -> None:
    """The fake reranker finds the last hybrid passages the most relevant."""
    context.passages = _hybrid_passages()
    context.reranker = FakeReranker(
        {p.passage_id: i / HYBRID_COUNT for i, p in enumerate(context.passages)}
    )


@given("brak konfiguracji rerankera")
def given_no_reranker(context: Context) -> None:
    """No provider is picked, so the worker wires the null gate."""
    context.passages = _hybrid_passages()
    context.reranker = NullReranker()


@when("przechodzą przez reranker")
@when("fragmenty przechodzą przez bramkę")
def when_reranked(context: Context) -> None:
    """Pass the passages for the claim through the configured reranker."""
    records = _Records()
    logger = logging.getLogger("meritum_core")
    logger.addHandler(records)
    previous = logger.level
    logger.setLevel(logging.INFO)
    try:
        context.ranked = asyncio.run(context.reranker.rerank(CLAIM, context.passages))
    finally:
        logger.removeHandler(records)
        logger.setLevel(previous)
    context.log = records.messages


_TOP_K_STEP = "do oceny wymowy trafia najwyżej tyle fragmentów, ile mówi stała, w kolejności trafności"  # ruff: ignore[line-too-long]  # step text copied from the issue's Gherkin


@then(_TOP_K_STEP)
def then_top_k_by_relevance(context: Context) -> None:
    """At most RERANK_TOP_K passages, most relevant first."""
    relevance = [r.relevance for r in context.ranked]
    assert len(context.ranked) == RERANK_TOP_K
    assert relevance == sorted(relevance, reverse=True)
    assert context.ranked[0].passage.passage_id == f"p{HYBRID_COUNT - 1}"


@then("kolejność z wyszukiwania hybrydowego zostaje, a log zapisuje pominięcie")
def then_hybrid_order_and_skip_logged(context: Context) -> None:
    """The hybrid order is kept (cut to the limit) and the skip is logged."""
    ids = [r.passage.passage_id for r in context.ranked]
    assert ids == [p.passage_id for p in context.passages][:RERANK_TOP_K]
    assert any("reranker not configured" in m for m in context.log)
