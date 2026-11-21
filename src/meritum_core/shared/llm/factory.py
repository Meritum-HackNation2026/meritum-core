"""Builds the LLM adapter named by ``MERITUM_LLM_PROVIDER``; nothing else does.

Features:
    US-WDR-02, F-30, ADR-11
"""

import json

from meritum_core.shared.llm.adapters import StubLlm, VertexLlm
from meritum_core.shared.llm.ports import LlmPort
from meritum_core.shared.llm.settings import LlmProvider, LlmSettings


def build_llm(settings: LlmSettings) -> LlmPort:
    """Build the adapter the settings name.

    Args:
        settings: LLM settings, usually ``LlmSettings()`` from the environment.

    Returns:
        The stub (fixtures from ``stub_fixtures``, none when unset) or Vertex AI.

    Features:
        US-WDR-02, F-30, ADR-11
    """
    match settings.provider:
        case LlmProvider.VERTEX:
            return VertexLlm(settings)
        case LlmProvider.STUB:
            path = settings.stub_fixtures
            fixtures = {} if path is None else json.loads(path.read_text("utf-8"))
            return StubLlm(fixtures)
