/// The `LocalNotifications` Flet service: a 1:1 bridge from the Python
/// control to `flutter_local_notifications`.
library;

import 'dart:async';
import 'dart:convert';
import 'dart:typed_data';
import 'dart:ui' show Color;

import 'package:flet/flet.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart'
    as fln;
import 'package:flutter_timezone/flutter_timezone.dart';
import 'package:shared_preferences/shared_preferences.dart';
// Mirrors the plugin's own example: the database lives in the data library
// since timezone 0.10; both libraries share the `tz` prefix.
import 'package:timezone/data/latest_all.dart' as tz;
import 'package:timezone/timezone.dart' as tz;

import 'background_handler.dart';
import 'parsers.dart';
import 'scheduling.dart';

class LocalNotificationsService extends FletService {
  LocalNotificationsService({required super.control});

  static const String _channelId = "flet_notifications";
  static const String _channelName = "Notifications";
  static const String _darwinCategoryPrefix = "flet_notifications_actions_";
  static const String _defaultWindowsGuid =
      "9F4B0E2A-1C3D-4E5F-8A9B-0C1D2E3F4A5B";

  fln.FlutterLocalNotificationsPlugin? _plugin;
  bool _initialized = false;
  bool _replaying = false;
  Future<void>? _initFuture;

  @override
  void init() {
    super.init();
    control.addInvokeMethodListener(invokeMethod);
    unawaited(_ensureInitialized());
  }

  @override
  void dispose() {
    control.removeInvokeMethodListener(invokeMethod);
    super.dispose();
  }

  // ── Initialization ──────────────────────────────────────────────────

  /// Idempotent initialization. Concurrent callers await the same future, so
  /// invokes issued before initialization completes wait for it instead of
  /// silently no-oping.
  Future<void> _ensureInitialized({bool force = false}) {
    if (force || _initFuture == null) {
      _initFuture = _doInitialize();
    }
    return _initFuture!;
  }

  Future<void> _doInitialize() async {
    try {
      // The timezone database is only needed for scheduling; if it fails to
      // load, notifications still show.
      try {
        tz.initializeTimeZones();
        final info = await FlutterTimezone.getLocalTimezone();
        tz.setLocalLocation(tz.getLocation(info.identifier));
      } catch (_) {
        // Device timezone lookup failed; scheduled times fall back to UTC.
      }

      _plugin ??= fln.FlutterLocalNotificationsPlugin();
      await _plugin!.initialize(
        settings: _buildInitializationSettings(),
        onDidReceiveNotificationResponse: _handleResponse,
        onDidReceiveBackgroundNotificationResponse:
            notificationTapBackground,
      );
      _initialized = true;
      await _replayQueuedTaps();
      await _replayLaunchDetails();
    } catch (_) {
      // Initialization failed (e.g. invalid platform settings). Allow a
      // retry on the next invoke and surface the failure to the caller.
      _initialized = false;
      _initFuture = null;
    }
  }

  fln.InitializationSettings _buildInitializationSettings({
    List<fln.DarwinNotificationCategory> darwinCategories =
        const <fln.DarwinNotificationCategory>[],
  }) {
    final defaultIcon =
        control.getString("default_icon") ?? "@mipmap/ic_launcher";
    final darwin = fln.DarwinInitializationSettings(
      requestAlertPermission: control.getBool(
        "request_alert_permission",
        true,
      )!,
      requestSoundPermission: control.getBool(
        "request_sound_permission",
        true,
      )!,
      requestBadgePermission: control.getBool(
        "request_badge_permission",
        true,
      )!,
      requestCriticalPermission: control.getBool(
        "request_critical_permission",
        false,
      )!,
      notificationCategories: darwinCategories,
    );
    return fln.InitializationSettings(
      android: fln.AndroidInitializationSettings(defaultIcon),
      iOS: darwin,
      macOS: darwin,
      linux: const fln.LinuxInitializationSettings(
        defaultActionName: "Open",
      ),
      windows: fln.WindowsInitializationSettings(
        appName: control.getString("app_name") ?? "Flet App",
        appUserModelId:
            control.getString("app_user_model_id") ?? "Flet.App.Notifications",
        guid: control.getString("windows_guid") ?? _defaultWindowsGuid,
      ),
      web: const fln.WebInitializationSettings(),
    );
  }

