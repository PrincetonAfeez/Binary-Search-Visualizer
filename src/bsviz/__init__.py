"""Binary Search Visualizer package."""

from .algorithms import SearchRegistry, run_search
from .models import (
    ComparisonEvent,
    ComparisonResult,
    ExecutionMode,
    SearchOutcome,
    SearchResult,
    SearchState,
    Variant,
)

__all__ = [
    "ComparisonEvent",
    "ComparisonResult",
    "ExecutionMode",
    "SearchOutcome",
    "SearchRegistry",
    "SearchResult",
    "SearchState",
    "Variant",
    "run_search",
]

