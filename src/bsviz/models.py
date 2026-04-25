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

    @classmethod
    def from_json(cls, payload: dict[str, Any]) -> ComparisonEvent:
        return cls(
            step=int(payload["step"]),
            low=int(payload["low"]),
            high=int(payload["high"]),
            mid=int(payload["mid"]),
            value=payload["value"],
            comparison=ComparisonResult(payload["comparison"]),
        )

@dataclass(frozen=True)
class SearchState:
    array: tuple[Number, ...]
    low: int
    high: int
    mid: int | None
    target: Number
    comparison: ComparisonResult
    step: int
    comparisons: int
    outcome: SearchOutcome
    variant: Variant
    result_index: int | None = None
    elapsed_ms: float = 0.0
    note: str = ""
    history: tuple[ComparisonEvent, ...] = ()

    @property
    def mid_value(self) -> Number | None:
        if self.mid is None:
            return None
        return self.array[self.mid]

    @property
    def is_terminal(self) -> bool:
        return self.outcome is not SearchOutcome.IN_PROGRESS

    def to_json(self) -> dict[str, Any]:
        return {
            "array": list(self.array),
            "low": self.low,
            "high": self.high,
            "mid": self.mid,
            "target": self.target,
            "comparison": self.comparison.value,
            "step": self.step,
            "comparisons": self.comparisons,
            "outcome": self.outcome.value,
            "variant": self.variant.value,
            "result_index": self.result_index,
            "elapsed_ms": self.elapsed_ms,
            "note": self.note,
            "history": [event.to_json() for event in self.history],
        }

    @classmethod
    def from_json(cls, payload: dict[str, Any]) -> SearchState:
        return cls(
            array=tuple(payload["array"]),
            low=int(payload["low"]),
            high=int(payload["high"]),
            mid=None if payload["mid"] is None else int(payload["mid"]),
            target=payload["target"],
            comparison=ComparisonResult(payload["comparison"]),
            step=int(payload["step"]),
            comparisons=int(payload["comparisons"]),
            outcome=SearchOutcome(payload["outcome"]),
            variant=Variant(payload["variant"]),
            result_index=None
            if payload.get("result_index") is None
            else int(payload["result_index"]),
            elapsed_ms=float(payload.get("elapsed_ms", 0.0)),
            note=str(payload.get("note", "")),
            history=tuple(
                ComparisonEvent.from_json(event) for event in payload.get("history", [])
            ),
        )

@dataclass(frozen=True)
class SearchResult:
    variant: Variant
    outcome: SearchOutcome
    target: Number
    steps_taken: int
    total_comparisons: int
    elapsed_ms: float
    found_index: int | None
