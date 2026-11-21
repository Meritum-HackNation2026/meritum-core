"""Constants of the job contract between meritum-backend and meritum-worker.

Features:
    ADR-03
"""

from typing import Final

CONTRACT_VERSION: Final = 2
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
