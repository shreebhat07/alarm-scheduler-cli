"""Business logic for alarm management."""

from __future__ import annotations

import logging
from datetime import datetime

from alarm_scheduler.models import Alarm, validate_time_string
from alarm_scheduler.storage import AlarmStorage

logger = logging.getLogger(__name__)


class AlarmNotFoundError(KeyError):
    """Raised when an alarm ID does not exist."""


class AmbiguousAlarmIdError(ValueError):
    """Raised when an ID prefix matches more than one alarm."""


class AlarmService:
    """Coordinates alarm CRUD operations and persistence."""

    def __init__(self, storage: AlarmStorage) -> None:
        self._storage = storage

    def _resolve_alarm_id(self, alarm_id: str, alarms: list[Alarm]) -> str:
        """Match full UUID or unique prefix (as shown by `alarm list`)."""
        for alarm in alarms:
            if alarm.id == alarm_id:
                return alarm.id

        prefix_matches = [alarm for alarm in alarms if alarm.id.startswith(alarm_id)]
        if len(prefix_matches) == 1:
            return prefix_matches[0].id
        if len(prefix_matches) > 1:
            raise AmbiguousAlarmIdError(
                f"Alarm ID prefix {alarm_id!r} matches multiple alarms; "
                "use a longer prefix or the full ID"
            )
        raise AlarmNotFoundError(alarm_id)

    def list_alarms(self) -> list[Alarm]:
        return self._storage.load()

    def add_alarm(self, label: str, time_str: str) -> Alarm:
        normalized = validate_time_string(time_str)
        alarms = self._storage.load()
        alarm = Alarm(label=label, time=normalized)
        alarms.append(alarm)
        self._storage.save(alarms)
        logger.info("Added alarm %s at %s", alarm.id, alarm.time)
        return alarm

    def delete_alarm(self, alarm_id: str) -> Alarm:
        alarms = self._storage.load()
        resolved_id = self._resolve_alarm_id(alarm_id, alarms)
        for index, alarm in enumerate(alarms):
            if alarm.id == resolved_id:
                removed = alarms.pop(index)
                self._storage.save(alarms)
                logger.info("Deleted alarm %s", resolved_id)
                return removed
        raise AlarmNotFoundError(alarm_id)

    def set_enabled(self, alarm_id: str, enabled: bool) -> Alarm:
        alarms = self._storage.load()
        resolved_id = self._resolve_alarm_id(alarm_id, alarms)
        for alarm in alarms:
            if alarm.id == resolved_id:
                alarm.enabled = enabled
                self._storage.save(alarms)
                logger.info("Alarm %s enabled=%s", resolved_id, enabled)
                return alarm
        raise AlarmNotFoundError(alarm_id)

    def snooze_alarm(self, alarm_id: str, now: datetime, minutes: int) -> Alarm:
        if minutes <= 0:
            raise ValueError("Snooze minutes must be positive")

        alarms = self._storage.load()
        resolved_id = self._resolve_alarm_id(alarm_id, alarms)
        for alarm in alarms:
            if alarm.id == resolved_id:
                alarm.snooze(now, minutes)
                self._storage.save(alarms)
                logger.info("Snoozed alarm %s for %d minute(s)", resolved_id, minutes)
                return alarm
        raise AlarmNotFoundError(alarm_id)

    def mark_ringing(self, alarm_id: str, now: datetime) -> Alarm:
        alarms = self._storage.load()
        resolved_id = self._resolve_alarm_id(alarm_id, alarms)
        for alarm in alarms:
            if alarm.id == resolved_id:
                alarm.mark_triggered(now)
                self._storage.save(alarms)
                return alarm
        raise AlarmNotFoundError(alarm_id)
