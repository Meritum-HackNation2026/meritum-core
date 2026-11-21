"""Security slice: input gates, personal-data masking and injection defences.

Public API of the domain: re-exports only.

Features:
    none (infrastructure)
"""

from meritum_core.security.pii import MaskedText, mask_personal_data

__all__ = ["MaskedText", "mask_personal_data"]
