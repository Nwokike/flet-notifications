"""Example app for flet-notifications.

Exercises the extension API phase by phase: show / actions / cancel /
permissions / scheduling, with a live event log for taps, actions and
dismissals. The app grows a section per phase as the API expands.
"""

from datetime import datetime, timedelta

import flet as ft

from flet_notifications import (
    AndroidOptions,
    AndroidScheduleMode,
    BigTextStyle,
    DarwinOptions,
    DateTimeComponents,
    GroupAlertBehavior,
    Importance,
    InboxStyle,
    LocalNotifications,
    NotificationAction,
    NotificationActionInput,
    NotificationChannel,
    NotificationOptions,
    RepeatInterval,
)


async def main(page: ft.Page):
    page.title = "flet-notifications example"
    page.padding = 24

    notifications = LocalNotifications()

    log = ft.ListView(expand=True, spacing=4, auto_scroll=True)
    next_id = {"value": 1}
    backend_missing = {"warned": False}

    def log_line(text: str) -> None:
        log.controls.append(ft.Text(text, size=13))
        page.update(log)

    def log_event(kind: str, e) -> None:
        log_line(
            f"{kind}: id={e.id} action={e.action_id!r} "
            f"payload={e.payload!r} input={e.input!r}"
        )

    def warn_no_backend() -> None:
        """Plain `flet run` uses Flet's prebuilt client, which does not contain
        this extension's Dart backend — invokes time out. Explain once instead
        of raising a wall of tracebacks."""
        if backend_missing["warned"]:
            return
        backend_missing["warned"] = True
        log_line(
            "No notification backend in this runner: `flet run` launches the "
            "prebuilt client without extension code. Run a built app instead "
            "— a release artifact (Windows zip / APK / dmg / Linux bundle) or "
            "`flet build windows|macos|linux|apk` locally."
        )

    def backend_guard(handler):
        """Wrap an on_click handler so a missing backend degrades to a log
        line instead of a traceback."""

        async def wrapper(e):
            try:
                await handler(e)
            except Exception:  # noqa: BLE001 - any backend failure degrades
                warn_no_backend()

        return wrapper

    async def on_tap(e):
        log_event("tap", e)
        page.update(log)

    async def on_action(e):
        log_event("action", e)
        page.update(log)

    async def on_dismissed(e):
        log_event("dismissed", e)
        page.update(log)

    notifications.on_tap = on_tap
    notifications.on_action = on_action
    notifications.on_dismissed = on_dismissed

    status = ft.Text("", size=13)

    def set_status(text: str) -> None:
        status.value = text
        page.update(status)

    async def request_permissions(_):
        granted = await notifications.request_permissions()
        set_status(f"permissions granted: {granted}")

    request_permissions = backend_guard(request_permissions)

    async def show(_):
        await notifications.show(
            id=next_id["value"],
            title="Hello",
            body="A plain notification from flet-notifications.",
            payload="plain",
        )
        next_id["value"] += 1

    show = backend_guard(show)

    async def show_with_actions(_):
        await notifications.show(
            id=next_id["value"],
            title="Action buttons",
            body="Tap a button — the reply field returns text.",
            payload="actions",
            actions=[
                NotificationAction(id="open", title="Open"),
                NotificationAction(
                    id="reply",
                    title="Reply",
                    foreground=False,
                    input=NotificationActionInput(label="Type a reply"),
                ),
            ],
        )
        next_id["value"] += 1

    show_with_actions = backend_guard(show_with_actions)

    async def cancel(_):
        await notifications.cancel(next_id["value"] - 1)

    cancel = backend_guard(cancel)

    async def cancel_all(_):
        await notifications.cancel_all()

    cancel_all = backend_guard(cancel_all)

    # ── Scheduling ──────────────────────────────────────────────────────

    async def schedule_delayed(_):
        await notifications.schedule(
            id=next_id["value"],
            when=timedelta(seconds=10),
            title="Delayed",
            body="10 seconds after you tapped.",
            payload="delayed",
        )
        next_id["value"] += 1
        set_status("scheduled: 10 second delay")

    schedule_delayed = backend_guard(schedule_delayed)

    async def schedule_daily(_):
        tomorrow = datetime.now() + timedelta(days=1)
        await notifications.schedule(
            id=next_id["value"],
            when=tomorrow.replace(hour=8, minute=30, second=0, microsecond=0),
            title="Daily reminder",
            body="Every day at 08:30.",
            payload="daily",
            match_components=DateTimeComponents.TIME,
            schedule_mode=AndroidScheduleMode.EXACT_ALLOW_WHILE_IDLE,
        )
        next_id["value"] += 1
        set_status("scheduled: daily at 08:30")

    schedule_daily = backend_guard(schedule_daily)

    async def schedule_periodic(_):
        await notifications.periodically_show(
            id=next_id["value"],
            repeat_interval=RepeatInterval.HOURLY,
            title="Hourly",
            body="An hourly notification.",
            payload="hourly",
        )
        next_id["value"] += 1
        set_status("scheduled: hourly")

    schedule_periodic = backend_guard(schedule_periodic)

    async def list_pending(_):
        pending = await notifications.get_pending_notifications()
        log.controls.append(ft.Text(f"pending: {[p.id for p in pending]}", size=13))
        page.update(log)

    list_pending = backend_guard(list_pending)

    async def cancel_pending(_):
        await notifications.cancel_pending()
        set_status("cancelled all pending")

    cancel_pending = backend_guard(cancel_pending)

    async def check_exact_alarms(_):
        allowed = await notifications.can_schedule_exact_notifications()
        set_status(f"exact alarms allowed: {allowed}")
        if not allowed:
            await notifications.request_exact_alarm_permission()

    check_exact_alarms = backend_guard(check_exact_alarms)

    # ── Rich notifications (Phase 3) ────────────────────────────────────

    async def create_channel(_):
        await notifications.create_notification_channel(
            NotificationChannel(
                id="alerts",
                name="Alerts",
                description="High-priority alerts",
                importance=Importance.HIGH,
            )
        )
        set_status("channel 'alerts' created")

    create_channel = backend_guard(create_channel)

    async def list_channels(_):
        channels = await notifications.get_notification_channels()
        log.controls.append(
            ft.Text(f"channels: {[(c.id, c.name) for c in channels]}", size=13)
        )
        page.update(log)

    list_channels = backend_guard(list_channels)

    async def show_big_text(_):
        await notifications.show(
            id=next_id["value"],
            title="Long read",
            body="Tap to expand.",
            payload="bigtext",
            style=BigTextStyle(
                big_text="The quick brown fox jumps over the lazy dog. " * 3
            ),
        )
        next_id["value"] += 1

    show_big_text = backend_guard(show_big_text)

    async def show_inbox(_):
        await notifications.show(
            id=next_id["value"],
            title="Inbox",
            body="3 unread.",
            payload="inbox",
            style=InboxStyle(lines=["First", "Second", "Third"]),
        )
        next_id["value"] += 1

    show_inbox = backend_guard(show_inbox)

    async def show_progress(_):
        await notifications.show(
            id=next_id["value"],
            title="Downloading",
            body="0%",
            payload="progress",
            show_progress=True,
            max_progress=4,
            progress=1,
        )
        next_id["value"] += 1
        set_status("progress started — tap Progress again to advance the id")

    show_progress = backend_guard(show_progress)

    async def show_grouped(_):
        await notifications.show(
            id=next_id["value"],
            title="Summary",
            body="Group summary.",
            payload="group",
            group_key="demo_group",
            set_as_group_summary=True,
            group_alert_behavior=GroupAlertBehavior.SUMMARY,
        )
        next_id["value"] += 1
        set_status("group summary shown")

    show_grouped = backend_guard(show_grouped)

    async def show_options(_):
        """Platform-specific options in one call: silent alarm-category
        notification on Android, passive interruption on iOS/macOS."""
        await notifications.show(
            id=next_id["value"],
            title="Silent alarm",
            body="Posted with full platform options.",
            payload="options",
            options=NotificationOptions(
                android=AndroidOptions(
                    silent=True,
                    category="alarm",
                    ongoing=False,
                    visibility="public",
                ),
                iOS=DarwinOptions(interruption_level="passive"),
            ),
        )
        next_id["value"] += 1

    show_options = backend_guard(show_options)

    async def start_fgs(_):
        await notifications.start_foreground_service(
            id=next_id["value"],
            title="Foreground service",
            body="Work in progress…",
            payload="fgs",
        )
        next_id["value"] += 1
        set_status("foreground service started")

    start_fgs = backend_guard(start_fgs)

    async def stop_fgs(_):
        await notifications.stop_foreground_service()
        set_status("foreground service stopped")

    stop_fgs = backend_guard(stop_fgs)

    # ── Probes (Phase 4) ────────────────────────────────────────────────

    async def check_enabled(_):
        enabled = await notifications.are_notifications_enabled()
        set_status(f"notifications enabled: {enabled}")

    check_enabled = backend_guard(check_enabled)

    async def open_settings(_):
        await notifications.open_app_notification_settings()
        set_status("opened OS notification settings")

    open_settings = backend_guard(open_settings)

    async def list_active(_):
        active = await notifications.get_active_notifications()
        log.controls.append(
            ft.Text(f"active: {[(a.id, a.title) for a in active]}", size=13)
        )
        page.update(log)

    list_active = backend_guard(list_active)

    async def check_launch(_):
        details = await notifications.get_notification_app_launch_details()
        if details.did_notification_launch_app:
            set_status(f"launched by notification: {details.notification.payload!r}")
        else:
            set_status("not launched by a notification")

    check_launch = backend_guard(check_launch)

    async def check_policy(_):
        granted = await notifications.has_notification_policy_access()
        set_status(f"DND access: {granted}")
        if not granted:
            await notifications.request_notification_policy_access()

    check_policy = backend_guard(check_policy)

    async def channel_groups(_):
        await notifications.create_notification_channel_group("demo", "Demo group")
        set_status("channel group 'demo' created")

    channel_groups = backend_guard(channel_groups)

    page.add(
        ft.Text("flet-notifications", size=24, weight=ft.FontWeight.BOLD),
        ft.Text(
            "Notifications need a built app: `flet run` uses the prebuilt "
            "client without extension code. Build with `flet build "
            "<platform>` (or install a release artifact) to see notifications.",
            size=12,
            color=ft.Colors.ORANGE_400,
        ),
        status,
        ft.Row(
            [
                ft.FilledButton("Request permissions", on_click=request_permissions),
                ft.FilledButton("Show", on_click=show),
                ft.FilledButton("Show with actions", on_click=show_with_actions),
                ft.FilledButton("Cancel last", on_click=cancel),
                ft.FilledButton("Cancel all", on_click=cancel_all),
            ],
            wrap=True,
            spacing=8,
        ),
        ft.Divider(),
        ft.Row(
            [
                ft.FilledButton("Schedule in 10s", on_click=schedule_delayed),
                ft.FilledButton("Schedule daily 08:30", on_click=schedule_daily),
                ft.FilledButton("Schedule hourly", on_click=schedule_periodic),
                ft.FilledButton("List pending", on_click=list_pending),
                ft.FilledButton("Cancel pending", on_click=cancel_pending),
                ft.FilledButton("Check exact alarms", on_click=check_exact_alarms),
            ],
            wrap=True,
            spacing=8,
        ),
        ft.Row(
            [
                ft.FilledButton("Create channel", on_click=create_channel),
                ft.FilledButton("List channels", on_click=list_channels),
                ft.FilledButton("Big text style", on_click=show_big_text),
                ft.FilledButton("Inbox style", on_click=show_inbox),
                ft.FilledButton("Progress", on_click=show_progress),
                ft.FilledButton("Grouped", on_click=show_grouped),
                ft.FilledButton("Options", on_click=show_options),
                ft.FilledButton("Start FGS", on_click=start_fgs),
                ft.FilledButton("Stop FGS", on_click=stop_fgs),
            ],
            wrap=True,
            spacing=8,
        ),
        ft.Row(
            [
                ft.FilledButton("Are enabled", on_click=check_enabled),
                ft.FilledButton("Open settings", on_click=open_settings),
                ft.FilledButton("Active list", on_click=list_active),
                ft.FilledButton("Launch details", on_click=check_launch),
                ft.FilledButton("DND access", on_click=check_policy),
                ft.FilledButton("Channel group", on_click=channel_groups),
            ],
            wrap=True,
            spacing=8,
        ),
        ft.Divider(),
        ft.Text("Event log", weight=ft.FontWeight.BOLD),
        log,
    )


ft.run(main)
