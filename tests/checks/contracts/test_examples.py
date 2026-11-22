"""Every example in contracts/examples.json validates against its root contract."""

from typing import Any

import pytest
from pydantic import TypeAdapter
from tests.checks.contracts.samples import EXAMPLES

from meritum_core.checks import contracts as c

ROOTS: dict[str, Any] = {
    "CheckRequest": c.CheckRequest,
    "CheckResult": c.CheckResult,
    "CachedResult": c.CachedResult,
    "AnalysisStatus": c.AnalysisStatus,
    "CheckRecord": c.CheckRecord,
    "ModeratorCase": c.ModeratorCase,
    "CatalogEntry": c.CatalogEntry,
    "Notification": c.Notification,
    "EvalRun": c.EvalRun,
}


@pytest.mark.parametrize("name", sorted(EXAMPLES))
def test_examples_are_valid(name: str) -> None:
    TypeAdapter(ROOTS[name.split(".", maxsplit=1)[0]]).validate_python(EXAMPLES[name])
