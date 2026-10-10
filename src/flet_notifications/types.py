"""Enums for scheduling parameters, mirroring flutter_local_notifications."""

from __future__ import annotations

from enum import Enum


class RepeatInterval(str, Enum):
    """Repeat cadence for periodic notifications (Android/iOS/macOS)."""

    EVERY_MINUTE = "everyMinute"
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"


class DateTimeComponents(str, Enum):
    """Which parts of the scheduled date repeat (daily/weekly/monthly/yearly)."""

    TIME = "time"  # every day at the given time
    DAY_OF_WEEK_AND_TIME = "dayOfWeekAndTime"
    DAY_OF_MONTH_AND_TIME = "dayOfMonthAndTime"
    DATE_AND_TIME = "dateAndTime"


class AndroidScheduleMode(str, Enum):
    """Android alarm exactness mode."""

    ALARM_CLOCK = "alarmClock"  # exact + shows in alarm-clock UI
    EXACT = "exact"
    EXACT_ALLOW_WHILE_IDLE = "exactAllowWhileIdle"  # default; survives doze
    INEXACT = "inexact"
    INEXACT_ALLOW_WHILE_IDLE = "inexactAllowWhileIdle"
