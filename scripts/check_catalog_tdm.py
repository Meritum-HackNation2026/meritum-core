"""Manual check, local only (never in CI): read every catalogue owner's TDM opt-out.

Fetches each entry's root as a source through the SSRF-safe page fetcher, which
honours robots.txt and its Content-Signal, and prints the entries whose recorded
``tdm_reservation`` (or exclusion) differs from the result. The curator copies
the printed values into src/meritum_core/corpus/catalog/catalog.yaml.

    uv run python scripts/check_catalog_tdm.py
"""

import asyncio
import sys

from meritum_core.corpus.catalog import check_tdm, load_catalog
from meritum_core.corpus.fetching import build_page_fetcher


async def report() -> int:
    """Check every entry and print the differences.

    Returns:
        How many entries differ from the catalogue.
    """
    fetcher = build_page_fetcher()
    differ = 0
    for entry in load_catalog():
        checked = await check_tdm(entry, fetcher)
        if checked != entry:
            differ += 1
            sys.stdout.write(
                f"{entry.domain}: tdm_reservation {entry.tdm_reservation} -> "
                f"{checked.tdm_reservation}, excluded {checked.excluded}\n"
            )
    return differ


if __name__ == "__main__":
    sys.exit(1 if asyncio.run(report()) else 0)
