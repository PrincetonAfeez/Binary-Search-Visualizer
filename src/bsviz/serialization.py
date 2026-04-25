"""JSON replay and frame export."""

from __future__ import annotations

import json
from pathlib import Path

from .models import SearchState
from .renderers import Renderer


def dump_states(states: list[SearchState] | tuple[SearchState, ...], path: Path) -> None:
    payload = "\n".join(json.dumps(state.to_json(), sort_keys=True) for state in states)
    path.write_text(payload + ("\n" if payload else ""), encoding="utf-8")


def load_states(path: Path) -> list[SearchState]:
    raw = path.read_text(encoding="utf-8").strip()
    if not raw:
        return []
    if raw.startswith("["):
        payload = json.loads(raw)
        return [SearchState.from_json(item) for item in payload]
    return [SearchState.from_json(json.loads(line)) for line in raw.splitlines() if line.strip()]


def export_frames(
    states: list[SearchState] | tuple[SearchState, ...],
    renderer: Renderer,
    directory: Path,
) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    for index, state in enumerate(states, start=1):
        path = directory / f"step_{index:03d}.txt"
        path.write_text(renderer.render(state) + "\n", encoding="utf-8")

