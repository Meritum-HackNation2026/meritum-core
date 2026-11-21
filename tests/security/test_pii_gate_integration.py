"""Real Sensitive Data Protection call: local only, ``uv run pytest -m integration``.

Needs Application Default Credentials, the DLP API enabled in the project and
``MERITUM_PII_PROJECT``; never runs in CI.
"""

import asyncio
import os

import pytest

from meritum_core.security import PiiGateSettings, build_pii_gate, mask_personal_data


@pytest.mark.integration
def test_real_sensitive_data_protection_masks_a_polish_address() -> None:
    project = os.environ.get("MERITUM_PII_PROJECT")
    if project is None:
        pytest.skip("MERITUM_PII_PROJECT is not set")
    gate = build_pii_gate(PiiGateSettings(gate="sdp", project=project))
    text = "Mieszkam przy ul. Marszałkowskiej 12/4, 00-590 Warszawa. Szczepionki zawierają chipy."
    result = asyncio.run(mask_personal_data(text, gate))
    assert "Marszałkowskiej" not in result.text
    assert "[adres]" in result.text
    assert result.text.endswith("Szczepionki zawierają chipy.")
