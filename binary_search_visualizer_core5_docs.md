# Architecture Decision Record
## App 31 — Binary Search Visualizer
**Algorithm Visualization Group | Document 1 of 5**
**Status: Accepted**

---

## Context

Binary Search Visualizer is a terminal-based teaching tool for binary search and closely related variants. The app has to do more than return an index: it must expose the reasoning path of the search, render each step clearly, support interactive stepping, allow replay from saved runs, compare variants, and produce benchmark-style comparison counts.

The core architectural problem is that a normal binary search function hides most of the learning value. A conventional implementation receives a sorted array and a target, then returns an index or insertion point. For this app, every intermediate state matters: `low`, `high`, `mid`, comparison result, candidate result, note text, comparison history, elapsed time, and final outcome all have to be visible and serializable.

The implementation therefore uses immutable `SearchState` objects as the central boundary between algorithms, renderers, interactive controls, export/replay, and tests.

---

## Decisions

### Decision 1 — Use generator-based algorithms instead of direct-return functions

**Chosen:** Each search variant is implemented as a generator that yields one immutable `SearchState` per visual step.

**Rejected:** A traditional function that returns only the final result index.

**Reason:** The app is a visualizer, not just a lookup utility. Manual stepping, auto-advance, `step` output, frame export, replay, explanations, and tests all need the full sequence of intermediate states. A generator gives the caller a stream of frames while preserving the natural control flow of binary search.

---

### Decision 2 — Use frozen dataclasses for visual states

**Chosen:** `SearchState`, `ComparisonEvent`, and `SearchResult` are frozen dataclasses.

**Rejected:** Mutable dictionaries or ad hoc tuples.

**Reason:** Each frame should be a stable value. Renderers should be able to receive a state without worrying that another component will mutate it. Frozen dataclasses also make tests clearer: the app can assert exact equality after JSON round trips and can verify immutability directly.

---

### Decision 3 — Treat `SearchState` as the system boundary

**Chosen:** Algorithms emit `SearchState`; renderers consume `SearchState`; serialization writes and reads `SearchState`; the controller caches `SearchState`; interactive mode displays `SearchState`.

**Rejected:** Letting renderers call algorithm internals directly, or letting replay re-run the algorithm.

**Reason:** Replay is the proof that the abstraction is correct. If a saved run can be loaded and rendered without algorithm code running again, then the state object contains the right information. This keeps live execution, replay, testing, and rendering aligned around one domain model.

---

### Decision 4 — Register variants as strategy objects

**Chosen:** Search implementations conform to a `BinarySearch` protocol and are registered in `SearchRegistry` by `Variant` enum.

**Rejected:** A long `if/elif` chain in the CLI that calls separate functions.

**Reason:** The app supports five variants: `classic`, `leftmost`, `rightmost`, `lower_bound`, and `upper_bound`. A registry makes variant selection explicit and keeps the CLI from owning algorithm selection logic. It also makes comparison mode simple: iterate through `SearchRegistry.variants()` and run each strategy through the same interface.

---

### Decision 5 — Keep renderers pure

**Chosen:** Renderers accept a `SearchState` and return a string. They do not print, read keys, clear the terminal, modify state, or know whether the state came from a live search or replay file.

**Rejected:** Renderer classes that directly control terminal output or mutate the interactive session.

**Reason:** Rendering is formatting, not operation. Pure renderers are easier to test and reuse. The same renderer can serve `step`, replay, frame export, non-TTY output, and interactive redraw because terminal I/O is isolated in `terminal.py` and `Display`.

---

### Decision 6 — Use cached forward iteration for backward stepping

**Chosen:** `StepController` wraps a forward-only state iterator and caches states as they are produced. Moving backward returns a previously cached frame.

**Rejected:** Recomputing the search from the beginning every time the user presses Left.

**Reason:** Binary search produces only `O(log n)` states, so caching is cheap. It also preserves exact frame identity, including elapsed timestamps and notes. Recomputing would be unnecessary complexity and could produce slightly different timing data.

---

### Decision 7 — Use JSON Lines for export and replay

**Chosen:** `--export` writes one serialized `SearchState` per line; `--replay` loads the same states back from disk. The loader also accepts a JSON array for tolerance.

**Rejected:** Pickle, plain text frame export only, or a custom binary format.

**Reason:** JSON Lines is readable, append-friendly, inspectable in a terminal, and easy to diff. It captures semantic state rather than rendered text, which means the same replay file can be rendered with a different renderer or color setting later.

---

### Decision 8 — Use `argparse` and stdlib-first packaging

**Chosen:** `argparse` handles the CLI; `tomllib` handles config; the package uses a `src/` layout with a console script entry point named `bsviz`.

**Rejected:** Third-party CLI frameworks such as Click or Typer.

**Reason:** The learning goal is to build a capable CLI using Python fundamentals and the standard library. `argparse` is sufficient for subcommands, mutually exclusive input sources, renderer choices, and error reporting. The package still has professional structure through `pyproject.toml`, editable installation, and a console script.

---

### Decision 9 — Validate sorted input explicitly

**Chosen:** The app validates that arrays are non-empty, sorted ascending, homogeneous by numeric type, and finite when floats are used. Unsorted arrays raise `UnsortedArrayError` with the offending index.

**Rejected:** Relying on assertions or silently sorting user input.

**Reason:** Binary search only works on sorted data. Silently sorting would hide an important precondition from learners and would change the meaning of user-provided indexes. Explicit validation teaches the precondition and prevents misleading visualizations.

---

### Decision 10 — Keep interactive mode single-threaded

**Chosen:** Auto-advance is implemented as timed key polling in one loop.

**Rejected:** Threads, async tasks, or a background timer.

**Reason:** The app is terminal-based and state transitions are simple. A single-threaded loop keeps shutdown, terminal restoration, and error handling easy to reason about. It also matches the educational scope better than introducing concurrency for a problem that does not need it.

---

## Consequences

**Positive:**
- The app has a clean domain boundary: algorithms produce immutable states, and every other subsystem consumes them.
- Replay, export, frame rendering, explanation mode, and interactive mode all reuse the same state stream.
- Five search variants share one protocol and can be tested through common expectations.
- Renderer purity keeps CLI output, non-TTY behavior, and interactive redraw separated.
- JSON Lines replay files are easy to inspect and can be rendered differently after export.
- Explicit input validation prevents false teaching examples caused by unsorted arrays.

