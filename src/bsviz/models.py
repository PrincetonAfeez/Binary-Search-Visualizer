from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, TypeAlias

Number: TypeAlias = int | float

class ComparisonResult(str, Enum):
    LESS = "less"
    EQUAL = "equal"
    GREATER = "greater"
    NOT_APPLICABLE = "not_applicable"

class SearchOutcome(str, Enum):
    IN_PROGRESS = "in_progress"
    FOUND = "found"
    NOT_FOUND = "not_found"
    ABORTED = "aborted"

class Variant(str, Enum):
    CLASSIC = "classic"
    LEFTMOST = "leftmost"
    RIGHTMOST = "rightmost"
    LOWER_BOUND = "lower_bound"
    UPPER_BOUND = "upper_bound"

class ExecutionMode(str, Enum):
    MANUAL = "manual"
    AUTO = "auto"
    FAST_FORWARD = "fast_forward"

@dataclass(frozen=True)
class ComparisonEvent:
    step: int
    low: int
    high: int
    mid: int
    value: Number
    comparison: ComparisonResult

    def to_json(self) -> dict[str, Any]:
        return {
            "step": self.step,
            "low": self.low,
            "high": self.high,
            "mid": self.mid,
            "value": self.value,
            "comparison": self.comparison.value,
        }
