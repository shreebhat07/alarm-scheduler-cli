"""Tests for alarm domain model logic."""

from __future__ import annotations

from datetime import datetime

import pytest

from alarm_scheduler.models import Alarm, validate_time_string


def test_validate_time_string_accepts_valid_time() -> None:
    assert validate_time_string("07:30") == "07:30"


def test_validate_time_string_rejects_invalid_time() -> None:
    with pytest.raises(ValueError):
        validate_time_string("25:00")


def test_should_ring_at_scheduled_time_once_per_day() -> None:
    alarm = Alarm(label="Wake", time="08:00")
    morning = datetime(2026, 6, 9, 8, 0, 0)

    assert alarm.should_ring_at(morning) is True
    alarm.mark_triggered(morning)
    assert alarm.should_ring_at(morning.replace(second=30)) is False


def test_disabled_alarm_does_not_ring() -> None:
    alarm = Alarm(label="Wake", time="08:00", enabled=False)
    morning = datetime(2026, 6, 9, 8, 0, 0)
    assert alarm.should_ring_at(morning) is False


def test_snooze_defers_scheduled_ring() -> None:
    alarm = Alarm(label="Wake", time="08:00")
    morning = datetime(2026, 6, 9, 8, 0, 0)
    alarm.snooze(morning, minutes=10)

    assert alarm.should_ring_at(morning) is False
    assert alarm.should_ring_at(datetime(2026, 6, 9, 8, 10, 0)) is True


def test_snooze_clears_after_trigger() -> None:
    alarm = Alarm(label="Wake", time="08:00")
    now = datetime(2026, 6, 9, 8, 5, 0)
    alarm.snooze(now, minutes=5)
    alarm.mark_triggered(datetime(2026, 6, 9, 8, 10, 0))

    assert alarm.snooze_until is None
    assert alarm.last_triggered == "2026-06-09"


def test_round_trip_dict() -> None:
    original = Alarm(label="Meeting", time="14:15", enabled=False)
    restored = Alarm.from_dict(original.to_dict())
    assert restored == original