**Negative / Trade-offs:**
- The codebase is larger than a basic CLI exercise because it separates algorithms, models, rendering, input sources, terminal control, interactive session logic, and serialization.
- The generator/state abstraction adds more types and files than a beginner binary search implementation would require.
- Interactive mode depends on terminal capabilities and has different behavior in TTY vs non-TTY output.
- JSON state export records semantic frames, not exact terminal screenshots. This is the correct design for replay, but it means display output can change if renderers are later modified.
- `elapsed_ms` is stored in each state, which is useful for summaries but makes exact output timing machine-dependent.

---

## Alternatives Not Explored

- **Full-screen terminal UI frameworks** such as `curses`, `textual`, or `rich`: intentionally avoided to keep dependencies low and preserve focus on algorithms, state, and CLI design.
- **Web visualization:** outside the scope of a CLI roadmap app. A web version would require a different UI architecture.
- **Animation files or GIF export:** omitted because the app already supports text frame export and semantic replay.
- **Streaming massive arrays:** not necessary for an educational binary search visualizer. The array is materialized as a tuple because renderers need indexed access across the entire list.

---

*Constitution reference: Article 1 (Python fundamentals and architectural thinking), Article 3 / Amendment 3.4 (larger project classification), Article 4 (engineering quality), and Article 6 (verification). The project is larger than a 24-hour mini utility, but the scope is justified by the interactive UI, replay/export system, multiple renderers, and variant comparison features.*

---

# Technical Design Document
## App 31 — Binary Search Visualizer
**Algorithm Visualization Group | Document 2 of 5**

---

## Purpose & Scope

Binary Search Visualizer is a Python 3.11 CLI package that teaches binary search by exposing every intermediate state of the algorithm. It supports:

- classic binary search
- leftmost duplicate search
- rightmost duplicate search
- lower bound search
- upper bound search
- interactive stepping
- auto-advance
- renderer switching
- color scheme switching
- comparison across variants
- benchmark-style comparison counts
- JSON Lines export and replay
- text frame export

This document covers the internal implementation: package layout, module responsibilities, state model, data flow, algorithm logic, rendering, configuration, input handling, error handling, serialization, and operational constraints.

---

## System Context

The app runs as a local terminal CLI.

```
User / shell
    │
    ▼
bsviz console script or python -m bsviz
    │
    ▼
argparse CLI layer
    │
    ├── input source resolution: CLI string, file, stdin, random, range, preset
    ├── config resolution: CLI flags > ~/.bsviz/config.toml > defaults
    ├── algorithm execution: generator of SearchState objects
    ├── renderer selection: bar, table, tree, minimal
    ├── optional export: JSONL states and text frames
    └── optional interactive terminal session
```

The app reads from stdin only when `--stdin` is selected. It reads files only when `--file` or `--replay` is selected. It writes side-effect files only when `--export` or `--export-frames` is used. Interactive mode uses raw terminal input and ANSI cursor control when the output stream is a TTY.

---

## Component Breakdown

### `src/bsviz/__init__.py`
Package export surface. Re-exports the primary domain models, `SearchRegistry`, and `run_search()` for library-style use.

### `src/bsviz/__main__.py`
Module entry point. Calls `bsviz.cli.main()` so the package can run with `python -m bsviz`.

### `src/bsviz/models.py`
Defines immutable domain objects and enums:

- `ComparisonResult`
- `SearchOutcome`
- `Variant`
- `ExecutionMode`
- `ComparisonEvent`
- `SearchState`
- `SearchResult`
- `Number = int | float`

This is the central shared model layer for algorithms, renderers, serialization, replay, and tests.

### `src/bsviz/algorithms.py`
Implements binary-search variants as pure generator state machines:

- `ClassicBinarySearch`
- `LeftmostBinarySearch`
- `RightmostBinarySearch`
- `LowerBoundSearch`
- `UpperBoundSearch`

Also provides validation, comparison helpers, state construction, variant normalization, `SearchRegistry`, and `run_search()`.

### `src/bsviz/exceptions.py`
Defines expected domain errors:

- `VisualizerError`
- `InvalidArrayError`
- `UnsortedArrayError`
- `NoStepsAvailableError`
- `InvalidVariantError`

The CLI catches `VisualizerError` and reports it as a controlled user-facing error.

### `src/bsviz/cli.py`
Owns the command-line interface. Builds the parser, dispatches subcommands, loads effective settings, resolves renderers, runs algorithms, prints output, and triggers export/replay operations.

### `src/bsviz/input_sources.py`
Owns input source parsing and generation. Supports comma/space-separated arrays, UTF-8 files, stdin, random arrays, inclusive integer ranges, teaching presets, numeric target coercion, and benchmark size parsing.

### `src/bsviz/config.py`
Loads defaults from `~/.bsviz/config.toml` using `tomllib`. Merges config values with hardcoded defaults and then overrides them with CLI flags.

### `src/bsviz/ansi.py`
Contains ANSI constants, color schemes, color enablement checks, text colorization, cursor movement, and line clearing helpers.

### `src/bsviz/renderers.py`
Defines renderer interface and concrete renderers:

- `MinimalRenderer`
- `BarRenderer`
- `TableRenderer`
- `TreeRenderer`
- `VariablesRenderer`
- `LogRenderer`
- `CompositeRenderer`

Renderers are pure: `SearchState` in, string out.

### `src/bsviz/controller.py`
Defines `StepController`, which wraps any state generator and adds cached navigation: next, back, jump, reset, run to end, summary.

### `src/bsviz/interactive.py`
Defines `InteractiveSession` and the main interactive loop. Handles key commands, renderer cycling, color cycling, target changes, variant changes, auto-advance, help display, and terminal cleanup.

### `src/bsviz/terminal.py`
Owns raw terminal mode, cross-platform key reading, and diff-based redraw through `Display`. Falls back to plain printing for non-TTY output.

### `src/bsviz/commands.py`
Defines the interactive key command registry and help text.

### `src/bsviz/serialization.py`
Serializes and deserializes `SearchState` objects. Writes JSON Lines for replay and text files for frame export.

---

## Module Dependency Graph

