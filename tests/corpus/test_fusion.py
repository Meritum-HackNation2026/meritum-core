"""fuse_rankings: reciprocal rank fusion weighted by freshness against the claim date."""

from datetime import UTC, date, datetime, timedelta

import pytest

from meritum_core.corpus import Passage, freshness_weight, fuse_rankings

CLAIM_DATE = date(2026, 11, 20)


def passage(passage_id: str, *, age_days: int | None = 7) -> Passage:
    published = None if age_days is None else CLAIM_DATE - timedelta(days=age_days)
    return Passage(
        passage_id=passage_id,
        source_id="src",
        text=passage_id,
        published_on=published,
        fetched_at=datetime(2026, 11, 21, tzinfo=UTC),
    )


def ids(passages: list[Passage]) -> list[str]:
    return [p.passage_id for p in passages]


def test_passage_found_by_several_rankings_beats_one_found_by_a_single_ranking() -> (
    None
):
    a, b, c = passage("a"), passage("b"), passage("c")
    fused = fuse_rankings([[b, a], [a, c], [a]], claim_date=CLAIM_DATE, limit=10)
    assert ids(fused)[0] == "a"


def test_each_passage_appears_once_with_its_fused_score() -> None:
    a, b = passage("a"), passage("b")
    fused = fuse_rankings([[a, b], [b, a]], claim_date=CLAIM_DATE, limit=10)
    assert sorted(ids(fused)) == ["a", "b"]
    assert all(p.score > 0 for p in fused)


def test_fresher_passage_beats_a_slightly_better_but_older_match() -> None:
    # "aged" ranks first in both rankings and wins ties by id: only freshness lifts "fresh".
    aged, fresh = passage("aged", age_days=400), passage("fresh", age_days=3)
    fused = fuse_rankings(
        [[aged, fresh], [aged, fresh]], claim_date=CLAIM_DATE, limit=10
    )
    assert ids(fused) == ["fresh", "aged"]


def test_much_better_match_still_wins_over_freshness() -> None:
    old, new = passage("old", age_days=400), passage("new", age_days=3)
    filler = [passage(f"f{i}") for i in range(20)]
    rankings = [[old, *filler, new], [old, *filler, new], [old, *filler]]
    fused = ids(fuse_rankings(rankings, claim_date=CLAIM_DATE, limit=30))
    assert fused.index("old") < fused.index("new")


def test_limit_caps_the_results() -> None:
    many = [passage(f"p{i}") for i in range(10)]
    assert len(fuse_rankings([many], claim_date=CLAIM_DATE, limit=3)) == 3


def test_no_rankings_give_no_results() -> None:
    assert fuse_rankings([], claim_date=CLAIM_DATE, limit=5) == []


@pytest.mark.parametrize(
    ("age_days", "expected"),
    [(0, 1.0), (-5, 1.0), (None, 0.5)],
)
def test_freshness_weight_edges(age_days: int | None, expected: float) -> None:
    published = None if age_days is None else CLAIM_DATE - timedelta(days=age_days)
    assert freshness_weight(published, CLAIM_DATE) == pytest.approx(expected)


def test_freshness_weight_decays_with_age_but_never_below_the_floor() -> None:
    weights = [
        freshness_weight(CLAIM_DATE - timedelta(days=d), CLAIM_DATE)
        for d in (3, 180, 400, 10_000)
    ]
    assert weights == sorted(weights, reverse=True)
    assert weights[1] == pytest.approx(0.75)
    assert weights[-1] >= 0.5


@pytest.mark.parametrize("limit", [0, -1])
def test_limit_below_one_is_rejected(limit: int) -> None:
    with pytest.raises(ValueError, match="limit"):
        fuse_rankings([[passage("a")]], claim_date=CLAIM_DATE, limit=limit)
