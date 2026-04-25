"""Binary search variants implemented as pure generator state machines."""

from __future__ import annotations

import math
import time
from collections.abc import Iterator, Sequence
from typing import Protocol

from .exceptions import InvalidArrayError, InvalidVariantError, UnsortedArrayError
from .models import ComparisonEvent, ComparisonResult, Number, SearchOutcome, SearchState, Variant


class BinarySearch(Protocol):
    """Search strategy interface."""

    variant: Variant

    def search(self, array: Sequence[Number], target: Number) -> Iterator[SearchState]:
        """Yield immutable search states until a terminal state is reached."""


def normalize_variant(raw: str | Variant) -> Variant:
    if isinstance(raw, Variant):
        return raw
    aliases = {
        "lower": Variant.LOWER_BOUND,
        "lower-bound": Variant.LOWER_BOUND,
        "upper": Variant.UPPER_BOUND,
        "upper-bound": Variant.UPPER_BOUND,
    }
    normalized = raw.strip().lower().replace("-", "_")
    try:
        return aliases.get(normalized, Variant(normalized))
    except ValueError as exc:
        valid = ", ".join(variant.value for variant in Variant)
        raise InvalidVariantError(f"unknown variant {raw!r}; choose one of: {valid}") from exc


def validate_search_input(array: Sequence[Number], target: Number) -> tuple[Number, ...]:
    values = tuple(array)
    if not values:
        raise InvalidArrayError("array must contain at least one number")

    first_type = type(values[0])
    if first_type not in (int, float):
        raise InvalidArrayError("array values must be all ints or all floats")
    if type(target) is not first_type:
        raise InvalidArrayError(
            f"target must be a {first_type.__name__} because the array contains "
            f"{first_type.__name__} values"
        )

    for index, value in enumerate(values):
        if type(value) is not first_type:
            raise InvalidArrayError("array values must not mix ints and floats")
        if isinstance(value, float) and not math.isfinite(value):
            raise InvalidArrayError("array values must be finite")
        if index > 0 and values[index - 1] > value:
            raise UnsortedArrayError(index, values[index - 1], value)

    if isinstance(target, float) and not math.isfinite(target):
        raise InvalidArrayError("target must be finite")

    return values


def compare_values(value: Number, target: Number) -> ComparisonResult:
    if value < target:
        return ComparisonResult.LESS
    if value > target:
        return ComparisonResult.GREATER
    return ComparisonResult.EQUAL


def make_step(
    *,
    array: tuple[Number, ...],
    low: int,
    high: int,
    mid: int | None,
    target: Number,
    comparison: ComparisonResult,
    step: int,
    comparisons: int,
    outcome: SearchOutcome,
    variant: Variant,
    result_index: int | None,
    elapsed_ms: float,
    note: str,
    history: tuple[ComparisonEvent, ...],
) -> SearchState:
    if mid is None:
        next_history = history
    else:
        event = ComparisonEvent(
            step=step,
            low=low,
            high=high,
            mid=mid,
            value=array[mid],
            comparison=comparison,
        )
        next_history = (*history, event)

    return SearchState(
        array=array,
        low=low,
        high=high,
        mid=mid,
        target=target,
        comparison=comparison,
        step=step,
        comparisons=comparisons,
        outcome=outcome,
        variant=variant,
        result_index=result_index,
        elapsed_ms=elapsed_ms,
        note=note,
        history=next_history,
    )


def _elapsed(start: float) -> float:
    return (time.perf_counter() - start) * 1000.0


def _comparison_note(mid: int, value: Number, target: Number, comparison: ComparisonResult) -> str:
    if comparison is ComparisonResult.LESS:
        return f"mid={mid}, value {value!r} is less than {target!r}; discard the left half."
    if comparison is ComparisonResult.GREATER:
        return f"mid={mid}, value {value!r} is greater than {target!r}; discard the right half."
    return f"mid={mid}, value {value!r} equals {target!r}."


