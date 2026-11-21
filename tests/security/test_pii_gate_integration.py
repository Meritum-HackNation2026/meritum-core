"""Real Sensitive Data Protection call: local only, ``uv run pytest -m integration``.

Needs Application Default Credentials, the DLP API enabled in the project and
``MERITUM_PII_PROJECT``; never runs in CI.
"""

import asyncio
import os

import httpx2
import pytest

from meritum_core.security import (
    MaskedText,
    PiiGateSettings,
    build_pii_gate,
    mask_personal_data,
)
from meritum_core.security.pii.constants import HTTP_TIMEOUT_SECONDS


@pytest.mark.integration
def test_real_sensitive_data_protection_masks_a_polish_address() -> None:
    project = os.environ.get("MERITUM_PII_PROJECT")
    if project is None:
        pytest.skip("MERITUM_PII_PROJECT is not set")
    text = "Mieszkam przy ul. Marszałkowskiej 12/4, 00-590 Warszawa. Szczepionki zawierają chipy."
    result, again = asyncio.run(_mask_twice(project, text))
    assert "Marszałkowskiej" not in result.text
    assert "[adres]" in result.text
    assert result.text.endswith("Szczepionki zawierają chipy.")
    assert again == MaskedText(text=result.text, replaced=0)


async def _mask_twice(project: str, text: str) -> tuple[MaskedText, MaskedText]:
    """Mask, then mask the result: one event loop, one HTTP client, closed after."""
    async with httpx2.AsyncClient(timeout=HTTP_TIMEOUT_SECONDS) as client:
        settings = PiiGateSettings(gate="sdp", project=project)
        gate = build_pii_gate(settings, http_client=client)
        once = await mask_personal_data(text, gate)
        return once, await mask_personal_data(once.text, gate)
