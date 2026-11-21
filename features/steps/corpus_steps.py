"""Steps for features/corpus.feature: search through the port on the in-memory corpus.

The in-memory adapter and the stub embeddings stand in for PostgreSQL and Vertex AI;
the same scenarios run against the real database in tests/corpus (integration).
"""

import asyncio
import os
from datetime import UTC, date, datetime, timedelta

import httpx2
from behave import given, then, when
from behave.runner import Context
from google.oauth2.credentials import Credentials
from pydantic import ValidationError

from meritum_core.corpus import CorpusSettings, Passage, build_corpus_search
from meritum_core.shared.embeddings import EmbeddingsSettings, build_embeddings

VERSION = "2026-11-21T17:00"
CLAIM_DATE = date(2026, 11, 20)
DISTRACTORS = (
    "Sejm uchwalił ustawę o podatku od nieruchomości",
    "Ceny paliw na stacjach w listopadzie",
    "Rozkład jazdy pociągów regionalnych w województwie śląskim",
    "Szczepienia przeciw grypie w aptekach",
    "Wyniki matur z matematyki w 2026 roku",
    "Komunikat o jakości wody w Krakowie",
)


def _passage(passage_id: str, text: str, published_on: date | None) -> Passage:
    fetched = datetime(2026, 11, 21, tzinfo=UTC)
    return Passage(
        passage_id=passage_id,
        source_id=f"src-{passage_id}",
        text=text,
        published_on=published_on,
        fetched_at=fetched,
    )


def _search(context: Context, query: str) -> None:
    search = build_corpus_search(
        CorpusSettings(provider="memory"),
        build_embeddings(EmbeddingsSettings(provider="stub")),
        snapshots={VERSION: context.passages},
    )
    found = asyncio.run(
        search.search(query, claim_date=CLAIM_DATE, corpus_version=VERSION)
    )
    context.found = [p.passage_id for p in found]


@given('w korpusie jest fragment "{text}"')
def given_corpus_has_passage(context: Context, text: str) -> None:
    """The passage among unrelated ones, all published a week before the claim."""
    week_ago = CLAIM_DATE - timedelta(days=7)
    others = [_passage(f"d{i}", t, week_ago) for i, t in enumerate(DISTRACTORS)]
    context.passages = [*others, _passage("target", text, week_ago)]


@when('system szuka "{query}"')
def when_system_searches(context: Context, query: str) -> None:
    """Search the pinned snapshot."""
    _search(context, query)


@then("fragment jest w pierwszych 5 wynikach")
def then_passage_in_top_five(context: Context) -> None:
    """The inflected query still finds the passage."""
    assert "target" in context.found[:5]


@given(
    "dwa fragmenty o podobnym dopasowaniu, "
    "opublikowane 3 dni i 400 dni przed datą twierdzenia"
)
def given_fresh_and_stale(context: Context) -> None:
    """Same wording, different publication dates; the stale one is listed first."""
    text = "Komunikat IMGW o przymrozkach w województwie mazowieckim"
    context.passages = [
        _passage("aged", text, CLAIM_DATE - timedelta(days=400)),
        _passage("fresh", text, CLAIM_DATE - timedelta(days=3)),
    ]


@when("system szuka dla tego twierdzenia")
def when_system_searches_for_claim(context: Context) -> None:
    """Search with the claim's wording and date."""
    _search(context, "przymrozki na Mazowszu")


@then("świeższy fragment jest wyżej")
def then_fresh_ranks_higher(context: Context) -> None:
    """Freshness weighting breaks the tie."""
    assert context.found.index("fresh") < context.found.index("aged")


@given("korpus po ponownym przeliczeniu")
def given_corpus_reembedded(context: Context) -> None:
    """Re-embed passages with the default Vertex settings, Vertex answering offline."""
    for name in ("MERITUM_EMBEDDINGS_MODEL", "MERITUM_EMBEDDINGS_REGION"):
        context.add_cleanup(_restore_env, name, os.environ.pop(name, None))
    context.settings = EmbeddingsSettings(provider="vertex", project="meritum-test")
    context.sent = []

    def reply(request: httpx2.Request) -> httpx2.Response:
        context.sent.append(request)
        return httpx2.Response(200, json={"predictions": [_PREDICTION] * 3})

    client = httpx2.AsyncClient(transport=httpx2.MockTransport(reply), timeout=60)
    token = Credentials(token="recorded")  # ruff: ignore[hardcoded-password-func-arg]  # fake token, no network
    port = build_embeddings(context.settings, credentials=token, http_client=client)
    asyncio.run(port.embed_documents(DISTRACTORS[:3]))


@when("sprawdzam metadane przebiegów embeddingów i logi Vertex AI")
def when_checking_run_metadata(context: Context) -> None:
    """Collect the run's model and region and every Vertex request path."""
    context.run = (context.settings.model, context.settings.region)
    context.paths = [request.url.path for request in context.sent]


@then(
    "każdy wektor pochodzi z regionu UE wybranego modelu, "
    "a wektory z us-central1 są usunięte"
)
def then_vectors_come_from_the_eu(context: Context) -> None:
    """Warsaw and gemini-embedding-001 by default; us-central1 cannot be configured."""
    assert context.run == ("gemini-embedding-001", "europe-central2")
    assert context.paths
    for path in context.paths:
        assert "/locations/europe-central2/" in path
        assert path.endswith("/models/gemini-embedding-001:predict")
    assert not _accepts_region("us-central1")


def _accepts_region(region: str) -> bool:
    try:
        EmbeddingsSettings(provider="vertex", region=region)
    except ValidationError:
        return False
    return True


def _restore_env(name: str, value: str | None) -> None:
    if value is not None:
        os.environ[name] = value


_PREDICTION = {"embeddings": {"values": [0.6, 0.8]}}
