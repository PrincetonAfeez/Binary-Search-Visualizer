"""Domain exceptions for the visualizer."""


class VisualizerError(Exception):
    """Base class for expected visualizer errors."""


class InvalidArrayError(VisualizerError):
    """Raised when an array is empty or contains unsupported values."""


class UnsortedArrayError(InvalidArrayError):
    """Raised when the binary-search precondition is violated."""

    def __init__(self, offending_index: int, previous: object, current: object) -> None:
        self.offending_index = offending_index
        self.previous = previous
        self.current = current
        super().__init__(
            "array must be sorted in ascending order; "
            f"index {offending_index - 1} has {previous!r}, "
            f"index {offending_index} has {current!r}"
        )


class NoStepsAvailableError(VisualizerError):
    """Raised when a controller cannot move in the requested direction."""


class InvalidVariantError(VisualizerError):
    """Raised when a requested search variant is unknown."""