```text
__main__.py
    └── cli.py

cli.py
    ├── algorithms.py
    ├── ansi.py
    ├── config.py
    ├── exceptions.py
    ├── input_sources.py
    ├── interactive.py
    ├── models.py
    ├── renderers.py
    └── serialization.py

interactive.py
    ├── algorithms.py
    ├── ansi.py
    ├── commands.py
    ├── controller.py
    ├── exceptions.py
    ├── input_sources.py
    ├── models.py
    ├── renderers.py
    └── terminal.py

algorithms.py
    ├── exceptions.py
    └── models.py

renderers.py
    ├── ansi.py
    └── models.py

serialization.py
    ├── models.py
    └── renderers.py

controller.py
    ├── exceptions.py
    └── models.py

input_sources.py
    ├── exceptions.py
    └── models.py

terminal.py
    └── ansi.py
```

The dependency direction is intentionally layered: domain models sit at the center, algorithms and renderers depend on models, CLI and interactive orchestration depend on both, and terminal control is isolated at the edge.

---

## Core Algorithms & Logic

### Shared input validation

Before any search variant runs, `validate_search_input(array, target)` converts the sequence to a tuple and checks:

1. the array is not empty
2. the first value is an `int` or `float`
3. the target has the same exact type as the array values
4. all array values share the same exact type
5. float values are finite
6. each value is less than or equal to the next value
7. the float target is finite

If a sort-order violation occurs, `UnsortedArrayError` records the offending index plus the previous and current values.

---

### Classic binary search

1. Set `low = 0`, `high = len(array) - 1`.
2. While `low <= high`:
   - compute `mid = (low + high) // 2`
   - compare `array[mid]` against `target`
   - increment comparison count
   - yield a `SearchState`
   - if equal, mark `FOUND` and return
   - if less, move `low = mid + 1`
   - if greater, move `high = mid - 1`
3. If the loop exits, yield a terminal `NOT_FOUND` state with `mid=None`.

Classic search returns any matching index, not necessarily the first or last duplicate.

---

### Leftmost duplicate search

1. Maintain `candidate: int | None`.
2. On equality, store `candidate = mid` but continue searching left by setting `high = mid - 1`.
3. On less-than, search right.
4. On greater-than, search left.
5. After the window closes, yield a terminal state:
   - `FOUND` with candidate if one was recorded
   - `NOT_FOUND` if no candidate was recorded

This mirrors `bisect_left` behavior for exact duplicates.

---

### Rightmost duplicate search

1. Maintain `candidate: int | None`.
2. On equality, store `candidate = mid` but continue searching right by setting `low = mid + 1`.
3. On greater-than, search left.
4. On less-than, search right.
5. After the window closes, yield a terminal state with the last matching candidate if present.

This mirrors `bisect_right(array, target) - 1` when the target exists.

---

### Lower bound search

Lower bound returns the first index where `array[i] >= target`.

1. Initialize `candidate = len(array)`.
2. On equal or greater comparison:
   - set `candidate = mid`
   - search left for an earlier valid bound
3. On less-than comparison:
   - search right
4. At termination:
   - if candidate is within the array, report that index
   - otherwise report insertion point `len(array)` after the array

The final `result_index` is the insertion point even when the outcome is `NOT_FOUND`.

---

### Upper bound search

Upper bound returns the first index where `array[i] > target`.

1. Initialize `candidate = len(array)`.
2. On greater-than comparison:
   - set `candidate = mid`
   - search left for an earlier valid upper bound
3. On equal or less-than comparison:
   - search right
4. At termination:
   - if candidate is within the array, report that index
   - otherwise report insertion point `len(array)` after the array

---

### Rendering flow

```text
SearchState
    │
    ├── MinimalRenderer → one-line machine-readable-ish summary
    ├── BarRenderer → inline indexed cells with pointer marker
    ├── TableRenderer → ASCII table with L/M/H/R markers
    ├── TreeRenderer → comparison path view
    └── CompositeRenderer → visual renderer + variables + recent log
```

`renderer_for()` returns the requested renderer. For `bar`, `table`, and `tree`, it wraps the main renderer in `CompositeRenderer` so the output also includes variable and log panels. `minimal` stays single-line and is useful for tests, scripts, and plain output.

---

### Interactive control flow

```text
InteractiveSession
    │
    ├── StepController(lambda: SearchRegistry.get(variant).search(array, target))
    ├── renderer_for(renderer_name, scheme, color_enabled)
    └── Display.draw(session.frame())
```

The session stores current variant, target, renderer, color scheme, speed, auto/manual mode, and help visibility. Key handling updates those fields or moves the controller through the state stream.

---

## Data Structures

### `SearchState`

```python
@dataclass(frozen=True)
class SearchState:
    array: tuple[int | float, ...]
    low: int
    high: int
    mid: int | None
    target: int | float
    comparison: ComparisonResult
    step: int
    comparisons: int
    outcome: SearchOutcome
    variant: Variant
    result_index: int | None = None
    elapsed_ms: float = 0.0
    note: str = ""
    history: tuple[ComparisonEvent, ...] = ()
```

Purpose: complete visual frame for one algorithm step.

### `ComparisonEvent`

```python
@dataclass(frozen=True)
class ComparisonEvent:
    step: int
    low: int
    high: int
    mid: int
    value: int | float
    comparison: ComparisonResult
```

Purpose: one actual array comparison. Stored in `SearchState.history` for tree and log renderers.

### `SearchResult`

```python
@dataclass(frozen=True)
class SearchResult:
    variant: Variant
    outcome: SearchOutcome
    target: int | float
    steps_taken: int
    total_comparisons: int
    elapsed_ms: float
    found_index: int | None
```

Purpose: terminal summary built from a completed state list.

### `PRESETS`

```python
{
    "best-case": (1, 3, 5, 7, 9, 11, 13),
    "worst-case": (2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30),
    "duplicates": (1, 2, 2, 2, 4, 5, 5, 8, 13, 13, 21),
}
```

Purpose: teaching inputs for common binary-search cases.

### `SCHEMES`

Dictionary mapping color-scheme names to frozen `ColorScheme` dataclasses. Supported schemes are `classic`, `monochrome`, and `colorblind-safe`.

### `StepController` cache

```python
_cache: list[SearchState]
_index: int
_exhausted: bool
_iterator: Iterator[SearchState]
```

Purpose: make a forward-only generator navigable backward and jumpable without recomputing previously seen states.

---

## State Management

State is held in four places:

1. **Algorithm state:** local variables inside each generator (`low`, `high`, `mid`, `candidate`, `comparisons`, `step`, `history`).
2. **Frame state:** immutable `SearchState` objects yielded by algorithms.
3. **Controller state:** cached list of states and current index for interactive navigation.
4. **Session state:** current variant, target, renderer, color scheme, speed, help visibility, auto mode, and current frame.

