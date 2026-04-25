# Schema

Simple JSON Schema files for the Binary Search Visualizer repository.

## Files

- `common.schema.json` — shared enums and reusable types.
- `comparison-event.schema.json` — one comparison made during a search.
- `search-state.schema.json` — one exported/replayable visual search step.
- `search-result.schema.json` — summary data for a completed search.
- `config.schema.json` — supported `~/.bsviz/config.toml` settings represented as JSON.
- `cli-options.schema.json` — object-shaped representation of supported CLI commands/options.
- `search-export.schema.json` — array form for a loaded JSONL export file.

## Notes

The project writes replay data as JSON Lines, so validate each line against
`search-state.schema.json`. If you load the JSONL file into an array first, you
can validate the array against `search-export.schema.json`.

These schemas are intentionally simple and repository-friendly: they document the
current public data contracts without requiring a new runtime dependency.
