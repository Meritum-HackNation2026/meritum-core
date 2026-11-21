"""The WebSearchProviderPort contract, shipped so core/024 runs it on its adapters.

A test calls ``provider_contract_violations(provider)`` on an adapter that answers
the query with results (recorded or stubbed) and expects an empty list.

Features:
    US-KOR-04, US-WDR-02, F-13
"""

from urllib.parse import urlsplit

from meritum_core.corpus.web_search.constants import CONTRACT_QUERY, WEB_SCHEMES
from meritum_core.corpus.web_search.ports import WebSearchProviderPort


def _is_web_url(url: str) -> bool:
    parts = urlsplit(url)
    return parts.scheme in WEB_SCHEMES and bool(parts.hostname)


async def provider_contract_violations(provider: WebSearchProviderPort) -> list[str]:
    """Check one provider adapter against the port's promises.

    Args:
        provider: the adapter, set up to answer ``CONTRACT_QUERY`` with at
            least two results.

    Returns:
        A message per broken promise; empty when the adapter keeps them all.

    Features:
        US-KOR-04, US-WDR-02, F-13
    """
    limit = 10
    several = await provider.search(CONTRACT_QUERY, limit=limit)
    one = await provider.search(CONTRACT_QUERY, limit=1)
    checks = {
        "returned nothing for a query with results": bool(several),
        f"returned {len(several)} addresses for limit {limit}": len(several) <= limit,
        f"returned {len(one)} addresses for limit 1": len(one) <= 1,
        "returned an address that is not an absolute http(s) URL": all(
            map(_is_web_url, several)
        ),
        "result is not a list of str": isinstance(several, list)
        and all(isinstance(u, str) for u in several),
    }
    return [message for message, holds in checks.items() if not holds]
