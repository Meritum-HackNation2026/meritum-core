"""Cloud Vision adapter over REST: ``DOCUMENT_TEXT_DETECTION`` at the EU endpoint.

Features:
    US-SPR-08, F-33, ADR-30, ADR-14, ADR-31
"""

import asyncio
import base64

from google.auth import default as adc_lookup
from google.auth.credentials import Credentials
from google.auth.exceptions import GoogleAuthError
from google.auth.transport.requests import Request
from httpx2 import AsyncClient, TransportError, codes
from pydantic import BaseModel, Field, JsonValue, ValidationError

from meritum_core.checks.ocr.constants import (
    HTTP_TIMEOUT_SECONDS,
    RETRY_BACKOFF_SECONDS,
    VISION_ENDPOINT,
    VISION_FEATURES,
    VISION_LANGUAGE_HINTS,
    VISION_SCOPES,
)
from meritum_core.checks.ocr.errors import OcrUnavailableError
from meritum_core.checks.ocr.image import find_date, inspect_image
from meritum_core.checks.ocr.models import OcrResult
from meritum_core.checks.ocr.settings import OcrSettings
from meritum_core.shared.blobs import BlobStore


class _Status(BaseModel):
    message: str = ""


class _FullText(BaseModel):
    text: str = ""


class _Response(BaseModel):
    error: _Status | None = None
    full_text: _FullText = Field(default=_FullText(), alias="fullTextAnnotation")


class _Annotated(BaseModel):
    responses: list[_Response] = []


class VisionOcr:
    """OcrPort on Google Cloud Vision API in the EU (ADR-30).

    Args:
        settings: Validated ``vision`` settings (the project is set).
        blobs: The store holding the images.
        credentials: Google credentials; Application Default Credentials when None.
        http_client: HTTP client to use; tests pass one with recorded replies.

    Features:
        US-SPR-08, F-33, ADR-30, ADR-14, ADR-31
    """

    def __init__(
        self,
        settings: OcrSettings,
        blobs: BlobStore,
        *,
        credentials: Credentials | None = None,
        http_client: AsyncClient | None = None,
    ) -> None:
        self._blobs = blobs
        self._retries = settings.retries
        self._project = settings.project
        self._credentials = credentials
        self._client = http_client or AsyncClient(timeout=HTTP_TIMEOUT_SECONDS)

    async def read(self, image_id: str) -> OcrResult:
        """Send the image to Vision and return its text.

        Args:
            image_id: The blob id of the image.

        Returns:
            The text, its date candidate and the file metadata.

        Raises:
            UnsupportedImageError: Not a supported image (``inspect_image``).
            OcrUnavailableError: The provider failed or refused the credentials
                after the configured retries, rejected the image, or its reply
                did not parse.
            BlobNotFoundError: No image under ``image_id``.
        """  # ruff: ignore[docstring-extraneous-exception]  # raised by inspect_image and _send
        data = await self._blobs.get(image_id)
        info = inspect_image(data)
        body: dict[str, JsonValue] = {
            "requests": [
                {
                    "image": {"content": base64.b64encode(data).decode("ascii")},
                    "features": VISION_FEATURES,
                    "imageContext": {"languageHints": VISION_LANGUAGE_HINTS},
                }
            ]
        }
        reply = await self._send(body)
        try:
            annotated = _Annotated.model_validate_json(reply)
        except ValidationError as exc:
            msg = "vision reply is not an annotate response"
            raise OcrUnavailableError(msg) from exc
        if len(annotated.responses) != 1 or annotated.responses[0].error:
            msg = "vision rejected the image"
            raise OcrUnavailableError(msg)
        text = annotated.responses[0].full_text.text.strip()
        return OcrResult(text=text, claim_date=find_date(text), metadata=info)

    async def _send(self, body: dict[str, JsonValue]) -> bytes:
        """POST the request, retrying transient failures.

        Returns:
            The body of the first successful reply.

        Raises:
            OcrUnavailableError: Every attempt failed, or the provider rejected
                the request.
        """
        headers = {
            "Authorization": f"Bearer {await self._token()}",
            "x-goog-user-project": str(self._project),
        }
        last = "no reply"
        for attempt in range(self._retries):
            if attempt:
                await asyncio.sleep(RETRY_BACKOFF_SECONDS * 2 ** (attempt - 1))
            try:
                response = await self._client.post(
                    VISION_ENDPOINT, json=body, headers=headers
                )
            except TransportError as exc:
                last = f"{type(exc).__name__} on attempt {attempt + 1}"
                continue
            last = f"HTTP {response.status_code} on attempt {attempt + 1}"
            if response.is_success:
                return response.content
            if not _is_transient(response.status_code):
                break
        msg = f"vision request failed: {last}"
        raise OcrUnavailableError(msg)

    async def _token(self) -> str:
        try:
            if self._credentials is None:
                self._credentials, _ = await asyncio.to_thread(
                    adc_lookup, scopes=VISION_SCOPES
                )
            credentials = self._credentials
            if not credentials.valid:
                await asyncio.to_thread(credentials.refresh, Request())
        except GoogleAuthError as exc:
            msg = "vision credentials were refused"
            raise OcrUnavailableError(msg) from exc
        return str(credentials.token)


def _is_transient(status: int) -> bool:
    return status == codes.TOO_MANY_REQUESTS or status >= codes.INTERNAL_SERVER_ERROR
