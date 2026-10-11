"""Example app for flet-notifications — every API on one screen.

House example pattern: adaptive AppBar, scrollable page, activity terminal
(Courier New on dark background, timestamped, auto-scroll).
"""

import asyncio
import contextlib
import datetime

import flet as ft

from flet_notifications import (
    AndroidOptions,
    AndroidScheduleMode,
    BigTextStyle,
    DarwinOptions,
    DateTimeComponents,
    InboxStyle,
    LocalNotifications,
    NotificationAction,
    NotificationActionInput,
    NotificationChannel,
    NotificationOptions,
    RepeatInterval,
)

# Activity terminal — house pattern (Courier New, #A6E22E on #0D0D0D).
TERMINAL_BG = "#0D0D0D"
TERMINAL_TEXT = "#A6E22E"


def main(page: ft.Page):
    page.appbar = ft.AppBar(adaptive=True, title="flet-notifications Example")
    page.scroll = ft.ScrollMode.AUTO
    page.padding = 16

    notifications = LocalNotifications()

    log_text = ft.Text(
        value="",
        font_family="Courier New",
        size=12,
        color=TERMINAL_TEXT,
        selectable=True,
    )
    log_col = ft.Column(controls=[log_text], scroll=ft.ScrollMode.AUTO, expand=True)
    log_terminal = ft.Container(
        content=log_col,
        bgcolor=TERMINAL_BG,
        padding=12,
        border=ft.Border.all(1, ft.Colors.with_opacity(0.15, ft.Colors.WHITE)),
        border_radius=8,
        height=320,
    )

    def log_line(message: str):
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        log_text.value = (
            f"{log_text.value}\n[{ts}] {message}"
            if log_text.value
            else f"[{ts}] {message}"
        )
        page.update(log_text)

        async def _scroll_to_end():
            await asyncio.sleep(0.05)
            with contextlib.suppress(Exception):
                await log_col.scroll_to(offset=-1)  # offset=-1: jump to newest

        page.run_task(_scroll_to_end)

    # Plain `flet run` uses the prebuilt client without this extension's
    # Dart half; invokes time out. Degrade to a terminal line.
    missing_backend = {"warned": False}

    def warn_no_backend(method: str):
        if missing_backend["warned"]:
            return
        missing_backend["warned"] = True
        log_line(f"{method}: no notification backend in this runner.")
        log_line("Run a built app instead: a release artifact, or")
        log_line("  uv run flet build windows|macos|linux|apk")

    def guarded(coro, method: str):
        async def _run():
            try:
                await coro
            except Exception:  # noqa: BLE001 - any backend failure degrades
                warn_no_backend(method)

        page.run_task(_run)

    # ── Events ──
    notifications.on_tap = lambda e: log_line(f"tap: id={e.id} payload={e.payload!r}")
    notifications.on_action = lambda e: log_line(
        f"action: {e.action_id!r} payload={e.payload!r} input={e.input!r}"
    )
    notifications.on_dismissed = lambda e: log_line(f"dismissed: id={e.id}")

    # ── Show ──
    def show_plain(e):
        guarded(
            notifications.show(
                id=1, title="Hello", body="A plain notification.", payload="plain"
            ),
            "show",
        )

    def show_actions(e):
        guarded(
            notifications.show(
                id=2,
                title="Action buttons",
                body="Tap a button — the reply field returns text.",
                actions=[
                    NotificationAction(id="open", title="Open"),
                    NotificationAction(
                        id="reply",
                        title="Reply",
                        foreground=False,
                        input=NotificationActionInput(label="Type a reply"),
                    ),
                ],
            ),
            "show",
        )

    def request_permissions(e):
        async def _req():
            try:
                granted = await notifications.request_permissions()
                log_line(f"permissions granted: {granted}")
            except Exception:  # noqa: BLE001
                warn_no_backend("request_permissions")

        page.run_task(_req)

    # ── Scheduling ──
    def schedule_delayed(e):
        guarded(
            notifications.schedule(
                id=3,
                when=datetime.timedelta(seconds=10),
                title="Delayed",
                body="10 seconds after you tapped.",
            ),
            "schedule",
        )

    def schedule_daily(e):
        guarded(
            notifications.schedule(
                id=4,
                when=(datetime.datetime.now() + datetime.timedelta(days=1)).replace(
                    hour=8, minute=30, second=0, microsecond=0
                ),
                title="Daily reminder",
                body="Every day at 08:30.",
                match_components=DateTimeComponents.TIME,
                schedule_mode=AndroidScheduleMode.EXACT_ALLOW_WHILE_IDLE,
            ),
            "schedule",
        )

    def schedule_hourly(e):
        guarded(
            notifications.periodically_show(
                id=3,
                repeat_interval=RepeatInterval.HOURLY,
                title="Hourly",
                body="An hourly notification.",
            ),
            "periodically_show",
        )

    def list_pending(e):
        async def _list():
            try:
                pending = await notifications.get_pending_notifications()
                log_line(f"pending: {[p.id for p in pending]}")
            except Exception:  # noqa: BLE001
                warn_no_backend("get_pending_notifications")

        page.run_task(_list)

    def cancel_pending(e):
        guarded(notifications.cancel_pending(), "cancel_pending")

    def check_exact(e):
        async def _check():
            try:
                allowed = await notifications.can_schedule_exact_notifications()
                log_line(f"exact alarms allowed: {allowed}")
                if not allowed:
                    await notifications.request_exact_alarm_permission()
            except Exception:  # noqa: BLE001
                warn_no_backend("can_schedule_exact_notifications")

        page.run_task(_check)

    # ── Channels & styles ──
    def create_channel(e):
        guarded(
            notifications.create_notification_channel(
                NotificationChannel(
                    id="alerts",
                    name="Alerts",
                    description="High-priority alerts",
                )
            ),
            "create_notification_channel",
        )

    def list_channels(e):
        async def _list():
            try:
                channels = await notifications.get_notification_channels()
                log_line(f"channels: {[c.id for c in channels]}")
            except Exception:  # noqa: BLE001
                warn_no_backend("get_notification_channels")

        page.run_task(_list)

    def show_big_text(e):
        guarded(
            notifications.show(
                id=5,
                title="Long read",
                body="Tap to expand.",
                style=BigTextStyle(
                    big_text="The quick brown fox jumps over the lazy dog. " * 3
                ),
            ),
            "show",
        )

    def show_inbox(e):
        guarded(
            notifications.show(
                id=6,
                title="Inbox",
                body="3 unread.",
                style=InboxStyle(lines=["First", "Second", "Third"]),
            ),
            "show",
        )

    def show_progress(e):
        guarded(
            notifications.show(
                id=7,
                title="Downloading",
                body="0%",
                show_progress=True,
                max_progress=4,
                progress=1,
            ),
            "show",
        )

    def show_grouped(e):
        guarded(
            notifications.show(
                id=8,
                title="Summary",
                body="Group summary.",
                group_key="demo_group",
                set_as_group_summary=True,
            ),
            "show",
        )

    def show_options(e):
        guarded(
            notifications.show(
                id=9,
                title="Silent alarm",
                body="Full platform options.",
                options=NotificationOptions(
                    android=AndroidOptions(
                        silent=True, category="alarm", visibility="public"
                    ),
                    iOS=DarwinOptions(interruption_level="passive"),
                ),
            ),
            "show",
        )

    # ── Foreground service (Android) ──
    def start_fgs(e):
        guarded(
            notifications.start_foreground_service(
                id=10, title="Foreground service", body="Work in progress…"
            ),
            "start_foreground_service",
        )

    def stop_fgs(e):
        guarded(notifications.stop_foreground_service(), "stop_foreground_service")

    # ── Probes ──
    def check_enabled(e):
        async def _check():
            try:
                log_line(f"enabled: {await notifications.are_notifications_enabled()}")
            except Exception:  # noqa: BLE001
                warn_no_backend("are_notifications_enabled")

        page.run_task(_check)

    def open_settings(e):
        guarded(
            notifications.open_app_notification_settings(),
            "open_app_notification_settings",
        )

    def list_active(e):
        async def _list():
            try:
                active = await notifications.get_active_notifications()
                log_line(f"active: {[a.id for a in active]}")
            except Exception:  # noqa: BLE001
                warn_no_backend("get_active_notifications")

        page.run_task(_list)

    def check_launch(e):
        async def _check():
            try:
                details = await notifications.get_notification_app_launch_details()
                log_line(
                    f"launched by notification: {details.did_notification_launch_app}"
                )
            except Exception:  # noqa: BLE001
                warn_no_backend("get_notification_app_launch_details")

        page.run_task(_check)

    def check_policy(e):
        async def _check():
            try:
                granted = await notifications.has_notification_policy_access()
                log_line(f"DND access: {granted}")
                if not granted:
                    await notifications.request_notification_policy_access()
            except Exception:  # noqa: BLE001
                warn_no_backend("has_notification_policy_access")

        page.run_task(_check)

    def channel_groups(e):
        guarded(
            notifications.create_notification_channel_group("demo", "Demo group"),
            "create_notification_channel_group",
        )

    # ── Layout: sectioned buttons in one scrollable column ──
    def section(title, buttons):
        return [
            ft.Text(title, weight=ft.FontWeight.BOLD),
            *buttons,
            ft.Divider(),
        ]

    page.add(
        ft.Column(
            controls=[
                *section(
                    "Show",
                    [
                        ft.OutlinedButton(content="Show", on_click=show_plain),
                        ft.OutlinedButton(
                            content="Show with actions", on_click=show_actions
                        ),
                        ft.OutlinedButton(
                            content="Request permissions", on_click=request_permissions
                        ),
                    ],
                ),
                *section(
                    "Scheduling",
                    [
                        ft.OutlinedButton(
                            content="Schedule in 10s", on_click=schedule_delayed
                        ),
                        ft.OutlinedButton(
                            content="Schedule daily 08:30", on_click=schedule_daily
                        ),
                        ft.OutlinedButton(
                            content="Schedule hourly", on_click=schedule_hourly
                        ),
                        ft.OutlinedButton(
                            content="List pending", on_click=list_pending
                        ),
                        ft.OutlinedButton(
                            content="Cancel pending", on_click=cancel_pending
                        ),
                        ft.OutlinedButton(
                            content="Check exact alarms", on_click=check_exact
                        ),
                    ],
                ),
                *section(
                    "Channels & styles",
                    [
                        ft.OutlinedButton(
                            content="Create channel", on_click=create_channel
                        ),
                        ft.OutlinedButton(
                            content="List channels", on_click=list_channels
                        ),
                        ft.OutlinedButton(
                            content="Big text style", on_click=show_big_text
                        ),
                        ft.OutlinedButton(content="Inbox style", on_click=show_inbox),
                        ft.OutlinedButton(content="Progress", on_click=show_progress),
                        ft.OutlinedButton(content="Grouped", on_click=show_grouped),
                        ft.OutlinedButton(
                            content="Options (per-platform)", on_click=show_options
                        ),
                    ],
                ),
                *section(
                    "Foreground service (Android)",
                    [
                        ft.OutlinedButton(
                            content="Start foreground service", on_click=start_fgs
                        ),
                        ft.OutlinedButton(
                            content="Stop foreground service", on_click=stop_fgs
                        ),
                    ],
                ),
                *section(
                    "Probes",
                    [
                        ft.OutlinedButton(
                            content="Are enabled", on_click=check_enabled
                        ),
                        ft.OutlinedButton(
                            content="Open settings", on_click=open_settings
                        ),
                        ft.OutlinedButton(content="Active list", on_click=list_active),
                        ft.OutlinedButton(
                            content="Launch details", on_click=check_launch
                        ),
                        ft.OutlinedButton(content="DND access", on_click=check_policy),
                        ft.OutlinedButton(
                            content="Channel group", on_click=channel_groups
                        ),
                    ],
                ),
                ft.Text("Event log", weight=ft.FontWeight.BOLD),
                log_terminal,
            ],
            spacing=8,
        )
    )


if __name__ == "__main__":
    ft.run(main)
