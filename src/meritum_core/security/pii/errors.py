"""Errors of the personal-data masking gate.

Features:
    US-BEZ-04, F-20, ADR-13, ADR-35
"""


class PiiGateUnavailableError(Exception):
    """The masking gate failed; the caller skips it.

    No reply, a refused request or credentials, a reply that did not parse, or
    a transformation the provider could not apply.

    ``mask_personal_data`` catches it, logs the skip and masks with patterns
    only, so a gate failure never stops a check (ADR-35).

    Features:
        US-BEZ-04, F-20, ADR-13, ADR-35
    """
