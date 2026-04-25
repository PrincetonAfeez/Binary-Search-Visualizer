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

