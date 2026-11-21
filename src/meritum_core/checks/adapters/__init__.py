"""CheckRecordRepository adapters, built only by ``meritum_core.observability.factory``.

Features:
    US-OBS-01, US-BEZ-05, F-22, F-24
"""

from ._postgres import PostgresCheckRecordRepository, delete_subject_records

__all__ = ["PostgresCheckRecordRepository", "delete_subject_records"]
