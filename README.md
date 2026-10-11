# flet-notifications

[![PyPI](https://img.shields.io/badge/pypi-flet--notifications-blue)](https://pypi.org/project/flet-notifications/)
[![Python](https://img.shields.io/badge/python-%3E%3D3.10-blue)](https://pypi.org/project/flet-notifications/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-100%20pytest%20%2B%2070%20dart-brightgreen)](.github/workflows/compat.yml)

Cross-platform local notifications for Flet apps, built on
[`flutter_local_notifications`](https://pub.dev/packages/flutter_local_notifications)
22.3.1. One `uv add flet-notifications` gives you native OS notifications on
**Android, iOS, macOS, Windows, Linux and Web** — no extra Python
dependencies.

### Install

```bash
uv add flet-notifications
# or: pip install flet-notifications
```

## Platform Support

| Platform | Show | Schedule | Actions & callbacks | Channels | Progress | Notes |
|---|---|---|---|---|---|---|
| Android | ✅ | ✅ (AlarmManager, boot restore) | ✅ background + foreground | ✅ | ✅ | Android 7.0+ (API 24) |
| iOS | ✅ | ✅ (OS-owned) | ✅ | — | — | iOS 13+; attachments, interruption levels |
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
        # e: NotificationEvent — e.id, e.action_id, e.payload, e.input,
        # e.response_type ("tap" | "action" | "dismissed"), e.data
        print("tapped:", e.payload)

    async def on_action(e):
        # e.action_id names the button; e.input holds any reply text;
        # e.data carries Windows input values by input id
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

Handlers are typed with `ft.EventHandler[NotificationEvent[...]]` — the
same `ft.EventHandler` form `flet-ads` uses for typed payload events (never
`ControlEventHandler`, which double-wraps and breaks `.payload`-style
access). Taps on notifications that arrived while the app was not running
are delivered on the next start (Android background taps, iOS/macOS
launches).

## API reference

### `LocalNotifications` — the service

Construct once; it registers itself with the page. No `page.add()` needed.
It never calls `update()`, so it is safe inside Flet 1.0's frozen
declarative trees.

**Showing**

| Method | Purpose |
|---|---|
| `show(id, title, body, payload, actions, style, …)` | Show immediately; same id updates (live progress) |
| `schedule(id, when, match_components, …)` | OS-owned scheduling; `when` is a `datetime` or `timedelta` |
| `periodically_show(id, repeat_interval, …)` | Fixed interval, optional custom duration (≥ 60 s) |
| `cancel(id, tag=None)` / `cancel_all()` / `cancel_pending()` | Dismiss shown or scheduled notifications |

**Permissions & probes**

| Method | Returns |
|---|---|
| `request_permissions()` | `bool` (longer timeout for the OS dialog) |
| `are_notifications_enabled()` | `bool` — provisional grants count as enabled on Apple |
| `can_schedule_exact_notifications()` / `request_exact_alarm_permission()` | Android 12+/14+ alarm access |
| `request_full_screen_intent_permission()` | Android 14+ |
| `has_notification_policy_access()` / `request_notification_policy_access()` | Android Do-Not-Disturb access |
| `open_app_notification_settings()` | `bool` — opens the OS settings page |

**Queries**

| Method | Returns |
|---|---|
| `get_pending_notifications()` | `list[PendingNotification]` — scheduled, undelivered |
| `get_active_notifications()` | `list[ActiveNotification]` — currently in the tray |
| `get_notification_app_launch_details()` | `LaunchDetails` — how the app was launched |

**Channels (Android 8.0+)**

`create_notification_channel(NotificationChannel(...))`,
`delete_notification_channel(id)`, `get_notification_channels()`,
plus `create_notification_channel_group(id, name, description="")` and
`delete_notification_channel_group(id)`.

**Foreground service (Android)**

`start_foreground_service(id≠0, title, body, …, start_type,
foreground_service_types=[…])` and `stop_foreground_service()`.

### Configuration types

| Type | What it configures |
|---|---|
| `NotificationAction` / `NotificationActionInput` | Buttons and inline-reply fields |
| `BigTextStyle` / `BigPictureStyle` / `InboxStyle` / `MessagingStyle` | Expandable styles (+ `Person`, `Message`, `AndroidIcon`) |
| `NotificationChannel` | Channel id/name, importance, sound, vibration, badge, DND, lights |
| `NotificationOptions` (+ `AndroidOptions`, `DarwinOptions`, `LinuxOptions`, `WindowsOptions`, `WebOptions`) | The full per-platform detail surface |

## Per-platform options

`NotificationOptions` mirrors the upstream plugin's `NotificationDetails`
one-to-one:

```python
from flet_notifications import AndroidOptions, DarwinOptions, NotificationOptions

await notifications.show(
    id=1,
    title="Silent alarm",
    body="Full platform options.",
    options=NotificationOptions(
        android=AndroidOptions(
            silent=True,
            category="alarm",
            ongoing=False,
            visibility="public",
            color="#FF5722",
            sound="alert_tone",
            vibration_pattern=[0, 250, 100],
            full_screen_intent=False,
        ),
        iOS=DarwinOptions(
            interruption_level="passive",
            badge_number=1,
            thread_identifier="group-1",
        ),
    ),
)
```

Android covers channel description, icon, importance/priority, sound (raw or
URI), vibration, LED lights, the ongoing/silent/color/colorized/auto-cancel/
only-alert-once flags, chronometer, badge number, visibility, timeout,
category, full-screen intent, ticker and sub-text. Darwin covers sound,
badge number, subtitle, thread grouping, interruption level, critical sound
volume, attachments and the presentation flags. Linux, Windows and Web
cover the details their platforms expose.

## Scheduling

```python
from datetime import datetime, timedelta

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
that `[tool.flet.android.*]` can only partially express:

**Permissions** (`[tool.flet.android.permission]` in the app's
`pyproject.toml` — supported directly):

```toml
[tool.flet.android.permission]
RECEIVE_BOOT_COMPLETED = true   # restore alarms after reboot
SCHEDULE_EXACT_ALARM = true     # exact schedule modes
```

**Receivers** (`ScheduledNotificationBootReceiver`,
`ScheduledNotificationReceiver`, `ActionBroadcastReceiver`) are
`<application>` children, which Flet cannot declare from `pyproject.toml` —
use the patcher below.

### `flet-notifications-patch`

Ships as a console script; run it after `flet build apk` to inject the
receivers, the required permissions and the core-library-desugaring Gradle
flags the plugin needs (idempotent):

```bash
uv run flet build apk --yes --project myapp --org com.example -v
uv run flet-notifications-patch --project-root build/flutter
# foreground services (opt-in):
uv run flet-notifications-patch --project-root build/flutter \
    --foreground-service-type specialUse
# then compile with the patched project:
cd build/flutter/android && ./gradlew assembleRelease -Psplit-per-abi=true
```

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

# foreground service (Android; needs manifest entries — see the patcher)
await notifications.start_foreground_service(id=5, title="Syncing")
await notifications.stop_foreground_service()
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
| `unknown_method` | No such invoke (a version mismatch between halves) |

## Limitations

- **Linux/Web have no OS scheduler** — `schedule`/`periodically_show` raise
  `NotificationError("unsupported_platform")`. Windows schedules one-shot
  only (repeat components are ignored by the platform).
- **Windows** `cancel`/`getActiveNotifications` need an MSIX package
  identity; web actions work in Chrome/Edge only and permissions must come
  from a user gesture.
- **Android** channel sound/vibration are immutable after creation (create a
  new channel id to change them); aggressive OEM skins (Xiaomi/Huawei) may
  drop scheduled alarms after force-stop; Samsung caps ~500 alarms.
- **iOS** interruptions beyond `passive` need capabilities in Xcode; badge
  control is limited to per-notification badge numbers.
- **iOS packaging is owner-side** — IPAs need Apple signing, so CI builds
  every platform except iOS.
- Deliberately **not** wrapped (upstream niche, on the roadmap): HTML-format
  style flags, `MediaStyle`, action `semanticAction`/`invisible`/
  `contextual` flags, CarPlay, message data MIME/URI, Windows text inputs
  beyond actions, `getActiveNotificationMessagingStyle`, and per-call
  `timeout` parameters (permission flows already use 300 s).

## Development status

All five build phases are complete: core show/cancel/permissions/events,
scheduling, rich styles/channels/progress/grouping/foreground service,
platform completion (probes, error taxonomy, Android patcher). See
[docs/roadmap.md](docs/roadmap.md) for the phase history and
[CHANGELOG.md](CHANGELOG.md) for this release.

## Prebuilt example

The example app exercises every API on one screen. Prebuilt binaries for
every platform are attached to each GitHub release: per-ABI Android APKs
and AAB, Windows zip, macOS dmg, Linux tar.gz/deb/rpm, and a web bundle.
Sideload any of them — the example needs no account and no configuration.
Note that plain `flet run` launches Flet's prebuilt client, which does not
contain this extension's Dart half — notifications need a built app.

## Documentation

- [Changelog](CHANGELOG.md)
- [Roadmap & phase history](docs/roadmap.md)
- [flutter_local_notifications docs](https://pub.dev/packages/flutter_local_notifications)
  — the upstream plugin this extension wraps

## License

MIT