class ClassicBinarySearch:
    variant = Variant.CLASSIC

    def search(self, array: Sequence[Number], target: Number) -> Iterator[SearchState]:
        values = validate_search_input(array, target)
        low = 0
        high = len(values) - 1
        comparisons = 0
        step = 0
        history: tuple[ComparisonEvent, ...] = ()
        start = time.perf_counter()

        while low <= high:
            mid = (low + high) // 2
            comparison = compare_values(values[mid], target)
            comparisons += 1
            outcome = (
                SearchOutcome.FOUND
                if comparison is ComparisonResult.EQUAL
                else SearchOutcome.IN_PROGRESS
            )
            note = _comparison_note(mid, values[mid], target, comparison)
            state = make_step(
                array=values,
                low=low,
                high=high,
                mid=mid,
                target=target,
                comparison=comparison,
                step=step,
                comparisons=comparisons,
                outcome=outcome,
                variant=self.variant,
                result_index=mid if outcome is SearchOutcome.FOUND else None,
                elapsed_ms=_elapsed(start),
                note=note,
                history=history,
            )
            history = state.history
            yield state

            if comparison is ComparisonResult.EQUAL:
                return
            if comparison is ComparisonResult.LESS:
                low = mid + 1
            else:
                high = mid - 1
            step += 1

        yield make_step(
            array=values,
            low=low,
            high=high,
            mid=None,
            target=target,
            comparison=ComparisonResult.NOT_APPLICABLE,
            step=step,
            comparisons=comparisons,
            outcome=SearchOutcome.NOT_FOUND,
            variant=self.variant,
            result_index=None,
            elapsed_ms=_elapsed(start),
            note=f"{target!r} is not present; the search window is empty.",
            history=history,
        )


class LeftmostBinarySearch:
    variant = Variant.LEFTMOST

    def search(self, array: Sequence[Number], target: Number) -> Iterator[SearchState]:
        values = validate_search_input(array, target)
        low = 0
        high = len(values) - 1
        comparisons = 0
        step = 0
        candidate: int | None = None
        history: tuple[ComparisonEvent, ...] = ()
        start = time.perf_counter()

        while low <= high:
            mid = (low + high) // 2
            comparison = compare_values(values[mid], target)
            comparisons += 1
            if comparison is ComparisonResult.EQUAL:
                candidate = mid
                note = (
                    f"mid={mid} matches; keep searching left for the first occurrence."
                )
            else:
                note = _comparison_note(mid, values[mid], target, comparison)

            state = make_step(
                array=values,
                low=low,
                high=high,
                mid=mid,
                target=target,
                comparison=comparison,
                step=step,
                comparisons=comparisons,
                outcome=SearchOutcome.IN_PROGRESS,
                variant=self.variant,
                result_index=candidate,
                elapsed_ms=_elapsed(start),
                note=note,
                history=history,
            )
            history = state.history
            yield state

            if comparison is ComparisonResult.LESS:
                low = mid + 1
            else:
                high = mid - 1
            step += 1

        outcome = SearchOutcome.FOUND if candidate is not None else SearchOutcome.NOT_FOUND
        yield make_step(
            array=values,
            low=low,
            high=high,
            mid=None,
            target=target,
            comparison=ComparisonResult.NOT_APPLICABLE,
            step=step,
            comparisons=comparisons,
            outcome=outcome,
            variant=self.variant,
            result_index=candidate,
            elapsed_ms=_elapsed(start),
            note=(
                f"first occurrence is index {candidate}."
                if candidate is not None
                else f"{target!r} is not present."
            ),
            history=history,
        )


class RightmostBinarySearch:
    variant = Variant.RIGHTMOST

    def search(self, array: Sequence[Number], target: Number) -> Iterator[SearchState]:
        values = validate_search_input(array, target)
        low = 0
        high = len(values) - 1
        comparisons = 0
        step = 0
        candidate: int | None = None
        history: tuple[ComparisonEvent, ...] = ()
        start = time.perf_counter()

        while low <= high:
            mid = (low + high) // 2
            comparison = compare_values(values[mid], target)
            comparisons += 1
            if comparison is ComparisonResult.EQUAL:
                candidate = mid
                note = (
                    f"mid={mid} matches; keep searching right for the last occurrence."
                )
            else:
                note = _comparison_note(mid, values[mid], target, comparison)

            state = make_step(
                array=values,
                low=low,
                high=high,
                mid=mid,
                target=target,
                comparison=comparison,
                step=step,
                comparisons=comparisons,
                outcome=SearchOutcome.IN_PROGRESS,
                variant=self.variant,
                result_index=candidate,
                elapsed_ms=_elapsed(start),
                note=note,
                history=history,
            )
            history = state.history
            yield state

            if comparison is ComparisonResult.GREATER:
                high = mid - 1
            else:
                low = mid + 1
            step += 1

        outcome = SearchOutcome.FOUND if candidate is not None else SearchOutcome.NOT_FOUND
        yield make_step(
            array=values,
            low=low,
            high=high,
            mid=None,
            target=target,
            comparison=ComparisonResult.NOT_APPLICABLE,
            step=step,
            comparisons=comparisons,
            outcome=outcome,
            variant=self.variant,
            result_index=candidate,
            elapsed_ms=_elapsed(start),
            note=(
                f"last occurrence is index {candidate}."
                if candidate is not None
                else f"{target!r} is not present."
            ),
            history=history,
        )


