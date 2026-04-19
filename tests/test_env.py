"""Tests for ``sre_agent.cli.env`` round-tripping."""

from pathlib import Path

import pytest

from sre_agent.cli.env import read_env_file, write_env_file


@pytest.mark.parametrize(
    "value",
    [
        "plain",
        "with spaces",
        '"starts with quote',
        'ends with quote"',
        '"quoted"',
        "a=b=c",
        "line1\nline2",
        "   ",
        "back\\slash",
        "# starts with hash",
        'has "inner" quotes',
        "mix \"of\\weird' chars",
    ],
)
def test_env_roundtrip(tmp_path: Path, value: str) -> None:
    """Writing a value and reading it back returns the same value."""
    env_file = tmp_path / ".env"
    write_env_file(env_file, {"MY_KEY": value})
    parsed = read_env_file(env_file)
    assert parsed["MY_KEY"] == value


def test_env_roundtrip_is_idempotent(tmp_path: Path) -> None:
    """Re-writing an already-stored value must not mutate it."""
    env_file = tmp_path / ".env"
    value = '"quoted"'
    write_env_file(env_file, {"API_KEY": value})
    first = read_env_file(env_file)["API_KEY"]
    # Simulate the wizard running again — re-persist the previously read value.
    write_env_file(env_file, {"API_KEY": first})
    second = read_env_file(env_file)["API_KEY"]
    assert first == value
    assert second == value


def test_env_preserves_other_keys(tmp_path: Path) -> None:
    """Updating one key must not disturb others."""
    env_file = tmp_path / ".env"
    write_env_file(env_file, {"KEEP": "keep-value", "UPDATE": "v1"})
    write_env_file(env_file, {"UPDATE": "v2"})
    parsed = read_env_file(env_file)
    assert parsed == {"KEEP": "keep-value", "UPDATE": "v2"}


def test_env_removes_empty_values(tmp_path: Path) -> None:
    """Empty updates clear the corresponding key."""
    env_file = tmp_path / ".env"
    write_env_file(env_file, {"DELETE_ME": "value"})
    write_env_file(env_file, {"DELETE_ME": ""})
    parsed = read_env_file(env_file)
    assert "DELETE_ME" not in parsed


def test_env_reads_legacy_single_quoted(tmp_path: Path) -> None:
    """Legacy files written with single-quoted values still parse cleanly."""
    env_file = tmp_path / ".env"
    env_file.write_text("TOKEN='value with space'\n")
    assert read_env_file(env_file) == {"TOKEN": "value with space"}
