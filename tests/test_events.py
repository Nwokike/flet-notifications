"""Tests for NotificationEvent hydration from Dart payloads."""

from flet.utils import from_dict

from flet_notifications import LocalNotifications, NotificationEvent, ResponseType


def _control():
    return LocalNotifications()


def test_event_from_tap_payload():
    control = _control()
    event = from_dict(
        NotificationEvent,
        {
            "control": control,
            "name": "tap",
            "id": 5,
            "action_id": "",
            "payload": "hello",
            "input": "",
            "response_type": "tap",
        },
    )
    assert event.id == 5
    assert event.action_id == ""
    assert event.payload == "hello"
    assert event.input == ""
    assert event.response_type == ResponseType.TAP.value


def test_event_from_action_payload():
    control = _control()
    event = from_dict(
        NotificationEvent,
        {
            "control": control,
            "name": "action",
            "id": 5,
            "action_id": "reply",
            "payload": "hello",
            "input": "my reply text",
            "response_type": "action",
        },
    )
    assert event.action_id == "reply"
    assert event.input == "my reply text"
    assert event.response_type == ResponseType.ACTION.value


def test_event_from_dismissed_payload():
    control = _control()
    event = from_dict(
        NotificationEvent,
        {
            "control": control,
            "name": "dismissed",
            "id": 5,
            "response_type": "dismissed",
        },
    )
    assert event.response_type == ResponseType.DISMISSED.value


def test_event_defaults():
    control = _control()
    event = from_dict(NotificationEvent, {"control": control, "name": "tap"})
    assert event.id == 0
    assert event.action_id == ""
    assert event.payload == ""
    assert event.input == ""
    assert event.response_type == ResponseType.TAP.value
