import 'package:flet_notifications/src/parsers.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group("parseActions", () {
    test("null yields an empty list", () {
      expect(parseActions(null), isEmpty);
    });

    test("parses defaults", () {
      final actions = parseActions([
        {"id": "open", "title": "Open"},
      ]);
      expect(actions, hasLength(1));
      expect(actions.single.id, "open");
      expect(actions.single.title, "Open");
      expect(actions.single.destructive, isFalse);
      expect(actions.single.foreground, isTrue);
      expect(actions.single.cancelNotification, isTrue);
      expect(actions.single.input, isNull);
    });

    test("parses flags and nested input", () {
      final actions = parseActions([
        {
          "id": "reply",
          "title": "Reply",
          "destructive": true,
          "foreground": false,
          "cancel_notification": false,
          "input": {
            "label": "Type here",
            "choices": ["Yes", "No"],
            "allow_free_form_input": false,
            "allowed_mime_types": ["image/png"],
          },
        },
      ]);
      final action = actions.single;
      expect(action.destructive, isTrue);
      expect(action.foreground, isFalse);
      expect(action.cancelNotification, isFalse);
      final input = action.input!;
      expect(input.label, "Type here");
      expect(input.choices, ["Yes", "No"]);
      expect(input.allowFreeFormInput, isFalse);
      expect(input.allowedMimeTypes, {"image/png"});
    });

    test("rejects non-list input", () {
      expect(() => parseActions("nope"), throwsFormatException);
    });

    test("rejects action without id", () {
      expect(
        () => parseActions([
          {"title": "Open"},
        ]),
        throwsFormatException,
      );
    });

    test("rejects action without title", () {
      expect(
        () => parseActions([
          {"id": "open"},
        ]),
        throwsFormatException,
      );
    });

    test("rejects non-map entry", () {
      expect(() => parseActions(["open"]), throwsFormatException);
    });
  });

  group("parseInput", () {
    test("null yields null", () {
      expect(parseInput(null), isNull);
    });

    test("defaults", () {
      final input = parseInput({})!;
      expect(input.label, "");
      expect(input.choices, isEmpty);
      expect(input.allowFreeFormInput, isTrue);
      expect(input.allowedMimeTypes, isEmpty);
    });

    test("rejects non-map", () {
      expect(() => parseInput("nope"), throwsFormatException);
    });
  });
}
