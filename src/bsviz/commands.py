"""Keyboard command registry for interactive mode."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StepCommand:
    key: str
    name: str
    description: str


COMMANDS: tuple[StepCommand, ...] = (
    StepCommand("space/right", "next", "advance one step"),
    StepCommand("left", "previous", "go back one cached step"),
    StepCommand("r", "reset", "restart the current search"),
    StepCommand("g", "end", "run to the terminal state"),
    StepCommand("j", "jump", "jump to a step number"),
    StepCommand("a", "auto", "toggle auto-advance"),
    StepCommand("+/-", "speed", "adjust auto-advance speed"),
    StepCommand("v", "variant", "cycle search variant"),
    StepCommand("t", "target", "enter a new target"),
    StepCommand("m", "renderer", "cycle renderer"),
    StepCommand("c", "colors", "cycle color scheme"),
    StepCommand("?", "help", "show or hide this help"),
    StepCommand("q", "quit", "quit"),
)


def help_text() -> str:
    width = max(len(command.key) for command in COMMANDS)
    lines = ["keys"]
    for command in COMMANDS:
        lines.append(f"  {command.key.ljust(width)}  {command.description}")
    return "\n".join(lines)

