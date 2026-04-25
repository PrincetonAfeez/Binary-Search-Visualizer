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

