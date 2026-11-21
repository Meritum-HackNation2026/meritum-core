"""Models of the `readiness` workflow: what the worker lacks to run checks.

Features:
    US-WDR-08, ADR-03
"""

from datetime import datetime

from meritum_core.jobs.contracts._base import JobModel


class ReadinessInput(JobModel):
    """Input of the `readiness` workflow: nothing but the contract version.

    Features:
        US-WDR-08, ADR-03
    """


class ReadinessReport(JobModel):
    """Output of the `readiness` workflow, also published as an event.

    Attributes:
        missing_env: names of required environment variables that are unset.
        unavailable_providers: providers the worker could not reach.
        checked_at: when the worker checked.

    Features:
        US-WDR-08, ADR-03
    """

    missing_env: list[str]
    unavailable_providers: list[str]
    checked_at: datetime
