"""Security slice: input gates, personal-data masking and injection defences.

Public API of the domain: re-exports only.

Features:
    none (infrastructure)
"""

from meritum_core.security.injection import (
    InjectionDetectorPort,
    InjectionGatePort,
    InjectionScan,
    NullInjectionGate,
    build_injection_detector,
    instruction_removed,
)
from meritum_core.security.pii import (
    MaskedText,
    NullPiiGate,
    PiiGatePort,
    PiiGateSettings,
    PiiGateUnavailableError,
    build_pii_gate,
    mask_personal_data,
)

__all__ = [
    "InjectionDetectorPort",
    "InjectionGatePort",
    "InjectionScan",
    "MaskedText",
    "NullInjectionGate",
    "NullPiiGate",
    "PiiGatePort",
    "PiiGateSettings",
    "PiiGateUnavailableError",
    "build_injection_detector",
    "build_pii_gate",
    "instruction_removed",
    "mask_personal_data",
]
