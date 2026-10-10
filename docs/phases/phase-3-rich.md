# Phase 3 — Rich Notifications

**Goal:** the full expressive surface: notification styles (big text,
big picture, inbox, messaging), complete action buttons with inline reply,
Android channel CRUD, progress bars with live updates, grouping, and the
foreground service.

## Verified API (FLN 22.3.1)

- Styles: `BigTextStyleInformation(bigText, contentTitle?, summaryText?)`,
  `BigPictureStyleInformation(bigPicture: AndroidBitmap<Object>, largeIcon?, contentTitle?, summaryText?)`,
  `InboxStyleInformation(lines, contentTitle?, summaryText?)`,
  `MessagingStyleInformation(person: Person, conversationTitle?, groupConversation?, messages: List<Message>)`
- `Person(name, key?, icon?, bot?, important?, uri?)`;
  `Message(text, timestamp: DateTime, person, dataMimeType?, dataUri?)`
- Bitmaps: `DrawableResourceAndroidBitmap(drawableResource)`,
  `FilePathAndroidBitmap(filePath)`, `ContentUriAndroidBitmap(contentUri)`,
  `ByteArrayAndroidBitmap(byteArray)`, `FlutterBitmapAssetAndroidBitmap(assetPath)`
- Details additions: `groupKey`, `setAsGroupSummary`,
  `groupAlertBehavior(GroupAlertBehavior.all/summary/children)`,
  `showProgress/maxProgress/progress/indeterminate`, `color`, `subText`,
  `visibility`, `category`, `timeoutAfter`, `onlyAlertOnce`
- Channels: `AndroidNotificationChannel(id, name, description?, groupId?, importance, bypassDnd, playSound, sound?, enableVibration, vibrationPattern?, showBadge, enableLights, ledColor?, audioAttributesUsage?)`;
  CRUD: `createNotificationChannel`, `deleteNotificationChannel`, `getNotificationChannels`
- Importance: `unspecified/min/none/low/defaultImportance/high/max`
- `startForegroundService({required int id (!=0), title?, body?, notificationDetails?, payload?, startType?, foregroundServiceTypes?})`, `stopForegroundService()`
- Progress "live update" = call `show` again with the same id.

## Files

| File | Action |
|---|---|
| `src/flet_notifications/styles.py` | NEW — the four style dataclasses + `Person`, `Message`, `AndroidIcon` |
| `src/flet_notifications/types.py` | EDIT — add `Importance`, `GroupAlertBehavior` |
| `src/flet_notifications/channels.py` | NEW — `NotificationChannel` |
| `src/flet_notifications/local_notifications.py` | EDIT — `show`/`schedule`/`periodically_show` gain `style`, progress and grouping kwargs; channel CRUD; foreground service |
| `src/flet_notifications/scheduling.py` | EDIT — forward style/progress/grouping through `build_schedule_args` |
| Dart `parsers.dart` | EDIT — style/person/message/bitmap parsing |
| Dart `scheduling.dart` | no change |
| Dart `notifications_service.dart` | EDIT — style→`styleInformation`, progress/grouping fields, channel CRUD, FGS |
| `tests/test_styles.py`, `tests/test_channels.py` | NEW |
| Dart `test/parsers_test.dart` | EDIT — style/person/channel parsing |
| Dart `test/notifications_service_test.dart` | EDIT — channel/FGS routing |
| `examples/.../src/main.py` | EDIT — style/progress/channel buttons |
| `README.md` | EDIT — styles/channels/progress/FGS docs + FGS manifest note |

## Python API additions

```python
# styles (mutually compatible per call)
await notifications.show(
    id=1, title="t", body="b",
    style=BigTextStyle(big_text="..."),
    style=InboxStyle(lines=["a", "b"]),
    style=BigPictureStyle(image=AndroidIcon(file_path="/tmp/x.png")),
    style=MessagingStyle(person=Person(name="Ada"), messages=[Message(...)]),
    # progress
    show_progress=True, max_progress=100, progress=40,
    # grouping
    group_key="updates", set_as_group_summary=False,
    group_alert_behavior=GroupAlertBehavior.ALL,
)

# channels
await notifications.create_notification_channel(NotificationChannel(id="alerts", name="Alerts", importance=Importance.HIGH))
await notifications.delete_notification_channel("alerts")
await notifications.get_notification_channels() -> list[NotificationChannel]

# foreground service (Android; needs manifest entries — see README)
await notifications.start_foreground_service(id=1, title="Syncing", body="Working…")
await notifications.stop_foreground_service()
```

`show`/`schedule`/`periodically_show` all accept the same `style=`,
`show_progress=`, `max_progress=`, `progress=`, `indeterminate=`,
`group_key=`, `set_as_group_summary=`, `group_alert_behavior=` kwargs
(serialized into the per-platform details).

## Error taxonomy additions

`invalid_style` (bad style/bitmap — exactly-one source, empty lines),
`invalid_channel` (channel id/name empty, led color format),
`channel_failed`, `foreground_service_failed` (id == 0, no Android platform).

## Tests

Python: style `to_dict` shapes (all four), `AndroidIcon` exactly-one
validation, `Message` requires person+text, channel defaults + importance
enum values, show() forwards style/progress/grouping into the wire payload,
schedule forwards the same, FGS id!=0 guard, channel method routing.

Dart: parser tests (styles → value objects, bitmap variants, person/message),
service routing for channel CRUD + FGS + progress/grouping fields on details.

## Definition of done

ruff + pytest green; dart analyze + flutter test green; example app exercises
one of each style, a channel, a progress update and the foreground service;
README documents the FGS manifest requirements.
