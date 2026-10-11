# flet-notifications

[![pypi](https://img.shields.io/pypi/v/flet-notifications.svg)](https://pypi.python.org/pypi/flet-notifications)
[![python](https://img.shields.io/badge/python-%3E%3D3.10-%2334D058)](https://pypi.org/project/flet-notifications)
[![license](https://img.shields.io/badge/License-MIT-green.svg)](https://github.com/Nwokike/flet-notifications/blob/main/LICENSE)

Cross-platform local notifications for [Flet](https://flet.dev) apps.

A 1:1 wrapping of the official [flutter_local_notifications](https://pub.dev/packages/flutter_local_notifications) Flutter plugin, in the same architecture as [flet-ads](https://pypi.org/project/flet-ads/). One `uv add flet-notifications` covers Android, iOS, macOS, Windows, Linux and Web — no Python dependencies beyond `flet` (verified on Flet 0.85.0 through 1.0.x in CI).

## Test it without an account

Every release builds the example app for every platform. Sideload any of them and every button is live:

| Variant | Download | Notes |
| :--- | :---: | :--- |
| 📱 **ARM64** (most phones/TVs) | [**app-arm64-v8a-release.apk**](https://github.com/Nwokike/flet-notifications/releases/latest/download/app-arm64-v8a-release.apk) | Modern 64-bit Android devices — grab this one unless you know otherwise |
| 📱 **ARMv7** (older phones/TV boxes) | [**app-armeabi-v7a-release.apk**](https://github.com/Nwokike/flet-notifications/releases/latest/download/app-armeabi-v7a-release.apk) | Legacy 32-bit Android devices |
| 💻 **x86_64** (emulators/ChromeOS) | [**app-x86_64-release.apk**](https://github.com/Nwokike/flet-notifications/releases/latest/download/app-x86_64-release.apk) | Android emulators & Chromebooks |
| 🖥️ **Windows** | [**flet-notifications-example-windows.zip**](https://github.com/Nwokike/flet-notifications/releases/latest/download/flet-notifications-example-windows.zip) | Portable zip |
| 🍎 **macOS** | [**flet-notifications-example-macos.dmg**](https://github.com/Nwokike/flet-notifications/releases/latest/download/flet-notifications-example-macos.dmg) | Disk image |
| 🐧 **Linux** | [**tar.gz**](https://github.com/Nwokike/flet-notifications/releases/latest/download/flet-notifications-example-linux-x86_64.tar.gz) · [**deb**](https://github.com/Nwokike/flet-notifications/releases/latest/download/flet-notifications-example_amd64.deb) · [**rpm**](https://github.com/Nwokike/flet-notifications/releases/latest/download/flet-notifications-example_x86_64.rpm) | Bundle or packages |
| 🌐 **Web** | [**flet-notifications-example-web.tar.gz**](https://github.com/Nwokike/flet-notifications/releases/latest/download/flet-notifications-example-web.tar.gz) | Static bundle |

Plain `flet run` launches the prebuilt client without the extension's Dart half — notifications need a built app (an artifact above, or `flet build <platform>`).

## Platform Support

| Platform | Show | Schedule | Actions & callbacks | Channels | Progress | Notes |
|----------|:----:|:--------:|:-------------------:|:--------:|:--------:|-------|
| iOS      |  ✅  |    ✅    |         ✅          |    —     |    —     | 13+; attachments, interruption levels |
| Android  |  ✅  |    ✅    |         ✅          |    ✅    |    ✅    | 7.0+ (API 24); Android TV works |
| macOS    |  ✅  |    ✅    |         ✅          |    —     |    —     | 10.15+ |
| Windows  |  ✅  | one-shot |         ✅          |    —     |    ✅    | 10+; `cancel`/queries need MSIX identity |
| Linux    |  ✅  |    —     |         ✅          |    —     |    —     | D-Bus server; capabilities vary |
| Web      |  ✅  |    —     |   Chrome/Edge only  |    —     |    —     | Notifications API; gesture-gated permissions |

## Usage

```bash
uv add flet-notifications
```

```python
import flet as ft
from flet_notifications import LocalNotifications

def main(page: ft.Page):
    notifications = LocalNotifications()

    async def on_tap(e):
        print("tapped:", e.payload)

    notifications.on_tap = on_tap

    if await notifications.request_permissions():
        await notifications.show(id=1, title="Hello", body="Hello!")

ft.run(main)
```

## Controls

| Control | Base | Purpose |
|---|---|---|
| `LocalNotifications` | `ft.Service` | Show/schedule/cancel, permissions, probes, channels; construct once, it registers itself |

### Event handlers

```python
notifications.on_tap = on_tap          # typed: NotificationEvent
notifications.on_action = on_action    # typed: e.action_id, e.input, e.data
notifications.on_dismissed = handler   # typed
```

Typed handlers must use `ft.EventHandler[NotificationEvent]`, **not** `ft.ControlEventHandler[NotificationEvent]` — `ControlEventHandler[X]` double-wraps `X` in `Event[...]`, so `e.payload` raises `AttributeError`. `NotificationEvent` carries `id`, `action_id`, `payload`, `input`, `data` and `response_type`.

Taps that arrive while the app wasn't running are replayed on the next start (Android background taps, iOS/macOS cold-start launches).

### Configuration

Scheduling on Android needs permissions in the app's `pyproject.toml`:

```toml
[tool.flet.android.permission]
RECEIVE_BOOT_COMPLETED = true   # restore alarms after reboot
SCHEDULE_EXACT_ALARM = true     # exact schedule modes
```

The scheduled-notification receivers are `<application>` children, which `[tool.flet.android.*]` cannot declare — the `flet-notifications-patch` console script injects them (plus the core-library-desugaring Gradle flags the plugin needs), idempotently:

```bash
uv run flet build apk --yes --project myapp --org com.example -v
uv run flet-notifications-patch --project-root build/flutter
cd build/flutter/android && ./gradlew assembleRelease -Psplit-per-abi=true
```

## Configuration reference

**Types:** `NotificationAction`/`NotificationActionInput` (buttons, inline reply) · `BigTextStyle`/`BigPictureStyle`/`InboxStyle`/`MessagingStyle` (+ `Person`, `Message`, `AndroidIcon`) · `NotificationChannel` (importance, sound, vibration, badge, DND, lights) · `NotificationOptions` with `AndroidOptions`/`DarwinOptions`/`LinuxOptions`/`WindowsOptions`/`WebOptions` (the full per-platform detail surface) · enums `RepeatInterval`, `DateTimeComponents`, `AndroidScheduleMode`, `Importance`, `GroupAlertBehavior`, `InterruptionLevel`.

**Calls:** `show` · `schedule` · `periodically_show` · `cancel`/`cancel_all`/`cancel_pending` · `request_permissions` · `are_notifications_enabled` · `can_schedule_exact_notifications`/`request_exact_alarm_permission` · `request_full_screen_intent_permission` · `has`/`request_notification_policy_access` · `open_app_notification_settings` · `get_pending_notifications`/`get_active_notifications`/`get_notification_app_launch_details` · `create`/`delete`/`get_notification_channels` (+ groups) · `start`/`stop_foreground_service`.

**Errors:** `NotificationError` with a stable `code` — `unsupported_platform`, `init_failed`, `show_failed`, `schedule_failed`, `invalid_action`, `invalid_schedule`, `invalid_style`, `invalid_channel`, `invalid_option`, `invalid_service_id`, `channel_failed`, `foreground_service_failed`, `query_failed`, `permission_failed`, `unknown_method`.

## Limitations

- Linux/Web have no OS scheduler; Windows schedules one-shot only.
- Android channel sound/vibration are immutable after creation; aggressive OEM skins may drop alarms after force-stop; Samsung caps ~500 alarms.
- Interruptions beyond `passive` on Apple need Xcode capabilities.
- Not wrapped (upstream niche): HTML-format style flags, `MediaStyle`, action `semanticAction`/`invisible`/`contextual`, CarPlay, message data MIME/URI, Linux custom hints.
- iOS IPAs need Apple signing and are built owner-side; CI builds every other platform.

## Example

`examples/flet_notifications_example` — every API on one screen with a timestamped event log, built for Windows, macOS, Linux, Android and Web on every release.

## License

MIT
