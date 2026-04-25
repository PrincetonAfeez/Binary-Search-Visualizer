"""Terminal display and raw key input."""

from __future__ import annotations

import contextlib
import os
import sys
import time
from collections.abc import Iterator
from typing import TextIO

from .ansi import CLEAR_SCREEN, HIDE_CURSOR, SHOW_CURSOR, clear_line, move_to

if os.name == "nt":
    import msvcrt
else:  # pragma: no cover - exercised on Unix terminals
    import select
    import termios
    import tty


@contextlib.contextmanager
def raw_terminal() -> Iterator[None]:
    """Context manager for raw terminal input."""
    if os.name == "nt":
        yield
        return

    fd = sys.stdin.fileno()
    original = termios.tcgetattr(fd)  # type: ignore[attr-defined]
    try:
        tty.setcbreak(fd)  # type: ignore[attr-defined]
        yield
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, original)  # type: ignore[attr-defined]


def read_key(timeout: float) -> str | None:
    """Read a key from the terminal."""
    if os.name == "nt":
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if msvcrt.kbhit():
                char = msvcrt.getwch()
                if char in ("\x00", "\xe0"):
                    arrow = msvcrt.getwch()
                    return {"K": "left", "M": "right"}.get(arrow, arrow)
                if char == "\r":
                    return "enter"
                if char == " ":
                    return "space"
                return char
            time.sleep(0.01)
        return None

    readable, _, _ = select.select([sys.stdin], [], [], timeout)
    if not readable:
        return None
    char = sys.stdin.read(1)
    if char == "\x1b":
        rest = sys.stdin.read(2)
        if rest == "[D":
            return "left"
        if rest == "[C":
            return "right"
    if char == " ":
        return "space"
    return char


class Display:
    """Diff-based terminal redraw.

    Only changed lines are rewritten after the first frame. Non-TTY output falls
    back to plain printing so tests and pipes remain readable.
    """

    def __init__(self, stream: TextIO = sys.stdout) -> None:
        """Initialize the display."""
        self.stream = stream
        self._last_lines: list[str] = []

    def draw(self, text: str) -> None:
        """Draw the text on the display."""
        if not self.stream.isatty():
            print(text, file=self.stream)
            return
        lines = text.splitlines()
        if not self._last_lines:
            self.stream.write(HIDE_CURSOR + CLEAR_SCREEN + move_to(1, 1) + text)
        else:
            for index in range(max(len(lines), len(self._last_lines))):
                current = lines[index] if index < len(lines) else ""
                previous = self._last_lines[index] if index < len(self._last_lines) else ""
                if current != previous:
                    self.stream.write(move_to(index + 1, 1) + clear_line() + current)
        self.stream.flush()
        self._last_lines = lines

    def close(self) -> None:
        """Close the display."""
        if self.stream.isatty():
            self.stream.write(SHOW_CURSOR + "\n")
            self.stream.flush()
