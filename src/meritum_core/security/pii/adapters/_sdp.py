"""Google Sensitive Data Protection (DLP API v2) adapter over REST, EU region only.

One ``content:deidentify`` call on the regional endpoint replaces every finding
of ``INFO_TYPE_MARKERS`` with its marker.

Features:
    US-BEZ-04, F-20, ADR-13, ADR-14, ADR-35
"""

import asyncio

from google.auth import default as adc_lookup
from google.auth.credentials import Credentials
from google.auth.exceptions import GoogleAuthError
from google.auth.transport.requests import Request
from httpx2 import AsyncClient, TransportError
from pydantic import BaseModel, Field, JsonValue, ValidationError

from meritum_core.security.pii.constants import (
    ENDPOINT,
    HTTP_TIMEOUT_SECONDS,
    INFO_TYPE_MARKERS,
    MIN_LIKELIHOOD,
    QUOTA_PROJECT_HEADER,
    SCOPES,
    SUCCESS_CODE,
)
from meritum_core.security.pii.errors import PiiGateUnavailableError
from meritum_core.security.pii.models import MaskedText
from meritum_core.security.pii.settings import PiiGateSettings


class _Item(BaseModel):
    value: str


class _Result(BaseModel):
    count: int = 0
    code: str = ""


class _Summary(BaseModel):
    results: list[_Result] = []


class _Overview(BaseModel):
    summaries: list[_Summary] = Field(default=[], alias="transformationSummaries")


class _Reply(BaseModel):
    item: _Item  # required: a reply without the text must not blank it
    overview: _Overview = _Overview()


def _deidentify_config() -> dict[str, JsonValue]:
    transformations: list[JsonValue] = [
        {
            "infoTypes": [{"name": info_type}],
            "primitiveTransformation": {
                "replaceConfig": {"newValue": {"stringValue": marker}}
            },
        }
        for info_type, marker in INFO_TYPE_MARKERS.items()
    ]
    return {"infoTypeTransformations": {"transformations": transformations}}


def _inspect_config() -> dict[str, JsonValue]:
    info_types: list[JsonValue] = [{"name": name} for name in INFO_TYPE_MARKERS]
    return {"infoTypes": info_types, "minLikelihood": MIN_LIKELIHOOD}


class SensitiveDataProtectionGate:
    """PiiGatePort on Google Sensitive Data Protection in an EU region (ADR-35).

    Args:
        settings: Validated ``sdp`` settings (the project is set).
        credentials: Google credentials; Application Default Credentials when None.
        http_client: HTTP client to use; tests pass one with recorded replies.

    Features:
        US-BEZ-04, F-20, ADR-13, ADR-14, ADR-35
    """

    def __init__(
        self,
        settings: PiiGateSettings,
        *,
        credentials: Credentials | None = None,
        http_client: AsyncClient | None = None,
    ) -> None:
        self._credentials = credentials
        self._client = http_client or AsyncClient(timeout=HTTP_TIMEOUT_SECONDS)
        location = settings.location
        self._project = str(settings.project)
        self._url = (
            f"{ENDPOINT.format(location=location)}/projects/{settings.project}"
            f"/locations/{location}/content:deidentify"
        )

    async def mask(self, text: str) -> MaskedText:
        """Replace the configured infoTypes in ``text`` with their markers.

        Args:
            text: Free text that may contain personal data.

        Returns:
            The masked text and how many findings were replaced.

        Raises:
            PiiGateUnavailableError: No reply, a rejected request or credentials,
                a reply that did not parse, or a transformation that failed.
        """
        if not text:
            return MaskedText(text=text, replaced=0)  # DLP omits an empty value
        body: dict[str, JsonValue] = {
            "item": {"value": text},
            "inspectConfig": _inspect_config(),
            "deidentifyConfig": _deidentify_config(),
        }
        headers = {
            "Authorization": f"Bearer {await self._token()}",
            QUOTA_PROJECT_HEADER: self._project,
        }
        try:
            response = await self._client.post(self._url, json=body, headers=headers)
        except TransportError as exc:
            msg = f"sensitive data protection unreachable: {type(exc).__name__}"
            raise PiiGateUnavailableError(msg) from exc
        if not response.is_success:
            msg = f"sensitive data protection answered HTTP {response.status_code}"
            raise PiiGateUnavailableError(msg)
        return _parse_reply(response.content)

    async def _token(self) -> str:
        try:
            if self._credentials is None:
                self._credentials, _ = await asyncio.to_thread(
                    adc_lookup, scopes=SCOPES
                )
            credentials = self._credentials
            if not credentials.valid:
                await asyncio.to_thread(credentials.refresh, Request())
        except GoogleAuthError as exc:
            msg = "sensitive data protection credentials were refused"
            raise PiiGateUnavailableError(msg) from exc
        return str(credentials.token)


def _parse_reply(content: bytes) -> MaskedText:
    try:
        reply = _Reply.model_validate_json(content)
    except ValidationError:
        msg = "sensitive data protection reply did not parse"
        # from None: the validation error quotes the reply, which holds user text
        raise PiiGateUnavailableError(msg) from None
    results = [r for s in reply.overview.summaries for r in s.results]
    if any(r.code != SUCCESS_CODE for r in results):
        msg = "sensitive data protection could not apply a transformation"
        raise PiiGateUnavailableError(msg)
    return MaskedText(text=reply.item.value, replaced=sum(r.count for r in results))
