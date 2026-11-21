"""Prompt-injection detector: PL/EN patterns, a classifier gate and an isolated LLM.

Public API: the ports, the factory, the null gate, models, ``instruction_removed``
and the contract's ``InjectionEvent`` it fills.
The fake gate for tests is in ``meritum_core.security.injection.fakes``.

Features:
    US-BEZ-01, F-19, ADR-12, ADR-23, ADR-35
"""

from meritum_core.checks import InjectionEvent
from meritum_core.security.injection.factory import build_injection_detector
from meritum_core.security.injection.gates import NullInjectionGate
from meritum_core.security.injection.models import (
    CleanedInput,
    DetectionLayer,
    InjectionClassification,
    InjectionScan,
    InjectionSpan,
    TextRange,
)
from meritum_core.security.injection.ports import (
    InjectionDetectorPort,
    InjectionGatePort,
)
from meritum_core.security.injection.removal import instruction_removed

__all__ = [
    "CleanedInput",
    "DetectionLayer",
    "InjectionClassification",
    "InjectionDetectorPort",
    "InjectionEvent",
    "InjectionGatePort",
    "InjectionScan",
    "InjectionSpan",
    "NullInjectionGate",
    "TextRange",
    "build_injection_detector",
    "instruction_removed",
]
