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
def test_real_sensitive_data_protection_keeps_a_name_and_masks_identifiers() -> None:
    project = os.environ.get("MERITUM_PII_PROJECT")
    if project is None:
        pytest.skip("MERITUM_PII_PROJECT is not set")
    text = (
        "Donald Tusk powiedział, że zadzwoni pod 601 234 567, PESEL 44051401359,"
        " dowód ABA300000. Sejm przy ul. Wiejskiej 4 wydał 850 000 000 zł."
    )
    result, again = asyncio.run(_mask_twice(project, text))
    assert result.text.startswith("Donald Tusk powiedział")
    assert all(s not in result.text for s in ("44051401359", "ABA300000"))
    assert "Sejm przy ul. Wiejskiej 4 wydał 850 000 000 zł." in result.text
    assert again == MaskedText(text=result.text, replaced=0)


async def _mask_twice(project: str, text: str) -> tuple[MaskedText, MaskedText]:
    """Mask, then mask the result: one event loop, one HTTP client, closed after."""
    async with httpx2.AsyncClient(timeout=HTTP_TIMEOUT_SECONDS) as client:
        settings = PiiGateSettings(gate="sdp", project=project)
        gate = build_pii_gate(settings, http_client=client)
        once = await mask_personal_data(text, gate)
        return once, await mask_personal_data(once.text, gate)
