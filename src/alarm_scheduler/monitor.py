"""Alarm monitoring loop."""

from __future__ import annotations

import logging
import sys
import time as time_module
from collections.abc import Callable
from datetime import datetime

from alarm_scheduler.models import Alarm
from alarm_scheduler.service import AlarmService

logger = logging.getLogger(__name__)

DEFAULT_SNOOZE_MINUTES = 5

Clock = Callable[[], datetime]
Sleeper = Callable[[float], None]
Notifier = Callable[[Alarm], None]
InputFunc = Callable[[str], str]


def format_alarm_message(alarm: Alarm) -> str:
    """Build a visible buzzing alarm message for the terminal."""
    banner = "ZZZZZZ ZZZZZ ZZZZ ZZZ ZZ Z"
    return (
        f"\n{banner}\n"
        f"  ALARM: {alarm.label} ({alarm.time})\n"
    )


def format_alarm_prompt(snooze_minutes: int) -> str:
    return (
        "\nChoose an option:\n"
        f"  1) Snooze ({snooze_minutes} minutes)\n"
        "  2) Disable alarm\n"
        "  3) Ignore (dismiss for today)\n"
        "> "
    )


def ring_alarm(alarm: Alarm) -> None:
    """Print alarm notification and emit terminal bells."""
    print(format_alarm_message(alarm), flush=True)
    for _ in range(3):
        sys.stdout.write("\a")
    sys.stdout.flush()


def default_notifier(alarm: Alarm) -> None:
    """Non-interactive notifier (used in tests)."""
    ring_alarm(alarm)


def handle_alarm_choice(
    service: AlarmService,
    alarm: Alarm,
    now: datetime,
    choice: str,
    *,
    snooze_minutes: int = DEFAULT_SNOOZE_MINUTES,
) -> str:
    """Apply the user's response to a ringing alarm."""
    if choice == "1":
        updated = service.snooze_alarm(alarm.id, now, snooze_minutes)
        return f"Snoozed until {updated.snooze_until}."

    if choice == "2":
        service.set_enabled(alarm.id, False)
        return f"Alarm '{alarm.label}' disabled."

    if choice == "3":
        service.mark_ringing(alarm.id, now)
        return "Alarm dismissed for today."

    service.mark_ringing(alarm.id, now)
    return "Invalid choice. Alarm dismissed for today."


def interactive_alarm_handler(
    service: AlarmService,
    alarm: Alarm,
    now: datetime,
    *,
    input_func: InputFunc = input,
    snooze_minutes: int = DEFAULT_SNOOZE_MINUTES,
) -> str:
    """Show alarm, prompt for action, and persist the user's choice."""
    ring_alarm(alarm)
    choice = input_func(format_alarm_prompt(snooze_minutes)).strip()
    message = handle_alarm_choice(
        service, alarm, now, choice, snooze_minutes=snooze_minutes
    )
    print(message, flush=True)
    return message


class AlarmMonitor:
    """Polls enabled alarms and triggers notifications."""

    def __init__(
        self,
        service: AlarmService,
        *,
        clock: Clock | None = None,
        sleeper: Sleeper | None = None,
        notifier: Notifier | None = None,
        input_func: InputFunc | None = None,
        interactive: bool = False,
        snooze_minutes: int = DEFAULT_SNOOZE_MINUTES,
        poll_interval: float = 1.0,
    ) -> None:
        self._service = service
        self._clock = clock or datetime.now
        self._sleeper = sleeper or time_module.sleep
        self._notifier = notifier or default_notifier
        self._input_func = input_func or input
        self._interactive = interactive
        self._snooze_minutes = snooze_minutes
        self._poll_interval = poll_interval
        self._running = False

    def stop(self) -> None:
        self._running = False

    def run_once(self, now: datetime | None = None) -> list[Alarm]:
        """Evaluate alarms once; useful for tests."""
        current = now or self._clock()
        triggered: list[Alarm] = []

        for alarm in self._service.list_alarms():
            if alarm.should_ring_at(current):
                if self._interactive:
                    interactive_alarm_handler(
                        self._service,
                        alarm,
                        current,
                        input_func=self._input_func,
                        snooze_minutes=self._snooze_minutes,
                    )
                else:
                    self._notifier(alarm)
                    self._service.mark_ringing(alarm.id, current)
                triggered.append(alarm)

        return triggered

    def run(self) -> None:
        """Block until stopped, checking alarms on each poll interval."""
        self._running = True
        logger.info("Alarm monitor started (poll interval=%ss)", self._poll_interval)

        while self._running:
            try:
                self.run_once()
            except Exception:
                logger.exception("Monitor loop error")
            self._sleeper(self._poll_interval)