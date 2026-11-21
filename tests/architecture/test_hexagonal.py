"""Hexagonal architecture: domain code never imports adapters or frameworks.

Domain means every module outside ``WIRING`` (adapters, factories, app wiring);
the settings are in conftest.py.
"""

from collections.abc import Callable

type Forbid = Callable[[list[str], list[str]], None]


def test_domain_never_imports_frameworks(
    domain: list[str], frameworks: list[str], forbid: Forbid
) -> None:
    forbid(domain, frameworks)


def test_domain_never_imports_adapters(
    domain: list[str], adapters: list[str], forbid: Forbid
) -> None:
    forbid(domain, adapters)


LLM = "meritum_core.shared.llm"


def test_llm_adapters_are_wiring_not_domain(domain: list[str], own: list[str]) -> None:
    llm_adapters = [m for m in own if m.startswith(f"{LLM}.adapters.")]
    assert llm_adapters
    assert f"{LLM}.factory" not in domain
    assert not set(llm_adapters) & set(domain)


def test_only_the_factory_imports_llm_adapters(
    own: list[str], adapters: list[str], forbid: Forbid
) -> None:
    llm_adapters = [m for m in adapters if m.startswith(f"{LLM}.adapters")]
    importers = [
        m for m in own if m != f"{LLM}.factory" and not m.startswith(f"{LLM}.adapters")
    ]
    forbid(importers, llm_adapters)
