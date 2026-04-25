# Binary Search Visualizer

A terminal visualizer for binary search and its closely related variants. The
project is built around immutable `SearchState` objects: algorithms yield states,
renderers turn states into strings, the controller caches states for stepping
backward, and replay reads the same states back from disk.

## Install

```powershell
python -m pip install -e .
```

Then run:

```powershell
bsviz step --array 1,3,5,7,9 --target 7
bsviz compare --array 1,2,2,2,3,4 --target 2
bsviz bench --sizes 100,1000,10000
bsviz visualize --random 30 --seed 42 --target 17
```

Without installation, run from the project folder with:

```powershell
$env:PYTHONPATH='src'
python -m bsviz step --array 1,3,5,7,9 --target 7
```

## Commands

`visualize` opens the interactive terminal UI. In a plain pipe or replay flow,
it can also print frames.

`step` prints every state and exits, which is useful for lessons, tests, and
handouts.

`compare` runs all five variants on the same array and target.

`bench` measures comparison counts and elapsed time across input sizes.

`explain` prints the narration attached to every state.

## Variants

| Variant | Meaning |
| --- | --- |
| `classic` | Find any matching index. |
| `leftmost` | Find the first matching index in duplicated data. |
| `rightmost` | Find the last matching index in duplicated data. |
| `lower_bound` | First index where `array[i] >= target`. |
| `upper_bound` | First index where `array[i] > target`. |

## Input Sources

```powershell
bsviz step --array 1,2,3,4 --target 3
bsviz step --file numbers.txt --target 42
bsviz step --stdin --target 42
bsviz step --random 20 --seed 7 --target 12
bsviz step --range 1-100 --target 33
bsviz step --preset duplicates --target 2
```

Arrays must be sorted. If they are not, `bsviz` reports the first offending
index instead of relying on assertions.

## Export And Replay

```powershell
bsviz step --array 1,2,3,4,5 --target 4 --export out.jsonl
bsviz step --replay out.jsonl --renderer table
bsviz step --array 1,2,3,4,5 --target 4 --export-frames frames
```

`--export` writes JSON Lines: one serialized `SearchState` per visual step.
`--export-frames` writes rendered text files such as `step_001.txt`.

## Interactive Keys

| Key | Action |
| --- | --- |
| Space / Right | Next step |
| Left | Previous cached step |
| `r` | Reset |
| `g` | Go to terminal state |
| `j` | Jump to a step |
| `a` | Toggle auto-advance |
| `+` / `-` | Adjust auto speed |
| `v` | Cycle variant |
| `t` | Change target |
| `c` | Cycle color scheme |
| `m` | Cycle renderer |
| `?` | Help |
| `q` | Quit |

## Configuration

Defaults can live in `~/.bsviz/config.toml`:

```toml
variant = "classic"
renderer = "bar"
colors = "classic"
speed = 2.0
seed = 42
```

Precedence is CLI flags, then config file, then hardcoded defaults.

