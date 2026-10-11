# Changelog

All notable changes to `flet-notifications` are documented here. The format
follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this
project adheres to [Semantic Versioning](https://semver.org/).

## [0.1.0] - 2026-10-11

First release. Cross-platform local notifications for Flet apps — a one-to-one
wrap of [`flutter_local_notifications`](https://pub.dev/packages/flutter_local_notifications)
22.3.1 as a native `ft.Service`.

### Added

- **`LocalNotifications`** — one headless service on the page: `show`,
  `schedule`, `periodically_show`, `cancel`/`cancel_all`/`cancel_pending`,
  `request_permissions`, and the full probe set (`are_notifications_enabled`,
  `can_schedule_exact_notifications`, exact-alarm / full-screen-intent /
  notification-policy access, `open_app_notification_settings`).
- **Actions & callbacks** — action buttons with inline-reply input on
  Android/iOS/macOS/Windows; taps, actions and dismissals arrive on
  `on_tap` / `on_action` / `on_dismissed` as typed `NotificationEvent`s.
  Taps that arrive while the app is not running are queued and replayed on
  next start (Android background isolate; iOS/macOS cold-start launch
  details).
- **Scheduling** — one-shot, daily/weekly/monthly/yearly recurrence,
  periodic intervals and custom durations; naive datetimes are wall-clock in
  a named IANA timezone, aware datetimes keep the exact instant. OS-owned;
  survives restarts and (Android, once patched) reboots.
- **Rich notifications** — big-text / big-picture / inbox / messaging styles
  with people and messages; Android channels and channel groups (CRUD);
  progress bars with live updates; grouping; foreground service start/stop
  with `start_type` and `foreground_service_types`.
- **Per-platform options** — `NotificationOptions` with
  `AndroidOptions` / `DarwinOptions` / `LinuxOptions` / `WindowsOptions` /
  `WebOptions` covering the upstream plugin's detail surface: sound,
  vibration, LED lights, ongoing/silent/color flags, chronometer, badge
  numbers, thread grouping, interruption levels, attachments, urgency,
  timeouts, Windows header/audio/scenario/images/bindings and web flags.
- **`flet-notifications-patch`** — console script run after `flet build
  apk` that injects the scheduled-notification receivers, permissions and
  core-library-desugaring Gradle flags the plugin needs (idempotent), with
  an opt-in foreground-service mode.
- **Error taxonomy** — `NotificationError` with stable
  `NotificationErrorCode`s (`unsupported_platform`, `init_failed`,
  `show_failed`, `schedule_failed`, `invalid_action`, `invalid_schedule`,
  `invalid_style`, `invalid_channel`, `invalid_service_id`, `channel_failed`,
  `foreground_service_failed`, `query_failed`, `permission_failed`,
  `unknown_method`).
- **Example app** exercising every API, an all-platform build workflow and
  96 Python + 70 Dart tests.

### Platform notes

- Android 7.0+ (API 24), iOS 13+, macOS 10.15+, Windows 10+, Linux
  (freedesktop D-Bus), Web (Browser Notification API).
- Linux/Web have no OS scheduling; Windows schedules one-shot only.
- iOS IPK/IPA signing is provisioned owner-side.

[0.1.0]: https://github.com/Nwokike/flet-notifications/releases/tag/v0.1.0
