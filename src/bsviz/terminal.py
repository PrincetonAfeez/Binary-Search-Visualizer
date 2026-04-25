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

