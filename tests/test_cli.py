"""Tests for CLI argument handling and exit codes."""

from __future__ import annotations

from alarm_scheduler.cli import run_cli, build_parser


def test_bare_alarm_shows_help(capsys) -> None:
    parser = build_parser()
    args = parser.parse_args([])
    assert args.command is None

    from alarm_scheduler.cli import main
    import pytest

    with pytest.raises(SystemExit) as exc_info:
        main([])
    assert exc_info.value.code == 0
    output = capsys.readouterr().out
    assert "add" in output
    assert "list" in output
    assert "monitor" in output


def test_add_and_list_via_cli(storage_path, capsys) -> None:
    parser = build_parser()
    add_args = parser.parse_args(
        ["--storage", str(storage_path), "add", "Standup", "09:30"]
    )
    assert run_cli(add_args) == 0

    list_args = parser.parse_args(["--storage", str(storage_path), "list"])
    assert run_cli(list_args) == 0
    output = capsys.readouterr().out
    assert "09:30" in output
    assert "Standup" in output


def test_invalid_time_returns_error(storage_path, capsys) -> None:
    parser = build_parser()
    args = parser.parse_args(
        ["--storage", str(storage_path), "add", "Bad", "99:99"]
    )
    assert run_cli(args) == 1
    assert "Error" in capsys.readouterr().err


def test_delete_missing_alarm_returns_error(storage_path, capsys) -> None:
    parser = build_parser()
    args = parser.parse_args(
        ["--storage", str(storage_path), "delete", "does-not-exist"]
    )
    assert run_cli(args) == 1
    assert "not found" in capsys.readouterr().err
