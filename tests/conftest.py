"""Shared pytest fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest

from alarm_scheduler.storage import AlarmStorage


@pytest.fixture
def storage_path(tmp_path: Path) -> Path:
    return tmp_path / "alarms.json"


@pytest.fixture
def storage(storage_path: Path) -> AlarmStorage:
    return AlarmStorage(storage_path)
