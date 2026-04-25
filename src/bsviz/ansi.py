"""Small ANSI helper module."""

from __future__ import annotations

import os
from dataclasses import dataclass

RESET = "\033[0m"
CLEAR_SCREEN = "\033[2J"
HIDE_CURSOR = "\033[?25l"
SHOW_CURSOR = "\033[?25h"

COLOR_CODES = {
    "black": "30",
    "red": "31",
    "green": "32",
    "yellow": "33",
    "blue": "34",
    "magenta": "35",
    "cyan": "36",
    "white": "37",
    "gray": "90",
    "bright_red": "91",
    "bright_green": "92",
    "bright_yellow": "93",
    "bright_blue": "94",
    "bright_magenta": "95",
    "bright_cyan": "96",
}


@dataclass(frozen=True)
class ColorScheme:
    name: str
    low: str
    high: str
    mid: str
    found: str
    eliminated: str
    target: str
    text: str
    muted: str


SCHEMES: dict[str, ColorScheme] = {
    "classic": ColorScheme(
        name="classic",
        low="green",
        high="green",
        mid="yellow",
        found="bright_green",
        eliminated="gray",
        target="cyan",
        text="white",
        muted="gray",
    ),
    "monochrome": ColorScheme(
        name="monochrome",
        low="white",
        high="white",
        mid="white",
        found="white",
        eliminated="gray",
        target="white",
        text="white",
        muted="gray",
    ),
    "colorblind-safe": ColorScheme(
        name="colorblind-safe",
        low="blue",
        high="blue",
        mid="bright_yellow",
        found="bright_blue",
        eliminated="gray",
        target="magenta",
        text="white",
        muted="gray",
    ),
}


def should_color(no_color: bool = False) -> bool:
    return not no_color and "NO_COLOR" not in os.environ


def colorize(text: str, color: str, enabled: bool) -> str:
    if not enabled:
        return text
    code = COLOR_CODES.get(color)
    if code is None:
        return text
    return f"\033[{code}m{text}{RESET}"


def move_to(row: int, column: int) -> str:
    return f"\033[{row};{column}H"


def clear_line() -> str:
    return "\033[2K"

