"""Example app for flet-notifications.

Exercises the Phase 1 core API: show / show with action buttons / cancel /
cancel all / permissions, with a live event log for taps, actions and
dismissals. The app grows a section per phase as the extension API expands.
"""

import flet as ft

from flet_notifications import (
    LocalNotifications,
    NotificationAction,
    NotificationActionInput,
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

    async def request_permissions(_):
        granted = await notifications.request_permissions()
        status.value = f"permissions granted: {granted}"
        page.update(status)

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
        ft.Text("Event log", weight=ft.FontWeight.BOLD),
        log,
    )


ft.run(main)
