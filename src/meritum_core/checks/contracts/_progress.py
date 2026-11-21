"""Progress of a running check, polled or streamed by every channel.

Features:
    US-SPR-02, ADR-02
"""

from typing import Annotated, Literal

from pydantic import Field

from ._base import _Model
from ._results import CheckResult


class AnalysisStep(_Model):
    """One step of the processing strip shown between „Sprawdź” and the result.

    Attributes:
        code: which step of the pipeline.
        status: the step's state.

    Features:
        US-SPR-02, US-SPR-11, ADR-02
    """

    code: Literal[
        "receive",
        "fetch_url",
        "transcribe_audio",
        "screen_injection",
        "extract_claims",
        "search_corpus",
        "search_web",
        "search_fact_checks",
        "assess_evidence",
        "verify_citations",
        "write_answer",
        "save_record",
    ]
    status: Literal["pending", "active", "done", "skipped", "failed"]


class AnalysisStatus(_Model):
    """Polled (or streamed) by every channel while a check runs; mirrors the DBOS workflow.

    Attributes:
        check_id: the running check.
        steps: the processing steps in order.
        result: the result, once the check finished.

    Features:
        US-SPR-02, ADR-02
    """

    check_id: str
    steps: Annotated[list[AnalysisStep], Field(min_length=1)]
    result: CheckResult | None = None
