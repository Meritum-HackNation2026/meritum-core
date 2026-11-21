"""Notifications slice: messages sent about checks and cases.

Public API of the domain: re-exports only. The in-memory fake is in
``meritum_core.notifications.fakes``.

Features:
    US-POW-01, F-22
"""

from meritum_core.notifications.ports import NotificationRepository, RecipientKind

__all__ = [
    "NotificationRepository",
    "RecipientKind",
]
