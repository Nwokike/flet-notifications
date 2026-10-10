/// Pure parsers for notification actions.
///
/// Kept free of `flutter_local_notifications` model dependencies so they can
/// be unit-tested without a plugin platform. The service maps the parsed
/// results onto platform-specific action objects.
library;

class ParsedInput {
  const ParsedInput({
    this.label = "",
    this.choices = const [],
    this.allowFreeFormInput = true,
    this.allowedMimeTypes = const {},
  });

  final String label;
  final List<String> choices;
  final bool allowFreeFormInput;
  final Set<String> allowedMimeTypes;
}

class ParsedAction {
  const ParsedAction({
    required this.id,
    required this.title,
    this.destructive = false,
    this.foreground = true,
    this.cancelNotification = true,
    this.input,
  });

  final String id;
  final String title;
  final bool destructive;
  final bool foreground;
  final bool cancelNotification;
  final ParsedInput? input;
}

/// Parses the `actions` argument (a list of dicts sent from Python) into
/// [ParsedAction]s.
///
/// Throws [FormatException] with a human-readable message on bad input; the
/// service converts it into an `error:invalid_action:...` invoke result.
List<ParsedAction> parseActions(Object? raw) {
  if (raw == null) return const [];
  if (raw is! List) {
    throw const FormatException("actions must be a list");
  }
  return raw.map((entry) {
    if (entry is! Map) {
      throw const FormatException("each action must be a map");
    }
    final id = entry["id"];
    final title = entry["title"];
    if (id is! String || id.isEmpty) {
      throw const FormatException("action id must be a non-empty string");
    }
    if (title is! String || title.isEmpty) {
      throw const FormatException("action title must be a non-empty string");
    }
    return ParsedAction(
      id: id,
      title: title,
      destructive: _optionalBool(entry["destructive"]) ?? false,
      foreground: _optionalBool(entry["foreground"]) ?? true,
      cancelNotification: _optionalBool(entry["cancel_notification"]) ?? true,
      input: parseInput(entry["input"]),
    );
  }).toList();
}

/// Parses the optional inline-reply `input` of an action.
ParsedInput? parseInput(Object? raw) {
  if (raw == null) return null;
  if (raw is! Map) {
    throw const FormatException("input must be a map");
  }
  final choices = raw["choices"];
  final mimeTypes = raw["allowed_mime_types"];
  return ParsedInput(
    label: raw["label"] is String ? raw["label"] as String : "",
    choices: choices is List ? choices.cast<String>() : const [],
    allowFreeFormInput: _optionalBool(raw["allow_free_form_input"]) ?? true,
    allowedMimeTypes: mimeTypes is List ? mimeTypes.cast<String>().toSet() : const {},
      );
}

bool? _optionalBool(Object? value) {
  if (value == null) return null;
  if (value is bool) return value;
  throw const FormatException("expected a boolean");
}
