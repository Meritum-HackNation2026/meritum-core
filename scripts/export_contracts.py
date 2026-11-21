"""Write contracts/meritum.schema.json from meritum_core.checks.contracts.

Run through scripts/generate-contracts.sh, which also writes contracts/meritum.ts.
"""

import json
import sys
from pathlib import Path
from typing import Any

from pydantic import TypeAdapter

from meritum_core.checks import contracts as c

ROOTS: dict[str, Any] = {
    "CheckRequest": c.CheckRequest,
    "CheckResult": c.CheckResult,
    "AnalysisStatus": c.AnalysisStatus,
    "CheckRecord": c.CheckRecord,
    "ModeratorCase": c.ModeratorCase,
    "CatalogEntry": c.CatalogEntry,
}


def schema_document() -> dict[str, object]:
    """Build one JSON Schema with every root contract under $defs.

    Returns:
        The schema document, with the contract version.
    """
    defs: dict[str, object] = {}
    for name, tp in ROOTS.items():
        schema = TypeAdapter(tp).json_schema(ref_template="#/$defs/{model}")
        defs.update(schema.pop("$defs", {}))
        defs[name] = schema
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "Meritum contracts",
        "x-contract-version": c.CONTRACT_VERSION,
        "$defs": defs,
    }


if __name__ == "__main__":
    out = Path(sys.argv[1])
    text = json.dumps(schema_document(), ensure_ascii=False, indent=2) + "\n"
    out.write_text(text, encoding="utf-8")
