"""Example app for flet-notifications.

Exercises the extension API phase by phase: show / actions / cancel /
permissions / scheduling, with a live event log for taps, actions and
dismissals. The app grows a section per phase as the API expands.
"""

from datetime import datetime, timedelta

import flet as ft

from flet_notifications import (
    AndroidScheduleMode,
    DateTimeComponents,
    LocalNotifications,
    NotificationAction,
    NotificationActionInput,
    RepeatInterval,
)


async def main(page: ft.Page):
    page.title = "flet-notifications example"
    page.padding = 24

    notifications = LocalNotifications()

    log = ft.ListView(expand=True, spacing=4, auto_scroll=True)
    next_id = {"value": 1}

    def log_event(kind: str, e) -> None:
        log.controls.append(
            ft.Text(
                f"{kind}: id={e.id} action={e.action_id!r} "
                f"payload={e.payload!r} input={e.input!r}",
                size=13,
            )
        )

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

    async def show(_):
        await notifications.show(
            id=next_id["value"],
            title="Hello",
            body="A plain notification from flet-notifications.",
            payload="plain",
        )
        next_id["value"] += 1

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

    async def cancel(_):
        await notifications.cancel(next_id["value"] - 1)

    async def cancel_all(_):
        await notifications.cancel_all()

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

    async def list_pending(_):
        pending = await notifications.get_pending_notifications()
        log.controls.append(ft.Text(f"pending: {[p.id for p in pending]}", size=13))
        page.update(log)

    async def cancel_pending(_):
        await notifications.cancel_pending()
        set_status("cancelled all pending")

    async def check_exact_alarms(_):
        allowed = await notifications.can_schedule_exact_notifications()
        set_status(f"exact alarms allowed: {allowed}")
        if not allowed:
            await notifications.request_exact_alarm_permission()

    page.add(
        ft.Text("flet-notifications", size=24, weight=ft.FontWeight.BOLD),
        status,
        ft.Row(
            [
                ft.ElevatedButton("Request permissions", on_click=request_permissions),
                ft.ElevatedButton("Show", on_click=show),
                ft.ElevatedButton("Show with actions", on_click=show_with_actions),
                ft.ElevatedButton("Cancel last", on_click=cancel),
                ft.ElevatedButton("Cancel all", on_click=cancel_all),
            ],
            wrap=True,
            spacing=8,
        ),
        ft.Divider(),
        ft.Row(
            [
                ft.ElevatedButton("Schedule in 10s", on_click=schedule_delayed),
                ft.ElevatedButton("Schedule daily 08:30", on_click=schedule_daily),
                ft.ElevatedButton("Schedule hourly", on_click=schedule_periodic),
                ft.ElevatedButton("List pending", on_click=list_pending),
                ft.ElevatedButton("Cancel pending", on_click=cancel_pending),
                ft.ElevatedButton("Check exact alarms", on_click=check_exact_alarms),
            ],
            wrap=True,
            spacing=8,
        ),
        ft.Divider(),
        ft.Text("Event log", weight=ft.FontWeight.BOLD),
        log,
    )


ft.run(main)
