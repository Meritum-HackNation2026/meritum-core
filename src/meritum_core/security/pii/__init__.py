"""Personal-data masking: one function for the backend, the worker and error reports.

Public API: the masking function, its result, its markers, the gate port, the null gate,
settings, errors and the factory.

Features:
    US-BEZ-04, F-20, ADR-13, ADR-35
"""

from meritum_core.security.pii.constants import MARKERS
from meritum_core.security.pii.errors import PiiGateUnavailableError
from meritum_core.security.pii.factory import build_pii_gate
from meritum_core.security.pii.gates import NullPiiGate
from meritum_core.security.pii.models import MaskedText
from meritum_core.security.pii.ports import PiiGatePort
from meritum_core.security.pii.settings import PiiGateProvider, PiiGateSettings

from ._mask import mask_personal_data

__all__ = [
    "MARKERS",
    "MaskedText",
    "NullPiiGate",
    "PiiGatePort",
    "PiiGateProvider",
    "PiiGateSettings",
    "PiiGateUnavailableError",
    "build_pii_gate",
    "mask_personal_data",
]
