"""Step controller that wraps any state generator and adds replay/backtracking."""

from __future__ import annotations

from collections.abc import Callable, Iterator

from .exceptions import NoStepsAvailableError
from .models import SearchResult, SearchState


class StepController:
    """Interactive controller over a forward-only state iterator.

    Backtracking is intentionally implemented by caching states. For binary search
    this costs only O(log n) states, even for very large arrays.
    """

    def __init__(self, state_factory: Callable[[], Iterator[SearchState]]) -> None:
        self._state_factory = state_factory
        self.reset()

    @classmethod
    def from_states(cls, states: list[SearchState] | tuple[SearchState, ...]) -> StepController:
        snapshot = tuple(states)
        return cls(lambda: iter(snapshot))

    def reset(self) -> None:
        self._iterator = self._state_factory()
        self._cache: list[SearchState] = []
        self._index = -1
        self._exhausted = False

    @property
    def index(self) -> int:
        return self._index

    @property
    def states(self) -> tuple[SearchState, ...]:
        return tuple(self._cache)

    @property
    def current(self) -> SearchState | None:
        if self._index < 0:
            return None
        return self._cache[self._index]

    def _advance_cache(self) -> SearchState:
        if self._exhausted:
            raise NoStepsAvailableError("no more steps are available")
        try:
            state = next(self._iterator)
        except StopIteration as exc:
            self._exhausted = True
            raise NoStepsAvailableError("no more steps are available") from exc
        self._cache.append(state)
        return state

    def next(self) -> SearchState:
        if self._index + 1 < len(self._cache):
            self._index += 1
            return self._cache[self._index]
        state = self._advance_cache()
        self._index += 1
        return state

    def back(self) -> SearchState:
        if self._index <= 0:
            raise NoStepsAvailableError("already at the first step")
        self._index -= 1
        return self._cache[self._index]

    def jump_to(self, step_number: int) -> SearchState:
        if step_number < 0:
            raise NoStepsAvailableError("step number must be non-negative")
        while len(self._cache) <= step_number:
            self._advance_cache()
        self._index = step_number
        return self._cache[self._index]

    def run_to_end(self) -> SearchState:
        while not self._exhausted:
            try:
                self._advance_cache()
            except NoStepsAvailableError:
                break
        if not self._cache:
            raise NoStepsAvailableError("no states were produced")
        self._index = len(self._cache) - 1
        return self._cache[self._index]

    def summary(self) -> SearchResult:
        self.run_to_end()
        return SearchResult.from_states(self._cache)

