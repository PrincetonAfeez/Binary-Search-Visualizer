"""Tests for the algorithms module."""

from __future__ import annotations

import bisect
from dataclasses import FrozenInstanceError

import pytest
from hypothesis import given
from hypothesis import strategies as st

from bsviz.algorithms import run_search
from bsviz.exceptions import InvalidArrayError, UnsortedArrayError
from bsviz.models import SearchOutcome, SearchState, Variant


@pytest.mark.parametrize(
    ("variant", "array", "target", "expected"),
    [
        (Variant.CLASSIC, [1, 2, 3, 4, 5], 3, 2),
        (Variant.CLASSIC, [1, 2, 3, 4, 5], 9, None),
        (Variant.LEFTMOST, [1, 2, 2, 2, 5], 2, 1),
        (Variant.RIGHTMOST, [1, 2, 2, 2, 5], 2, 3),
        (Variant.LOWER_BOUND, [1, 2, 2, 2, 5], 2, 1),
        (Variant.UPPER_BOUND, [1, 2, 2, 2, 5], 2, 4),
        (Variant.LOWER_BOUND, [1, 3, 5], 9, 3),
        (Variant.UPPER_BOUND, [1, 3, 5], 9, 3),
    ],
)
def test_variants_return_expected_indices(variant, array, target, expected):
    states = run_search(variant, array, target)
    assert states[-1].result_index == expected


def test_unsorted_array_reports_offending_index():
    with pytest.raises(UnsortedArrayError) as exc:
        run_search(Variant.CLASSIC, [1, 4, 3, 5], 3)
    assert exc.value.offending_index == 2


def test_empty_array_is_invalid():
    with pytest.raises(InvalidArrayError):
        run_search(Variant.CLASSIC, [], 1)


def test_state_is_immutable():
    state = run_search(Variant.CLASSIC, [1, 2, 3], 2)[0]
    with pytest.raises(FrozenInstanceError):
        state.low = 99  # type: ignore[misc]


@pytest.mark.parametrize("size", [1, 2, 3, 10, 100, 1000])
def test_classic_step_count_is_logarithmic(size):
    states = run_search(Variant.CLASSIC, list(range(size)), size + 1)
    assert states[-1].comparisons <= size.bit_length()
    assert len(states) <= size.bit_length() + 1


@given(st.lists(st.integers(min_value=-50, max_value=50), min_size=1).map(sorted), st.integers(-60, 60))
def test_classic_agrees_with_python_index(array: list[int], target: int):
    states = run_search(Variant.CLASSIC, array, target)
    result = states[-1].result_index
    if target in array:
        assert result is not None
        assert array[result] == target
    else:
        assert result is None
        assert states[-1].outcome is SearchOutcome.NOT_FOUND


@given(st.lists(st.integers(min_value=-20, max_value=20), min_size=1).map(sorted), st.integers(-25, 25))
def test_bounds_agree_with_bisect(array: list[int], target: int):
    lower = run_search(Variant.LOWER_BOUND, array, target)[-1].result_index
    upper = run_search(Variant.UPPER_BOUND, array, target)[-1].result_index
    assert lower == bisect.bisect_left(array, target)
    assert upper == bisect.bisect_right(array, target)


@given(st.lists(st.integers(min_value=-20, max_value=20), min_size=1).map(sorted), st.integers(-25, 25))
def test_leftmost_and_rightmost_match_duplicate_edges(array: list[int], target: int):
    left = run_search(Variant.LEFTMOST, array, target)[-1].result_index
    right = run_search(Variant.RIGHTMOST, array, target)[-1].result_index
    if target not in array:
        assert left is None
        assert right is None
    else:
        assert left == bisect.bisect_left(array, target)
        assert right == bisect.bisect_right(array, target) - 1


def test_json_round_trip():
    state = run_search(Variant.CLASSIC, [1, 3, 5], 5)[0]
    restored = SearchState.from_json(state.to_json())
    assert restored == state

