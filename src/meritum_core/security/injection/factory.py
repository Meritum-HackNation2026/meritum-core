"""Compose the injection detector's layers (ADR-12, ADR-35).

Features:
    US-BEZ-01, F-19, ADR-12, ADR-23, ADR-35
"""

from meritum_core.security.injection._classifier import LlmClassifierGate
from meritum_core.security.injection._detector import LayeredInjectionDetector
from meritum_core.security.injection._patterns import PatternGate
from meritum_core.security.injection.models import DetectionLayer
from meritum_core.security.injection.ports import (
    InjectionDetectorPort,
    InjectionGatePort,
)
from meritum_core.shared.llm import LlmPort


def build_injection_detector(
    *, llm: LlmPort, gate: InjectionGatePort
) -> InjectionDetectorPort:
    """Build the detector: PL/EN patterns, the classifier gate, the isolated LLM.

    The gate comes ready-made: the worker's factory picks its provider adapter
    (worker/032), or passes ``NullInjectionGate``; no model name lives in core.

    Args:
        llm: The model the isolated classifier calls.
        gate: The classifier gate of ADR-35.

    Returns:
        The composed detector.

    Features:
        US-BEZ-01, F-19, ADR-12, ADR-23, ADR-35
    """
    return LayeredInjectionDetector(
        (
            (DetectionLayer.PATTERNS, PatternGate()),
            (DetectionLayer.GATE, gate),
            (DetectionLayer.CLASSIFIER, LlmClassifierGate(llm)),
        )
    )
