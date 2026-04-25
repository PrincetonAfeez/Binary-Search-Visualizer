"""Pure renderers: state in, string out."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable

from .ansi import ColorScheme, SCHEMES, colorize
from .models import ComparisonEvent, ComparisonResult, SearchOutcome, SearchState


class Renderer(ABC):
    """Renderer ABC."""
    @abstractmethod
    def render(self, state: SearchState) -> str:
        """Return a display string for a state."""


class BaseRenderer(Renderer):
    def __init__(self, scheme: ColorScheme | None = None, use_color: bool = True) -> None:
        """Initialize a base renderer."""
        self.scheme = scheme or SCHEMES["classic"]
        self.use_color = use_color

    def _paint(self, text: str, role: str) -> str:
        """Paint a text with a color."""
        color = getattr(self.scheme, role)
        return colorize(text, color, self.use_color)


class MinimalRenderer(Renderer):
    def render(self, state: SearchState) -> str:
        """Render the minimal for a search state."""
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
        """Role for an index."""
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


class TableRenderer(BaseRenderer):
    def render(self, state: SearchState) -> str:
        """Render the table for a search state."""
        values = [repr(value) for value in state.array]
        widths = [
            max(len(str(index)), len(value), 3) for index, value in enumerate(values)
        ]
        divider = "+" + "+".join("-" * (width + 2) for width in widths) + "+"
        index_row = "|" + "|".join(
            f" {self._paint(str(index).center(width), 'muted')} "
            for index, width in enumerate(widths)
        ) + "|"
        value_row = "|" + "|".join(
            f" {self._paint(values[index].center(width), self._role_for_index(state, index))} "
            for index, width in enumerate(widths)
        ) + "|"
        marker_row = "|" + "|".join(
            f" {self._marker_for_index(state, index).center(width)} "
            for index, width in enumerate(widths)
        ) + "|"
        return "\n".join([divider, index_row, divider, value_row, divider, marker_row, divider])

    def _role_for_index(self, state: SearchState, index: int) -> str:
        """Role for an index."""
        if state.result_index == index and state.outcome is not SearchOutcome.IN_PROGRESS:
            return "found"
        if state.mid == index:
            return "mid"
        if index < state.low or index > state.high:
            return "eliminated"
        if index == state.low or index == state.high:
            return "low"
        return "text"

    def _marker_for_index(self, state: SearchState, index: int) -> str:
        """Marker for an index."""
        markers: list[str] = []
        if index == state.low:
            markers.append("L")
        if index == state.mid:
            markers.append("M")
        if index == state.high:
            markers.append("H")
        if state.result_index == index:
            markers.append("R")
        return "/".join(markers)


class TreeRenderer(BaseRenderer):
    def render(self, state: SearchState) -> str:
        """Render the tree for a search state."""
        lines = ["search path"]
        if not state.history:
            lines.append("(no comparisons yet)")
        for event in state.history:
            current = event.step == state.step and state.mid == event.mid
            prefix = "=> " if current else "   "
            indent = "  " * event.step
            symbol = _comparison_symbol(event.comparison)
            text = (
                f"{prefix}{indent}idx {event.mid}: {event.value!r} "
                f"{symbol} {state.target!r}  window=[{event.low}, {event.high}]"
            )
            lines.append(self._paint(text, "mid" if current else "text"))
        if state.is_terminal:
            lines.append(self._paint(_terminal_line(state), "found" if state.result_index is not None else "muted"))
        return "\n".join(lines)


class VariablesRenderer(BaseRenderer):
    def render(self, state: SearchState) -> str:
        """Render the variables for a search state."""
        mid = "-" if state.mid is None else state.mid
        value = "-" if state.mid_value is None else repr(state.mid_value)
        result = "-" if state.result_index is None else state.result_index
        return "\n".join(
            [
                f"variant:     {state.variant.value}",
                f"target:      {state.target!r}",
                f"low/mid/high:{state.low}/{mid}/{state.high}",
                f"mid value:   {value}",
                f"comparison:  {state.comparison.value}",
                f"outcome:     {state.outcome.value}",
                f"result:      {result}",
                f"comparisons: {state.comparisons}",
                f"elapsed:     {state.elapsed_ms:.3f} ms",
            ]
        )


class LogRenderer(BaseRenderer):
    def render(self, state: SearchState) -> str:
        """Render a log of recent comparison events."""
        recent = state.history[-5:]
        if not recent and not state.note:
            return ""
        lines = ["log"]
        for event in recent:
            lines.append(_event_line(event, state.target))
        if state.note:
            lines.append(self._paint(state.note, "muted"))
        return "\n".join(lines)


class CompositeRenderer(BaseRenderer):
    def __init__(self, main: Renderer, scheme: ColorScheme | None = None, use_color: bool = True) -> None:
        """Initialize a composite renderer."""
        super().__init__(scheme, use_color)
        self.main = main
        self.variables = VariablesRenderer(scheme, use_color)
        self.log = LogRenderer(scheme, use_color)

    def render(self, state: SearchState) -> str:
        """Render a composite of the main and variables renderers."""
        top = _side_by_side(self.main.render(state), self.variables.render(state))
        log = self.log.render(state)
        return top if not log else f"{top}\n\n{log}"


def renderer_for(name: str, scheme: ColorScheme | None = None, use_color: bool = True) -> Renderer:
    """Create a renderer for a given name."""
    normalized = name.strip().lower()
    if normalized == "minimal":
        return MinimalRenderer()
    main: Renderer
    if normalized == "bar":
        main = BarRenderer(scheme, use_color)
    elif normalized == "table":
        main = TableRenderer(scheme, use_color)
    elif normalized == "tree":
        main = TreeRenderer(scheme, use_color)
    else:
        valid = "bar, table, tree, minimal"
        raise ValueError(f"unknown renderer {name!r}; choose one of: {valid}")
    return CompositeRenderer(main, scheme, use_color)


def available_renderers() -> tuple[str, ...]:
    """Available renderers."""
    return ("bar", "table", "tree", "minimal")


def render_states(states: Iterable[SearchState], renderer: Renderer) -> str:
    """Render a sequence of search states."""
    frames = []
    for state in states:
        frames.append(renderer.render(state))
    return "\n\n".join(frames)


def _plain_cell(index: int, value: object) -> str:
    """Plain cell for a value."""
    return f"[{index}:{value!r}]"


def _comparison_symbol(comparison: ComparisonResult) -> str:
    """Comparison symbol for a comparison result."""
    if comparison is ComparisonResult.LESS:
        return "<"
    if comparison is ComparisonResult.GREATER:
        return ">"
    if comparison is ComparisonResult.EQUAL:
        return "=="
    return "?"


def _event_line(event: ComparisonEvent, target: object) -> str:
    """Event line for a comparison event."""
    return (
        f"step {event.step}: idx {event.mid}, value {event.value!r} "
        f"{_comparison_symbol(event.comparison)} {target!r}"
    )


def _terminal_line(state: SearchState) -> str:
    """Terminal line for a search state."""
    if state.result_index is None:
        return f"terminal: {state.outcome.value}"
    return f"terminal: {state.outcome.value} at index {state.result_index}"


def _side_by_side(left: str, right: str, gap: int = 4) -> str:
    """Side-by-side layout of two strings."""
    left_lines = left.splitlines() or [""]
    right_lines = right.splitlines() or [""]
    width = max(len(_strip_ansi(line)) for line in left_lines)
    rows = max(len(left_lines), len(right_lines))
    output: list[str] = []
    for row in range(rows):
        left_line = left_lines[row] if row < len(left_lines) else ""
        right_line = right_lines[row] if row < len(right_lines) else ""
        padding = " " * (width - len(_strip_ansi(left_line)) + gap)
        output.append(f"{left_line}{padding}{right_line}")
    return "\n".join(output)


def _strip_ansi(value: str) -> str:
    """Strip ANSI escape codes from a string."""
    result: list[str] = []
    index = 0
    while index < len(value):
        if value[index] == "\033":
            index += 1
            while index < len(value) and value[index] != "m":
                index += 1
        else:
            result.append(value[index])
        index += 1
    return "".join(result)

