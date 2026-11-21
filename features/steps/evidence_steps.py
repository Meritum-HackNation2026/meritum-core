"""Steps for features/evidence.feature: the verbatim citation check on one source."""

from typing import Any

from behave import given, then, when
from behave.runner import Context
from pydantic import ValidationError

from meritum_core.checks.contracts import ClaimResult, Source
from meritum_core.evidence import CitationDraft, SourceDocument, verify_citation

_SOURCE: dict[str, Any] = {
    "id": "imgw-ostrzezenie-1",
    "title": "Ostrzeżenia meteorologiczne",
    "publisher": "IMGW-PIB",
    "publisher_id": "imgw",
    "url": "https://meteo.imgw.pl/ostrzezenia",
    "domain": "meteo.imgw.pl",
    "kind": "instytucja",
    "tier": "primary",
    "fetched_at": "2026-11-21T12:00:00+01:00",
}


def _remember_source(context: Context, text: str) -> None:
    source = Source.model_validate(_SOURCE)
    context.sources = {source.id: SourceDocument(source=source, text=text)}


@given("źródło zawiera tekst „{text}”")
def given_source_text(context: Context, text: str) -> None:
    """The database holds one source with this text."""
    _remember_source(context, text)


@given('źródło nie zawiera zdania "{sentence}"')
def given_source_without(context: Context, sentence: str) -> None:
    """The database holds one source; the sentence is not in it."""
    _remember_source(context, "Komunikat IMGW: ostrzeżenie II stopnia do 18:00.")
    context.fragment = sentence


def _verify(context: Context) -> None:
    draft = CitationDraft(
        source_id=_SOURCE["id"], fragment=context.fragment, stance="supports"
    )
    context.citation = verify_citation(draft, context.sources)


@when('model zwraca cytat "{fragment}"')
def when_model_quotes(context: Context, fragment: str) -> None:
    """The model cites the source with this fragment."""
    context.fragment = fragment
    _verify(context)


@when("model zwraca ten cytat")
def when_model_quotes_it(context: Context) -> None:
    """The model cites the source with the sentence from the Given step."""
    _verify(context)


@then("cytat przechodzi weryfikację")
def then_citation_passes(context: Context) -> None:
    """The citation keeps the source's own wording and metadata."""
    assert context.citation is not None
    assert context.citation.fragment == "Ostrzeżenie  II stopnia obowiązuje do 18:00"
    assert context.citation.source.title == _SOURCE["title"]


@then("cytat nie trafia do odpowiedzi")
def then_citation_dropped(context: Context) -> None:
    """The invented fragment is dropped."""
    assert context.citation is None


@then("twierdzenie bez innego cytatu traci werdykt rozstrzygający")
def then_claim_cannot_settle(context: Context) -> None:
    """With no citation left, a settling verdict breaks the contract rules."""
    citations = [c for c in [context.citation] if c is not None]
    try:
        ClaimResult.model_validate(
            {
                "claim": "Szkoły w Polsce są zamknięte do odwołania.",
                "verdict": "confirmed",
                "strength": {
                    "level": "moderate",
                    "premises": {
                        "independent_sources": 1,
                        "primary_sources": 1,
                        "validity": "expires",
                        "agreement": "consistent",
                    },
                },
                "citations": citations,
                "explanation": "Źródło potwierdza zamknięcie szkół do odwołania.",
            }
        )
    except ValidationError as error:
        context.error = str(error)
    else:
        context.error = "accepted"
    assert "needs citations" in context.error