class LowerBoundSearch:
    variant = Variant.LOWER_BOUND

    def search(self, array: Sequence[Number], target: Number) -> Iterator[SearchState]:
        values = validate_search_input(array, target)
        low = 0
        high = len(values) - 1
        comparisons = 0
        step = 0
        candidate = len(values)
        history: tuple[ComparisonEvent, ...] = ()
        start = time.perf_counter()

        while low <= high:
            state_low = low
            state_high = high
            mid = (low + high) // 2
            comparison = compare_values(values[mid], target)
            comparisons += 1
            if comparison in (ComparisonResult.EQUAL, ComparisonResult.GREATER):
                candidate = mid
                note = f"index {mid} can be the lower bound; search left for an earlier one."
                high = mid - 1
            else:
                note = f"value {values[mid]!r} is less than {target!r}; lower bound is to the right."
                low = mid + 1

            state = make_step(
                array=values,
                low=state_low,
                high=state_high,
                mid=mid,
                target=target,
                comparison=comparison,
                step=step,
                comparisons=comparisons,
                outcome=SearchOutcome.IN_PROGRESS,
                variant=self.variant,
                result_index=candidate if candidate < len(values) else None,
                elapsed_ms=_elapsed(start),
                note=note,
                history=history,
            )
            history = state.history
            yield state
            step += 1

        outcome = SearchOutcome.FOUND if candidate < len(values) else SearchOutcome.NOT_FOUND
        yield make_step(
            array=values,
            low=low,
            high=high,
            mid=None,
            target=target,
            comparison=ComparisonResult.NOT_APPLICABLE,
            step=step,
            comparisons=comparisons,
            outcome=outcome,
            variant=self.variant,
            result_index=candidate,
            elapsed_ms=_elapsed(start),
            note=(
                f"lower bound is index {candidate}."
                if candidate < len(values)
                else f"lower bound is the insertion point {candidate} after the array."
            ),
            history=history,
        )


class UpperBoundSearch:
    variant = Variant.UPPER_BOUND

    def search(self, array: Sequence[Number], target: Number) -> Iterator[SearchState]:
        values = validate_search_input(array, target)
        low = 0
        high = len(values) - 1
        comparisons = 0
        step = 0
        candidate = len(values)
        history: tuple[ComparisonEvent, ...] = ()
        start = time.perf_counter()

        while low <= high:
            state_low = low
            state_high = high
            mid = (low + high) // 2
            comparison = compare_values(values[mid], target)
            comparisons += 1
            if comparison is ComparisonResult.GREATER:
                candidate = mid
                note = f"index {mid} can be the upper bound; search left for an earlier one."
                high = mid - 1
            else:
                note = (
                    f"value {values[mid]!r} is not greater than {target!r}; "
                    "upper bound is to the right."
                )
                low = mid + 1

            state = make_step(
                array=values,
                low=state_low,
                high=state_high,
                mid=mid,
                target=target,
                comparison=comparison,
                step=step,
                comparisons=comparisons,
                outcome=SearchOutcome.IN_PROGRESS,
                variant=self.variant,
                result_index=candidate if candidate < len(values) else None,
                elapsed_ms=_elapsed(start),
                note=note,
                history=history,
            )
            history = state.history
            yield state
            step += 1

        outcome = SearchOutcome.FOUND if candidate < len(values) else SearchOutcome.NOT_FOUND
        yield make_step(
            array=values,
            low=low,
            high=high,
            mid=None,
            target=target,
            comparison=ComparisonResult.NOT_APPLICABLE,
            step=step,
            comparisons=comparisons,
            outcome=outcome,
            variant=self.variant,
            result_index=candidate,
            elapsed_ms=_elapsed(start),
            note=(
                f"upper bound is index {candidate}."
                if candidate < len(values)
                else f"upper bound is the insertion point {candidate} after the array."
            ),
            history=history,
        )


class SearchRegistry:
    """Registry for strategy selection."""

    _searches: dict[Variant, BinarySearch] = {
        Variant.CLASSIC: ClassicBinarySearch(),
        Variant.LEFTMOST: LeftmostBinarySearch(),
        Variant.RIGHTMOST: RightmostBinarySearch(),
        Variant.LOWER_BOUND: LowerBoundSearch(),
        Variant.UPPER_BOUND: UpperBoundSearch(),
    }

    @classmethod
    def get(cls, variant: str | Variant) -> BinarySearch:
        return cls._searches[normalize_variant(variant)]

    @classmethod
    def variants(cls) -> tuple[Variant, ...]:
        return tuple(cls._searches)


def run_search(
    variant: str | Variant, array: Sequence[Number], target: Number
) -> list[SearchState]:
    return list(SearchRegistry.get(variant).search(array, target))
