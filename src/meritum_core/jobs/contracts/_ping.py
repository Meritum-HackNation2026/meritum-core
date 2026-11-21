"""Models of the `ping` smoke-test workflow.

Features:
    ADR-03
"""

from pydantic import Field

from meritum_core.jobs.contracts._base import JobModel


class PingInput(JobModel):
    """Input of the `ping` smoke-test workflow.

    Attributes:
        message: text the worker echoes back.

    Features:
        ADR-03
    """

    message: str = Field(default="ping", max_length=200)


class PingOutput(JobModel):
    """Output of the `ping` workflow: the echoed message and the worker's env.

    Attributes:
        message: the echoed text.
        worker_env: the environment name of the worker that ran the job.

    Features:
        ADR-03
    """

    message: str
    worker_env: str
