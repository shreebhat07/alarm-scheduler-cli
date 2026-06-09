# Alarm Scheduler CLI

A lightweight and simple Python CLI alarm clock with JSON persistence.

## Demo Video

**[Watch the demo recording →](https://drive.google.com/file/d/18mDV754KFsJD_0j59TT61yy_PYKHwzWu/view?usp=drive_link)**

The video walks through the full CLI: setting up alarms, managing them, and running the monitor to show how notifications appear when an alarm fires.

---

## 1. Project Overview

This tool lets you manage daily alarms from the terminal: create them, list/delete them, enable or disable them, snooze them, and run a background monitor that rings at the scheduled time.

**Tech stack:** Python 3.10+, stdlib only (`argparse`, `json`, `dataclasses`, `logging`).

---

## 2. Problem Definition

### Core Problem Statement

> Build a **local CLI alarm clock** that lets a user schedule daily alarms, persist them across restarts, and receive a terminal notification when an alarm fires

### MVP Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| R1 | Add an alarm (label + HH:MM time) | P1 |
| R2 | List all alarms with status | P1 |
| R3 | Delete an alarm by ID | P1 |
| R4 | Enable / disable an alarm | P1 |
| R5 | Run a monitoring loop that rings at scheduled times | P1 |
| R6 | Snooze a firing alarm for N minutes | P1 |
| R7 | Persist alarms to local JSON storage | P1 |
| R8 | Type hints, logging, and error handling | P1 |
| R9 | Automated tests (pytest) | P1 |

### Assumptions

- **Single user**, single machine, no authentication.
- Alarms repeat **daily** at a fixed local time (HH:MM, 24-hour).
- **Local system timezone** is authoritative; no timezone picker.
- Notifications are **terminal-based** (printed message + bell character).
- Storage path defaults to `~/.alarm-scheduler/alarms.json` (override with `--storage`).

### Future-Plans

- GUI, web UI, or mobile push notifications
- Database, ORM, or cloud sync
- Weekday/recurrence rules (e.g., "Mon–Fri only")
- Multiple users or alarm sharing
- Audio file playback or OS notification APIs
- NTP / timezone conversion

---

## 3. Architecture

### Folder Structure

```
alarm-scheduler-cli/
├── pyproject.toml
├── README.md
├── RECORDING_SCRIPT.md
├── src/
│   └── alarm_scheduler/
│       ├── __init__.py
│       ├── __main__.py      # python -m alarm_scheduler
│       ├── cli.py           # argparse commands, exit codes
│       ├── models.py        # Alarm dataclass + ring logic
│       ├── storage.py       # JSON read/write
│       ├── service.py       # CRUD + snooze orchestration
│       ├── monitor.py       # polling loop (injectable clock)
│       └── logging_config.py
└── tests/
    ├── conftest.py
    ├── test_models.py
    ├── test_storage.py
    ├── test_service.py
    ├── test_monitor.py
    └── test_cli.py
```

### Module Responsibilities

| Module | Responsibility |
|--------|----------------|
| `models` | Domain types, validation, **when should an alarm ring?** |
| `storage` | Serialize/deserialize alarms to JSON |
| `service` | Business operations; single place for persistence side effects |
| `monitor` | Poll loop; trigger notifications; mark alarms as fired |
| `cli` | Parse args, wire dependencies, print user-facing output |

### Class Design

```
Alarm (dataclass)
  ├── id, label, time, enabled
  ├── snooze_until, last_triggered
  ├── should_ring_at(now) -> bool    # core domain logic
  ├── snooze(now, minutes)
  └── mark_triggered(now)

AlarmStorage
  ├── load() -> list[Alarm]
  └── save(alarms)

AlarmService
  ├── add_alarm / delete_alarm / set_enabled / snooze_alarm
  └── mark_ringing (called by monitor)

AlarmMonitor
  ├── run()          # blocking loop
  └── run_once(now)  # test-friendly single tick
```

### Data Model

```json
[
  {
    "id": "uuid-string",
    "label": "Morning standup",
    "time": "09:30",
    "enabled": true,
    "snooze_until": "2026-06-09T09:40:00",
    "last_triggered": "2026-06-09"
  }
]
```


---

## 4. Installation

```bash
# Clone / enter project directory
cd alarm-scheduler-cli

# Install package + dev dependencies
pip install -e ".[dev]"
```

Requires **Python 3.10+**.

---

## 5. Usage

### Command overview

| Command | Purpose |
|---------|---------|
| `alarm add` | Create a new alarm |
| `alarm list` | View all alarms and their status |
| `alarm delete` | Remove an alarm |
| `alarm enable` / `alarm disable` | Turn an alarm on or off |
| `alarm snooze` | Manually snooze an alarm (optional; also available interactively in monitor) |
| **`alarm monitor`** | **Run the live alarm loop — shows how notifications appear when an alarm fires** |

> **Setup vs. demo flow:** Commands like `add`, `list`, `delete`, `enable`, `disable`, and `snooze` are for **setting up and managing** your alarms. The **`alarm monitor`** command is what you run to **see the full notification flow** — the buzzing alert, terminal beep, and interactive menu (snooze / disable / ignore) when an alarm triggers.

### Setup & management commands

Use these to configure alarms before (or while) the monitor is running:

```bash
# Add alarms
alarm add "Morning standup" 09:30
alarm add "Take meds" 21:00

# List (shows short ID prefix, time, label, status)
alarm list

# Disable / enable (ID or prefix from alarm list)
alarm disable <alarm-id>
alarm enable <alarm-id>

# Manual snooze (optional — monitor also prompts interactively)
alarm snooze <alarm-id>
alarm snooze <alarm-id> --minutes 10

# Delete
alarm delete <alarm-id>

# Custom storage path (useful for testing)
alarm --storage ./my-alarms.json list
```

### Monitor command (notification demo)

Run this in a terminal and leave it open. When an enabled alarm's time matches, you'll see the notification and can respond on the spot:

```bash
alarm monitor

# Optional: custom default snooze when pressing 1
alarm monitor --snooze-minutes 10
```

**What happens when an alarm fires:**

```
ZZZZZZ ZZZZZ ZZZZ ZZZ ZZ Z
  ALARM: Morning standup (09:30)

Choose an option:
  1) Snooze (5 minutes)
  2) Disable alarm
  3) Ignore (dismiss for today)
>
```

| Option | Action |
|--------|--------|
| **1** | Snooze for 5 minutes (or `--snooze-minutes` value), then ring again |
| **2** | Disable the alarm permanently until re-enabled |
| **3** | Dismiss for today; rings again tomorrow at the scheduled time |

Press **Ctrl+C** to stop the monitor.

Each alarm rings **at most once per calendar day** unless snoozed.

### JSON storage location

Alarms are persisted at:

```
~/.alarm-scheduler/alarms.json
```

On Windows: `C:\Users\<you>\.alarm-scheduler\alarms.json`

---

## 6. Usage Examples (quick reference)

```bash
alarm                          # show all commands
alarm add "Water break" 14:30
alarm list
alarm monitor                  # demo: watch notifications appear
```


## 7. Testing

```bash
pytest -v
```

### Test Coverage Rationale

| Test file | What it protects | Why it exists |
|-----------|------------------|---------------|
| `test_models.py` | Time validation, ring-once-per-day, snooze semantics | Highest-risk logic; bugs here cause missed or duplicate alarms |
| `test_storage.py` | JSON round-trip, missing file, corrupt file | Persistence failures silently lose user data |
| `test_service.py` | CRUD, not-found errors, snooze validation | Ensures service layer contracts |
| `test_monitor.py` | Trigger, interactive choices, skip disabled | Notification flow and user response handling |
| `test_cli.py` | Exit codes, stdout/stderr | User-facing contract |

### Example Output

```
tests/test_models.py::test_should_ring_at_scheduled_time_once_per_day PASSED
tests/test_monitor.py::test_run_once_triggers_enabled_alarm PASSED
tests/test_cli.py::test_add_and_list_via_cli PASSED
...
```

---

## 8. How AI Was Used

This project was developed with AI assistance. Below is an account of that collaboration.

### Prompts Given

1. *"Before writing code, help define MVP requirements, assumptions, non-goals."*
2. *"Design a clean Python package structure with separation of concerns, no database, JSON persistence, and pytest-friendly monitor loop."*
3. *"Implement the planned architecture and wth minimal dependencies."*
4. *"Write pytest tests for time logic, persistence, service errors, and CLI exit codes."*

---

## 9. Future Improvements

If this were a real product (beyond the exercise):

1. **Weekday recurrence** — add optional `days: [0-6]` field
2. **ID prefix matching** — `alarm delete abc` matches unique prefix from `alarm list` *(implemented)*
3. **Support multi timezone** — timezone conversion
4. **GUI** — to schedule and maintain alarms.
5. **File locking** — safe concurrent monitor + CLI writes
6. **notifications** — OS-native alerts via optional dependency
7. **Config file** — default snooze duration, poll interval

---