Replay state is file-based through JSON Lines. Configuration state is file-based through `~/.bsviz/config.toml`. No persistent database is used.

---

## Error Handling Strategy

Expected user errors are represented as `VisualizerError` subclasses and surfaced by the CLI as:

```text
bsviz: error: <message>
```

with exit code `2`.

Controlled errors include:

- empty arrays
- invalid number tokens
- mixed int/float arrays
- non-finite floats
- unsorted arrays
- invalid variants
- invalid range specs
- invalid benchmark sizes
- controller navigation beyond available states

`argparse` also reports command syntax errors with exit code `2`.

Unexpected exceptions, such as invalid TOML syntax, OS-level file errors, or permission errors, are not fully wrapped by the app-specific exception hierarchy and may surface as Python tracebacks. This is a known hardening opportunity.

---

## External Dependencies

### Runtime dependencies

Core runtime is stdlib-first:

- `argparse`
- `bisect` only in tests, not runtime algorithms
- `contextlib`
- `dataclasses`
- `enum`
- `json`
- `math`
- `os`
- `pathlib`
- `random`
- `re`
- `sys`
- `time`
- `tomllib`
- `typing`
- platform terminal modules: `msvcrt` on Windows, `select`, `termios`, and `tty` on Unix-like terminals

### Packaging/build dependency

- `setuptools>=69`

### Development/test dependencies

- `pytest>=8`
- `hypothesis>=6`
- `ruff>=0.7`
- `mypy>=1.10`

The package requires Python `>=3.11`.

---

## Concurrency Model

The app is synchronous and single-threaded.

- Algorithms yield states one at a time.
- Interactive mode polls for keys with a timeout.
- Auto-advance is implemented by advancing the controller when no key is pressed during the auto interval.
- No background worker, async event loop, or thread is used.

This keeps terminal cleanup and state transitions predictable.

---

## Known Limitations

- Arrays must be sorted ascending before search begins.
- Arrays must contain all ints or all floats; mixed numeric types are rejected.
- Empty arrays are rejected even though some lower/upper-bound APIs could theoretically return insertion point `0`.
- All input arrays are materialized as tuples; the app is not designed for streaming huge arrays.
- Interactive mode depends on terminal behavior and is intentionally simpler than a full-screen TUI framework.
- There is no persistent logging system.
- Invalid config file syntax is not normalized into a friendly `VisualizerError`.
- The benchmark command measures elapsed time on the local machine, so only comparison counts are stable across systems.

---

## Design Patterns Used

### Strategy Pattern
Each search variant is a strategy object selected through `SearchRegistry`.

### Iterator / Generator State Machine
Algorithms are implemented as generators. Each `yield` is one visual state.

### Value Object Pattern
`SearchState` and `ComparisonEvent` are immutable values passed across subsystem boundaries.

### Factory Pattern
`renderer_for()` constructs the correct renderer from a string name.

### Controller Pattern
`StepController` mediates navigation over a state stream and isolates stepping/backtracking behavior from the interactive UI.

### Composite Pattern
`CompositeRenderer` combines a main renderer, variable panel, and log panel into one display string.

---

# Interface Design Specification
## App 31 — Binary Search Visualizer
**Algorithm Visualization Group | Document 3 of 5**

---

## Invocation Syntax

After editable installation:

```bash
bsviz <command> [options]
```

Without installation, from the repository root:

```bash
PYTHONPATH=src python -m bsviz <command> [options]
```

PowerShell equivalent:

```powershell
$env:PYTHONPATH='src'
python -m bsviz <command> [options]
```

---

## Commands

| Command | Purpose |
|---|---|
| `visualize` | Opens the interactive terminal visualizer, or prints replay frames when `--replay` is used. |
| `step` | Prints every state and exits. Useful for tests, lessons, handouts, and export. |
| `compare` | Runs all five search variants on the same array and target, then prints a comparison table. |
| `explain` | Prints the teaching narration attached to every state. |
| `bench` | Measures comparison counts and elapsed time across input sizes. |

---

## Runtime Options

These options apply to `visualize`, `step`, `compare`, and `explain` unless otherwise noted.

| Name | Type | Required | Default | Valid Values | Description |
|---|---:|---:|---|---|---|
| `--variant` | choice/string | No | `classic` | `classic`, `leftmost`, `rightmost`, `lower_bound`, `upper_bound`; aliases `lower`, `lower-bound`, `upper`, `upper-bound` | Search variant to run. Ignored by `compare`, which runs all variants. Used by `bench`. |
| `--renderer` | choice | No | `bar` | `bar`, `table`, `tree`, `minimal` | Renderer for visual output. Not available on `bench`. |
| `--colors` | choice | No | `classic` | `classic`, `monochrome`, `colorblind-safe` | Color scheme. Not available on `bench`. |
| `--no-color` | bool flag | No | `False` | present / absent | Disables ANSI color output. Not available on `bench`. |
| `--export` | path | No | none | writable file path | Writes one serialized `SearchState` per JSONL line. Not available on `bench`. |
| `--export-frames` | path | No | none | writable directory path | Writes rendered frames as `step_001.txt`, `step_002.txt`, etc. Not available on `bench`. |
| `--replay` | path | No | none | readable JSONL or JSON array file | Loads states from a previous export instead of running an algorithm. Not available on `bench`. |
| `--target` | int/float string | Usually yes | none | same numeric type as array | Target value. Required for `step`, `compare`, and `explain` unless `--replay` is used. In `visualize`, missing target prompts interactively. Not available on `bench`. |
| `--speed` | float | No | `2.0` | positive float; interactive session clamps minimum to `0.25` Hz | Auto-advance speed in interactive mode. Accepted by `bench` but not materially used there. |
| `--seed` | int | No | config/default | any integer | Seed for random array generation. |

---

## Input Source Options

For `visualize`, `step`, `compare`, and `explain`, the input source options are mutually exclusive.

| Name | Type | Required | Default | Valid Values | Description |
|---|---:|---:|---|---|---|
| `--array` | str | No | none | comma- or whitespace-separated numbers | Direct array input. Example: `1,2,3,4` or `1 2 3 4`. |
| `--file` | path | No | none | UTF-8 text file containing numbers | Reads numbers from a file. |
| `--stdin` | bool flag | No | `False` | present / absent | Reads numbers from standard input. |
| `--random N` | int | No | none | `N > 0` | Generates `N` sorted random integers. |
| `--range A-B` | range string | No | none | inclusive integer range where `A <= B` | Generates a sorted integer range. Example: `1-100`. |
| `--preset` | choice | No | `duplicates` if no source is given | `best-case`, `worst-case`, `duplicates` | Uses a built-in teaching preset. |

