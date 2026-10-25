"""
schedule_utils.py — Shared parsing and display formatting for bus schedule times.

Times travel through the API as 24-hour "HH:MM" strings so they sort and compare
correctly. User-facing values go through `format_12h`, which is the ONLY place an
AM/PM suffix is ever appended.

Appending the suffix by hand is what produced values such as "16:30 AM" and
"1612:07 AM": the underlying string was already 24-hour, so "08:30" + " AM"
looked fine until a schedule ran past 12:00.
"""

from __future__ import annotations

from datetime import datetime, time

# Ordered most-specific first; the first pattern that parses wins.
_ACCEPTED_FORMATS = ("%H:%M", "%H:%M:%S", "%I:%M %p", "%I:%M%p", "%I%p")

UNKNOWN_TIME = "--:--"


def to_time(value: str | time | datetime | None) -> time | None:
    """Normalises a schedule value to a `datetime.time`, or None if unparseable."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.time()
    if isinstance(value, time):
        return value

    text = str(value).strip()
    if not text:
        return None

    for fmt in _ACCEPTED_FORMATS:
        try:
            return datetime.strptime(text, fmt).time()
        except ValueError:
            continue
    return None


def format_24h(value: str | time | datetime | None, default: str = UNKNOWN_TIME) -> str:
    """Renders a schedule value as "HH:MM" in 24-hour form."""
    parsed = to_time(value)
    if parsed is None:
        return default
    return f"{parsed.hour:02d}:{parsed.minute:02d}"


def format_12h(value: str | time | datetime | None, default: str = UNKNOWN_TIME) -> str:
    """Renders a schedule value as "hh:mm AM/PM" in 12-hour form."""
    parsed = to_time(value)
    if parsed is None:
        return default
    hour12 = parsed.hour % 12 or 12
    suffix = "AM" if parsed.hour < 12 else "PM"
    return f"{hour12:02d}:{parsed.minute:02d} {suffix}"


def clamp_to(value: time, earliest: time, latest: time) -> tuple[time, bool]:
    """
    Clamps `value` into [earliest, latest].

    Returns (clamped_value, was_clamped) so callers can surface infeasible
    schedules instead of silently presenting impossible times.
    """
    if value < earliest:
        return earliest, True
    if value > latest:
        return latest, True
    return value, False