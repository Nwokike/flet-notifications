"""Tests for the platform probes and OS-integration methods."""

import pytest

from flet_notifications import (
    ActiveNotification,
    LocalNotifications,
    NotificationError,
    NotificationErrorCode,
)


class RecordingService(LocalNotifications):
    def __init__(self):
        super().__init__()
        self.calls: list[tuple[str, dict | None]] = []

    async def _invoke_method(self, method_name, arguments=None, timeout=None):
        self.calls.append((method_name, arguments))
        return "ok"


async def test_are_notifications_enabled():
    service = LocalNotifications()

    async def invoke(method_name, arguments=None, timeout=None):
        return "true"

    service._invoke_method = invoke
    assert await service.are_notifications_enabled() is True


async def test_open_app_settings():
    service = RecordingService()
    await service.open_app_notification_settings()
    assert service.calls[-1] == ("open_app_settings", None)


async def test_get_active_notifications_parses_records():
    service = LocalNotifications()

    async def invoke(method_name, arguments=None, timeout=None):
        assert method_name == "get_active"
        return [
            {
                "id": 5,
                "channel_id": "alerts",
                "group_key": "g",
                "tag": "t",
                "title": "T",
                "body": "B",
                "payload": "p",
                "big_text": "long",
            }
        ]

    service._invoke_method = invoke
    active = await service.get_active_notifications()
    assert active == [
        ActiveNotification(
            id=5,
            channel_id="alerts",
            group_key="g",
            tag="t",
            title="T",
            body="B",
            payload="p",
            big_text="long",
        )
    ]


async def test_get_active_notifications_empty_on_other_platforms():
    service = LocalNotifications()

    async def invoke(method_name, arguments=None, timeout=None):
        return []

    service._invoke_method = invoke
    assert await service.get_active_notifications() == []


async def test_launch_details_not_from_notification():
    service = LocalNotifications()

    async def invoke(method_name, arguments=None, timeout=None):
        return {"did_notification_launch_app": False}

    service._invoke_method = invoke
    details = await service.get_notification_app_launch_details()
    assert details.did_notification_launch_app is False
    assert details.notification is None


async def test_launch_details_from_notification():
    from flet.utils import from_dict

    from flet_notifications import NotificationEvent

    service = LocalNotifications()

    async def invoke(method_name, arguments=None, timeout=None):
        return {
            "did_notification_launch_app": True,
            "notification": {
                "id": 9,
                "action_id": "open",
                "payload": "deep",
                "input": "",
                "response_type": "action",
            },
        }

    service._invoke_method = invoke
    details = await service.get_notification_app_launch_details()
    assert details.did_notification_launch_app is True
    assert details.notification is not None
    assert isinstance(details.notification, NotificationEvent)
    event = from_dict(
        NotificationEvent,
        {"control": service, "name": "tap", "payload": "deep"},
    )
    assert event.payload == "deep"


async def test_launch_details_error_raises():
    service = LocalNotifications()

    async def invoke(method_name, arguments=None, timeout=None):
        return "error:query_failed:nope"

    service._invoke_method = invoke
    with pytest.raises(NotificationError) as exc:
        await service.get_notification_app_launch_details()
    assert exc.value.code == NotificationErrorCode.QUERY_FAILED


async def test_policy_probes():
    service = LocalNotifications()
    seen = []

    async def invoke(method_name, arguments=None, timeout=None):
        seen.append((method_name, timeout))
        return "false"

    service._invoke_method = invoke
    assert await service.has_notification_policy_access() is False
    assert await service.request_notification_policy_access() is False
    assert seen[0][0] == "has_notification_policy_access"
    assert seen[1][0] == "request_notification_policy_access"
    assert seen[1][1] == 300  # permission screens take a while


async def test_channel_groups():
    service = RecordingService()
    await service.create_notification_channel_group("updates", "Updates")
    assert service.calls[-1] == (
        "create_notification_channel_group",
        {"group_id": "updates", "name": "Updates"},
    )
    await service.delete_notification_channel_group("updates")
    assert service.calls[-1] == (
        "delete_notification_channel_group",
        {"group_id": "updates"},
    )


def test_error_codes_documented():
    assert NotificationErrorCode.UNSUPPORTED_PLATFORM == "unsupported_platform"
    assert NotificationErrorCode.INVALID_STYLE == "invalid_style"
    assert NotificationErrorCode.INVALID_SCHEDULE == "invalid_schedule"
