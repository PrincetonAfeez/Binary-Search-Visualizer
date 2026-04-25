from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable

from .ansi import ColorScheme, SCHEMES, colorize
from .models import ComparisonEvent, ComparisonResult, SearchOutcome, SearchState

