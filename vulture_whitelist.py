"""Names vulture cannot see being used: public API read by other repos and fields.

Run: ``uv run vulture`` (paths come from ``[tool.vulture]`` in pyproject.toml).
"""

from meritum_core.jobs.adapters import DbosJobQueue
from meritum_core.jobs.contracts import PingInput, PingOutput
from meritum_core.jobs.ports import JobQueue

DbosJobQueue  # built by meritum-backend's composition root
DbosJobQueue.enqueue  # called by meritum-backend through the JobQueue port
DbosJobQueue.state  # called by meritum-backend through the JobQueue port
JobQueue.enqueue  # port methods, implemented by DbosJobQueue
JobQueue.state
PingInput.contract_version  # serialized with model_dump
PingOutput.contract_version  # serialized with model_dump
PingOutput.worker_env  # serialized with model_dump
