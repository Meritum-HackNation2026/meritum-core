"""Constants of the job contract between meritum-backend and meritum-worker.

Features:
    ADR-03
"""

from typing import Final

CONTRACT_VERSION: Final = 5
"""Version of the job contract; raise it on any change a consumer cannot read."""

APPLICATION_NAME: Final = "meritum-worker"
"""DBOS application name; the worker launches with it, the backend enqueues to it."""

DEFAULT_QUEUE: Final = "default"
"""Queue of the workflows that need no dedicated concurrency limits."""

PROGRESS_KEY: Final = "progress"
"""Stream key of the `check` workflow: each value is one AnalysisStatus (F-09)."""

READINESS_KEY: Final = "readiness"
"""Event key of the `readiness` workflow: the latest ReadinessReport (US-WDR-08)."""

EVENT_TIMEOUT_SECONDS: Final = 60.0
"""How long `JobQueue.event` waits for a value before returning None (DBOS default)."""

HASH_PATTERN: Final = r"^[0-9a-f]{64}$"
"""Salted SHA-256 of a channel user id, as hex; the raw id never enters a job."""

MAX_JUSTIFICATION_CHARS: Final = 1000
"""Longest masked justification of a "Zgłoś błąd" dispute (US-MOD-03)."""

ID_MIN_CHARS: Final = 8
"""Shortest session or user id, as in the checks contracts (CheckRecord)."""

ID_MAX_CHARS: Final = 64
"""Longest session or user id, as in the checks contracts (CheckRecord)."""

MAX_PING_MESSAGE_CHARS: Final = 200
"""Longest text the `ping` workflow echoes."""

CHECK_ID_MAX_CHARS: Final = 40
"""Longest check id, as in CheckResult.check_id."""

ARCHIVE_URL_MAX_CHARS: Final = 2048
"""Longest page URL the `archive_page` workflow takes."""

ARCHIVE_URL_PATTERN: Final = r"^https?://\S+$"
"""Only http(s) URLs reach the worker's fetcher (which also blocks private hosts)."""
