"""User env file helpers for the CLI."""

import os
import re
from pathlib import Path

from sre_agent.config.paths import env_path

# Characters that require a value to be quoted when serialised.
_SHELL_SPECIAL = re.compile(r"[\s\"'\\#]")


def load_env_values() -> dict[str, str]:
    """Load env file values and overlay environment variables.

    Returns:
        Combined env file and environment variable values.
    """
    values = read_env_file(env_path())
    for key, value in os.environ.items():
        if value:
            values[key] = value
    return values


def read_env_file(path: Path) -> dict[str, str]:
    """Read simple key/value pairs from an env file.

    Args:
        path: Path to the env file.

    Returns:
        Parsed key/value pairs.
    """
    if not path.exists():
        return {}

    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = _unescape_env_value(value.strip())
    return values


def write_env_file(path: Path, updates: dict[str, str]) -> None:
    """Write updates to the env file.

    Args:
        path: Path to the env file.
        updates: Values to write into the file.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    current = read_env_file(path)
    for key, value in updates.items():
        if value:
            current[key] = value
        elif key in current:
            current.pop(key, None)

    lines = []
    for key, value in current.items():
        safe_value = _escape_env_value(value)
        lines.append(f"{key}={safe_value}")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _escape_env_value(value: str) -> str:
    """Escape a value for env output.

    Wraps the value in double quotes when it contains whitespace, quote
    characters, a leading ``#``, or backslashes, and escapes embedded double
    quotes and backslashes so the value survives a round-trip through
    :func:`read_env_file`.

    Args:
        value: Value to escape.

    Returns:
        The escaped value.
    """
    if not _SHELL_SPECIAL.search(value):
        return value
    escaped = (
        value.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\r", "\\r")
        .replace("\t", "\\t")
    )
    return f'"{escaped}"'


def _unescape_env_value(value: str) -> str:
    """Reverse of :func:`_escape_env_value`.

    Handles values that were written either by the current escaping scheme
    or by the legacy scheme that only stripped outer quotes. Returns the
    value as-is when it is not wrapped in matching quotes, so unquoted
    values that happen to contain a leading or trailing quote character
    are preserved.

    Args:
        value: Raw value read from an env file (already stripped of
            surrounding whitespace).

    Returns:
        The decoded value.
    """
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
        inner = value[1:-1]
        if value[0] == '"':
            return _decode_double_quoted(inner)
        return inner
    return value


_ESCAPE_MAP = {
    '"': '"',
    "\\": "\\",
    "n": "\n",
    "r": "\r",
    "t": "\t",
}


def _decode_double_quoted(inner: str) -> str:
    r"""Decode the body of a double-quoted env value in a single pass.

    Recognises ``\\``, ``\"``, ``\n``, ``\r``, and ``\t`` escape sequences.
    An unknown escape (e.g. ``\z``) is preserved verbatim, matching the
    behaviour of common ``.env`` parsers.

    Args:
        inner: The characters between the surrounding double quotes.

    Returns:
        The decoded string.
    """
    out: list[str] = []
    i = 0
    length = len(inner)
    while i < length:
        ch = inner[i]
        if ch == "\\" and i + 1 < length:
            nxt = inner[i + 1]
            out.append(_ESCAPE_MAP.get(nxt, ch + nxt))
            i += 2
            continue
        out.append(ch)
        i += 1
    return "".join(out)