  // ── Tap replay (background taps + cold starts) ──────────────────────

  Future<void> _replayQueuedTaps() async {
    if (_replaying) return;
    _replaying = true;
    try {
      final prefs = await SharedPreferences.getInstance();
      for (final event in await drainTapQueue(prefs)) {
        _emit(event);
      }
    } catch (_) {
      // Best-effort: preferences unavailable must not break the service.
    } finally {
      _replaying = false;
    }
  }

  Future<void> _replayLaunchDetails() async {
    try {
      final details = await _plugin?.getNotificationAppLaunchDetails();
      if (details?.didNotificationLaunchApp != true ||
          details?.notificationResponse == null) {
        return;
      }
      final event = responseToEvent(details!.notificationResponse!);
      final prefs = await SharedPreferences.getInstance();
      if (await shouldEmitLaunch(prefs, event)) {
        _emit(event);
      }
    } catch (_) {
      // Best-effort: preferences unavailable must not break the service.
    }
  }

  void _handleResponse(fln.NotificationResponse response) {
    _emit(responseToEvent(response));
  }

  void _emit(Map<String, Object?> event) {
    final type = event["response_type"];
    final name = switch (type) {
      "action" => "action",
      "dismissed" => "dismissed",
      _ => "tap",
    };
    control.triggerEvent(name, event);
  }

  // ── Method routing ──────────────────────────────────────────────────

  /// Routes an invoke call from the Python control. Public so the invoke
  /// seam can be exercised in tests (Flet delivers invokes here via the
  /// listener registered in [init]).
  Future<dynamic> invokeMethod(String name, [dynamic args]) async {
    if (name != "initialize") {
      await _ensureInitialized();
      if (!_initialized) {
        return "error:init_failed:notification backend unavailable";
      }
    }
    try {
      return await _dispatch(name, args);
    } on UnimplementedError {
      // The plugin/platform cannot do this (e.g. scheduling on Linux/web).
      return "error:unsupported_platform:$name is not available on this "
          "platform";
    } on UnsupportedError {
      return "error:unsupported_platform:$name is not available on this "
          "platform";
    }
  }

  Future<dynamic> _dispatch(String name, dynamic args) async {
    switch (name) {
      case "initialize":
        await _ensureInitialized(force: true);
        return _initialized ? "ok" : "error:init_failed:initialize failed";

      case "show":
        return await _show(args);

      case "cancel":
        await _plugin?.cancel(id: (args as Map)["id"] as int);
        return "ok";

      case "cancel_all":
        await _plugin?.cancelAll();
        return "ok";

      case "schedule":
        return await _schedule(args);

      case "periodically_show":
        return await _periodicallyShow(args);

      case "cancel_pending":
        await _plugin?.cancelAllPendingNotifications();
        return "ok";

      case "get_pending":
        return await _getPending();

      case "create_notification_channel":
        return await _createChannel(args);

      case "delete_notification_channel":
        return await _deleteChannel(args);

      case "get_notification_channels":
        return await _getChannels();

      case "start_foreground_service":
        return await _startForegroundService(args);

      case "stop_foreground_service":
        return await _stopForegroundService();

      case "request_permissions":
        return (await _requestPermissions()) ? "true" : "false";

      case "can_schedule_exact_notifications":
        final android = _androidPlugin;
        if (android == null) return "true";
        return (await android.canScheduleExactNotifications() ?? false)
            ? "true"
            : "false";

      case "request_exact_alarm_permission":
        final android = _androidPlugin;
        if (android == null) return "false";
        return (await android.requestExactAlarmsPermission() ?? false)
            ? "true"
            : "false";

      case "are_notifications_enabled":
        return (await _areNotificationsEnabled()) ? "true" : "false";

      case "open_app_settings":
        await _plugin?.openAppNotificationSettings();
        return "ok";

      case "get_active":
        return await _getActive();

      case "get_launch_details":
        return await _getLaunchDetails();

      case "request_full_screen_intent":
        final android = _androidPlugin;
        return (await android?.requestFullScreenIntentPermission() ?? false)
            ? "true"
            : "false";

      case "has_notification_policy_access":
        return (await _hasNotificationPolicyAccess()) ? "true" : "false";

      case "request_notification_policy_access":
        final android = _androidPlugin;
        return (await android?.requestNotificationPolicyAccess() ?? false)
            ? "true"
            : "false";

      case "create_notification_channel_group":
        return await _createChannelGroup(args);

      case "delete_notification_channel_group":
        return await _deleteChannelGroup(args);

      default:
        throw Exception("Unknown LocalNotifications method: $name");
    }
  }