If no input source is provided, the app uses the `duplicates` preset.

---

## Bench Options

| Name | Type | Required | Default | Valid Values | Description |
|---|---:|---:|---|---|---|
| `--sizes` | str | No | `100,1000,10000,100000` | comma-separated positive integers | Input sizes to benchmark. |
| `--variant` | choice/string | No | `classic` | supported variants | Variant to benchmark. |
| `--speed` | float | No | `2.0` | any float | Accepted through shared runtime options but not meaningful for benchmark output. |
| `--seed` | int | No | none | any integer | Accepted through shared runtime options but not meaningful because benchmark arrays are deterministic ranges. |

---

## Input Contract

### Number formats

- Integers are parsed with regex: optional sign followed by digits.
- Non-integer tokens are parsed as floats.
- Arrays must be homogeneous by exact type: all `int` or all `float`.
- Targets must match the array's exact numeric type.
- Float values and float targets must be finite.

### Array contract

- Array must contain at least one number.
- Array must be sorted ascending.
- Duplicate values are allowed.
- The app reports the first offending index for unsorted input.

### File/stdin contract

- Files are read as UTF-8 text.
- Numbers may be separated by commas, whitespace, or both.

### Replay contract

- Replay files must contain either:
  - JSON Lines, one serialized state per line, or
  - one JSON array containing serialized state objects
- Replay states must match the `SearchState.to_json()` schema.

---

## Output Contract

### `step`

Prints each rendered state to stdout. Frames are separated by a blank line. Renderer controls the exact format.

Example with `minimal`:

```text
step=0 variant=classic low=0 mid=2 high=4 value=3 target=3 comparison=equal outcome=found result=2 comparisons=1
```

### `explain`

Prints one narration line per state, then a summary line.

```text
step 0: mid=2, value 3 equals 3.
classic: found, result=2, comparisons=1, states=1, elapsed=0.012ms
```

### `compare`

Prints a fixed-width table with one row per variant.

```text
variant      outcome    index  comparisons  states
-----------  ---------  -----  -----------  ------
classic      found      2      1            1
leftmost     found      1      3            4
rightmost    found      3      3            4
lower_bound  found      1      3            4
upper_bound  found      4      3            4
```

### `bench`

Prints a fixed-width table.

```text
size    comparisons  states  elapsed_ms
------  -----------  ------  ----------
100     7            8       0.034
1000    10           11      0.041
```

Elapsed time is machine-dependent; comparison counts are the stable teaching signal.

### `visualize`

In TTY mode, redraws the terminal display interactively. In replay mode, prints each replayed frame to stdout and exits.

### `--export`

Writes JSON Lines using UTF-8 encoding.

Each line has this schema:

```json
{
  "array": [1, 2, 3],
  "low": 0,
  "high": 2,
  "mid": 1,
  "target": 2,
  "comparison": "equal",
  "step": 0,
  "comparisons": 1,
  "outcome": "found",
  "variant": "classic",
  "result_index": 1,
  "elapsed_ms": 0.012,
  "note": "mid=1, value 2 equals 2.",
  "history": [
    {
      "step": 0,
      "low": 0,
      "high": 2,
      "mid": 1,
      "value": 2,
      "comparison": "equal"
    }
  ]
}
```

### `--export-frames`

Creates a directory if needed and writes files named:

```text
step_001.txt
step_002.txt
step_003.txt
```

Each file contains one rendered frame plus a trailing newline.

---

## Exit Code Reference

| Exit Code | Condition |
|---:|---|
| `0` | Successful command completion. |
| `2` | CLI syntax error, missing required target, invalid visualizer input, invalid variant, unsorted array, invalid range, invalid sizes, or controlled interactive error. |
| nonzero Python exception | Unexpected runtime error not wrapped by `VisualizerError`, such as malformed TOML, permission errors, or unhandled file I/O failure. |

---

## Error Output Behavior

Controlled CLI errors are written to stderr in this format:

```text
bsviz: error: <message>
```

`argparse` errors also print usage information to stderr and exit with code `2`.

Normal command output goes to stdout. Rendered frames, tables, explanation lines, and benchmark tables are stdout output. The app does not emit machine-readable error JSON.

---

## Environment Variables

| Variable | Effect | Precedence |
|---|---|---|
| `NO_COLOR` | Disables ANSI color output when present. | Acts alongside `--no-color`; either disables color. |
| `PYTHONPATH` | Allows running from source without editable installation when set to `src`. | Shell/runtime behavior, not app config. |

---

## Configuration Files

Default config path:

```text
~/.bsviz/config.toml
```

Supported keys:

```toml
variant = "classic"
renderer = "bar"
colors = "classic"
speed = 2.0
seed = 42
```

### Precedence

```text
CLI flags > ~/.bsviz/config.toml > hardcoded defaults
```

Unknown config keys are ignored. Supported keys with `None` values fall back to defaults unless overridden by CLI flags.

---

## Side Effects

| Operation | Side Effect |
|---|---|
| `--export out.jsonl` | Creates or overwrites a UTF-8 JSONL file. |
| `--export-frames frames/` | Creates the directory if needed and writes `step_###.txt` files. |
| `--file numbers.txt` | Reads UTF-8 text from a file. |
| `--stdin` | Reads stdin to EOF. |
| `--replay out.jsonl` | Reads a replay file. |
| `visualize` | Temporarily changes terminal input mode and uses ANSI redraw when attached to a TTY. |

No network calls are made. No database, cache directory, or hidden runtime state is created by normal execution.

---

## Usage Examples

### Basic use

```bash
bsviz step --array 1,3,5,7,9 --target 7 --renderer minimal --no-color
```

### Compare all variants on duplicated data

```bash
bsviz compare --array 1,2,2,2,3,4 --target 2
```

### Use a teaching preset

```bash
bsviz step --preset duplicates --target 2 --variant leftmost --renderer table --no-color
```

### Generate random sorted input

```bash
bsviz visualize --random 30 --seed 42 --target 17
```

### Use an inclusive integer range

```bash
bsviz explain --range 1-100 --target 33 --variant lower_bound
```

### Export semantic replay states

```bash
bsviz step --array 1,2,3,4,5 --target 4 --export out.jsonl --renderer minimal
```

### Replay with a different renderer

