"""Tests for CLI and env argument parsing in sre_agent.run."""

import pytest

from sre_agent.run import _load_request_from_args_or_env, _parse_time_range_minutes


def test_parse_time_range_minutes_valid() -> None:
    """Valid integer strings are parsed."""
    assert _parse_time_range_minutes("15") == 15


def test_parse_time_range_minutes_non_integer_exits(capsys: pytest.CaptureFixture[str]) -> None:
    """Non integer input exits with a friendly message rather than crashing."""
    with pytest.raises(SystemExit) as excinfo:
        _parse_time_range_minutes("abc")
    assert excinfo.value.code == 1
    assert "must be an integer" in capsys.readouterr().out


@pytest.mark.parametrize("raw", ["0", "-5"])
def test_parse_time_range_minutes_non_positive_exits(
    raw: str, capsys: pytest.CaptureFixture[str]
) -> None:
    """Zero and negative values are rejected."""
    with pytest.raises(SystemExit) as excinfo:
        _parse_time_range_minutes(raw)
    assert excinfo.value.code == 1
    assert "greater than 0" in capsys.readouterr().out


def test_cli_args_invalid_time_range_exits(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Bad CLI third argument exits cleanly instead of raising ValueError."""
    monkeypatch.setattr("sys.argv", ["run.py", "log-group", "service", "abc"])
    with pytest.raises(SystemExit) as excinfo:
        _load_request_from_args_or_env()
    assert excinfo.value.code == 1
    assert "must be an integer" in capsys.readouterr().out


def test_cli_args_non_positive_time_range_exits(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A zero or negative CLI third argument is rejected."""
    monkeypatch.setattr("sys.argv", ["run.py", "log-group", "service", "0"])
    with pytest.raises(SystemExit) as excinfo:
        _load_request_from_args_or_env()
    assert excinfo.value.code == 1
    assert "greater than 0" in capsys.readouterr().out


def test_cli_args_valid() -> None:
    """Valid CLI args parse as expected."""
    import sys

    original = sys.argv
    try:
        sys.argv = ["run.py", "log-group", "service", "42"]
        assert _load_request_from_args_or_env() == ("log-group", "service", 42)
    finally:
        sys.argv = original
