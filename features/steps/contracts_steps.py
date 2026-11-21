"""Steps for the contracts-package scenario: the public import surface is stable.

The JSON Schema is rebuilt in-process and compared with the committed file. meritum.ts
is generated from that schema by the pinned json-schema-to-typescript, which needs
Node: the CI job ``scripts/generate-contracts.sh --check`` compares it.
"""

import importlib
import json
import pkgutil
import runpy
from pathlib import Path

from behave import given, then, when
from behave.runner import Context

ROOT = Path(__file__).resolve().parents[2]
# Every public name of meritum_core.checks.contracts before the split (contracts v3).
PUBLIC_NAMES = [
    "AGREEING_STANCE",
    "CASE_KINDS",
    "CHECK_KINDS",
    "CONTRACT_VERSION",
    "DEFAULT_MAX_AGE_HOURS",
    "MIN_TEXT_CHARS",
    "PER_EVIDENCE_VALIDITY",
    "SESSIONLESS_CHANNELS",
    "SETTLING",
    "STRONG_MIN_SOURCES",
    "Agreement",
    "AnalysisStatus",
    "AnalysisStep",
    "CacheableStatus",
    "CachedResult",
    "CaseClaim",
    "CaseReason",
    "CatalogEntry",
    "Channel",
    "CheckRecord",
    "CheckRequest",
    "CheckResult",
    "CheckStatus",
    "Citation",
    "ClaimDateSource",
    "ClaimResult",
    "ClaimReviewContext",
    "Escalation",
    "EvidenceStrength",
    "IncidentMatch",
    "InjectionEvent",
    "ModelUsage",
    "ModeratorCase",
    "Notification",
    "NotificationKind",
    "Premises",
    "PublisherId",
    "Source",
    "SourceKind",
    "SourceStatusWarning",
    "SourceTier",
    "SourceVia",
    "StaffRole",
    "Stance",
    "Strength",
    "TechniqueCode",
    "Validity",
    "Verdict",
    "is_stale",
    "strength_for",
]


@given('kod backendu, workera i testy importują "{statement}"')
def given_consumer_import(context: Context, statement: str) -> None:
    """Resolve the ``from <module> import <name>`` statement the consumers use."""
    module, _, name = statement.removeprefix("from ").partition(" import ")
    context.imported = getattr(importlib.import_module(module), name)


@when('kontrakty są pakietem "{path}" z prywatnymi modułami')
def when_contracts_are_a_package(context: Context, path: str) -> None:
    """The contracts are a package whose modules are all private."""
    package = importlib.import_module("meritum_core.checks.contracts")
    assert package.__file__ is not None
    assert Path(package.__file__).parent.as_posix().endswith(path.rstrip("/"))
    modules = [m.name for m in pkgutil.iter_modules(package.__path__)]
    assert modules
    assert all(name.startswith("_") for name in modules), modules
    context.package = package


@then("każdy dotychczasowy import działa bez zmian")
def then_old_imports_work(context: Context) -> None:
    """Every name of the former module is still exported by the package."""
    assert context.imported is context.package.CheckResult
    missing = [n for n in PUBLIC_NAMES if not hasattr(context.package, n)]
    assert missing == [], missing
    assert set(PUBLIC_NAMES) <= set(context.package.__all__)


@then('wygenerowane "{schema}" i "{ts}" są identyczne jak przed zmianą')
def then_generated_files_unchanged(_context: Context, schema: str, ts: str) -> None:
    """The schema built now equals the committed one; meritum.ts exists next to it."""
    exporter = runpy.run_path(str(ROOT / "scripts" / "export_contracts.py"))
    built = json.dumps(exporter["schema_document"](), ensure_ascii=False, indent=2)
    assert built + "\n" == (ROOT / schema).read_text(encoding="utf-8")
    assert (ROOT / ts).is_file()
