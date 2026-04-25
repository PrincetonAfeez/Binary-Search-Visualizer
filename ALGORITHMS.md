# Algorithms

## Classic

Classic binary search returns as soon as it finds an equal middle value. On each
step, it compares `array[mid]` with the target. If the value is too small, the
left half is eliminated. If the value is too large, the right half is eliminated.

## Leftmost

Leftmost search is for arrays with duplicates. When it finds a match, it records
that index as a candidate, then keeps searching left. The final candidate is the
first occurrence.

Example: in `[1, 2, 2, 2, 4]`, searching for `2` returns index `1`.

## Rightmost

Rightmost search mirrors leftmost search. When it finds a match, it records the
candidate, then keeps searching right. The final candidate is the last
occurrence.

Example: in `[1, 2, 2, 2, 4]`, searching for `2` returns index `3`.

## Lower Bound

Lower bound returns the first index where `array[i] >= target`. It is equivalent
to `bisect.bisect_left` in the Python standard library.

If every value is smaller than the target, the insertion point is `len(array)`.

## Upper Bound

Upper bound returns the first index where `array[i] > target`. It is equivalent
to `bisect.bisect_right` in the Python standard library.

If no value is greater than the target, the insertion point is `len(array)`.

