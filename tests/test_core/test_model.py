import pytest

from sre_agent.core.models import LogEntry


def test_log_entry_valid_creation():
    entry = LogEntry(
        timestamp="2026-01-01T00:00:00Z",
        message="Service started",
        log_stream="my-log-stream",
    )

    assert entry.timestamp == "2026-01-01T00:00:00Z"
    assert entry.message == "Service started"
    assert entry.log_stream == "my-log-stream"
