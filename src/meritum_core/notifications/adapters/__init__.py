"""NotificationRepository adapters, built only by ``observability.factory``.

Features:
    US-POW-01, US-BEZ-05, F-22
"""

from ._postgres import PostgresNotificationRepository, delete_recipient_notifications

__all__ = ["PostgresNotificationRepository", "delete_recipient_notifications"]
