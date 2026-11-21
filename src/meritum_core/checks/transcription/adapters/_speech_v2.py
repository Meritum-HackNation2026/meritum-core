"""Speech-to-Text v2 adapter over REST: Chirp 3 in the ``eu`` multi-region, pl-PL.

Short recordings go inline to synchronous ``recognize``; longer ones, and those
whose length the container does not state, go to ``batchRecognize``, which reads
the file from the blob store's ``gs://`` address.

Features:
    US-SPR-11, F-08, ADR-14, ADR-30, ADR-31
"""

import asyncio
import base64

from google.auth import default as adc_lookup
from google.auth.credentials import Credentials
from google.auth.exceptions import GoogleAuthError
from google.auth.transport.requests import Request
from httpx2 import AsyncClient, TransportError, codes
from pydantic import BaseModel, Field, JsonValue, ValidationError

from meritum_core.checks.transcription.audio import inspect_audio
from meritum_core.checks.transcription.constants import (
    BATCH_POLL_SECONDS,
    BATCH_TIMEOUT_SECONDS,
    HTTP_TIMEOUT_SECONDS,
    LANGUAGE,
    RECOGNITION_CONFIG,
    RETRY_BACKOFF_SECONDS,
    SPEECH_ENDPOINT,
    SPEECH_LOCATION,
    SPEECH_SCOPES,
    SYNC_MAX_BYTES,
    SYNC_MAX_SECONDS,
)
from meritum_core.checks.transcription.errors import TranscriptionUnavailableError
from meritum_core.checks.transcription.models import AudioInfo, Transcript
from meritum_core.checks.transcription.settings import TranscriptionSettings
from meritum_core.shared.blobs import BlobStore


class _Alternative(BaseModel):
    transcript: str = ""


class _Result(BaseModel):
    alternatives: list[_Alternative] = []


class _Recognition(BaseModel):
    results: list[_Result] = []


class _Status(BaseModel):
    message: str = ""


class _InlineResult(BaseModel):
    transcript: _Recognition = _Recognition()


class _FileResult(BaseModel):
    error: _Status | None = None
    inline_result: _InlineResult | None = Field(default=None, alias="inlineResult")


class _BatchResponse(BaseModel):
    results: dict[str, _FileResult] = {}


class _Operation(BaseModel):
    name: str
    done: bool = False
    error: _Status | None = None
    response: _BatchResponse | None = None


