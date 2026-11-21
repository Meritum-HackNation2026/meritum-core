"""Detector built by the public factory with a stub LLM and a chosen classifier gate."""

import asyncio
import json
from collections.abc import Callable
from pathlib import Path

import pytest
from pydantic import JsonValue

from meritum_core.security.injection import (
    InjectionGatePort,
    InjectionScan,
    NullInjectionGate,
    build_injection_detector,
)
from meritum_core.shared.llm import LlmSettings, build_llm

type Scan = Callable[..., InjectionScan]

CLEAN: JsonValue = {"injected": False, "instructions": []}


@pytest.fixture
def scan(tmp_path: Path) -> Scan:
    """Scan a text; ``classifier`` is the stub's answer, ``gate`` the classifier gate."""

    def run(
        text: str,
        *,
        classifier: JsonValue = CLEAN,
        gate: InjectionGatePort | None = None,
    ) -> InjectionScan:
        fixtures = tmp_path / "llm.json"
        answer = {"InjectionClassification": classifier}
        fixtures.write_text(json.dumps(answer), encoding="utf-8")
        llm = build_llm(LlmSettings(provider="stub", stub_fixtures=fixtures))
        detector = build_injection_detector(llm=llm, gate=gate or NullInjectionGate())
        return asyncio.run(detector.scan(text))

    return run
