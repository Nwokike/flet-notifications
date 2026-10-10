# Phase 1 — Core

**Goal:** end-to-end `show` / `cancel` / permissions / tap+action+dismissed events,
on Android + iOS + macOS + Windows + Linux + Web (basic show), with the
background-tap queue, example app buttons, tests, and compat CI.

## Verified ground truth (done in Phase 0)

- FLN 22.3.1 signatures: `show({required int id, String? title, String? body,
  NotificationDetails? notificationDetails, String? payload})`,
  `initialize(settings, onDidReceiveNotificationResponse, onDidReceiveBackgroundNotificationResponse)`,
  `cancel({required int id, String? tag})`, `requestPermissions`, `checkPermissions`.
  Reference clone: `~/fln-reference` (tag `flutter_local_notifications-v22.3.1`).
- FLN plugin AndroidManifest ships only `VIBRATE` + `POST_NOTIFICATIONS`; the
  three receivers (`ScheduledNotificationReceiver`, `ScheduledNotificationBootReceiver`,
  `ActionBroadcastReceiver`) are **app-manifest** entries → documented in README +
  patched in Phase 4.
- FletService Dart contract (from flet-yandex-ads): `init()` calls `super.init()`
  then `control.addInvokeMethodListener(_invokeMethod)`; methods via
  `Future<dynamic> _invokeMethod(String name, dynamic args)` switch; events via
  `control.triggerEvent(name, payloadMap)`; props via `control.getBool/getString`
  with defaults; `dispose()` removes the listener.
- Versions: `flutter_local_notifications: ^22.3.1`, `timezone: ^0.11.0`,
  `flutter_timezone: ^5.1.1`, `shared_preferences: ^2.5.6`, `flet: ^1.0.0`.

## Files

| File | Action |
|---|---|
| `src/flet_notifications/base.py` | NEW — `NotificationError`, `NotificationEvent`, `ResponseType` helpers, wire helpers |
| `src/flet_notifications/actions.py` | NEW — `NotificationAction`, `NotificationActionInput` |
| `src/flet_notifications/local_notifications.py` | NEW — `LocalNotifications(ft.Service)` |
| `src/flet_notifications/__init__.py` | EDIT — exports + `__all__` |
| `src/flutter/flet_notifications/lib/src/extension.dart` | EDIT — `createService` route |
| `src/flutter/flet_notifications/lib/src/parsers.dart` | NEW — pure JSON→model parsers (unit-testable, no FLN model deps) |
| `src/flutter/flet_notifications/lib/src/notifications_service.dart` | NEW — `LocalNotificationsService` |
| `src/flutter/flet_notifications/lib/src/background_handler.dart` | NEW — top-level `@pragma('vm:entry-point')` tap persistence + queue replay |
| `tests/test_service.py` | NEW |
| `tests/test_events.py` | NEW |
| `tests/test_actions.py` | NEW |
| `test/parsers_test.dart` (in Dart pkg) | NEW |
| `test/notifications_service_test.dart` (in Dart pkg) | NEW |
| `examples/.../src/main.py` | EDIT — buttons + event log |
| `.github/workflows/compat.yml` | NEW |
| `README.md` | EDIT — usage with events |

## Python API surface (final for Phase 1)

```python
class ResponseType(str, Enum):
    TAP = "tap"
    ACTION = "action"
    DISMISSED = "dismissed"

@dataclass(kw_only=True)
class NotificationActionInput:
    label: str = ""
    choices: list[str] = field(default_factory=list)
    allow_free_form_input: bool = True
    allowed_mime_types: list[str] = field(default_factory=list)

@dataclass(kw_only=True)
class NotificationAction:
    id: str
    title: str
    destructive: bool = False          # iOS/macOS
    foreground: bool = True            # bring app to foreground on tap
    cancel_notification: bool = True   # Android
    input: Optional[NotificationActionInput] = None

@dataclass
class NotificationEvent(ft.Event[ft.EventControlType]):
    id: int = 0
    action_id: str = ""                # "" for plain tap; "dismiss" for dismissed
    payload: str = ""
    input: str = ""                    # inline-reply text (Windows/Darwin)
    response_type: str = "tap"         # ResponseType value

class NotificationError(Exception):
    def __init__(self, code: str, message: str = ""): ...
    # code ∈ unsupported_platform | init_failed | show_failed | permission_failed | unknown_method

@ft.control("LocalNotifications")
class LocalNotifications(ft.Service):
    # init settings (props → Dart init)
    default_icon: Optional[str] = None            # Android drawable name
    request_alert_permission: bool = True         # Darwin
    request_sound_permission: bool = True
    request_badge_permission: bool = True
    request_critical_permission: bool = False
    app_name: Optional[str] = None                # Windows
    app_user_model_id: Optional[str] = None       # Windows
    windows_guid: Optional[str] = None            # Windows

    # events
    on_tap: Optional[ft.EventHandler[NotificationEvent["LocalNotifications"]]] = None
    on_action: Optional[ft.EventHandler[NotificationEvent["LocalNotifications"]]] = None
    on_dismissed: Optional[ft.EventHandler[NotificationEvent["LocalNotifications"]]] = None

    async def initialize(self) -> None
    async def show(self, id: int, title: Optional[str] = None, body: Optional[str] = None,
                   payload: str = "", actions: Optional[list[NotificationAction]] = None) -> None
    async def cancel(self, id: int) -> None
    async def cancel_all(self) -> None
    async def request_permissions(self) -> bool    # invoke timeout=300 (dialogs)
```

