"""PostgreSQL migrations of the app schema and the command that runs them.

Features:
    US-OBS-01, US-BEZ-05, F-22, ADR-03, ADR-04
"""

from ._migrations import apply_migrations, main

__all__ = ["apply_migrations", "main"]
