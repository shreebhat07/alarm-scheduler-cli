"""Tests for alarm service operations."""

from __future__ import annotations

from datetime import datetime

import pytest

from alarm_scheduler.service import AlarmNotFoundError, AlarmService


def test_add_and_list(storage) -> None:
    service = AlarmService(storage)
    alarm = service.add_alarm("Morning", "06:45")
    alarms = service.list_alarms()
    assert len(alarms) == 1
    assert alarms[0].id == alarm.id


def test_delete_alarm(storage) -> None:
    service = AlarmService(storage)
    alarm = service.add_alarm("Temp", "09:00")
    removed = service.delete_alarm(alarm.id)
    assert removed.label == "Temp"
    assert service.list_alarms() == []


def test_delete_alarm_by_prefix(storage) -> None:
    service = AlarmService(storage)
    alarm = service.add_alarm("Temp", "09:00")
    removed = service.delete_alarm(alarm.id[:8])
    assert removed.label == "Temp"
    assert service.list_alarms() == []


def test_delete_missing_alarm_raises(storage) -> None:
    service = AlarmService(storage)
    with pytest.raises(AlarmNotFoundError):
        service.delete_alarm("missing-id")


def test_enable_disable(storage) -> None:
    service = AlarmService(storage)
    alarm = service.add_alarm("Toggle", "10:00")
    service.set_enabled(alarm.id, False)
    assert service.list_alarms()[0].enabled is False
    service.set_enabled(alarm.id, True)
    assert service.list_alarms()[0].enabled is True


def test_snooze_requires_positive_minutes(storage) -> None:
    service = AlarmService(storage)
    alarm = service.add_alarm("Nap", "12:00")
    with pytest.raises(ValueError, match="positive"):
        service.snooze_alarm(alarm.id, datetime(2026, 6, 9, 12, 0), 0)


def test_snooze_persists(storage) -> None:
    service = AlarmService(storage)
    alarm = service.add_alarm("Nap", "12:00")
    now = datetime(2026, 6, 9, 12, 0)
    service.snooze_alarm(alarm.id, now, minutes=15)
    updated = service.list_alarms()[0]
    assert updated.snooze_until is not None