```bash
bsviz step --replay out.jsonl --renderer table --no-color
```

### Export rendered frames

```bash
bsviz step --array 1,2,3,4,5 --target 4 --export-frames frames --renderer bar --no-color
```

### Benchmark logarithmic comparison growth

```bash
bsviz bench --sizes 100,1000,10000,100000 --variant classic
```

### Intentional failure: unsorted input

```bash
bsviz step --array 1,5,3,7 --target 3
```

Expected stderr:

```text
bsviz: error: array must be sorted in ascending order; index 1 has 5, index 2 has 3
```

---

# Runbook
## App 31 — Binary Search Visualizer
**Algorithm Visualization Group | Document 4 of 5**

---

## Prerequisites

- Python 3.11 or later
- Local terminal / shell
- `pip`
- Git if cloning from GitHub
- Optional development tools:
  - `pytest>=8`
  - `hypothesis>=6`
  - `ruff>=0.7`
  - `mypy>=1.10`

Supported OS targets are Windows, macOS, and Linux. Terminal behavior differs slightly by OS: Windows uses `msvcrt`; Unix-like systems use `select`, `termios`, and `tty`.

---

## Installation Procedure

### Editable install from repository root

```bash
git clone https://github.com/PrincetonAfeez/Binary-Search-Visualizer
cd Binary-Search-Visualizer
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
```

PowerShell activation:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .
```

Verify the console script:

```bash
bsviz --help
```

### Development install

```bash
python -m pip install -r requirements.txt
```

or:

```bash
python -m pip install -e ".[dev]"
```

### Run without installation

From the repository root:

```bash
PYTHONPATH=src python -m bsviz step --array 1,3,5,7,9 --target 7
```

PowerShell:

```powershell
$env:PYTHONPATH='src'
python -m bsviz step --array 1,3,5,7,9 --target 7
```

---

## Configuration Steps

Create an optional config file:

```bash
mkdir -p ~/.bsviz
cat > ~/.bsviz/config.toml <<'TOML'
variant = "classic"
renderer = "bar"
colors = "classic"
speed = 2.0
seed = 42
TOML
```

If the config file is missing, the app uses hardcoded defaults. If a CLI flag is provided, it overrides the config file.

Recommended safe defaults for plain terminals:

```toml
variant = "classic"
renderer = "minimal"
colors = "monochrome"
speed = 2.0
```

---

## Standard Operating Procedures

### Print a simple search trace

```bash
bsviz step --array 1,2,3,4,5 --target 3 --renderer minimal --no-color
```

Use this for quick correctness checks and handouts.

---

### Teach duplicate handling

```bash
bsviz compare --array 1,2,2,2,5 --target 2
```

Confirm that:

- classic may return any matching index
- leftmost returns the first `2`
- rightmost returns the last `2`
- lower bound returns the first index where value is at least `2`
- upper bound returns the first index where value is greater than `2`

---

### Explain a run in prose

```bash
bsviz explain --array 1,3,5,7,9 --target 6 --variant lower_bound
```

Use this when the goal is narration rather than visualization.

---

### Open interactive visualizer

```bash
bsviz visualize --preset duplicates --target 2 --variant classic
```

Useful keys:

```text
space/right  next
left         previous
r            reset
g            go to terminal state
j            jump to step
a            auto-advance
+/-          speed up/down
v            cycle variant
t            change target
m            cycle renderer
c            cycle color scheme
?            help
q            quit
```

---

### Export and replay

```bash
bsviz step --array 1,2,3,4,5 --target 4 --export out.jsonl --renderer minimal
bsviz step --replay out.jsonl --renderer table --no-color
```

Use export/replay when you want deterministic classroom material or want to inspect the same state sequence with multiple renderers.

---

### Export text frames

```bash
bsviz step --array 1,2,3,4,5 --target 4 --export-frames frames --renderer table --no-color
ls frames
```

Expected files:

```text
step_001.txt
step_002.txt
...
```

---

### Benchmark comparison counts

```bash
bsviz bench --sizes 100,1000,10000,100000 --variant classic
```

Use comparison counts as the meaningful measure. Elapsed milliseconds depend on the machine.

---

## Health Checks

### CLI parser check

```bash
bsviz --help
```

Expected: help text with subcommands.

### Minimal execution check

```bash
bsviz step --array 1,2,3 --target 2 --renderer minimal --no-color
```

Expected: exit code `0` and output containing:

```text
comparison=equal
outcome=found
result=1
```

### Variant comparison check

```bash
bsviz compare --array 1,2,2,2,5 --target 2
```

Expected: output includes `leftmost`, `rightmost`, `lower_bound`, and `upper_bound`.

### Export/replay check

```bash
bsviz step --array 1,2,3 --target 2 --export /tmp/bsviz-check.jsonl --renderer minimal --no-color
bsviz step --replay /tmp/bsviz-check.jsonl --renderer minimal --no-color
```

Expected: replay output contains `target=2`.

### Test suite check

```bash
pytest -q
```

Expected for a healthy checkout: all tests pass.

---

## Expected Output Samples

### Successful minimal search

```text
step=0 variant=classic low=0 mid=1 high=2 value=2 target=2 comparison=equal outcome=found result=1 comparisons=1
```

### Failed classic search

```text
step=0 variant=classic low=0 mid=1 high=2 value=2 target=4 comparison=less outcome=in_progress result=- comparisons=1

step=1 variant=classic low=2 mid=2 high=2 value=3 target=4 comparison=less outcome=in_progress result=- comparisons=2

