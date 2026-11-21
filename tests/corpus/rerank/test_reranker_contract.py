"""RerankerPort contract: core's null gate and fake pass it; worker/031 runs it on its adapters."""

import asyncio
import logging
from collections.abc import Callable

import pytest

from meritum_core.corpus import Passage
from meritum_core.corpus.rerank import (
    RERANK_TOP_K,
    NullReranker,
    RankedPassage,
    RerankerPort,
)
from meritum_core.corpus.rerank.contract import reranker_contract_violations
from meritum_core.corpus.rerank.fakes import FakeReranker

ADAPTERS: dict[str, Callable[[], RerankerPort]] = {
    "null": NullReranker,
    "fake": lambda: FakeReranker({"c2": 0.9, "c0": 0.4}),
}


@pytest.mark.parametrize("name", sorted(ADAPTERS))
def test_adapter_meets_the_reranker_contract(name: str) -> None:
    assert asyncio.run(reranker_contract_violations(ADAPTERS[name]())) == []


class _Broken:
    """Ignores the limit, repeats a passage and returns the worst first."""

    async def rerank(  # ruff: ignore[no-self-use]  # same signature as the port
        self,
        claim: str,  # ruff: ignore[unused-method-argument]  # same signature as the port
        passages: list[Passage],
        *,
        limit: int = RERANK_TOP_K,  # ruff: ignore[unused-method-argument]  # ignoring it is the bug
    ) -> list[RankedPassage]:
        doubled = [*passages, passages[0]] if passages else []
        return [RankedPassage(passage=p, relevance=i) for i, p in enumerate(doubled)]


def test_contract_reports_every_broken_rule() -> None:
    violations = asyncio.run(reranker_contract_violations(_Broken()))
    assert violations == [
        "returned 6 passages for limit 3",
        "returned a passage twice",
        "relevance is not non-increasing",
        "accepted limit 0",
    ]


def test_null_gate_logs_the_skip_without_the_claim(
    caplog: pytest.LogCaptureFixture,
) -> None:
    claim = "Tajne twierdzenie użytkownika"
    with caplog.at_level(logging.INFO):
        asyncio.run(NullReranker().rerank(claim, []))
    assert "reranker not configured" in caplog.text
    assert claim not in caplog.text
