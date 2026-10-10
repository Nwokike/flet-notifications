"""The LocalNotifications service: cross-platform notifications for Flet."""

from __future__ import annotations

from typing import Optional

import flet as ft

from flet_notifications.actions import NotificationAction
from flet_notifications.base import NotificationEvent, check_result, to_bool


@ft.control("LocalNotifications")
class LocalNotifications(ft.Service):
    """Cross-platform local notifications (Android, iOS, macOS, Windows,
    Linux, Web).

    A headless service — instantiate it once and it registers itself with the
    page. No need to add it to the page's controls.

    Example:
        .. code-block:: python

            import flet as ft
            from flet_notifications import LocalNotifications


            async def main(page: ft.Page):
                notifications = LocalNotifications()

                async def on_tap(e):
                    print("tapped:", e.payload)

                notifications.on_tap = on_tap

                if await notifications.request_permissions():
                    await notifications.show(
                        id=1, title="Hello", body="from flet-notifications"
                    )


            ft.run(main)
    """

    default_icon: Optional[str] = None
    """Android default small icon drawable name (default: the app launcher icon)."""

    request_alert_permission: bool = True
    """iOS/macOS: request the alert permission during initialization."""

    request_sound_permission: bool = True
    """iOS/macOS: request the sound permission during initialization."""

    request_badge_permission: bool = True
    """iOS/macOS: request the badge permission during initialization."""

    request_critical_permission: bool = False
    """iOS/macOS: request the critical-alert permission (needs an Apple entitlement)."""

    app_name: Optional[str] = None
    """Windows: application name shown on toasts."""

    app_user_model_id: Optional[str] = None
    """Windows: AppUserModelID used to group toasts under the app."""

    windows_guid: Optional[str] = None
    """Windows: GUID identifying the toast notifier."""

    on_tap: Optional[ft.EventHandler[NotificationEvent["LocalNotifications"]]] = None
    """Fired when the notification body is tapped."""

    on_action: Optional[ft.EventHandler[NotificationEvent["LocalNotifications"]]] = None
    """Fired when an action button is pressed (``action_id`` names the button)."""

    on_dismissed: Optional[ft.EventHandler[NotificationEvent["LocalNotifications"]]] = (
        None
    )
    """Fired when the OS reports the notification was dismissed/cleared."""

    async def initialize(self) -> None:
        """Initialize the notification backend.

        Initialization happens automatically when the service is created;
        call this only to force a re-initialization.
        """
        check_result(await self._invoke_method("initialize"))

    async def show(
        self,
        id: int,
        title: Optional[str] = None,
        body: Optional[str] = None,
        payload: str = "",
        actions: Optional[list[NotificationAction]] = None,
    ) -> None:
        """Show a notification immediately.

        Args:
            id: Notification id; showing again with the same id updates it.
            title: Notification title.
            body: Notification body text.
            payload: Opaque string handed back on tap (e.g. a deep link).
            actions: Action buttons shown on the notification.
        """
        check_result(
            await self._invoke_method(
                "show",
                {
                    "id": id,
                    "title": title,
                    "body": body,
                    "payload": payload,
                    "actions": [a.to_dict() for a in actions] if actions else None,
                },
            )
        )

    async def cancel(self, id: int) -> None:
        """Cancel a previously shown or scheduled notification by id."""
        check_result(await self._invoke_method("cancel", {"id": id}))

    async def cancel_all(self) -> None:
        """Cancel all shown notifications."""
        check_result(await self._invoke_method("cancel_all"))

    async def request_permissions(self) -> bool:
        """Request the OS notification permission.

        On platforms where permission is implicit (Windows, Linux, Web-before-
        prompt) this returns the current status. Windows raises the
        browser prompt; Android 13+ shows the runtime dialog.
        """
        # Permission dialogs can take a while; allow more than the default.
        return to_bool(await self._invoke_method("request_permissions", timeout=300))
