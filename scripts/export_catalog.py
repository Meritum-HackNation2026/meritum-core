"""Export the source catalogue: catalog/catalog.json and the audit table in README.md.

    uv run python scripts/export_catalog.py           write both
    uv run python scripts/export_catalog.py --check   fail if either is stale (CI)

meritum-frontend copies catalog/catalog.json with ``pnpm sync``; never edit it by
hand, change src/meritum_core/corpus/catalog/catalog.yaml and run this script.

Features:
    US-KOR-01, F-10
"""

import sys
from pathlib import Path

from meritum_core.corpus.catalog import catalog_json, catalog_markdown, load_catalog

ROOT = Path(__file__).resolve().parent.parent
JSON_FILE = ROOT / "catalog" / "catalog.json"
README = ROOT / "README.md"
START = "<!-- catalog:start (scripts/export_catalog.py) -->"
END = "<!-- catalog:end -->"


def readme_with(table: str, readme: str) -> str:
    """Replace the README text between the catalogue markers with ``table``.

    Args:
        table: the Markdown audit table.
        readme: the current README text.

    Returns:
        The README with the new table.

    Raises:
        SystemExit: The README lacks the markers.
    """
    head, found_start, rest = readme.partition(START)
    _, found_end, tail = rest.partition(END)
    if not (found_start and found_end):
        msg = f"README.md needs the markers {START!r} and {END!r}"
        raise SystemExit(msg)
    return f"{head}{START}\n{table}\n{END}{tail}"


def main(*, check: bool) -> int:
    """Write the exports, or with ``check`` report the stale ones.

    Args:
        check: compare instead of writing.

    Returns:
        The exit code: 1 when ``check`` finds a stale export.
    """
    entries = load_catalog()
    readme = README.read_text(encoding="utf-8")
    wanted = {
        JSON_FILE: catalog_json(entries),
        README: readme_with(catalog_markdown(entries), readme),
    }
    stale = [
        p
        for p, text in wanted.items()
        if not p.exists() or p.read_text(encoding="utf-8") != text
    ]
    if not check:
        for path in stale:
            path.write_text(wanted[path], encoding="utf-8")
        return 0
    for path in stale:
        name = path.relative_to(ROOT)
        sys.stderr.write(f"::error file={name}::stale, run scripts/export_catalog.py\n")
    return 1 if stale else 0


if __name__ == "__main__":
    sys.exit(main(check="--check" in sys.argv[1:]))
