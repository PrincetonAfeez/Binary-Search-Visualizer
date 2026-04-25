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
