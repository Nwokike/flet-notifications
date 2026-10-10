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
from flet_notifications import LocalNotifications

async def main(page: ft.Page):
    notifications = LocalNotifications()

    async def on_tap(e):
        print("tapped:", e.payload)

    notifications.on_tap = on_tap

    await notifications.request_permissions()
    await notifications.show(
        id=1,
        title="Hello",
        body="Hello from flet-notifications!",
        payload="hello",
    )

ft.run(main)
```

See [`examples/flet_notifications_example`](examples/flet_notifications_example)
for a full demo of every feature.

## Documentation

Full API reference coming with v0.1.0. In the meantime:

- [flutter_local_notifications docs](https://pub.dev/packages/flutter_local_notifications)
  — the upstream plugin this extension wraps

## License

MIT
