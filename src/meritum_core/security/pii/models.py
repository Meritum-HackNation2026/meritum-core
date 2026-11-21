"""Result of personal-data masking.

Features:
    US-BEZ-04, F-20, ADR-13
"""

from pydantic import BaseModel


class MaskedText(BaseModel, frozen=True):
    """Text with personal data replaced by markers; never holds the original.

    Attributes:
        text: the masked text.
        replaced: how many personal-data items were replaced.

    Features:
        US-BEZ-04, F-20, ADR-13
    """

    text: str
    replaced: int
