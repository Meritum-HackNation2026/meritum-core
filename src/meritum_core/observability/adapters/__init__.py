"""SubjectEraser adapters, built only by ``meritum_core.observability.factory``.

Features:
    US-BEZ-05, F-24
"""

from ._postgres import PostgresSubjectEraser

__all__ = ["PostgresSubjectEraser"]