  Future<String> _show(dynamic args) async {
    try {
      final map = args as Map;
      final id = map["id"] as int;
      final title = map["title"] as String?;
      final body = map["body"] as String?;
      final payload = map["payload"] as String? ?? "";
      final actions = parseActions(map["actions"]);
      final styleError = _invalidStyleCode(map["style"]);
      if (styleError != null) return styleError;
      await _plugin!.show(
        id: id,
        title: title,
        body: body,
        payload: payload,
        notificationDetails: await _buildNotificationDetails(
          id: id,
          actions: actions,
          style: parseStyle(map["style"]),
          details: map,
        ),
      );
      return "ok";
    } on FormatException catch (e) {
      return "error:invalid_action:${e.message}";
    } catch (e) {
      return "error:show_failed:$e";
    }
  }

  Future<String> _schedule(dynamic args) async {
    final map = args as Map;
    final List<ParsedAction> actions;
    try {
      actions = parseActions(map["actions"]);
    } on FormatException catch (e) {
      return "error:invalid_action:${e.message}";
    }
    final styleError = _invalidStyleCode(map["style"]);
    if (styleError != null) return styleError;
    final tz.TZDateTime scheduledDate;
    try {
      scheduledDate = parseWhen(map, tz.local);
    } on FormatException catch (e) {
      return "error:invalid_schedule:${e.message}";
    }
    try {
      await _plugin!.zonedSchedule(
        id: map["id"] as int,
        title: map["title"] as String?,
        body: map["body"] as String?,
        scheduledDate: scheduledDate,
        notificationDetails: await _buildNotificationDetails(
          id: map["id"] as int,
          actions: actions,
          style: parseStyle(map["style"]),
          details: map,
        ),
        androidScheduleMode: parseScheduleMode(map["schedule_mode"] as String?),
        payload: map["payload"] as String? ?? "",
        matchDateTimeComponents: parseMatchComponents(
          map["match_components"] as String?,
        ),
      );
      return "ok";
    } catch (e) {
      return "error:schedule_failed:$e";
    }
  }

  Future<String> _periodicallyShow(dynamic args) async {
    try {
      final map = args as Map;
      final id = map["id"] as int;
      final actions = parseActions(map["actions"]);
      final styleError = _invalidStyleCode(map["style"]);
      if (styleError != null) return styleError;
      final notificationDetails = await _buildNotificationDetails(
        id: id,
        actions: actions,
        style: parseStyle(map["style"]),
        details: map,
      );
      final scheduleMode = parseScheduleMode(map["schedule_mode"] as String?);
      final title = map["title"] as String?;
      final body = map["body"] as String?;
      final payload = map["payload"] as String? ?? "";
      final durationSeconds = map["repeat_duration_seconds"] as int?;
      if (durationSeconds != null) {
        await _plugin!.periodicallyShowWithDuration(
          id: id,
          title: title,
          body: body,
          payload: payload,
          notificationDetails: notificationDetails,
          repeatDurationInterval: Duration(seconds: durationSeconds),
          androidScheduleMode: scheduleMode,
        );
        return "ok";
      }
      await _plugin!.periodicallyShow(
        id: id,
        title: title,
        body: body,
        payload: payload,
        notificationDetails: notificationDetails,
        repeatInterval: parseRepeatInterval(map["repeat_interval"] as String?),
        androidScheduleMode: scheduleMode,
      );
      return "ok";
    } on FormatException catch (e) {
      return "error:invalid_action:${e.message}";
    } catch (e) {
      return "error:schedule_failed:$e";
    }
  }

  Future<String> _getPending() async {
    try {
      final pending = await _plugin!.pendingNotificationRequests();
      return jsonEncode(
        pending
            .map(
              (p) => {
                "id": p.id,
                "title": p.title,
                "body": p.body,
                "payload": p.payload,
              },
            )
            .toList(),
      );
    } catch (e) {
      return "error:query_failed:$e";
    }
  }

