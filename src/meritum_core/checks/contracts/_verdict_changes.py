"""The one rule that says what would change a verdict, read from its premises.

Features:
    US-ZRD-11, F-17, ADR-05
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from meritum_core.checks.constants import SETTLING, STRONG_MIN_SOURCES

from ._strength import is_stale

if TYPE_CHECKING:
    from ._strength import Premises
    from ._types import Verdict, VerdictChange


def verdict_changes_for(
    verdict: Verdict,
    premises: Premises | None,
    unresolved: str | None,
    *,
    conflicting: bool,
) -> list[VerdictChange]:
    """List, in a fixed order, the evidence that would change the verdict.

    Only what the premises lack is named, never a new fact: a settling verdict
    asks for a primary source, a second publisher or fresh evidence it does not
    have; conflicting sources ask for a source that resolves them; nothing found
    with a note of what is missing asks for a named source.

    Args:
        verdict: the verdict of the claim.
        premises: the premises of a settling verdict, None otherwise.
        unresolved: what could not be established.
        conflicting: whether current evidence both supports and refutes the claim.

    Returns:
        The codes the channel words from copy/pl.json; empty when nothing is missing.

    Features:
        US-ZRD-11, F-17, ADR-05
    """
    if conflicting:
        return ["needs_resolving_source"]
    if verdict == "insufficient_evidence":
        return ["needs_named_source"] if bool(unresolved) else []
    if verdict not in SETTLING or premises is None:
        return []
    codes: list[VerdictChange] = []
    if premises.primary_sources == 0:
        codes.append("needs_primary_source")
    if premises.independent_sources < STRONG_MIN_SOURCES:
        codes.append("needs_second_publisher")
    if is_stale(premises):
        codes.append("needs_fresh_evidence")
    return codes
