# flet-notifications — Phase Roadmap

One-to-one Flet extension wrapping `flutter_local_notifications` v22.3.1.
Each phase is planned in detail in its own doc before implementation, ends
green (ruff + pytest + dart analyze/test), and is committed + pushed.

| Phase | Scope | Doc |
|---|---|---|
| 0 — Scaffold & verify | Repo, deps pin verification, skeletons | done (commit `Initial scaffold`) |
| 1 — Core | Service, show/cancel, permissions, tap/action/dismissed events, background tap queue, example buttons, compat CI | [phase-1-core.md](phases/phase-1-core.md) |
| 2 — Scheduling | schedule/periodically_show/cancel_all_pending/pending queries, timezone, exact-alarm probes, boot-restore docs | [phase-2-scheduling.md](phases/phase-2-scheduling.md) |
| 3 — Rich notifications | Styles (big text/picture/inbox/messaging), action inputs + inline reply, channel CRUD, progress + live update, grouping, foreground service | [phase-3-rich.md](phases/phase-3-rich.md) |
| 4 — Platform completion | Windows/Linux/Web details + capability probes + UnsupportedError→NotificationError mapping, iOS dynamic Darwin categories + attachments + interruption levels, macOS parity, `flet-notifications-patch` console script, R8 keep rules | [phase-4-platforms.md](phases/phase-4-platforms.md) |
| 5 — Example app & release | All-platform example app, all-platform build CI (ktv-player pattern), full README, 3-agent verification swarm, tag v0.1.0, release notes | [phase-5-release.md](phases/phase-5-release.md) |

## Architecture (fixed, from research)

- Python: `@ft.control("LocalNotifications") class LocalNotifications(ft.Service)`.
  Only dependency: `flet`. Events via `ft.EventHandler[NotificationEvent[...]]`
  (never `ControlEventHandler[X]` for typed payloads — double-wrap bug).
- Dart: `Extension extends FletExtension` → `createService("LocalNotifications")`
  → `LocalNotificationsService extends FletService`, 1:1 over
  `FlutterLocalNotificationsPlugin`.
- Publish: pure-Python wheel to PyPI (Dart bundled via
  `[tool.setuptools.package-data] "flutter.flet_notifications" = ["**/*"]`).
  No pypi.flet.dev / mobile-forge — Flutter plugin native code compiles via
  `flutter pub` + Gradle/Xcode during `flet build`.

## Known platform limits (documented, surfaced via probes)

Linux/Web: no OS scheduling. Windows: one-shot schedule only; cancel/active
queries need MSIX identity. Web: gesture-gated permissions, actions
Chrome/Edge only. Android: channel sound/vibration immutable after creation;
OEM force-stop may drop alarms; Samsung ~500-alarm cap.
