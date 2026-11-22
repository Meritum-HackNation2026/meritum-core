"""Maps one HTTP call of a search provider onto the web search errors.

Features:
    US-KOR-04, US-WDR-02, F-13
"""

from collections.abc import Awaitable

from httpx2 import Response, TimeoutException, TransportError, codes

from meritum_core.corpus.web_search.errors import (
    WebSearchRateLimitError,
    WebSearchTimeoutError,
    WebSearchUnavailableError,
)


async def checked_reply(name: str, call: Awaitable[Response]) -> bytes:
    """Await one provider call and return its body when it succeeded.

    Args:
        name: the provider, for error messages (never the query).
        call: the pending request.

    Returns:
        The body of a 2xx reply.

    Raises:
        WebSearchTimeoutError: The HTTP call timed out.
        WebSearchRateLimitError: The provider answered 429.
        WebSearchUnavailableError: A transport error or any other error status.

    Features:
        US-KOR-04, US-WDR-02, F-13
    """
    try:
        response = await call
    except TimeoutException as exc:
        msg = f"{name} timed out"
        raise WebSearchTimeoutError(msg) from exc
    except TransportError as exc:
        msg = f"{name} unreachable: {type(exc).__name__}"
        raise WebSearchUnavailableError(msg) from exc
    if response.status_code == codes.TOO_MANY_REQUESTS:
        msg = f"{name} quota exceeded (HTTP 429)"
        raise WebSearchRateLimitError(msg)
    if not response.is_success:
        msg = f"{name} failed: HTTP {response.status_code}"
        raise WebSearchUnavailableError(msg)
    return response.content
