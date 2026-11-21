"""Errors of the LLM port.

Features:
    US-WDR-02, F-30, ADR-11
"""


class ProviderUnavailableError(Exception):
    """The provider failed after all retries; workflows map it to `technical_failure`.

    Features:
        US-WDR-02, F-30, ADR-11
    """