  fln.AndroidFlutterLocalNotificationsPlugin? get _androidPlugin =>
      _plugin?.resolvePlatformSpecificImplementation<
        fln.AndroidFlutterLocalNotificationsPlugin
      >();

  // ── Notification details construction ───────────────────────────────

  Future<fln.NotificationDetails> _buildNotificationDetails({
    required int id,
    required List<ParsedAction> actions,
    ParsedStyle? style,
    Map? details,
  }) async {
    final androidActions =
        actions
            .map(
              (a) => fln.AndroidNotificationAction(
                a.id,
                a.title,
                showsUserInterface: a.foreground,
                cancelNotification: a.cancelNotification,
                allowGeneratedReplies: a.input != null,
                inputs:
                    a.input == null
                        ? const []
                        : [
                          fln.AndroidNotificationActionInput(
                            label: a.input!.label.isEmpty
                                ? null
                                : a.input!.label,
                            choices: a.input!.choices,
                            allowFreeFormInput: a.input!.allowFreeFormInput,
                            allowedMimeTypes: a.input!.allowedMimeTypes,
                          ),
                        ],
              ),
            )
            .toList();

    final darwinDetails = fln.DarwinNotificationDetails(
      categoryIdentifier: actions.isEmpty
          ? null
          : "$_darwinCategoryPrefix$id",
    );

    if (actions.isNotEmpty) {
      await _registerDarwinCategories(id, actions);
    }

    final windowsActions =
        actions
            .map(
              (a) => fln.WindowsAction(
                content: a.title,
                arguments: a.id,
                activationBehavior: fln.WindowsNotificationBehavior.dismiss,
              ),
            )
            .toList();

    // Rich details forwarded from the invoke payload (all optional).
    final d = details ?? const {};
    final channelId = d["channel_id"] as String?;
    final groupKey = d["group_key"] as String?;
    final groupAlert = _mapGroupAlertBehavior(
      d["group_alert_behavior"] as String?,
    );

    return fln.NotificationDetails(
      android: fln.AndroidNotificationDetails(
        channelId ?? _channelId,
        _channelName,
        actions: androidActions,
        styleInformation: _mapStyleInformation(style),
        groupKey: groupKey,
        setAsGroupSummary: optionalBool(d["set_as_group_summary"]) ?? false,
        groupAlertBehavior: groupAlert,
        showProgress: optionalBool(d["show_progress"]) ?? false,
        maxProgress: (d["max_progress"] as int?) ?? 0,
        progress: (d["progress"] as int?) ?? 0,
        indeterminate: optionalBool(d["indeterminate"]) ?? false,
      ),
      iOS: darwinDetails,
      macOS: darwinDetails,
      linux: const fln.LinuxNotificationDetails(
        defaultActionName: "Open",
      ),
      windows: fln.WindowsNotificationDetails(actions: windowsActions),
    );
  }

  /// Maps a parsed style onto the Android `styleInformation` object.
  ///
  /// Styles are an Android concept in the plugin; iOS/macOS render titles,
  /// attachments and interruptions through their own details fields.
  fln.StyleInformation? _mapStyleInformation(ParsedStyle? style) {
    if (style == null) return null;
    switch (style.type) {
      case "big_text":
        return fln.BigTextStyleInformation(
          style.bigText!,
          contentTitle: style.contentTitle,
          summaryText: style.summaryText,
        );
      case "big_picture":
        return fln.BigPictureStyleInformation(
          _mapBitmap(style.image!)!,
          largeIcon: _mapBitmap(style.largeIcon),
          contentTitle: style.contentTitle,
          summaryText: style.summaryText,
        );
      case "inbox":
        return fln.InboxStyleInformation(
          style.lines,
          contentTitle: style.contentTitle,
          summaryText: style.summaryText,
        );
      case "messaging":
        return fln.MessagingStyleInformation(
          _mapPerson(style.person!),
          conversationTitle: style.conversationTitle,
          groupConversation: style.groupConversation,
          messages: style.messages
              .map(
                (m) => fln.Message(
                  m.text,
                  DateTime.parse(m.timestampIso),
                  _mapPerson(m.person),
                ),
              )
              .toList(),
        );
      default:
        throw FormatException("unknown style type: ${style.type}");
    }
  }

