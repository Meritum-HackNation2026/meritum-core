"""Models of the `archive_page` workflow: one public page archived for a citizen.

Features:
    US-KOR-07, F-38, ADR-03
"""

from typing import Annotated, Literal

from pydantic import AwareDatetime, Field

from meritum_core.jobs.constants import ARCHIVE_URL_MAX_CHARS, ARCHIVE_URL_PATTERN
from meritum_core.jobs.contracts._base import Identifier, JobModel

ArchiveRefusalCode = Literal[
    "login_wall", "robots_or_tdm", "fetch_failed", "rate_limited"
]
"""Why no copy was made (the worker's ``ArchiveRefusal``)."""


class ArchivePageInput(JobModel):
    """Input of the `archive_page` workflow.

    Attributes:
        archive_id: the copy's id, chosen by the backend; also the workflow id,
            so the client polls it.
        url: the page; only http(s), the worker's SSRF-safe fetcher checks the rest.
        owner_id: the session or user who asked; only they and moderators see it.

    Features:
        US-KOR-07, F-38
    """

    archive_id: Identifier
    url: Annotated[
        str, Field(max_length=ARCHIVE_URL_MAX_CHARS, pattern=ARCHIVE_URL_PATTERN)
    ]
    owner_id: Identifier


class ArchivePageOutput(JobModel):
    """Output of the `archive_page` workflow: the stored copy or a refusal.

    Attributes:
        archive_id: the copy's id.
        owner_id: who asked, so the backend can check access to a refusal.
        url: the final URL after redirects; None when refused.
        sha256: hash of the stored bytes; None when refused.
        archived_at: when the copy was made; None when refused.
        expires_at: when retention deletes it; None when refused.
        refusal: why there is no copy.
        message: what the citizen is told when refused.

    Features:
        US-KOR-07, F-38
    """

    archive_id: Identifier
    owner_id: Identifier
    url: str | None = None
    sha256: str | None = None
    archived_at: AwareDatetime | None = None
    expires_at: AwareDatetime | None = None
    refusal: ArchiveRefusalCode | None = None
    message: str | None = None
