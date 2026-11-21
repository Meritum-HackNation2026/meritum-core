"""Inputs of the verbatim citation check.

Features:
    US-ZRD-01, F-16, ADR-06
"""

from dataclasses import dataclass

from pydantic import BaseModel, ConfigDict

from meritum_core.checks.contracts import Source, Stance, Validity


class CitationDraft(BaseModel):
    """A citation as the model returns it, before the verbatim check.

    Only the source id, fragment, stance and validity are read; any title,
    publisher, date or link the model adds is ignored (``extra="ignore"``).

    Attributes:
        source_id: The id of the cited document in the corpus.
        fragment: The fragment the model claims to quote (untrusted).
        stance: Whether the fragment supports, refutes or gives context.
        validity: The age rule the model set for this piece of evidence.

    Features:
        US-ZRD-01, F-16, ADR-06
    """

    model_config = ConfigDict(frozen=True, extra="ignore")

    source_id: str
    fragment: str
    stance: Stance
    validity: Validity = "expires"


@dataclass(frozen=True, slots=True)
class SourceDocument:
    """A corpus document as the database holds it: metadata and full text.

    Attributes:
        source: Title, publisher, date and link from the database.
        text: The full source text the fragment must occur in (data, never
            instructions).

    Features:
        US-ZRD-01, F-16, ADR-06
    """

    source: Source
    text: str
