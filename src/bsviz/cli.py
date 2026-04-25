"""Command line interface for bsviz."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from .algorithms import SearchRegistry, normalize_variant, run_search
from .ansi import SCHEMES, should_color
from .config import effective_settings
from .exceptions import VisualizerError
from .input_sources import add_source_arguments, coerce_target, parse_sizes, resolve_array
from .interactive import InteractiveSession, run_interactive
from .models import SearchResult, SearchState, Variant
from .renderers import Renderer, available_renderers, renderer_for
from .serialization import dump_states, export_frames, load_states


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="bsviz", description="Binary Search Visualizer")
    subparsers = parser.add_subparsers(dest="command", required=True)

    for name, help_text in (
        ("visualize", "interactive visualizer"),
        ("step", "print all steps and exit"),
        ("compare", "compare all variants"),
        ("explain", "print teaching narration for each step"),
    ):
        sub = subparsers.add_parser(name, help=help_text)
        _add_runtime_options(sub)
        add_source_arguments(sub)

    bench = subparsers.add_parser("bench", help="measure comparison counts")
    _add_runtime_options(bench, include_renderer=False, include_target=False)
    bench.add_argument("--sizes", default="100,1000,10000,100000")

    return parser


def _add_runtime_options(
    parser: argparse.ArgumentParser,
    *,
    include_renderer: bool = True,
    include_target: bool = True,
) -> None:
    parser.add_argument("--variant", help="classic, leftmost, rightmost, lower_bound, upper_bound")
    if include_renderer:
        parser.add_argument("--renderer", choices=available_renderers())
        parser.add_argument("--colors", choices=tuple(SCHEMES))
        parser.add_argument("--no-color", action="store_true")
        parser.add_argument("--export", type=Path, help="write replay JSONL")
        parser.add_argument("--export-frames", type=Path, help="write rendered frames to a directory")
        parser.add_argument("--replay", type=Path, help="load states from a previous --export file")
    if include_target:
        parser.add_argument("--target", help="target value")
    parser.add_argument("--speed", type=float, help="auto-advance speed in Hz")
    parser.add_argument("--seed", type=int, help="random seed")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "visualize":
            return _visualize(args, parser)
        if args.command == "step":
            return _step(args, parser, explain=False)
        if args.command == "explain":
            return _step(args, parser, explain=True)
        if args.command == "compare":
            return _compare(args, parser)
        if args.command == "bench":
            return _bench(args)
    except VisualizerError as exc:
        parser.exit(2, f"bsviz: error: {exc}\n")
    return 0


def _settings_and_variant(args: argparse.Namespace) -> tuple[dict[str, object], Variant]:
    settings = effective_settings(args)
    return settings, normalize_variant(str(settings["variant"]))


def _renderer_from_settings(settings: dict[str, object], no_color: bool) -> Renderer:
    scheme = SCHEMES[str(settings["colors"])]
    return renderer_for(str(settings["renderer"]), scheme, should_color(no_color))


def _seed_from_settings(settings: dict[str, object]) -> int | None:
    seed = settings.get("seed")
    return seed if isinstance(seed, int) else None


def _speed_from_settings(settings: dict[str, object]) -> float:
    speed = settings.get("speed", 2.0)
    return float(speed) if isinstance(speed, (int, float, str)) else 2.0


def _states_from_args(
    args: argparse.Namespace,
    parser: argparse.ArgumentParser,
    variant: Variant,
) -> list[SearchState]:
    if getattr(args, "replay", None):
        return load_states(args.replay)
    array = resolve_array(args, seed=getattr(args, "seed", None))
    if args.target is None:
        parser.error("--target is required unless --replay is used")
    target = coerce_target(args.target, array)
    return run_search(variant, array, target)


def _visualize(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    settings, variant = _settings_and_variant(args)
    no_color = bool(getattr(args, "no_color", False))
    if args.replay:
        states = load_states(args.replay)
        if not states:
            parser.error("--replay file did not contain any states")
        renderer = _renderer_from_settings(settings, no_color)
        for state in states:
            print(renderer.render(state))
            print()
        return 0

    array = resolve_array(args, seed=_seed_from_settings(settings))
    if args.target is None:
        args.target = input("target: ")
    target = coerce_target(args.target, array)

    if args.export or args.export_frames:
        states = run_search(variant, array, target)
        renderer = _renderer_from_settings(settings, no_color)
        _maybe_export(args, states, renderer)

    session = InteractiveSession(
        array=array,
        target=target,
        variant=variant,
        renderer_name=str(settings["renderer"]),
        color_scheme=str(settings["colors"]),
        no_color=no_color,
        speed=_speed_from_settings(settings),
    )
    return run_interactive(session)


def _step(args: argparse.Namespace, parser: argparse.ArgumentParser, *, explain: bool) -> int:
    settings, variant = _settings_and_variant(args)
    no_color = bool(getattr(args, "no_color", False))
    renderer = _renderer_from_settings(settings, no_color)
    states = _states_from_args(args, parser, variant)
    _maybe_export(args, states, renderer)
    if explain:
        for state in states:
            print(f"step {state.step}: {state.note}")
        print(_summary_line(SearchResult.from_states(states)))
    else:
        for index, state in enumerate(states):
            if index:
                print()
            print(renderer.render(state))
    return 0


def _compare(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    settings, _ = _settings_and_variant(args)
    array = resolve_array(args, seed=_seed_from_settings(settings))
    if args.target is None:
        parser.error("--target is required")
    target = coerce_target(args.target, array)
    rows = []
    for variant in SearchRegistry.variants():
        states = run_search(variant, array, target)
        result = SearchResult.from_states(states)
        rows.append(
            (
                variant.value,
                result.outcome.value,
                "-" if result.found_index is None else str(result.found_index),
                str(result.total_comparisons),
                str(result.steps_taken),
            )
        )
    _print_table(("variant", "outcome", "index", "comparisons", "states"), rows)
    return 0


def _bench(args: argparse.Namespace) -> int:
    settings, variant = _settings_and_variant(args)
    sizes = parse_sizes(args.sizes)
    rows = []
    for size in sizes:
        array = tuple(range(size))
        target = size
        states = run_search(variant, array, target)
        result = SearchResult.from_states(states)
        rows.append(
            (
                str(size),
                str(result.total_comparisons),
                str(result.steps_taken),
                f"{result.elapsed_ms:.3f}",
            )
        )
    _print_table(("size", "comparisons", "states", "elapsed_ms"), rows)
    return 0


def _maybe_export(args: argparse.Namespace, states: list[SearchState], renderer: Renderer) -> None:
    if getattr(args, "export", None):
        dump_states(states, args.export)
    if getattr(args, "export_frames", None):
        export_frames(states, renderer, args.export_frames)


def _summary_line(result: SearchResult) -> str:
    return (
        f"{result.variant.value}: {result.outcome.value}, result={result.found_index}, "
        f"comparisons={result.total_comparisons}, states={result.steps_taken}, "
        f"elapsed={result.elapsed_ms:.3f}ms"
    )


def _print_table(headers: tuple[str, ...], rows: Sequence[Sequence[str]]) -> None:
    widths = [
        max(len(headers[index]), *(len(row[index]) for row in rows))
        for index in range(len(headers))
    ]
    print("  ".join(header.ljust(widths[index]) for index, header in enumerate(headers)))
    print("  ".join("-" * width for width in widths))
    for row in rows:
        print("  ".join(value.ljust(widths[index]) for index, value in enumerate(row)))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
