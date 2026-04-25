# Architecture

## Generators As State Machines

Each binary search implementation returns an iterator of `SearchState` objects.
The generator is the algorithm state machine: every `yield` is one comparison or
terminal state. That makes manual stepping, auto-advance, export, and replay
different consumers of the same stream.

## Immutable State

`SearchState` is a frozen dataclass. A step never mutates the previous step; it
creates a new state with the updated low, high, mid, comparison count, result,
and narration. This makes rendering and testing straightforward because every
frame is a value.

## Renderers Are Pure

Renderers accept a `SearchState` and return a string. They do not print, read
keys, clear the screen, or know whether a state came from a live algorithm or a
replay file. The `Display` class is the only code that owns terminal redraw.

## Replay Proves The Boundary

Replay loads serialized states and hands them to the same controller and
renderers used for live searches. No algorithm code runs during replay, which is
the proof that `SearchState` is the useful abstraction.

## Strategies

Search variants are strategy objects registered in `SearchRegistry`. The CLI and
interactive UI select a strategy by `Variant`, while tests can exercise every
implementation through the same protocol.

## Terminal Simplicity

The interactive loop runs in one thread. Auto-advance is just a timed key-polling
loop. This keeps shutdown and terminal restoration easy to reason about.

