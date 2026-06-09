"""Tests for JSON persistence."""

from __future__ import annotations

from alarm_scheduler.models import Alarm
from alarm_scheduler.storage import AlarmStorage


def test_load_returns_empty_when_file_missing(storage: AlarmStorage) -> None:
    assert storage.load() == []


def test_save_and_load_round_trip(storage: AlarmStorage) -> None:
    alarms = [Alarm(label="A", time="07:00"), Alarm(label="B", time="08:30")]
    storage.save(alarms)
    loaded = storage.load()
    assert len(loaded) == 2
    assert loaded[0].label == "A"
    assert loaded[1].time == "08:30"


def test_load_rejects_invalid_json(storage: AlarmStorage) -> None:
    import pytest

    storage.path.write_text("{not json", encoding="utf-8")
    with pytest.raises(ValueError, match="Invalid alarm storage"):
        storage.load()