  /// Maps an icon onto a style image. FLN's big-picture bitmaps support
  /// drawable, file-path and byte sources only.
  fln.AndroidBitmap<Object>? _mapBitmap(ParsedIcon? icon) {
    if (icon == null) return null;
    final drawable = icon.drawableResource;
    if (drawable != null) return fln.DrawableResourceAndroidBitmap(drawable);
    final path = icon.filePath;
    if (path != null) return fln.FilePathAndroidBitmap(path);
    final data = icon.data;
    if (data != null) return fln.ByteArrayAndroidBitmap(Uint8List.fromList(data));
    throw const FormatException(
      "big-picture images support drawable, file path and byte sources",
    );
  }

  /// Maps an icon onto an Android notification icon (all five sources).
  fln.AndroidIcon<Object>? _mapIcon(ParsedIcon? icon) {
    if (icon == null) return null;
    final drawable = icon.drawableResource;
    if (drawable != null) return fln.DrawableResourceAndroidIcon(drawable);
    final path = icon.filePath;
    if (path != null) return fln.BitmapFilePathAndroidIcon(path);
    final uri = icon.contentUri;
    if (uri != null) return fln.ContentUriAndroidIcon(uri);
    final asset = icon.flutterAsset;
    if (asset != null) return fln.FlutterBitmapAssetAndroidIcon(asset);
    final data = icon.data;
    if (data != null) return fln.ByteArrayAndroidIcon(Uint8List.fromList(data));
    throw const FormatException("icon has no source");
  }

  fln.Person _mapPerson(ParsedPerson person) {
    return fln.Person(
      name: person.name,
      key: person.key,
      bot: person.bot,
      important: person.important,
      uri: person.uri,
      icon: _mapIcon(person.icon),
    );
  }

  fln.GroupAlertBehavior _mapGroupAlertBehavior(String? value) {
    switch (value) {
      case "summary":
        return fln.GroupAlertBehavior.summary;
      case "children":
        return fln.GroupAlertBehavior.children;
      default:
        return fln.GroupAlertBehavior.all;
    }
  }

  /// Parses the optional style of a show/schedule payload, mapping format
  /// failures to the `invalid_style` error code.
  String? _invalidStyleCode(Object? raw) {
    try {
      parseStyle(raw);
    } on FormatException catch (e) {
      return "error:invalid_style:${e.message}";
    }
    return null;
  }

  /// Registers the action buttons as a Darwin notification category.
  ///
  /// iOS/macOS require categories to be registered through
  /// `InitializationSettings.notificationCategories` before a notification
  /// can reference them, and `setNotificationCategories` replaces the whole
  /// set — so each notification with actions gets its own category,
  /// registered by re-initializing the plugin. iOS `initialize` is
  /// re-entrant (it re-applies permissions and categories), which makes this
  /// safe. Without this, action buttons silently never appear on iOS.
  Future<void> _registerDarwinCategories(
    int id,
    List<ParsedAction> actions,
  ) async {
    final categoryActions =
        actions.map((a) {
          final options = <fln.DarwinNotificationActionOption>{
            if (a.destructive) fln.DarwinNotificationActionOption.destructive,
            if (a.foreground) fln.DarwinNotificationActionOption.foreground,
          };
          final input = a.input;
          if (input == null) {
            return fln.DarwinNotificationAction.plain(
              a.id,
              a.title,
              options: options,
            );
          }
          return fln.DarwinNotificationAction.text(
            a.id,
            a.title,
            buttonTitle: input.label.isEmpty ? a.title : input.label,
            placeholder: input.label.isEmpty ? null : input.label,
            options: options,
          );
        }).toList();

    await _plugin?.initialize(
      settings: _buildInitializationSettings(
        darwinCategories: [
          fln.DarwinNotificationCategory(
            "$_darwinCategoryPrefix$id",
            actions: categoryActions,
          ),
        ],
      ),
      onDidReceiveNotificationResponse: _handleResponse,
      onDidReceiveBackgroundNotificationResponse: notificationTapBackground,
    );
  }

  // ── Permissions ─────────────────────────────────────────────────────

