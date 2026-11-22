"""Page fetcher settings from ``MERITUM_FETCH_*``: whether Crawl4AI renders JS pages.

Features:
    US-SPR-07, US-KOR-03, F-06, ADR-32
"""

from pydantic import HttpUrl, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from meritum_core.corpus.fetching.constants import ENV_PREFIX


class FetchingSettings(BaseSettings):
    """Page fetcher configuration read from ``MERITUM_FETCH_*`` variables.

    Attributes:
        crawl4ai_url: base URL of the local Crawl4AI service (``http://crawl4ai:11235``);
            None (default) leaves pages that need JavaScript as
            ``javascript_required``.
        crawl4ai_token: the service's ``CRAWL4AI_API_TOKEN``, sent as a bearer token.

    Features:
        US-SPR-07, US-KOR-03, F-06, ADR-32
    """

    model_config = SettingsConfigDict(env_prefix=ENV_PREFIX, frozen=True)

    crawl4ai_url: HttpUrl | None = None
    crawl4ai_token: SecretStr | None = None
