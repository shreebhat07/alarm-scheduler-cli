"""JSON file persistence for alarms."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from alarm_scheduler.models import Alarm

logger = logging.getLogger(__name__)


class AlarmStorage:
    """Reads and writes alarms to a JSON file."""

    def __init__(self, path: Path) -> None:
        self._path = path

    @property
    def path(self) -> Path:
        return self._path

    def load(self) -> list[Alarm]:
        if not self._path.exists():
            logger.debug("No storage file at %s; starting empty", self._path)
            return []

        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid alarm storage file: {self._path}") from exc

        if not isinstance(raw, list):
            raise ValueError("Alarm storage must contain a JSON array")

        return [Alarm.from_dict(item) for item in raw]

    def save(self, alarms: list[Alarm]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        payload = [alarm.to_dict() for alarm in alarms]
        self._path.write_text(
            json.dumps(payload, indent=2) + "\n",
            encoding="utf-8",
        )
        logger.debug("Saved %d alarm(s) to %s", len(alarms), self._path)
