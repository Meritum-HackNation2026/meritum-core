"""Builds the masking gate named by ``MERITUM_PII_GATE``.

Features:
    US-BEZ-04, F-20, ADR-13, ADR-35
"""

from google.auth.credentials import Credentials
from httpx2 import AsyncClient

from meritum_core.security.pii.adapters import SensitiveDataProtectionGate
from meritum_core.security.pii.gates import NullPiiGate
from meritum_core.security.pii.ports import PiiGatePort
from meritum_core.security.pii.settings import PiiGateProvider, PiiGateSettings


def build_pii_gate(
    settings: PiiGateSettings,
    *,
    credentials: Credentials | None = None,
    http_client: AsyncClient | None = None,
) -> PiiGatePort:
    """Build the gate the settings name.

    Args:
        settings: Usually ``PiiGateSettings()`` from the environment.
        credentials: Google credentials; Application Default Credentials when
            None. Ignored by the null gate.
        http_client: HTTP client (shared pool, or recorded replies in tests); a
            new one when None. Ignored by the null gate.

    Returns:
        Sensitive Data Protection in the configured EU region, or the null gate.

    Features:
        US-BEZ-04, F-20, ADR-13, ADR-35
    """
    match settings.gate:
        case PiiGateProvider.SDP:
            return SensitiveDataProtectionGate(
                settings, credentials=credentials, http_client=http_client
            )
        case PiiGateProvider.NONE:
            return NullPiiGate()
