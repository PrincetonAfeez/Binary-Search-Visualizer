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
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--array", help="comma- or space-separated numbers")
    source.add_argument("--file", type=Path, help="read numbers from a file")
    source.add_argument("--stdin", action="store_true", help="read numbers from stdin")
    source.add_argument("--random", type=int, metavar="N", help="generate N sorted random ints")
    source.add_argument("--range", dest="range_spec", metavar="A-B", help="generate an inclusive range")
    source.add_argument("--preset", choices=sorted(PRESETS), help="use a teaching preset")



def resolve_array(args: argparse.Namespace, seed: int | None = None) -> tuple[Number, ...]:
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