step=2 variant=classic low=3 mid=- high=2 value=- target=4 comparison=not_applicable outcome=not_found result=- comparisons=2
```

### Compare table shape

```text
variant      outcome    index  comparisons  states
-----------  ---------  -----  -----------  ------
classic      found      2      1            1
leftmost     found      1      3            4
rightmost    found      3      3            4
lower_bound  found      1      3            4
upper_bound  found      4      3            4
```

---

## Known Failure Modes

| Symptom | Probable Cause | Diagnostic Step | Resolution |
|---|---|---|---|
| `bsviz: error: array must be sorted...` | Input violates binary search precondition. | Inspect the reported adjacent indexes. | Sort the input before passing it, or correct the source data. |
| `array must contain at least one number` | Empty `--array`, empty file, or empty stdin. | Print the source input. | Provide at least one number. |
| `could not parse number` | Non-numeric token in input. | Check separators and stray characters. | Use comma or whitespace separated ints/floats only. |
| `array values must not mix ints and floats` | Input combines `1` and `1.5`. | Inspect parsed tokens. | Use all ints or all floats. |
| `target must be a int/float...` | Target type does not match array type. | Compare input values and target string. | Use `2` with int arrays or `2.0` with float arrays. |
| `target ... cannot be parsed as int` | Int array received a float-like target. | Check target value. | Use an integer target or convert array to floats. |
| `--range must look like A-B` | Invalid range syntax. | Check the argument value. | Use `--range 1-100`. |
| `--random must be greater than zero` | Random count is zero or negative. | Check `N`. | Use a positive integer. |
| Replay prints nothing | Replay file is empty. | Check file size. | Regenerate export with a valid search. |
| ANSI codes show literally | Terminal does not support ANSI or color is forced. | Try `--no-color`. | Use `--no-color` or a compatible terminal. |
| Interactive view looks duplicated | Output is not a true TTY. | Check whether command is piped or captured. | Use `step` mode for pipes; use `visualize` in a real terminal. |
| Config causes traceback | Malformed TOML or unsupported value type. | Temporarily move `~/.bsviz/config.toml`. | Fix TOML syntax or remove the bad config. |

---

## Troubleshooting Decision Tree

```text
Command fails before running?
    ├── Does stderr show argparse usage?
    │       └── Fix command syntax or missing flags.
    ├── Does stderr show bsviz: error: ...?
    │       └── Treat as expected input/config issue.
    └── Does Python traceback appear?
            └── Check file permissions, malformed TOML, or unexpected environment issue.

Search result looks wrong?
    ├── Is the array sorted ascending?
    │       └── If no, fix input. Binary search requires sorted data.
    ├── Are duplicates involved?
    │       └── Use leftmost/rightmost/lower_bound/upper_bound intentionally.
    ├── Are ints and floats mixed?
    │       └── Normalize numeric type.
    └── Is this lower/upper bound?
            └── Remember result_index may be an insertion point.

Interactive display misbehaves?
    ├── Are you piping output?
    │       └── Use step mode instead.
    ├── Are colors unreadable?
    │       └── Use --no-color or --colors monochrome.
    └── Did the cursor stay hidden?
            └── Run: printf '\033[?25h\n'
```

---

## Dependency Failure Handling

### Missing package after clone

Symptom:

```text
ModuleNotFoundError: No module named 'bsviz'
```

Resolution:

```bash
python -m pip install -e .
```

or:

```bash
PYTHONPATH=src python -m bsviz --help
```

### Missing dev dependency

Symptom:

```text
ModuleNotFoundError: No module named 'pytest'
```

Resolution:

```bash
python -m pip install -r requirements.txt
```

### Replay or file input path unavailable

Symptom: file-related Python error or parser failure.

Resolution:

```bash
ls -l path/to/file
python -c "from pathlib import Path; print(Path('path/to/file').read_text(encoding='utf-8')[:100])"
```

Then rerun with a valid path.

---

## Recovery Procedures

### Clean up bad frame export

```bash
rm -rf frames
bsviz step --array 1,2,3,4,5 --target 4 --export-frames frames --renderer table --no-color
```

### Regenerate replay file

```bash
rm -f out.jsonl
bsviz step --array 1,2,3,4,5 --target 4 --export out.jsonl --renderer minimal --no-color
bsviz step --replay out.jsonl --renderer minimal --no-color
```

### Restore terminal cursor if interrupted badly

```bash
printf '\033[?25h\n'
```

### Bypass broken user config

```bash
mv ~/.bsviz/config.toml ~/.bsviz/config.toml.bak
bsviz step --array 1,2,3 --target 2 --renderer minimal --no-color
```

---

## Logging Reference

The app does not write persistent logs. Debugging information is available through:

- `--renderer minimal` for compact state lines
- `explain` command for state narration
- `--export out.jsonl` for semantic state inspection
- `--export-frames frames/` for rendered-frame inspection
- pytest output for development verification

To inspect exported state:

```bash
python -m json.tool out.jsonl
```

For JSON Lines, inspect line by line:

```bash
python - <<'PY'
import json
from pathlib import Path
for line in Path('out.jsonl').read_text(encoding='utf-8').splitlines():
    print(json.dumps(json.loads(line), indent=2))
