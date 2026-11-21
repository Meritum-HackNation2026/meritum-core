"""Masking gate adapters; only ``factory.py`` builds them.

Features:
    US-BEZ-04, F-20, ADR-13, ADR-35
"""

from ._sdp import SensitiveDataProtectionGate

__all__ = ["SensitiveDataProtectionGate"]
