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
from flet_notifications.channels import NotificationChannel
from flet_notifications.events import PendingNotification
from flet_notifications.local_notifications import LocalNotifications
from flet_notifications.styles import (
    AndroidIcon,
    BigPictureStyle,
    BigTextStyle,
    InboxStyle,
    Message,
    MessagingStyle,
    Person,
    Style,
)
from flet_notifications.types import (
    AndroidScheduleMode,
    DateTimeComponents,
    GroupAlertBehavior,
    Importance,
    RepeatInterval,
)

__version__ = "0.1.0"

__all__ = [
    "AndroidIcon",
    "AndroidScheduleMode",
    "BigPictureStyle",
    "BigTextStyle",
    "DateTimeComponents",
    "GroupAlertBehavior",
    "Importance",
    "InboxStyle",
    "LocalNotifications",
    "Message",
    "MessagingStyle",
    "NotificationAction",
    "NotificationActionInput",
    "NotificationChannel",
    "NotificationError",
    "NotificationEvent",
    "PendingNotification",
    "Person",
    "RepeatInterval",
    "ResponseType",
    "Style",
]
