"""Domain models for alarms."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time
from uuid import uuid4

TIME_FORMAT = "%H:%M"
ISO_DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S"


@dataclass
class Alarm:
    """A single alarm scheduled at a daily HH:MM time."""

    label: str
    time: str
    id: str = field(default_factory=lambda: str(uuid4()))
    enabled: bool = True
    snooze_until: str | None = None
    last_triggered: str | None = None

    def parsed_time(self) -> time:
        return datetime.strptime(self.time, TIME_FORMAT).time()

    def last_triggered_date(self) -> date | None:
        if self.last_triggered is None:
            return None
        return date.fromisoformat(self.last_triggered)

    def snooze_datetime(self) -> datetime | None:
        if self.snooze_until is None:
            return None
        return datetime.fromisoformat(self.snooze_until)

    def should_ring_at(self, now: datetime) -> bool:
        if not self.enabled:
            return False

        snooze = self.snooze_datetime()
        if snooze is not None:
            if now < snooze:
                return False
            return now.replace(second=0, microsecond=0) == snooze.replace(
                second=0, microsecond=0
            )

        if self.last_triggered_date() == now.date():
            return False

        return now.time().replace(second=0, microsecond=0) == self.parsed_time()

    def mark_triggered(self, now: datetime) -> None:
        self.last_triggered = now.date().isoformat()
        self.snooze_until = None

    def snooze(self, now: datetime, minutes: int) -> None:
        from datetime import timedelta

        target = now + timedelta(minutes=minutes)
        self.snooze_until = target.replace(second=0, microsecond=0).strftime(
            ISO_DATETIME_FORMAT
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "label": self.label,
            "time": self.time,
            "enabled": self.enabled,
            "snooze_until": self.snooze_until,
            "last_triggered": self.last_triggered,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> Alarm:
        return cls(
            id=str(data["id"]),
            label=str(data["label"]),
            time=str(data["time"]),
            enabled=bool(data.get("enabled", True)),
            snooze_until=(
                str(data["snooze_until"]) if data.get("snooze_until") else None
            ),
            last_triggered=(
                str(data["last_triggered"]) if data.get("last_triggered") else None
            ),
        )


def validate_time_string(value: str) -> str:
    """Validate and normalize an HH:MM time string."""
    parsed = datetime.strptime(value, TIME_FORMAT)
    return parsed.strftime(TIME_FORMAT)
