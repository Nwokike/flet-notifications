"""flet-notifications: cross-platform local notifications for Flet apps.

Wraps the battle-tested ``flutter_local_notifications`` Flutter plugin and
exposes it as a native Flet service (``ft.Service``), following the same
extension architecture as ``flet-ads`` / ``flet-yandex-ads``.
"""

from flet_notifications.actions import NotificationAction, NotificationActionInput
from flet_notifications.base import (
    NotificationError,
    NotificationEvent,
    ResponseType,
)
from flet_notifications.local_notifications import LocalNotifications

__version__ = "0.1.0"

__all__ = [
    "LocalNotifications",
    "NotificationAction",
    "NotificationActionInput",
    "NotificationError",
    "NotificationEvent",
    "ResponseType",
]
