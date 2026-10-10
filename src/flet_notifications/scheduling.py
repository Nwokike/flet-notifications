"""Schedule argument serialization (pure — unit tested)."""

from __future__ import annotations

from datetime import datetime, timedelta

from flet_notifications.types import (
    AndroidScheduleMode,
    DateTimeComponents,
    RepeatInterval,
)


def build_schedule_args(
    *,
    id: int,
    when: datetime | timedelta,
    title: str | None,
    body: str | None,
    payload: str,
    actions: list,
    repeat_interval: RepeatInterval | None,
    match_components: DateTimeComponents | None,
    schedule_mode: AndroidScheduleMode,
    time_zone: str | None,
) -> dict:
    """Build the `schedule` invoke payload.

    Naive datetimes are wall-clock times interpreted in ``time_zone`` (or the
    device timezone when ``time_zone`` is None); aware datetimes carry their
    offset so the exact instant is preserved.
    """
    if repeat_interval is not None and match_components is not None:
        raise ValueError("repeat_interval and match_components are mutually exclusive")

    if isinstance(when, timedelta):
        when_payload: dict = {
            "delay_seconds": when.total_seconds(),
            "time_zone": time_zone,
        }
    else:
        when_payload = {
            "iso": when.isoformat(),
            "utc_offset_seconds": when.utcoffset().total_seconds()
            if when.utcoffset() is not None
            else None,
            "time_zone": time_zone,
        }

    return {
        "id": id,
        "title": title,
        "body": body,
        "payload": payload,
        "actions": [a.to_dict() for a in actions] if actions else None,
        "when": when_payload,
        "repeat_interval": repeat_interval.value if repeat_interval else None,
        "match_components": match_components.value if match_components else None,
        "schedule_mode": schedule_mode.value,
    }


def build_periodic_args(
    *,
    id: int,
    repeat_interval: RepeatInterval,
    title: str | None,
    body: str | None,
    payload: str,
    actions: list,
    schedule_mode: AndroidScheduleMode,
    repeat_duration_seconds: int | None,
) -> dict:
    """Build the `periodically_show` invoke payload."""
    if repeat_duration_seconds is not None and repeat_duration_seconds < 60:
        raise ValueError("repeat_duration_seconds must be at least 60")
    return {
        "id": id,
        "title": title,
        "body": body,
        "payload": payload,
        "actions": [a.to_dict() for a in actions] if actions else None,
        "repeat_interval": repeat_interval.value,
        "schedule_mode": schedule_mode.value,
        "repeat_duration_seconds": repeat_duration_seconds,
    }
