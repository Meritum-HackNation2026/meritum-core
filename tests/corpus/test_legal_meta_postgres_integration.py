"""PostgresLegalActMeta on a real database: local only, ``uv run pytest -m integration``.

Needs the meritum-postgres image and ``MERITUM_CORPUS_DATABASE_URL``. Applies
every corpus migration twice and removes only the documents it added.

Features:
    US-KOR-02, F-12
"""

import asyncio
import os
import uuid
from collections.abc import Iterator
from datetime import date
from importlib.resources import files

import psycopg
import pytest

from meritum_core.corpus import (
    CorpusSettings,
    CorpusUnavailableError,
    LegalActMeta,
    build_legal_act_meta,
)

MIGRATIONS = files("meritum_core.corpus") / "migrations"
DOCUMENT = """
INSERT INTO corpus.documents (source_id, url, domain, publisher_id, license,
    fetched_at, checksum)
VALUES (%s, %s, 'api.sejm.gov.pl', 'sejm', 'public', now(), 'x')
"""
ACT = LegalActMeta(
    eli="DU/2024/1362",
    document_type="Rozporządzenie",
    legal_status="akt jednorazowy",
    in_force=False,
    in_force_from=date(2025, 1, 1),
    in_force_until=date(2025, 12, 31),
    journal_publisher="DU",
    journal_year=2024,
    journal_position=1362,
    display_address="Dz.U. 2024 poz. 1362",
)


@pytest.fixture
def corpus() -> Iterator[tuple[str, str]]:
    """Migrated corpus and this test's id prefix; returns (url, prefix)."""
    url = os.environ.get("MERITUM_CORPUS_DATABASE_URL", "")
    if not url:
        pytest.skip("set MERITUM_CORPUS_DATABASE_URL to the meritum-postgres image")
    scripts = sorted(
        (f for f in MIGRATIONS.iterdir() if f.name.endswith(".sql")),
        key=lambda f: f.name,
    )
    with psycopg.connect(url, autocommit=True) as conn:
        conn.execute("CREATE SCHEMA IF NOT EXISTS corpus")  # the platform's job
        for _ in range(2):
            for script in scripts:
                conn.execute(script.read_bytes())
    prefix = uuid.uuid4().hex
    yield url, prefix
    with psycopg.connect(url, autocommit=True) as conn:
        conn.execute(
            "DELETE FROM corpus.documents WHERE source_id LIKE %s", (f"{prefix}%",)
        )


@pytest.mark.integration
def test_issue_scenario_act_has_meta_and_page_has_none(
    corpus: tuple[str, str],
) -> None:
    url, prefix = corpus
    act, page = f"{prefix}-act", f"{prefix}-page"
    with psycopg.connect(url, autocommit=True) as conn:
        conn.execute(DOCUMENT, (act, f"https://api.sejm.gov.pl/{act}"))
        conn.execute(DOCUMENT, (page, f"https://gov.pl/{page}"))
    store = build_legal_act_meta(CorpusSettings(provider="postgres", database_url=url))
    asyncio.run(
        store.save(act, ACT.model_copy(update={"legal_status": "obowiązujący"}))
    )
    asyncio.run(store.save(act, ACT))
    assert asyncio.run(store.read([act, page])) == {act: ACT}


@pytest.mark.integration
def test_meta_goes_with_its_document_and_needs_one(corpus: tuple[str, str]) -> None:
    url, prefix = corpus
    act = f"{prefix}-act"
    store = build_legal_act_meta(CorpusSettings(provider="postgres", database_url=url))
    with pytest.raises(CorpusUnavailableError):
        asyncio.run(store.save(act, ACT))
    with psycopg.connect(url, autocommit=True) as conn:
        conn.execute(DOCUMENT, (act, f"https://api.sejm.gov.pl/{act}"))
    asyncio.run(store.save(act, ACT))
    with psycopg.connect(url, autocommit=True) as conn:
        conn.execute("DELETE FROM corpus.documents WHERE source_id = %s", (act,))
    assert asyncio.run(store.read([act])) == {}
