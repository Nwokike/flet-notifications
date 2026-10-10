# flet-notifications

Cross-platform local notifications for Flet apps, built on
[`flutter_local_notifications`](https://pub.dev/packages/flutter_local_notifications).

One `uv add flet-notifications` gives you native OS notifications on
**Android, iOS, macOS, Windows, Linux and Web** — no extra Python
dependencies.

## Platform Support

| Platform | Show | Schedule | Actions & callbacks | Channels | Progress | Notes |
|---|---|---|---|---|---|---|
| Android | ✅ | ✅ (AlarmManager, boot restore) | ✅ background + foreground | ✅ | ✅ | Android 7.0+ (API 24) |
| iOS | ✅ | ✅ (OS-owned) | ✅ | ✅ (iOS category groups) | — | iOS 13+; attachments, interruption levels |
| macOS | ✅ | ✅ | ✅ (main isolate) | — | — | macOS 10.15+ |
| Windows | ✅ | one-shot only | ✅ (max 5) | — | ✅ | WinRT toasts; `cancel`/queries need MSIX identity |
| Linux | ✅ | — | ✅ (server-dependent) | — | — | D-Bus; capabilities vary by notification server |
| Web | ✅ | — | Chrome/Edge only | — | — | Browser Notification API; gesture-gated permissions |

## Usage

```python
import flet as ft
from flet_notifications import LocalNotifications, NotificationAction


async def main(page: ft.Page):
    notifications = LocalNotifications()

    async def on_tap(e):
        print("tapped:", e.payload)

    async def on_action(e):
        # e.action_id names the button; e.input holds any reply text
        print(f"action {e.action_id!r} reply={e.input!r} payload={e.payload!r}")

    notifications.on_tap = on_tap
    notifications.on_action = on_action

    if await notifications.request_permissions():
        await notifications.show(
            id=1,
            title="Hello",
            body="Hello from flet-notifications!",
            payload="hello",
        )

        await notifications.show(
            id=2,
            title="Action buttons",
            body="Tap a button.",
            payload="actions",
            actions=[
                NotificationAction(id="open", title="Open"),
                NotificationAction(id="reply", title="Reply", foreground=False),
            ],
        )

ft.run(main)
```

Taps on notifications that arrived while the app was not running are
delivered on the next start (Android background taps, iOS/macOS launches).

See [`examples/flet_notifications_example`](examples/flet_notifications_example)
for a full demo of every feature.

## Development status

Phase 1 of 5 is complete (show / cancel / permissions / tap & action
events). Scheduling, rich styles, channels, progress and platform-specific
options land in the next phases — see
[docs/roadmap.md](docs/roadmap.md).

## Documentation

- [Roadmap & phase plans](docs/roadmap.md)
- [flutter_local_notifications docs](https://pub.dev/packages/flutter_local_notifications)
  — the upstream plugin this extension wraps

## License

MIT