class SpeechV2Transcriber:
    """TranscriptionPort on Google Speech-to-Text v2 (ADR-30).

    Args:
        settings: Validated ``speech_v2`` settings (the project is set).
        blobs: The store holding the recordings.
        credentials: Google credentials; Application Default Credentials when None.
        http_client: HTTP client to use; tests pass one with recorded replies.

    Features:
        US-SPR-11, F-08, ADR-14, ADR-30, ADR-31
    """

    def __init__(
        self,
        settings: TranscriptionSettings,
        blobs: BlobStore,
        *,
        credentials: Credentials | None = None,
        http_client: AsyncClient | None = None,
    ) -> None:
        self._blobs = blobs
        self._retries = settings.retries
        self._credentials = credentials
        self._client = http_client or AsyncClient(timeout=HTTP_TIMEOUT_SECONDS)
        self._recognizer = (
            f"{SPEECH_ENDPOINT}/projects/{settings.project}"
            f"/locations/{SPEECH_LOCATION}/recognizers/_"
        )

    async def transcribe(self, audio_id: str) -> Transcript:
        """Transcribe the recording, synchronously when short, in batch otherwise.

        Args:
            audio_id: The blob id of the recording.

        Returns:
            The transcript in ``pl-PL``.

        Raises:
            TranscriptionUnavailableError: The provider failed or refused the
                credentials after the configured retries, its reply did not
                parse, or the batch operation failed or timed out.
        """  # ruff: ignore[docstring-extraneous-exception]  # raised by _send and _batch
        data = await self._blobs.get(audio_id)
        info = inspect_audio(data)
        if _fits_sync(info, len(data)):
            content = base64.b64encode(data).decode("ascii")
            reply = await self._send(
                f"{self._recognizer}:recognize",
                {"config": RECOGNITION_CONFIG, "content": content},
            )
            recognition = _parse(_Recognition, reply)
        else:
            recognition = await self._batch(await self._blobs.uri(audio_id))
        texts = (
            r.alternatives[0].transcript for r in recognition.results if r.alternatives
        )
        return Transcript(
            text=" ".join(t.strip() for t in texts if t.strip()), language=LANGUAGE
        )

    async def _batch(self, uri: str) -> _Recognition:
        request: dict[str, JsonValue] = {
            "config": RECOGNITION_CONFIG,
            "files": [{"uri": uri}],
            "recognitionOutputConfig": {"inlineResponseConfig": {}},
        }
        started = _parse(
            _Operation, await self._send(f"{self._recognizer}:batchRecognize", request)
        )
        try:
            async with asyncio.timeout(BATCH_TIMEOUT_SECONDS):
                operation = await self._wait(started)
        except TimeoutError as exc:
            msg = f"batch operation {started.name} did not finish in time"
            raise TranscriptionUnavailableError(msg) from exc
        results = operation.response.results if operation.response else {}
        if operation.error or len(results) != 1:
            msg = f"batch operation {operation.name} failed"
            raise TranscriptionUnavailableError(msg)
        (result,) = results.values()
        if result.error or result.inline_result is None:
            reason = result.error.message if result.error else "no inline result"
            msg = f"batch operation {operation.name} failed on the file: {reason}"
            raise TranscriptionUnavailableError(msg)
        return result.inline_result.transcript

    async def _wait(self, operation: _Operation) -> _Operation:
        while not operation.done:
            reply = await self._send(f"{SPEECH_ENDPOINT}/{operation.name}", None)
            operation = _parse(_Operation, reply)
            if not operation.done:
                await asyncio.sleep(BATCH_POLL_SECONDS)
        return operation

    async def _send(self, url: str, body: dict[str, JsonValue] | None) -> bytes:
        """POST ``body`` (GET when None), retrying transient failures.

        Returns:
            The body of the first successful reply.

        Raises:
            TranscriptionUnavailableError: Every attempt failed, or the provider
                rejected the request.
        """
        headers = {"Authorization": f"Bearer {await self._token()}"}
        method = "GET" if body is None else "POST"
        last = "no reply"
        for attempt in range(self._retries):
            if attempt:
                await asyncio.sleep(RETRY_BACKOFF_SECONDS * 2 ** (attempt - 1))
            try:
                response = await self._client.request(
                    method, url, json=body, headers=headers
                )
            except TransportError as exc:
                last = f"{type(exc).__name__} on attempt {attempt + 1}"
                continue
            last = f"HTTP {response.status_code} on attempt {attempt + 1}"
            if response.is_success:
                return response.content
            if not _is_transient(response.status_code):
                break
        msg = f"speech-to-text {method} failed: {last}"
        raise TranscriptionUnavailableError(msg)

    async def _token(self) -> str:
        try:
            if self._credentials is None:
                self._credentials, _ = await asyncio.to_thread(
                    adc_lookup, scopes=SPEECH_SCOPES
                )
            credentials = self._credentials
            if not credentials.valid:
                await asyncio.to_thread(credentials.refresh, Request())
        except GoogleAuthError as exc:
            msg = "speech-to-text credentials were refused"
            raise TranscriptionUnavailableError(msg) from exc
        return str(credentials.token)


def _fits_sync(info: AudioInfo, size: int) -> bool:
    seconds = info.duration_seconds
    is_short = seconds is not None and seconds <= SYNC_MAX_SECONDS
    return is_short and size <= SYNC_MAX_BYTES


def _is_transient(status: int) -> bool:
    return status == codes.TOO_MANY_REQUESTS or status >= codes.INTERNAL_SERVER_ERROR


def _parse[T: BaseModel](model: type[T], reply: bytes) -> T:
    try:
        return model.model_validate_json(reply)
    except ValidationError as exc:
        msg = f"speech-to-text reply is not a {model.__name__.removeprefix('_')}"
        raise TranscriptionUnavailableError(msg) from exc
