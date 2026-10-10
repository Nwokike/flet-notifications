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

## Styles, channels, progress, foreground service

```python
from flet_notifications import BigTextStyle, Importance, NotificationChannel

# expandable styles
await notifications.show(id=1, title="Long read", body="…",
                         style=BigTextStyle(big_text="the long text"))

# Android channels (create once; sound/vibration are fixed at creation)
await notifications.create_notification_channel(
    NotificationChannel(id="alerts", name="Alerts", importance=Importance.HIGH)
)
await notifications.show(id=2, title="Alert", body="…", channel_id="alerts")

# progress — call show again with the same id to advance
await notifications.show(id=3, title="Downloading", show_progress=True,
                         max_progress=100, progress=40)

# grouping
await notifications.show(id=4, title="Summary", group_key="updates",
                         set_as_group_summary=True)

# foreground service (Android; needs FOREGROUND_SERVICE + a <service> entry)
await notifications.start_foreground_service(id=5, title="Syncing")
await notifications.stop_foreground_service()
```

The foreground service on Android additionally needs `FOREGROUND_SERVICE`
in `[tool.flet.android.permission]` and a `<service>` manifest entry —
declared the same way as the receivers above via the Phase 4 patcher.

## Scheduling

```python
from datetime import timedelta

from flet_notifications import DateTimeComponents, RepeatInterval

# one-shot, 10 seconds from now
await notifications.schedule(id=1, when=timedelta(seconds=10),
                             title="Delayed", body="10 seconds")

# daily at 08:30 device time (naive datetime = wall clock)
await notifications.schedule(id=2, when=datetime(2030, 1, 1, 8, 30),
                             title="Daily", body="Every day",
                             match_components=DateTimeComponents.TIME,
                             time_zone="Africa/Lagos")

# every hour
await notifications.periodically_show(id=3, repeat_interval=RepeatInterval.HOURLY,
                                      title="Hourly", body="Tick")

await notifications.get_pending_notifications()
await notifications.cancel_pending()
```

Scheduled notifications are owned by the OS and survive app restarts.

### Android manifest requirements

Scheduled notifications need entries in the generated `AndroidManifest.xml`
that Flet's `pyproject.toml` can only partially express:

**Permissions** (`[tool.flet.android.permission]` in the app's
`pyproject.toml` — supported directly):

```toml
[tool.flet.android.permission]
RECEIVE_BOOT_COMPLETED = true   # restore alarms after reboot
SCHEDULE_EXACT_ALARM = true     # exact schedule modes
```

**Receivers** (`ScheduledNotificationBootReceiver`,
`ScheduledNotificationReceiver`, `ActionBroadcastReceiver`) are
`<application>` children, which `[tool.flet.android.*]` cannot declare —
Flet exposes only `permission`, `feature`, `meta_data` and `provider`.
They must be injected into `build/flutter/android/app/src/main/
AndroidManifest.xml` after `flet build apk`.

### `flet-notifications-patch`

The extension ships a console script that does this for you — it adds the
receivers, the required permissions, and the core-library-desugaring Gradle
flags the plugin needs (idempotently):

```bash
uv run flet build apk --yes --project myapp --org com.example -v
uv run flet-notifications-patch --project-root build/flutter
# foreground services (opt-in):
uv run flet-notifications-patch --project-root build/flutter \
    --foreground-service-type specialUse
# then compile with the patched project:
cd build/flutter/android && ./gradlew assembleRelease -Psplit-per-abi=true
```

## Error codes

Failures raise `NotificationError` with a stable ``code``:

| Code | Meaning |
|---|---|
| `unsupported_platform` | The OS lacks the feature (e.g. scheduling on Linux/Web) |
| `init_failed` | The notification backend could not initialize |
| `show_failed` / `schedule_failed` | The OS rejected the notification |
| `invalid_action` / `invalid_style` / `invalid_schedule` / `invalid_channel` / `invalid_service_id` | Bad configuration |
| `channel_failed` / `foreground_service_failed` | Android channel/service failure |
| `query_failed` / `permission_failed` | Probe or permission failure |

## Development status

All five feature phases are complete: core show/cancel/permissions/events,
scheduling, rich styles/channels/progress/grouping/foreground service, and
platform completion (probes, error taxonomy, Android patcher). The first
PyPI release is next — see [docs/roadmap.md](docs/roadmap.md).

## Documentation

- [Roadmap & phase plans](docs/roadmap.md)
- [flutter_local_notifications docs](https://pub.dev/packages/flutter_local_notifications)
  — the upstream plugin this extension wraps

## License

MIT