Wire conventions:
- Errors: Dart methods return `"error:<code>:<message>"` strings; the Python
  service checks and raises `NotificationError`. `"ok"` / `"true"` / `"false"`
  return values map directly.
- Config dataclasses are `@dataclass(kw_only=True)` with `to_dict()`; never
  sent as Python objects.

## Dart design (Phase 1)

`LocalNotificationsService`:
- `init()` → `super.init()`, register listener, `_ensureInitialized()`.
- `_ensureInitialized()`: `tz.initializeTimeZones()`, `setLocalLocation` from
  `flutter_timezone`; build `InitializationSettings(android/iOS/macOS/linux/windows/web)`
  from control props; `plugin.initialize(onDidReceiveNotificationResponse: _onResponse,
  onDidReceiveBackgroundNotificationResponse: notificationTapBackground)`;
  then replay stored queue + cold-start launch details.
- `_onResponse(response)` → emit `control.triggerEvent(evtName, json)` where
  evtName = `tap` | `action` | `dismissed` per `response.notificationResponseType`.
  Dismissal reporting is opt-in on Android/Darwin (`dismissIsolate` /
  category `customDismissAction`) and is enabled by default where supported;
  Linux dismiss-reason-2 and Windows user-cancelled map to `dismissed` natively.

- `_invokeMethod` cases: `initialize` (re-init if needed), `show`, `cancel`,
  `cancel_all`, `request_permissions` → bool; unknown → throw.
- `parsers.dart` (pure): `parseActions(List?)`, `parseInput(Map?)` → plain
  structs `ParsedAction`, `ParsedInput`; validated (id/title non-empty; input
  requires allow_free_form_input or choices).
- `background_handler.dart`: top-level `notificationTapBackground` persists
  `{"id","action_id","payload","input","type"}` JSON to shared_preferences under
  `flet_notifications_queue_<µs>_<nonce>`; replay reads keys sorted, emits each
  via the active service, deletes; cold-start launch-details persisted under
  `flet_notifications_last_launch` for dedupe.

## Example app (Phase 1)

`examples/flet_notifications_example/src/main.py`: buttons **Show**, **Show with
action buttons**, **Request permissions**, **Cancel**, **Cancel all** + scrolling
event log fed by `on_tap` / `on_action` / `on_dismissed`. Guard: if the app runs
under a prebuilt client without the extension (plain `flet run` on desktop),
catch "Unknown control" and show an in-app notice (verified behavior in Phase 0
checks — desktop `flet run` logs the unknown service but keeps running).

## Tests

Python (`uv run pytest`):
- `test_service.py`: control type string is `"LocalNotifications"`; `before_update`
  does not raise on any platform; `show/cancel/request_permissions` invoke JSON
  with expected keys (monkeypatched `_invoke_method`); timeout for
  `request_permissions`; `NotificationError` construction/repr; `__all__` exports.
- `test_events.py`: `NotificationEvent` from_dict hydration from a Dart-shaped
  payload dict; default field values.
- `test_actions.py`: `NotificationAction.to_dict()` wire values; input
  serialization; defaults.

Dart (`flutter test` in the extension package):
- `parsers_test.dart`: action parse defaults, input validation errors, action
  with input → reply action shape.
- `notifications_service_test.dart`: fake `FlutterLocalNotificationsPlatform`
  (set `FlutterLocalNotificationsPlatform.instance`): show passes through to
  platform; `show` error path returns `error:show_failed:...`; cancel/cancel_all
  routing; background queue persists keys and replays in order with ack-delete;
  cold-start dedupe.

## CI (`.github/workflows/compat.yml`)

- Job `python`: matrix `flet: ["1.0.0", "1.0.3", "latest"]` × `python: ["3.12",
  "3.13"]` (drop to a single-python matrix if macOS-free simplicity is preferred
  — ubuntu only), ruff format check + pytest on each.
- Job `dart`: subosito/flutter-action pinned to **3.44.8** (Flet's embedded
  version), `flutter pub get` in `src/flutter/flet_notifications`, `dart analyze`,
  `flutter test`.
- Trigger: push + pull_request. No artifacts.

## Definition of done

- ruff check + format + pytest green locally; `dart analyze` + `flutter test`
  green locally (no `flet build` — owner rule).
- Example app updated and `flet run`-safe on desktop (services are headless; the
  prebuilt desktop client tolerates the unknown service — confirm in Phase 0
  verification before wiring UI).
- compat.yml pushed; CI green on GitHub.
- Device verification (Android) happens at tag time via CI-built APKs — not in
  this phase.
