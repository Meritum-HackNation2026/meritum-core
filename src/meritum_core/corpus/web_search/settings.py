"""Web search settings from ``MERITUM_WEB_SEARCH_*``: which provider answers.

Features:
    US-KOR-04, US-WDR-02, F-13
"""

from enum import StrEnum
from pathlib import Path
from typing import Self

from pydantic import Field, HttpUrl, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from meritum_core.corpus.web_search.constants import ENV_PREFIX, RESOURCE_ID_PATTERN


class WebSearchProvider(StrEnum):
    """Which adapter ``build_web_search`` builds.

    Features:
        US-KOR-04, US-WDR-02, F-13
    """

    STUB = "stub"
    VERTEX_SEARCH = "vertex_search"
    SEARXNG = "searxng"
    LINKUP = "linkup"


class WebSearchSettings(BaseSettings):
    """Web search configuration read from ``MERITUM_WEB_SEARCH_*`` variables.

    Attributes:
        provider: ``stub`` (default, no keys, no network), ``vertex_search``,
            ``searxng`` (the fallback) or ``linkup`` (optional).
        project: Google Cloud project of the search app; required for
            ``vertex_search``.
        engine: id of the Vertex AI Search app (engine) over the website data
            store; required for ``vertex_search``.
        stub_fixture: JSON list of result addresses the stub returns.
        searxng_url: base address of our SearXNG instance; required for ``searxng``.
        linkup_api_key: Linkup API key; required for ``linkup``.
        linkup_enabled: switch for Linkup; ``linkup`` is refused while it is off.

    Features:
        US-KOR-04, US-WDR-02, F-13
    """

    model_config = SettingsConfigDict(env_prefix=ENV_PREFIX, frozen=True)

    provider: WebSearchProvider = WebSearchProvider.STUB
    project: str | None = Field(default=None, pattern=RESOURCE_ID_PATTERN)
    engine: str | None = Field(default=None, pattern=RESOURCE_ID_PATTERN)
    stub_fixture: Path | None = None
    searxng_url: HttpUrl | None = None
    linkup_api_key: SecretStr | None = None
    linkup_enabled: bool = False

    @model_validator(mode="after")
    def _vertex_has_an_app(self) -> Self:
        needs_app = self.provider is WebSearchProvider.VERTEX_SEARCH
        if needs_app and (self.project is None or self.engine is None):
            msg = f"{ENV_PREFIX}PROJECT and _ENGINE are required for vertex_search"
            raise ValueError(msg)
        return self

    @model_validator(mode="after")
    def _fallbacks_are_configured(self) -> Self:
        if self.provider is WebSearchProvider.SEARXNG and self.searxng_url is None:
            msg = f"{ENV_PREFIX}SEARXNG_URL is required for searxng"
            raise ValueError(msg)
        if self.provider is WebSearchProvider.LINKUP:
            if self.linkup_api_key is None:
                msg = f"{ENV_PREFIX}LINKUP_API_KEY is required for linkup"
                raise ValueError(msg)
            if not self.linkup_enabled:
                msg = f"{ENV_PREFIX}LINKUP_ENABLED must be true for linkup"
                raise ValueError(msg)
        return self