  Future<bool> _requestPermissions() async {
    final android = _androidPlugin;
    if (android != null) {
      return await android.requestNotificationsPermission() ?? false;
    }

    final ios = _plugin?.resolvePlatformSpecificImplementation<
      fln.IOSFlutterLocalNotificationsPlugin
    >();
    if (ios != null) {
      return await ios.requestPermissions(
            sound: control.getBool("request_sound_permission", true)!,
            alert: control.getBool("request_alert_permission", true)!,
            badge: control.getBool("request_badge_permission", true)!,
            critical: control.getBool("request_critical_permission", false)!,
          ) ??
          false;
    }

    final macos = _plugin?.resolvePlatformSpecificImplementation<
      fln.MacOSFlutterLocalNotificationsPlugin
    >();
    if (macos != null) {
      return await macos.requestPermissions(
            sound: control.getBool("request_sound_permission", true)!,
            alert: control.getBool("request_alert_permission", true)!,
            badge: control.getBool("request_badge_permission", true)!,
            critical: control.getBool("request_critical_permission", false)!,
          ) ??
          false;
    }

    // Windows and Linux have no runtime notification permission; the web
    // plugin requests the browser permission on `show`.
    return true;
  }

  // ── Channels (Android 8.0+) ──────────────────────────────────────────

  Future<String> _createChannel(dynamic args) async {
    final android = _androidPlugin;
    if (android == null) {
      return "error:unsupported_platform:channels are Android-only";
    }
    try {
      final map = args as Map;
      final id = map["id"] as String;
      final name = map["name"] as String;
      if (id.isEmpty || name.isEmpty) {
        return "error:invalid_channel:id and name are required";
      }
      final ledColor = map["led_color"] as String?;
      await android.createNotificationChannel(
        fln.AndroidNotificationChannel(
          id,
          name,
          description: map["description"] as String?,
          importance: _mapImportance(map["importance"] as String?),
          bypassDnd: optionalBool(map["bypass_dnd"]) ?? false,
          playSound: optionalBool(map["play_sound"]) ?? true,
          sound:
              map["sound"] == null
                  ? null
                  : fln.RawResourceAndroidNotificationSound(
                    map["sound"] as String,
                  ),
          enableVibration: optionalBool(map["enable_vibration"]) ?? true,
          vibrationPattern: _toInt64List(map["vibration_pattern"]),
          showBadge: optionalBool(map["show_badge"]) ?? true,
          enableLights: optionalBool(map["enable_lights"]) ?? false,
          ledColor: ledColor == null ? null : _parseHexColor(ledColor),
        ),
      );
      return "ok";
    } catch (e) {
      return "error:channel_failed:$e";
    }
  }

  Future<String> _deleteChannel(dynamic args) async {
    final android = _androidPlugin;
    if (android == null) {
      return "error:unsupported_platform:channels are Android-only";
    }
    final map = args as Map;
    final channelId = map["channel_id"] as String;
    await android.deleteNotificationChannel(channelId: channelId);
    return "ok";
  }

  Future<String> _getChannels() async {
    final android = _androidPlugin;
    if (android == null) return "[]";
    try {
      final channels = await android.getNotificationChannels() ?? const [];
      return jsonEncode(
        channels
            .map(
              (c) => {
                "id": c.id,
                "name": c.name,
                "description": c.description ?? "",
                "importance": c.importance.name,
                "bypass_dnd": c.bypassDnd,
                "play_sound": c.playSound,
                "enable_vibration": c.enableVibration,
                "vibration_pattern": c.vibrationPattern?.toList(),
                "show_badge": c.showBadge,
              },
            )
            .toList(),
      );
    } catch (e) {
      return "error:channel_failed:$e";
    }
  }

  fln.Importance _mapImportance(String? value) {
    switch (value) {
      case "unspecified":
        return fln.Importance.unspecified;
      case "min":
        return fln.Importance.min;
      case "none":
        return fln.Importance.none;
      case "low":
        return fln.Importance.low;
      case "high":
        return fln.Importance.high;
      case "max":
        return fln.Importance.max;
      default:
        return fln.Importance.defaultImportance;
    }
  }

  Int64List? _toInt64List(Object? value) {
    if (value is! List) return null;
    return Int64List.fromList(value.map((e) => e as int).toList());
  }

