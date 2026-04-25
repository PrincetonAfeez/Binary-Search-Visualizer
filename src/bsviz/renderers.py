from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable

from .ansi import ColorScheme, SCHEMES, colorize
from .models import ComparisonEvent, ComparisonResult, SearchOutcome, SearchState


class Renderer(ABC):
    @abstractmethod
    def render(self, state: SearchState) -> str:
        """Return a display string for a state."""

class BaseRenderer(Renderer):
    def __init__(self, scheme: ColorScheme | None = None, use_color: bool = True) -> None:
        self.scheme = scheme or SCHEMES["classic"]
        self.use_color = use_color

    def _paint(self, text: str, role: str) -> str:
        color = getattr(self.scheme, role)
        return colorize(text, color, self.use_color)

class MinimalRenderer(Renderer):
    def render(self, state: SearchState) -> str:
        mid = "-" if state.mid is None else str(state.mid)
        value = "-" if state.mid_value is None else repr(state.mid_value)
        result = "-" if state.result_index is None else str(state.result_index)
        return (
            f"step={state.step} variant={state.variant.value} low={state.low} "
            f"mid={mid} high={state.high} value={value} target={state.target!r} "
            f"comparison={state.comparison.value} outcome={state.outcome.value} "
            f"result={result} comparisons={state.comparisons}"
        )

class BarRenderer(BaseRenderer):
    def render(self, state: SearchState) -> str:
        """Render the bar for a search state."""
        cells: list[str] = []
        for index, value in enumerate(state.array):
            label = f"{index}:{value!r}"
            role = self._role_for_index(state, index)
            cells.append(self._paint(f"[{label}]", role))
        pointer = [" " * len(_plain_cell(index, value)) for index, value in enumerate(state.array)]
        if state.mid is not None:
            pointer[state.mid] = " " * max(0, len(pointer[state.mid]) // 2) + "^"
        return " ".join(cells) + "\n" + " ".join(pointer)

    def _role_for_index(self, state: SearchState, index: int) -> str:
        if state.result_index == index and state.outcome is not SearchOutcome.IN_PROGRESS:
            return "found"
        if state.mid == index:
            return "mid"
        if index == state.low or index == state.high:
            return "low"
        if index < state.low or index > state.high:
            return "eliminated"
        if state.array[index] == state.target:
            return "target"
        return "text"