PY
```

---

## Maintenance Notes

- Keep `Variant` enum, `SearchRegistry`, README variant table, and tests synchronized when adding a new variant.
- Keep renderer names, `available_renderers()`, CLI choices, README, and tests synchronized when adding a renderer.
- Treat `SearchState.to_json()` and `SearchState.from_json()` as a compatibility contract for replay files.
- Harden `config.py` if the app is used beyond a controlled academic setting; malformed TOML should become a friendly `VisualizerError`.
- Add Windows and Unix terminal smoke checks if interactive mode becomes part of graded verification.
- Avoid adding third-party terminal UI dependencies unless the learning objective shifts from algorithm visualization to TUI framework practice.

---

# Lessons Learned
## App 31 — Binary Search Visualizer
**Algorithm Visualization Group | Document 5 of 5**

---

## Project Summary

Binary Search Visualizer is a terminal teaching app that turns binary search into a sequence of inspectable states. It supports classic binary search, leftmost and rightmost duplicate handling, lower and upper bound variants, interactive stepping, replay, frame export, comparison tables, and benchmark-style comparison counts. The project achieved more than a simple algorithm exercise: it became a small state-driven CLI system with clear boundaries between search logic, rendering, terminal operation, serialization, and testing.

---

## Original Goals vs. Actual Outcome

The original goal was to visualize binary search in the terminal. The delivered project goes beyond that baseline by supporting five algorithm variants, multiple renderers, interactive controls, config defaults, random/range/preset inputs, JSONL replay, and benchmark output. The final outcome is stronger architecturally than a one-file visualizer, but it is also larger and more complex than the smallest possible solution.

The main gap is hardening rather than core functionality. Expected domain errors are handled well, but some operational errors, such as malformed config files or file permission failures, can still surface outside the app-specific error hierarchy.

---

## Technical Decisions That Paid Off

### Immutable `SearchState` as the central abstraction

This was the most important decision. Once every subsystem agreed on `SearchState`, the app could support live rendering, replay, export, tests, explanations, and interactive stepping without duplicating algorithm logic.

### Generator-based algorithms

Yielding states instead of returning only a final index made the app naturally visual. The control flow still resembles binary search, but the caller can decide whether to print, render, cache, export, or replay each state.

### Pure renderers

Keeping renderers as `state -> string` functions made them easy to test and reuse. This avoided coupling display formatting to terminal redraw code.

### `StepController` cache

Caching produced states was a simple and correct way to support backward stepping. Because binary search is logarithmic, the memory cost is tiny relative to the clarity it provides.

### Property-based tests against `bisect`

Using Hypothesis and `bisect` for bounds-related behavior was a strong verification choice. Lower bound and upper bound are easy to get subtly wrong, especially with duplicates.

---

## Technical Decisions That Created Debt

### Config errors are not fully normalized

`load_config()` reads TOML directly and does not wrap malformed TOML in a friendly domain error. For an academic app this is acceptable, but a user-facing tool should catch and report config parse failures cleanly.

### Bench accepts some generic runtime options that do not matter

Because `bench` reuses shared runtime option structure, it accepts options like `--speed` and `--seed` even though benchmark arrays are deterministic and interactive speed is irrelevant. This is minor CLI surface debt.

### Replay compatibility is implicit

`SearchState.to_json()` and `from_json()` form a replay schema, but there is no explicit schema version field. If the state format changes later, old replay files may require migration logic.

### Terminal behavior is hard to test deeply

The terminal layer is intentionally thin, but raw key handling and cursor redraw are inherently harder to verify than pure functions. More integration testing would be needed if this became a production TUI.

---

## What Was Harder Than Expected

### Visualizing variants without confusing semantics

Classic binary search, leftmost, rightmost, lower bound, and upper bound are closely related but not identical. The hard part was not just implementing them; it was making their outcomes explainable. In particular, lower and upper bound may return insertion points, not found matches.

### Maintaining state history

Tree and log renderers need comparison history, but history must not mutate previous frames. Carrying a tuple of `ComparisonEvent` values through immutable states solved the problem but required deliberate design.

### Separating live execution from replay

Replay forced a clean boundary. If renderers or controllers had depended on algorithm internals, replay would have become a special case. Designing replay around serialized `SearchState` values made the architecture stronger.

### Terminal control

Interactive terminal apps require careful cleanup. Cursor visibility, raw input mode, non-TTY fallback, and cross-platform key reading add complexity that is unrelated to the algorithm itself.

---

## What Was Easier Than Expected

### `argparse` handled the CLI well

Subcommands, mutually exclusive input sources, choices, and typed flags were all possible with stdlib `argparse`. A third-party CLI framework was not necessary for this scope.

### Frame export came naturally after renderers were pure

Once a renderer returned a string, exporting frames was just writing each rendered state to a numbered text file.

### Variant comparison reused existing pieces

Because all variants conform to the same strategy interface and return the same state type, `compare` mode did not require special algorithm code.

---

## Python-Specific Learnings

- Frozen dataclasses are useful for domain values that should not mutate after creation.
- `Enum` subclasses with `str` values work well for CLI-facing constants and JSON serialization.
- Generators are a good fit for teaching algorithms because they expose intermediate computation without building a separate event system.
- `argparse` is powerful enough for multi-command CLI apps when structured carefully.
- `tomllib` provides a lightweight stdlib config path in Python 3.11+.
- `pathlib.Path` makes file input, export paths, and frame directories easier to work with than raw strings.
- `time.perf_counter()` is appropriate for elapsed timing, but elapsed values should not be treated as stable test assertions.
- Hypothesis is valuable for algorithm verification because it checks many sorted arrays and targets, not just a few hand-picked examples.

---

## Architecture Insights

The main insight is that visualization apps should separate **what happened** from **how it is displayed**. `SearchState` describes what happened; renderers decide how to display it; `Display` decides how to draw it; serialization decides how to store it. Keeping those decisions separate made the app easier to extend.

Another insight is that replay is a strong architectural test. If a replay file can drive the same renderers and controller as live algorithm output, the system boundary is probably well chosen.

---

## Testing Gaps

The existing tests cover core algorithm behavior, immutability, logarithmic step bounds, agreement with `bisect`, JSON round trip, CLI smoke behavior, export/replay, and renderer output. Remaining gaps include:

- malformed config file handling
- invalid file permissions and missing file paths
- terminal raw mode behavior under real TTY conditions
- interactive key sequences across platforms
- exact frame export contents beyond file creation
- schema migration for future replay changes
- color behavior under `NO_COLOR` and `--no-color`

These gaps are acceptable for an academic CLI project but should be addressed before treating the app as a polished distribution.

---

## Reusable Patterns Identified

### State-stream algorithm pattern

Algorithms that need visualization should yield immutable state objects rather than return only final answers. This can be reused for sorting visualizers, graph traversal visualizers, dynamic programming table builders, and parsing visualizers.

### Pure renderer pattern

Keeping renderers pure makes terminal output, tests, screenshots, exports, and replay easier to support.

### Registry-based variant selection

A registry of strategies is cleaner than scattering variant conditionals throughout CLI code.

### Controller cache pattern

When an algorithm naturally streams forward but the UI needs backward movement, caching states is a simple solution if the state count is bounded and small.

### JSONL replay pattern

Writing semantic states as JSON Lines is a reusable export format for CLI educational tools.

---

## If I Built This Again

The first improvement would be adding an explicit replay schema version, probably at the top of each exported state or as a metadata header. That would make future state-model changes safer.

The second improvement would be hardening the configuration and file I/O layer so every expected operational failure becomes a clean `bsviz: error: ...` message with exit code `2` instead of a possible traceback.

The third improvement would be adding a small non-interactive simulation harness for key commands. That would allow tests to verify `next`, `previous`, `jump`, renderer cycling, variant cycling, and target changes without depending on raw terminal behavior.

---

## Open Questions

- Should lower and upper bound terminal outcomes be represented as `FOUND` when the insertion point is inside the array, or should they use a separate `BOUND_FOUND` / `INSERTION_POINT` outcome for clarity?
- Should replay files include a schema version and app version?
- Should malformed config files be ignored, warned about, or treated as fatal errors?
- Should `bench` have its own smaller option surface instead of inheriting unused runtime options?
- Should empty arrays be allowed for lower/upper-bound educational examples, returning insertion point `0`, or should the current non-empty rule remain consistent across all variants?

---

*Constitution v2.0 checklist: This document satisfies Article 5 (trade-off documentation), Article 6 (verification discussion), and Article 7 (progressive complexity). The project demonstrates growth from single-purpose CLI apps toward a multi-module, state-driven, testable terminal system.*
