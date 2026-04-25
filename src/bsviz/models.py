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
