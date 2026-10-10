# Phase 2 — Scheduling

**Goal:** real OS-level scheduling (Android AlarmManager with boot restore, iOS/macOS
UNCalendar triggers, Windows one-shot), repeat intervals, timezone handling,
pending-request queries and exact-alarm probes.

## Verified API (FLN 22.3.1, reference clone)

- `zonedSchedule({required int id, required TZDateTime scheduledDate, required NotificationDetails notificationDetails, required AndroidScheduleMode androidScheduleMode, String? title, String? body, String? payload, DateTimeComponents? matchDateTimeComponents})`
- `periodicallyShow({required int id, required RepeatInterval repeatInterval, required NotificationDetails notificationDetails, required AndroidScheduleMode androidScheduleMode, String? title, String? body, String? payload})`
- `periodicallyShowWithDuration({required int id, required Duration repeatDurationInterval, ...})` (≥ 1 minute)
- `cancelAllPendingNotifications()`, `pendingNotificationRequests() -> List<PendingNotificationRequest(id, title, body, payload)>`
- Android: `requestExactAlarmsPermission()`, `canScheduleExactNotifications()`
- Enums: `AndroidScheduleMode{alarmClock, exact, exactAllowWhileIdle, inexact, inexactAllowWhileIdle}`,
  `DateTimeComponents{time, dayOfWeekAndTime, dayOfMonthAndTime, dateAndTime}`,
  `RepeatInterval{everyMinute, hourly, daily, weekly}`

## Files

| File | Action |
|---|---|
| `src/flet_notifications/types.py` | NEW — `RepeatInterval`, `DateTimeComponents`, `AndroidScheduleMode` |
| `src/flet_notifications/events.py` | NEW — `PendingNotification` |
| `src/flet_notifications/scheduling.py` | NEW — schedule argument parsing/serialization (pure, testable) |
| `src/flet_notifications/local_notifications.py` | EDIT — `schedule`, `periodically_show`, `cancel_pending`, `get_pending_notifications`, `can_schedule_exact_notifications`, `request_exact_alarm_permission` |
| `src/flet_notifications/__init__.py` | EDIT — exports |
| Dart `notifications_service.dart` | EDIT — `schedule`, `periodically_show`, `cancel_pending`, `get_pending`, exact-alarm probes |
| Dart `scheduling.dart` | NEW — pure time parsing: ISO string + tz name → TZDateTime; enum maps |
| Dart `extension.dart` | no change |
| `tests/test_scheduling.py` | NEW |
| Dart `test/scheduling_test.dart` | NEW |
| Dart `test/notifications_service_test.dart` | EDIT — fake gains schedule/periodic/pending methods |
| `examples/.../src/main.py` | EDIT — scheduling buttons |
| `README.md` | EDIT — scheduling usage + Android manifest requirements |

## Python API

```python
async def schedule(
    self,
    id: int,
    when: datetime | timedelta,
    title: str | None = None,
    body: str | None = None,
    payload: str = "",
    actions: list[NotificationAction] | None = None,
    repeat_interval: RepeatInterval | None = None,       # mutually exclusive with match_components
    match_components: DateTimeComponents | None = None,  # daily/weekly/monthly/yearly anchors
    schedule_mode: AndroidScheduleMode = AndroidScheduleMode.EXACT_ALLOW_WHILE_IDLE,
    time_zone: str | None = None,                        # IANA name; default device tz
) -> None

async def periodically_show(
    self,
    id: int,
    repeat_interval: RepeatInterval,
    title: str | None = None,
    body: str | None = None,
    payload: str = "",
    actions: list[NotificationAction] | None = None,
    schedule_mode: AndroidScheduleMode = AndroidScheduleMode.EXACT_ALLOW_WHILE_IDLE,
    repeat_duration_seconds: int | None = None,          # >= 60; custom interval
) -> None

async def cancel_pending(self) -> None                   # cancel all scheduled
async def get_pending_notifications(self) -> list[PendingNotification]
async def can_schedule_exact_notifications(self) -> bool
async def request_exact_alarm_permission(self) -> bool
```

Wire format for `schedule.when`:
- `datetime` → ISO 8601 string; aware datetimes carry an offset, naive ones are
  interpreted in `time_zone` (or the device timezone when `time_zone` is None)
- `timedelta` → `{"delay_seconds": n}`; Dart computes now + n in the target zone

Dart converts:
- naive + explicit tz → `tz.TZDateTime(tz.getLocation(tzName), y,m,d,h,mi,s)`
- naive, no tz → `tz.TZDateTime.from(parsedUtc, tz.local)` after shifting the
  wall-clock components into the local zone
- aware → keep the instant; use `tz.getLocation(tzName)` from the offset when
  available, else UTC
- timedelta → `tz.TZDateTime.now(location).add(duration)`

Repeat semantics preserved across DST: recurring schedules keep wall-clock
time (iOS calendar triggers do this natively; Android recomputes the alarm).

## Platform notes (documented in README)

- Android requires, in the app's `pyproject.toml`:
  `RECEIVE_BOOT_COMPLETED` (boot restore), `SCHEDULE_EXACT_ALARM` (exact modes),
  and the `ScheduledNotificationReceiver` / `ScheduledNotificationBootReceiver`
  manifest entries — copy-paste blocks in the README; automated patcher in Phase 4.
- Linux/Web: `zonedSchedule`/`periodicallyShow` throw `UnsupportedError` in the
  plugin → mapped to `error:unsupported_platform:...` by the service (Phase 4
  completes the full error taxonomy; Phase 2 returns the error string for
  these paths).
- Windows: one-shot schedule only (repeat components ignored by the platform).

## Tests

Python:
- enum wire values (all three enums)
- `schedule` with aware datetime / naive datetime + tz / timedelta → wire dicts
- mutually exclusive `repeat_interval` vs `match_components` → ValueError
- `periodically_show` default and custom-duration args
- `PendingNotification` from Dart-shaped dict
- probes return bool via "true"/"false"

Dart:
- `scheduling_test.dart`: naive ISO + tz name → correct TZDateTime wall clock;
  aware ISO → instant preserved; timedelta payload → future TZDateTime;
  enum name maps (schedule mode / match components / repeat interval)
- service tests: fake platform records `zonedSchedule`/`periodicallyShow`
  args; `get_pending` JSON shape; `cancel_pending` routing; unsupported
  platform error string

## Definition of done

ruff + pytest green; dart analyze + flutter test green on CI; example app
exercises one-shot + recurring + pending queries; README documents the
Android manifest requirements per feature.
