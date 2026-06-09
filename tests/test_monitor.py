"""Tests for the monitoring loop."""

from __future__ import annotations

from datetime import datetime

from alarm_scheduler.models import Alarm
from alarm_scheduler.monitor import (
    AlarmMonitor,
    format_alarm_message,
    handle_alarm_choice,
    interactive_alarm_handler,
)
from alarm_scheduler.service import AlarmService


def test_format_alarm_message_includes_buzz_and_label() -> None:
    alarm = Alarm(label="Water", time="09:30")
    message = format_alarm_message(alarm)

    assert "ZZZZZZ ZZZZZ ZZZZ ZZZ ZZ Z" in message
    assert "ALARM: Water (09:30)" in message


def test_run_once_triggers_enabled_alarm(storage) -> None:
    service = AlarmService(storage)
    service.add_alarm("Wake", "08:00")
    notifications: list[str] = []

    def notifier(alarm) -> None:
        notifications.append(alarm.label)

    monitor = AlarmMonitor(service, notifier=notifier)
    triggered = monitor.run_once(datetime(2026, 6, 9, 8, 0, 0))

    assert len(triggered) == 1
    assert notifications == ["Wake"]
    assert service.list_alarms()[0].last_triggered == "2026-06-09"


def test_run_once_skips_disabled_alarm(storage) -> None:
    service = AlarmService(storage)
    alarm = service.add_alarm("Off", "08:00")
    service.set_enabled(alarm.id, False)

    notifications: list[str] = []

    monitor = AlarmMonitor(
        service,
        notifier=lambda a: notifications.append(a.label),
    )
    triggered = monitor.run_once(datetime(2026, 6, 9, 8, 0, 0))

    assert triggered == []
    assert notifications == []


def test_handle_alarm_choice_snooze(storage) -> None:
    service = AlarmService(storage)
    alarm = service.add_alarm("Nap", "12:00")
    now = datetime(2026, 6, 9, 12, 0)

    message = handle_alarm_choice(service, alarm, now, "1", snooze_minutes=5)

    updated = service.list_alarms()[0]
    assert updated.snooze_until is not None
    assert "Snoozed until" in message


def test_handle_alarm_choice_disable(storage) -> None:
    service = AlarmService(storage)
    alarm = service.add_alarm("Nap", "12:00")
    now = datetime(2026, 6, 9, 12, 0)

    message = handle_alarm_choice(service, alarm, now, "2")

    assert service.list_alarms()[0].enabled is False
    assert "disabled" in message


def test_handle_alarm_choice_ignore(storage) -> None:
    service = AlarmService(storage)
    alarm = service.add_alarm("Nap", "12:00")
    now = datetime(2026, 6, 9, 12, 0)

    message = handle_alarm_choice(service, alarm, now, "3")

    assert service.list_alarms()[0].last_triggered == "2026-06-09"
    assert "dismissed" in message


def test_interactive_handler_snooze(storage, capsys) -> None:
    service = AlarmService(storage)
    alarm = service.add_alarm("Tea", "15:00")
    now = datetime(2026, 6, 9, 15, 0)

    interactive_alarm_handler(
        service,
        alarm,
        now,
        input_func=lambda _: "1",
        snooze_minutes=5,
    )

    assert service.list_alarms()[0].snooze_until is not None
    assert "Snoozed until" in capsys.readouterr().out


def test_interactive_monitor_run_once(storage) -> None:
    service = AlarmService(storage)
    service.add_alarm("Wake", "08:00")

    monitor = AlarmMonitor(
        service,
        interactive=True,
        input_func=lambda _: "3",
    )
    triggered = monitor.run_once(datetime(2026, 6, 9, 8, 0, 0))

    assert len(triggered) == 1
    assert service.list_alarms()[0].last_triggered == "2026-06-09"
