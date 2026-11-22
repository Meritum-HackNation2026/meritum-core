"""gold_weight, fuse_gold, merge_with_bronze and GoldChunk offsets."""

from datetime import UTC, date, datetime

import pytest
from pydantic import ValidationError

from meritum_core.corpus import Passage
from meritum_core.corpus.ready import (
    DocumentKind,
    GoldChunk,
    GoldHit,
    fuse_gold,
    gold_weight,
    merge_with_bronze,
)

CLAIM = date(2025, 6, 1)
AT = datetime(2026, 1, 1, tzinfo=UTC)


def hit(cid: str, kind: DocumentKind, **dates: date | None) -> GoldHit:
    return GoldHit(
        chunk_id=cid,
        source_id=cid,
        text=cid,
        published_on=dates.get("published"),
        fetched_at=AT,
        kind=kind,
        valid_from=dates.get("since"),
        valid_to=dates.get("until"),
        weight=1.0,
    )


def test_act_in_force_on_claim_date_outweighs_act_that_expired() -> None:
    pay_2025 = hit(
        "p25", DocumentKind.ACT, since=date(2025, 1, 1), until=date(2025, 12, 31)
    )
    pay_2026 = hit("p26", DocumentKind.ACT, since=date(2026, 1, 1))

    assert gold_weight(pay_2025, CLAIM) == pytest.approx(1.0)
    assert gold_weight(pay_2026, CLAIM) == pytest.approx(0.6)


def test_old_constitution_is_not_stale_but_old_news_is() -> None:
    constitution = hit("k", DocumentKind.ACT, published=date(1997, 7, 16))
    news = hit("n", DocumentKind.NEWS, published=date(2020, 1, 1))

    assert gold_weight(constitution, CLAIM) == pytest.approx(1.0)
    assert gold_weight(news, CLAIM) < 0.6


def test_fuse_gold_ranks_valid_act_first() -> None:
    expired = hit("a", DocumentKind.ACT, until=date(2024, 12, 31))
    valid = hit("b", DocumentKind.ACT)

    fused = fuse_gold([[expired, valid], [expired, valid]], claim_date=CLAIM)

    assert [p.passage_id for p in fused] == ["gold:b", "gold:a"]


def test_merge_drops_bronze_of_covered_sources_and_keeps_the_rest() -> None:
    gold = fuse_gold([[hit("k", DocumentKind.ACT)]], claim_date=CLAIM)
    bronze = [
        Passage(passage_id=i, source_id=s, text=i, published_on=None, fetched_at=AT)
        for i, s in (("b1", "k"), ("b2", "news"), ("b3", "news"))
    ]

    merged = merge_with_bronze(gold, bronze, covered={"k"}, limit=2)

    assert [p.passage_id for p in merged] == ["gold:k", "b2"]


def test_gold_chunk_offsets_must_span_its_text() -> None:
    with pytest.raises(ValidationError):
        GoldChunk(
            chunk_id="c",
            source_id="s",
            checksum="x",
            start_offset=10,
            end_offset=12,
            text="abc",
            header="",
            kind=DocumentKind.ACT,
        )
