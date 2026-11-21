"""Manual check, local only (never in CI): read every catalogue owner's TDM opt-out.

Reads each entry's robots.txt Content-Signal and root-page meta tags through the
SSRF-safe page fetcher (``check_tdm``) and prints the entries whose recorded
``tdm_reservation`` or exclusion differs. ``--write`` saves the results into
src/meritum_core/corpus/catalog/catalog.yaml; run scripts/export_catalog.py after.

    uv run python scripts/check_catalog_tdm.py [--write]

Features:
    US-KOR-01, F-10, ADR-24
"""

import asyncio
import sys

from meritum_core.checks.contracts import CatalogEntry
from meritum_core.corpus.catalog import catalog_yaml, check_tdm, load_catalog
from meritum_core.corpus.constants import CATALOG_FILE
from meritum_core.corpus.fetching import build_page_fetcher


async def checked_catalogue() -> list[CatalogEntry]:
    """Check every entry and print the ones that changed.

    Returns:
        The catalogue with every result recorded.
    """
    fetcher = build_page_fetcher()
    checked: list[CatalogEntry] = []
    for entry in load_catalog():
        result = await check_tdm(entry, fetcher)
        if result != entry:
            sys.stdout.write(
                f"{entry.domain}: tdm_reservation {entry.tdm_reservation} -> "
                f"{result.tdm_reservation}, excluded {result.excluded}\n"
            )
        checked.append(result)
    return checked


if __name__ == "__main__":
    entries = asyncio.run(checked_catalogue())
    if "--write" in sys.argv[1:]:
        current = CATALOG_FILE.read_text(encoding="utf-8")
        CATALOG_FILE.write_text(catalog_yaml(entries, current), encoding="utf-8")
