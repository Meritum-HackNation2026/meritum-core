"""Failures of live web search; messages never carry the query or provider text.

Every failure is a ``technical_failure`` of the check: without live search the
corpus alone answers, or the check ends without a verdict.

Features:
    US-KOR-04, US-WDR-02, F-13
"""

from typing import ClassVar

from meritum_core.checks.contracts import CheckStatus


class WebSearchError(Exception):
    """Base error of the web search port and its adapters.

    Attributes:
        check_status: The check status a workflow reports for it.

    Features:
        US-KOR-04, US-WDR-02, F-13
    """

    check_status: ClassVar[CheckStatus] = "technical_failure"


class WebSearchUnavailableError(WebSearchError):
    """The provider failed, refused the credentials or sent a reply that did not parse.

    Features:
        US-KOR-04, US-WDR-02, F-13
    """


class WebSearchTimeoutError(WebSearchError):
    """The search took longer than ``SEARCH_TIMEOUT_S``.

    Features:
        US-KOR-04, US-WDR-02, F-13
    """


class WebSearchRateLimitError(WebSearchError):
    """Over ``MAX_QUERIES_PER_MINUTE`` in this process, or the provider's quota (429).

    Features:
        US-KOR-04, US-WDR-02, F-13
    """
