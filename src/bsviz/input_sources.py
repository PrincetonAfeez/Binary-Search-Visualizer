"""Array parsing and generation helpers."""

from __future__ import annotations

import argparse
import random
import re
import sys
from pathlib import Path
from typing import Any

from .exceptions import InvalidArrayError
from .models import Number

PRESETS: dict[str, tuple[int, ...]] = {
    "best-case": (1, 3, 5, 7, 9, 11, 13),
    "worst-case": (2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30),
    "duplicates": (1, 2, 2, 2, 4, 5, 5, 8, 13, 13, 21),
}


def add_source_arguments(parser: argparse.ArgumentParser) -> None:
    """Add source arguments to the parser."""
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--array", help="comma- or space-separated numbers")
    source.add_argument("--file", type=Path, help="read numbers from a file")
    source.add_argument("--stdin", action="store_true", help="read numbers from stdin")
    source.add_argument("--random", type=int, metavar="N", help="generate N sorted random ints")
    source.add_argument("--range", dest="range_spec", metavar="A-B", help="generate an inclusive range")
    source.add_argument("--preset", choices=sorted(PRESETS), help="use a teaching preset")


def resolve_array(args: argparse.Namespace, seed: int | None = None) -> tuple[Number, ...]:
    """Resolve the array from the arguments."""
    if args.array:
        return parse_array_text(args.array)
    if args.file:
        return parse_array_text(args.file.read_text(encoding="utf-8"))
    if args.stdin:
        return parse_array_text(sys.stdin.read())
    if args.random is not None:
        return generate_random(args.random, seed)
    if args.range_spec:
        return parse_range(args.range_spec)
    if args.preset:
        return PRESETS[args.preset]
    return PRESETS["duplicates"]


def parse_array_text(text: str) -> tuple[Number, ...]:
    """Parse a comma-separated list of numbers."""
    tokens = [token for token in re.split(r"[\s,]+", text.strip()) if token]
    if not tokens:
        raise InvalidArrayError("array input did not contain any numbers")
    return tuple(parse_number(token) for token in tokens)


def parse_number(raw: str) -> Number:
    """Parse a number from a string."""
    value = raw.strip()
    if re.fullmatch(r"[+-]?\d+", value):
        return int(value)
    try:
        return float(value)
    except ValueError as exc:
        raise InvalidArrayError(f"could not parse number {raw!r}") from exc


def coerce_target(raw: str | Number, array: tuple[Number, ...]) -> Number:
    """Coerce the target to a number."""
    if isinstance(raw, (int, float)) and not isinstance(raw, bool):
        return raw
    text = str(raw)
    if not array:
        return parse_number(text)
    array_type = type(array[0])
    try:
        if array_type is int:
            if not re.fullmatch(r"[+-]?\d+", text.strip()):
                raise ValueError
            return int(text)
        if array_type is float:
            return float(text)
    except ValueError as exc:
        raise InvalidArrayError(
            f"target {raw!r} cannot be parsed as {array_type.__name__}"
        ) from exc
    return parse_number(text)


def generate_random(count: int, seed: int | None = None) -> tuple[int, ...]:
    """Generate a random array of integers."""
    if count <= 0:
        raise InvalidArrayError("--random must be greater than zero")
    rng = random.Random(seed)
    return tuple(sorted(rng.randint(0, max(10, count * 3)) for _ in range(count)))


def parse_range(spec: str) -> tuple[int, ...]:
    """Parse a range of integers."""
    match = re.fullmatch(r"\s*(-?\d+)\s*-\s*(-?\d+)\s*", spec)
    if not match:
        raise InvalidArrayError("--range must look like A-B, for example 1-100")
    start = int(match.group(1))
    stop = int(match.group(2))
    if start > stop:
        raise InvalidArrayError("--range start must be less than or equal to stop")
    return tuple(range(start, stop + 1))


def parse_sizes(raw: str) -> tuple[int, ...]:
    """Parse a comma-separated list of sizes."""
    sizes = tuple(int(part) for part in raw.split(",") if part.strip())
    if not sizes or any(size <= 0 for size in sizes):
        raise InvalidArrayError("--sizes must contain positive integers")
    return sizes


def namespace_has_replay(args: Any) -> bool:
    """Check if the namespace has a replay attribute."""
    return bool(getattr(args, "replay", None))

