"""Names vulture cannot see being used: public API read by other repos and fields.

Run: ``uv run vulture`` (paths come from ``[tool.vulture]`` in pyproject.toml).
"""

from meritum_core.checks import constants
from meritum_core.corpus import CorpusSettings, Passage
from meritum_core.corpus.constants import FULL_TEXT_RETENTION_DAYS
from meritum_core.jobs.adapters import DbosJobQueue
from meritum_core.jobs.contracts import (
    CheckInput,
    DeleteSubjectOutput,
    EscalateClaimOutput,
    PingInput,
    PingOutput,
    ReadinessReport,
)
from meritum_core.jobs.fakes import InMemoryJobQueue
from meritum_core.jobs.ports import JobQueue
from meritum_core.moderation import HighRiskTopic
from meritum_core.shared.blobs import BlobRef, BlobSettings
from meritum_core.shared.embeddings import EmbeddingsSettings
from meritum_core.shared.llm import LlmResult, LlmSettings, LlmUsage, Prompt

DbosJobQueue  # built by meritum-backend's composition root
DbosJobQueue.enqueue  # called by meritum-backend through the JobQueue port
DbosJobQueue.state  # called by meritum-backend through the JobQueue port
JobQueue.enqueue  # port methods, implemented by DbosJobQueue
JobQueue.state
PingInput.contract_version  # serialized with model_dump
PingOutput.contract_version  # serialized with model_dump
PingOutput.worker_env  # serialized with model_dump
BlobRef.model_config  # read by pydantic
BlobSettings.model_config  # read by pydantic-settings
Prompt.model_config  # Pydantic reads model_config
LlmUsage.model_config
LlmResult.model_config
LlmSettings.model_config
LlmSettings._vertex_is_pinned_and_in_the_eu  # ruff: ignore[private-member-access]  # Pydantic validator
JobQueue.stream
JobQueue.event
DbosJobQueue.stream  # called by meritum-backend through the JobQueue port
DbosJobQueue.event
InMemoryJobQueue  # used by the tests of meritum-backend and meritum-worker
PingInput.model_config  # read by Pydantic (set once on the shared base model)
CheckInput.received_at  # job payload fields: serialized with model_dump
EscalateClaimOutput.escalation
DeleteSubjectOutput.deleted
ReadinessReport.missing_env
ReadinessReport.unavailable_providers
ReadinessReport.checked_at

# Contract constants: read by the models in checks/contracts/, which vulture skips.
constants.MIN_TEXT_CHARS
constants.STRONG_MIN_SOURCES
constants.SETTLING
constants.AGREEING_STANCE
constants.PER_EVIDENCE_VALIDITY
constants.DEFAULT_MAX_AGE_HOURS
constants.SESSIONLESS_CHANNELS
constants.CHECK_KINDS
constants.CASE_KINDS
CorpusSettings.model_config  # read by pydantic-settings
CorpusSettings._postgres_has_a_database  # ruff: ignore[private-member-access]  # Pydantic validator
EmbeddingsSettings.model_config  # read by pydantic-settings
EmbeddingsSettings._vertex_is_in_the_eu  # ruff: ignore[private-member-access]  # Pydantic validator
Passage.model_config  # read by pydantic
HighRiskTopic.keywords  # read by the worker's topic step (keyword fallback)
FULL_TEXT_RETENTION_DAYS  # read by the worker retention job (US-KOR-05)
