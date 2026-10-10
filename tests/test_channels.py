"""Tests for notification channels."""

import pytest

from flet_notifications import Importance, NotificationChannel


def test_channel_defaults():
    channel = NotificationChannel(id="alerts", name="Alerts")
    d = channel.to_dict()
    assert d["importance"] == "defaultImportance"
    assert d["play_sound"] is True
    assert d["enable_vibration"] is True
    assert d["show_badge"] is True
    assert d["bypass_dnd"] is False


def test_channel_requires_id_and_name():
    with pytest.raises(ValueError, match="id"):
        NotificationChannel(id="", name="Alerts")
    with pytest.raises(ValueError, match="name"):
        NotificationChannel(id="alerts", name="")


def test_channel_vibration_pattern():
    channel = NotificationChannel(
        id="vib", name="Vibrate", vibration_pattern=[0, 250, 100]
    )
    assert channel.to_dict()["vibration_pattern"] == [0, 250, 100]


def test_channel_led_color_validated():
    channel = NotificationChannel(
        id="led", name="LED", led_color="#FF0000", enable_lights=True
    )
    assert channel.led_color == "#FF0000"
    with pytest.raises(ValueError, match="hex"):
        NotificationChannel(id="led", name="LED", led_color="red")
    with pytest.raises(ValueError, match="hex"):
        NotificationChannel(id="led", name="LED", led_color="#FFF")


def test_channel_from_dict_round_trip():
    original = NotificationChannel(
        id="c1",
        name="Channel One",
        description="desc",
        importance=Importance.HIGH,
        bypass_dnd=True,
        sound="alert",
    )
    restored = NotificationChannel.from_dict(original.to_dict())
    assert restored == original


def test_importance_enum_values():
    assert Importance.HIGH.value == "high"
    assert Importance.DEFAULT.value == "defaultImportance"
    assert Importance.MAX.value == "max"
