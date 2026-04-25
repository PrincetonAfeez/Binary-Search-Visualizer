from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable

from .ansi import ColorScheme, SCHEMES, colorize
from .models import ComparisonEvent, ComparisonResult, SearchOutcome, SearchState


class Renderer(ABC):
    @abstractmethod
    def render(self, state: SearchState) -> str:
        """Return a display string for a state."""
