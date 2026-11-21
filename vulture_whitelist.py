"""Names vulture cannot see being used: public API read by other repos and fields.

Run: ``uv run vulture`` (paths come from ``[tool.vulture]`` in pyproject.toml).
"""

from meritum_core.jobs.adapters import DbosJobQueue
from meritum_core.jobs.contracts import PingInput, PingOutput
from meritum_core.jobs.ports import JobQueue
from meritum_core.shared.blobs import BlobRef, BlobSettings
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
