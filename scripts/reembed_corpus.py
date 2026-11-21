"""Re-embed every corpus passage in place with the configured EU model (core#64).

Local, one-off; never in CI. Reads ``MERITUM_EMBEDDINGS_*`` (provider ``vertex``,
region checked against the EU list) and ``MERITUM_CORPUS_DATABASE_URL``, then
prints one JSON line describing the run: model, region, dimensions, passage
count, start and end time. Usage (variables as in the README)::

    uv run python scripts/reembed_corpus.py

Features:
    US-KOR-02, F-12, ADR-04, ADR-14
"""

import asyncio
import json
import sys
from datetime import UTC, datetime

from psycopg import AsyncConnection
from pydantic import ValidationError

from meritum_core.corpus import CorpusSettings
from meritum_core.shared.embeddings import (
    EmbeddingsPort,
    EmbeddingsProvider,
    EmbeddingsSettings,
    build_embeddings,
)
from meritum_core.shared.embeddings.constants import DEFAULT_DIMENSIONS, DEFAULT_MODEL

BATCH = 8
"""Passages per Vertex call: 8 x 2048 tokens stays under the 20,000-token cap."""

USAGE_ERROR = 2
"""Exit code when the settings do not describe an EU Vertex run on a database."""

_SELECT = """
SELECT passage_id, text FROM corpus.passages
WHERE passage_id LIKE %s ORDER BY passage_id
"""
_UPDATE = "UPDATE corpus.passages SET embedding = %s::vector WHERE passage_id = %s"


async def reembed(
    conninfo: str,
    embeddings: EmbeddingsPort,
    *,
    batch: int = BATCH,
    passage_ids: str = "%",
) -> int:
    """Replace the vector of every passage, committing after each batch.

    Args:
        conninfo: libpq connection string of the database with the ``corpus`` schema.
        embeddings: The model the corpus is re-embedded with.
        batch: Passages per embeddings call.
        passage_ids: SQL ``LIKE`` pattern of the passages to re-embed; all by default.

    Returns:
        How many passages got a new vector.

    Features:
        US-KOR-02, F-12, ADR-04, ADR-14
    """
    async with await AsyncConnection.connect(conninfo) as conn:
        # shortcut: loads all ids and texts at once; page by passage_id once the
        # corpus outgrows a few hundred MB of text.
        rows = await (await conn.execute(_SELECT, (passage_ids,))).fetchall()
        for start in range(0, len(rows), batch):
            chunk = rows[start : start + batch]
            vectors = await embeddings.embed_documents([text for _, text in chunk])
            params = [
                ("[" + ",".join(map(str, vector)) + "]", passage_id)
                for (passage_id, _), vector in zip(chunk, vectors, strict=True)
            ]
            async with conn.cursor() as cursor:
                await cursor.executemany(_UPDATE, params)
            await conn.commit()
        return len(rows)


def main() -> int:
    """Run the re-embedding and print its metadata as one JSON line.

    Returns:
        0 on success, ``USAGE_ERROR`` when the settings are not an EU Vertex run
        of the chosen model with the corpus table's vector size.

    Features:
        US-KOR-02, F-12, ADR-04, ADR-14
    """
    try:
        settings = EmbeddingsSettings()
        database_url = CorpusSettings().database_url
    except ValidationError as exc:
        sys.stderr.write(f"{exc}\n")
        return USAGE_ERROR
    is_vertex = settings.provider is EmbeddingsProvider.VERTEX
    is_chosen_model = settings.model == DEFAULT_MODEL
    fits_the_table = settings.dimensions == DEFAULT_DIMENSIONS
    is_chosen_run = is_vertex and is_chosen_model and fits_the_table
    if not is_chosen_run or database_url is None:
        sys.stderr.write(
            "set MERITUM_EMBEDDINGS_PROVIDER=vertex and MERITUM_CORPUS_DATABASE_URL;"
            f" the run uses {DEFAULT_MODEL} with {DEFAULT_DIMENSIONS} dimensions\n"
        )
        return USAGE_ERROR
    started_at = datetime.now(UTC)
    count = asyncio.run(
        reembed(database_url.get_secret_value(), build_embeddings(settings))
    )
    run = {
        "model": settings.model,
        "region": settings.region,
        "dimensions": settings.dimensions,
        "passages": count,
        "started_at": started_at.isoformat(),
        "finished_at": datetime.now(UTC).isoformat(),
    }
    sys.stdout.write(json.dumps(run) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
