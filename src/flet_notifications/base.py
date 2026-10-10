"""Shared types and helpers for flet-notifications."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

import flet as ft


class ResponseType(str, Enum):
    """Type of a notification response delivered from the OS to the app."""

    TAP = "tap"
    ACTION = "action"
    DISMISSED = "dismissed"


@dataclass
class NotificationEvent(ft.Event[ft.EventControlType]):
    """A notification tap, action-button press or dismissal.

    Delivered to ``on_tap`` / ``on_action`` / ``on_dismissed`` handlers.
    """

    id: int = 0
    action_id: str = ""  # "" for a plain tap; the button id for actions
    payload: str = ""
    input: str = ""  # inline-reply text, when the action had an input
    response_type: str = ResponseType.TAP.value


class NotificationError(Exception):
    """Raised when a notification operation fails.

    ``code`` is a stable machine-readable identifier:
    ``unsupported_platform``, ``init_failed``, ``show_failed``,
    ``cancel_failed``, ``permission_failed``, ``unknown_method``.
    """

    def __init__(self, code: str, message: str = "") -> None:
        self.code = code
        self.message = message
        super().__init__(f"{code}: {message}" if message else code)

    def __repr__(self) -> str:
        return f"NotificationError(code={self.code!r}, message={self.message!r})"


def check_result(result: object) -> None:
    """Raise :class:`NotificationError` if a Dart invoke returned an error string.

    Dart service methods return ``"error:<code>:<message>"`` on failure.
    """
    if isinstance(result, str) and result.startswith("error:"):
        _, _, rest = result.partition(":")
        code, _, message = rest.partition(":")
        raise NotificationError(code.strip(), message.strip())


def to_bool(result: object) -> bool:
    """Coerce a Dart invoke result to bool (``"true"``/``"false"``)."""
    check_result(result)
    if isinstance(result, bool):
        return result
    return str(result).strip().lower() == "true"
