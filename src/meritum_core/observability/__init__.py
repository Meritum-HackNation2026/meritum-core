"""Observability slice: the app repositories as one store, and erasing a person.

Public API of the domain: re-exports only. The in-memory eraser is in
``meritum_core.observability.fakes``.

Features:
    US-OBS-01, US-MOD-01, US-BEZ-05, F-22, F-24
"""

from meritum_core.observability.factory import build_app_repositories
from meritum_core.observability.models import AppRepositories
from meritum_core.observability.ports import SubjectEraser

__all__ = ["AppRepositories", "SubjectEraser", "build_app_repositories"]
