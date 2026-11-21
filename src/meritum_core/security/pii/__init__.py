"""Personal-data masking: one function for the backend, the worker and error reports.

Features:
    US-BEZ-04, F-20, ADR-13
"""

from ._mask import MaskedText, mask_personal_data

__all__ = ["MaskedText", "mask_personal_data"]
