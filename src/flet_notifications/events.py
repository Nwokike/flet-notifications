"""Event payload types delivered from the Dart side."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PendingNotification:
    """A scheduled notification that has not been delivered yet.

    Returned by :meth:`LocalNotifications.get_pending_notifications`.
    """

    id: int
    title: str = ""
    body: str = ""
    payload: str = ""
