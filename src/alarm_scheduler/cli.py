"""Command-line interface for the alarm scheduler."""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

from alarm_scheduler.logging_config import configure_logging
from alarm_scheduler.monitor import AlarmMonitor
from alarm_scheduler.service import AlarmNotFoundError, AlarmService
from alarm_scheduler.storage import AlarmStorage

DEFAULT_STORAGE_PATH = Path.home() / ".alarm-scheduler" / "alarms.json"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="alarm",
        description="A lightweight CLI alarm clock with persistent storage.",
    )
    parser.add_argument(
        "--storage",
        type=Path,
        default=DEFAULT_STORAGE_PATH,
        help=f"Path to alarm JSON file (default: {DEFAULT_STORAGE_PATH})",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable debug logging",
    )

    subparsers = parser.add_subparsers(
        dest="command",
        title="commands",
        metavar="command",
        help="Available commands (run `alarm <command> --help` for details)",
    )

    add_parser = subparsers.add_parser("add", help="Add a new alarm")
    add_parser.add_argument("label", help="Alarm label")
    add_parser.add_argument("time", help="Alarm time in HH:MM (24-hour)")

    subparsers.add_parser("list", help="List all alarms")

    delete_parser = subparsers.add_parser("delete", help="Delete an alarm")
    delete_parser.add_argument("id", help="Alarm ID or prefix (from alarm list)")

    enable_parser = subparsers.add_parser("enable", help="Enable an alarm")
    enable_parser.add_argument("id", help="Alarm ID or prefix (from alarm list)")

    disable_parser = subparsers.add_parser("disable", help="Disable an alarm")
    disable_parser.add_argument("id", help="Alarm ID or prefix (from alarm list)")

    snooze_parser = subparsers.add_parser("snooze", help="Snooze an alarm")
    snooze_parser.add_argument("id", help="Alarm ID or prefix (from alarm list)")
    snooze_parser.add_argument(
        "--minutes",
        type=int,
        default=5,
        help="Snooze duration in minutes (default: 5)",
    )

    monitor_parser = subparsers.add_parser(
        "monitor",
        help="Run the alarm monitoring loop (Ctrl+C to stop)",
    )
    monitor_parser.add_argument(
        "--snooze-minutes",
        type=int,
        default=5,
        help="Default snooze duration when pressing 1 at alarm time (default: 5)",
    )

    return parser


def format_alarm_line(alarm) -> str:
    status = "enabled" if alarm.enabled else "disabled"
    extras: list[str] = []
    if alarm.snooze_until:
        extras.append(f"snoozed until {alarm.snooze_until}")
    suffix = f" [{', '.join(extras)}]" if extras else ""
    return f"{alarm.id[:8]}  {alarm.time}  {alarm.label} ({status}){suffix}"


def run_cli(args: argparse.Namespace) -> int:
    storage = AlarmStorage(args.storage)
    service = AlarmService(storage)

    try:
        if args.command == "add":
            alarm = service.add_alarm(args.label, args.time)
            print(f"Added alarm {alarm.id[:8]} at {alarm.time}: {alarm.label}")
            return 0

        if args.command == "list":
            alarms = service.list_alarms()
            if not alarms:
                print("No alarms configured.")
                return 0
            for alarm in alarms:
                print(format_alarm_line(alarm))
            return 0

        if args.command == "delete":
            removed = service.delete_alarm(args.id)
            print(f"Deleted alarm {removed.id[:8]}: {removed.label}")
            return 0

        if args.command == "enable":
            alarm = service.set_enabled(args.id, True)
            print(f"Enabled alarm {alarm.id[:8]}: {alarm.label}")
            return 0

        if args.command == "disable":
            alarm = service.set_enabled(args.id, False)
            print(f"Disabled alarm {alarm.id[:8]}: {alarm.label}")
            return 0

        if args.command == "snooze":
            alarm = service.snooze_alarm(args.id, datetime.now(), args.minutes)
            print(
                f"Snoozed alarm {alarm.id[:8]} until {alarm.snooze_until}"
            )
            return 0

        if args.command == "monitor":
            print("Monitoring alarms. Press Ctrl+C to stop.")
            monitor = AlarmMonitor(
                service,
                interactive=True,
                snooze_minutes=args.snooze_minutes,
            )
            try:
                monitor.run()
            except KeyboardInterrupt:
                print("\nMonitor stopped.")
            return 0

    except AlarmNotFoundError as exc:
        print(f"Error: alarm not found: {exc.args[0]}", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(f"Unknown command: {args.command}", file=sys.stderr)
    return 1


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    configure_logging(args.verbose)
    if args.command is None:
        parser.print_help()
        raise SystemExit(0)
    raise SystemExit(run_cli(args))


if __name__ == "__main__":
    main()