  Color? _parseHexColor(String hex) {
    var v = hex.trim();
    if (!v.startsWith("#")) return null;
    v = v.substring(1);
    return Color(int.parse(v, radix: 16) | 0xFF000000);
  }

  // ── Foreground service (Android) ─────────────────────────────────────

  Future<String> _startForegroundService(dynamic args) async {
    final android = _androidPlugin;
    if (android == null) {
      return "error:unsupported_platform:foreground service is Android-only";
    }
    try {
      final map = args as Map;
      final id = map["id"] as int;
      if (id == 0) {
        return "error:invalid_service_id:foreground service id must be non-zero";
      }
      final actions = parseActions(map["actions"]);
      final styleError = _invalidStyleCode(map["style"]);
      if (styleError != null) return styleError;
      await android.startForegroundService(
        id: id,
        title: map["title"] as String?,
        body: map["body"] as String?,
        payload: map["payload"] as String? ?? "",
        notificationDetails: (await _buildNotificationDetails(
          id: id,
          actions: actions,
          style: parseStyle(map["style"]),
          details: map,
        )).android,
      );
      return "ok";
    } catch (e) {
      return "error:foreground_service_failed:$e";
    }
  }

  Future<String> _stopForegroundService() async {
    final android = _androidPlugin;
    if (android == null) {
      return "error:unsupported_platform:foreground service is Android-only";
    }
    await android.stopForegroundService();
    return "ok";
  }

  // ── Probes & OS integration ───────────────────────────────

  Future<bool> _areNotificationsEnabled() async {
    final android = _androidPlugin;
    if (android != null) {
      return await android.areNotificationsEnabled() ?? false;
    }
    final ios = _plugin?.resolvePlatformSpecificImplementation<
        fln.IOSFlutterLocalNotificationsPlugin>();
    if (ios != null) {
      return (await ios.checkPermissions())?.isEnabled ?? false;
    }
    final macos = _plugin?.resolvePlatformSpecificImplementation<
        fln.MacOSFlutterLocalNotificationsPlugin>();
    if (macos != null) {
      return (await macos.checkPermissions())?.isEnabled ?? false;
    }
    // Windows/Linux/web have no queryable gate.
    return true;
  }

  Future<bool> _hasNotificationPolicyAccess() async {
    final android = _androidPlugin;
    return await android?.hasNotificationPolicyAccess() ?? false;
  }

  Future<String> _getActive() async {
    try {
      final active = await _plugin?.getActiveNotifications() ?? const [];
      return jsonEncode(
        active
            .map(
              (a) => {
                "id": a.id,
                "channel_id": a.channelId,
                "group_key": a.groupKey,
                "tag": a.tag,
                "title": a.title,
                "body": a.body,
                "payload": a.payload,
                "big_text": a.bigText,
              },
            )
            .toList(),
      );
    } catch (e) {
      return "error:query_failed:$e";
    }
  }

  Future<String> _getLaunchDetails() async {
    try {
      final details = await _plugin?.getNotificationAppLaunchDetails();
      if (details == null || details.didNotificationLaunchApp != true) {
        return jsonEncode({"did_notification_launch_app": false});
      }
      final response = details.notificationResponse;
      return jsonEncode({
        "did_notification_launch_app": true,
        "notification":
            response == null ? null : responseToEvent(response),
      });
    } catch (e) {
      return "error:query_failed:$e";
    }
  }

  Future<String> _createChannelGroup(dynamic args) async {
    final android = _androidPlugin;
    if (android == null) {
      return "error:unsupported_platform:channel groups are Android-only";
    }
    try {
      final map = args as Map;
      await android.createNotificationChannelGroup(
        fln.AndroidNotificationChannelGroup(
          map["group_id"] as String,
          map["name"] as String,
        ),
      );
      return "ok";
    } catch (e) {
      return "error:channel_failed:$e";
    }
  }

  Future<String> _deleteChannelGroup(dynamic args) async {
    final android = _androidPlugin;
    if (android == null) {
      return "error:unsupported_platform:channel groups are Android-only";
    }
    final map = args as Map;
    await android.deleteNotificationChannelGroup(
      groupId: map["group_id"] as String,
    );
    return "ok";
  }
}
