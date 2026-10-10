import 'package:flet/flet.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart'
    as fln;
import 'package:flutter_test/flutter_test.dart';
import 'package:flet_notifications/src/notifications_service.dart';

/// Fake Android platform implementation recording what the service sends.
class _FakeAndroidPlugin extends fln.AndroidFlutterLocalNotificationsPlugin {
  final List<Map<String, Object?>> shown = [];
  final List<int> cancelled = [];
  int cancelAllCalls = 0;
  int permissionRequests = 0;
  bool permissionResult = true;

  @override
  Future<bool> initialize({
    required fln.AndroidInitializationSettings settings,
    fln.DidReceiveNotificationResponseCallback? onDidReceiveNotificationResponse,
    fln.DidReceiveBackgroundNotificationResponseCallback?
    onDidReceiveBackgroundNotificationResponse,
  }) async {
    return true;
  }

  @override
  Future<void> show({
    required int id,
    String? title,
    String? body,
    fln.AndroidNotificationDetails? notificationDetails,
    String? payload,
  }) async {
    shown.add({
      "id": id,
      "title": title,
      "body": body,
      "payload": payload,
      "details": notificationDetails,
    });
  }

  @override
  Future<void> cancel({required int id, String? tag}) async {
    cancelled.add(id);
  }

  @override
  Future<void> cancelAll() async {
    cancelAllCalls++;
  }

  @override
  Future<bool?> requestNotificationsPermission() async {
    permissionRequests++;
    return permissionResult;
  }
}

LocalNotificationsService _makeService({Map<String, dynamic>? properties}) {
  final backend = FletBackend(
    pageUri: Uri.parse("uri"),
    assetsDir: "",
    extensions: [],
    multiView: false,
  );
  final control = Control(
    id: 1,
    type: "LocalNotifications",
    properties: properties ?? const {},
    backend: backend,
  );
  return LocalNotificationsService(control: control);
}

void main() {
  late _FakeAndroidPlugin plugin;

  setUp(() {
    plugin = _FakeAndroidPlugin();
    fln.FlutterLocalNotificationsPlatform.instance = plugin;
  });

  test("show forwards id/title/body/payload to the platform", () async {
    final service = _makeService();
    final result = await service.invokeMethod("show", {
      "id": 42,
      "title": "Title",
      "body": "Body",
      "payload": "deep.link",
      "actions": null,
    });
    expect(result, "ok");
    expect(plugin.shown, hasLength(1));
    final call = plugin.shown.single;
    expect(call["id"], 42);
    expect(call["title"], "Title");
    expect(call["body"], "Body");
    expect(call["payload"], "deep.link");
    final details = call["details"] as fln.AndroidNotificationDetails?;
    expect(details, isNotNull);
    expect(details!.channelId, "flet_notifications");
    expect(details.channelName, "Notifications");
    expect(details.actions, isEmpty);
  });

  test("show maps actions onto AndroidNotificationAction", () async {
    final service = _makeService();
    final result = await service.invokeMethod("show", {
      "id": 1,
      "title": "t",
      "body": "b",
      "payload": "",
      "actions": [
        {
          "id": "open",
          "title": "Open",
          "destructive": false,
          "foreground": true,
          "cancel_notification": true,
          "input": null,
        },
        {
          "id": "reply",
          "title": "Reply",
          "destructive": false,
          "foreground": false,
          "cancel_notification": true,
          "input": {
            "label": "Say",
            "choices": <String>[],
            "allow_free_form_input": true,
            "allowed_mime_types": <String>[],
          },
        },
      ],
    });
    expect(result, "ok");
    final details =
        plugin.shown.single["details"] as fln.AndroidNotificationDetails;
    final actions = details.actions;
    expect(actions, hasLength(2));
    expect(actions[0].id, "open");
    expect(actions[0].title, "Open");
    expect(actions[0].showsUserInterface, isTrue);
    expect(actions[1].id, "reply");
    expect(actions[1].showsUserInterface, isFalse);
    expect(actions[1].allowGeneratedReplies, isTrue);
    expect(actions[1].inputs, hasLength(1));
    expect(actions[1].inputs.single.label, "Say");
  });

  test("show with invalid action returns an error string", () async {
    final service = _makeService();
    final result = await service.invokeMethod("show", {
      "id": 1,
      "title": "t",
      "body": "b",
      "payload": "",
      "actions": [
        {"title": "no id"},
      ],
    });
    expect(result, startsWith("error:invalid_action:"));
    expect(plugin.shown, isEmpty);
  });

  test("cancel and cancel_all route to the platform", () async {
    final service = _makeService();
    expect(await service.invokeMethod("cancel", {"id": 9}), "ok");
    expect(plugin.cancelled, [9]);
    expect(await service.invokeMethod("cancel_all", null), "ok");
    expect(plugin.cancelAllCalls, 1);
  });

  test("request_permissions uses the Android runtime permission", () async {
    final service = _makeService();
    expect(await service.invokeMethod("request_permissions", null), "true");
    expect(plugin.permissionRequests, 1);

    plugin.permissionResult = false;
    expect(await service.invokeMethod("request_permissions", null), "false");
  });

  test("unknown method throws", () {
    final service = _makeService();
    expect(
      () => service.invokeMethod("nope", null),
      throwsA(isA<Exception>()),
    );
  });
}
