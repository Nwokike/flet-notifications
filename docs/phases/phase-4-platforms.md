# Phase 4 — Platform Completion & Hardening

**Goal:** every platform behaves predictably: honest capability probes,
a complete error taxonomy that surfaces OS limits instead of crashing, the
full API parity surface (probes for all platforms), and the
`flet-notifications-patch` console script that makes Android builds work
without manual manifest edits.

## Scope

1. **Capability probes** (Python → Dart → platform):
   - `are_notifications_enabled() -> bool` — Android `areNotificationsEnabled`,
     Darwin `checkPermissions().isEnabled`, Linux/Windows/Web `true`
   - `has_full_screen_intent_permission()` — Android only
   - `request_full_screen_intent_permission()`
   - `has_notification_policy_access()` / `request_notification_policy_access()`
   - `get_notification_groups()` / create+delete channel groups (Android)
2. **Error taxonomy finalization** — documented codes in the README:
   `unsupported_platform`, `init_failed`, `show_failed`, `schedule_failed`,
   `invalid_action`, `invalid_schedule`, `invalid_style`, `invalid_channel`,
   `invalid_service_id`, `channel_failed`, `foreground_service_failed`,
   `query_failed`, `permission_failed`, `unknown_method`.
   Dart maps plugin `UnimplementedError`/`UnsupportedError` to
   `error:unsupported_platform:<method>` so e.g. `schedule` on Linux/web
   raises `NotificationError` instead of an opaque failure.
3. **Late-development additions surfaced here**:
   - `open_app_notification_settings()` (FLN v22.3.0; Android/iOS/macOS)
   - `get_active_notifications()` (Android/iOS/macOS)
   - `get_notification_app_launch_details()` (cold-start query)
   - `cancel_all_pending` already exists as `cancel_pending`
4. **`flet-notifications-patch` console script** — Python entry point in the
   wheel (`[project.scripts]`), run after `flet build apk`:
   - injects the 3 receivers + permissions into the app manifest
     (XML-aware, idempotent)
   - enables core-library desugaring + multiDex in `build.gradle.kts`
   - flags: `--project-root`, `--foreground-service-type` (opt-in, like
     alex-stoica's patcher)
5. **Web honest-support documentation** — gesture-gated permissions; no
   scheduling; actions Chrome/Edge only; in-app fallback guidance.

## Files

| File | Action |
|---|---|
| `src/flet_notifications/errors.py` | NEW — documented `NotificationErrorCode` constants (or extend base) |
| `src/flet_notifications/local_notifications.py` | EDIT — probes, launch details, active notifications |
| Dart `notifications_service.dart` | EDIT — probe cases, `UnsupportedError` mapping, launch-details/active cases |
| `src/flet_notifications/patcher.py` | NEW — console-script implementation |
| `pyproject.toml` | EDIT — `[project.scripts]` |
| `tests/test_patcher.py`, `tests/test_probes.py` | NEW |
| Dart `test/notifications_service_test.dart` | EDIT — probe + unsupported-error routing |
| `README.md` | EDIT — error-code table, patcher usage, Web limits |

## Patcher design (from alex-stoica + ktv-player patterns)

```bash
flet build apk ...
uv run flet-notifications-patch --project-root build/flutter \
    [--foreground-service-type specialUse]
cd build/flutter/android && ./gradlew assembleRelease -Psplit-per-abi=true
```

- Manifest: parse with `xml.etree.ElementTree` (namespace-preserving),
  insert `ScheduledNotificationBootReceiver` (with BOOT_COMPLETED /
  MY_PACKAGE_REPLACED / QUICKBOOT filters), `ScheduledNotificationReceiver`,
  `ActionBroadcastReceiver` when missing; ensure `POST_NOTIFICATIONS`,
  `RECEIVE_BOOT_COMPLETED`, `SCHEDULE_EXACT_ALARM`, `VIBRATE`.
  Idempotent: second run is a no-op.
- Gradle: guarded seds inserting `isCoreLibraryDesugaringEnabled = true`,
  `multiDexEnabled = true` and `coreLibraryDesugaring(...)` exactly like
  ktv-player's build-all.yml.
- FGS: only when `--foreground-service-type` is passed (matches
  alex-stoica's opt-in since 0.12.0).

## Definition of done

- All probes work on the platforms where they exist; the rest return
  documented results (`true`/`false`/empty list) rather than raising.
- `schedule()` on Linux/web raises `NotificationError("unsupported_platform")`
  with a message naming the method.
- Patcher unit-tested on a fixture manifest + gradle file (idempotency,
  no-dup receivers, desugaring insertion).
- ruff + pytest green; dart analyze + flutter test green; README documents
  the full error table and the patch workflow.
