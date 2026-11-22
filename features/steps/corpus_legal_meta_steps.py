"""Steps for the legal act metadata scenario in features/corpus.feature.

CI has no database, so the steps go through ``LegalActMetaPort`` built for the
memory provider; tests/corpus/test_legal_meta_postgres_integration.py runs the
same writes and reads against PostgreSQL.

Features:
    US-KOR-02, F-12
"""

import asyncio
from datetime import date

from behave import given, then, when
from behave.runner import Context

from meritum_core.corpus import CorpusSettings, LegalActMeta, build_legal_act_meta

ACT_SOURCE = "src-du-2024-1362"
PAGE_SOURCE = "src-gov-page"


@given("akt {eli} z ELI z in_force_until {until}")
def given_act(context: Context, eli: str, until: str) -> None:
    """The minimum wage regulation for 2025, as ELI describes it."""
    publisher, year, position = eli.split("/")
    context.act = LegalActMeta(
        eli=eli,
        document_type="Rozporządzenie",
        legal_status="akt jednorazowy",
        in_force=False,
        in_force_from=date(2025, 1, 1),
        in_force_until=date.fromisoformat(until),
        journal_publisher=publisher,
        journal_year=int(year),
        journal_position=int(position),
        display_address=f"Dz.U. {year} poz. {position}",
    )


@when("ingest zapisuje dokument w corpus.documents")
def when_ingest_saves(context: Context) -> None:
    """Save the act's metadata; the page outside ELI gets none."""
    store = build_legal_act_meta(CorpusSettings(provider="memory"))
    asyncio.run(store.save(ACT_SOURCE, context.act))
    context.read = asyncio.run(store.read([ACT_SOURCE, PAGE_SOURCE]))


@then(
    'wiersz dokumentu ma eli "{eli}", document_type "{kind}" i in_force_until {until}'
)
def then_act_has_meta(context: Context, eli: str, kind: str, until: str) -> None:
    """Read the act's fields back."""
    meta = context.read[ACT_SOURCE]
    assert meta.eli == eli
    assert meta.document_type == kind
    assert meta.in_force_until == date.fromisoformat(until)


@then("dokument strony spoza ELI ma te pola puste")
def then_page_has_none(context: Context) -> None:
    """A page outside ELI has no metadata row."""
    assert PAGE_SOURCE not in context.read
