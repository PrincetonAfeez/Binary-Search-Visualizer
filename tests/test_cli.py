"""Tests for the CLI module."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src")
    return subprocess.run(
        [sys.executable, "-m", "bsviz", *args],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def test_step_command_outputs_states():
    result = run_cli(
        "step",
        "--array",
        "1,2,3,4,5",
        "--target",
        "3",
        "--renderer",
        "minimal",
        "--no-color",
    )
    assert result.returncode == 0
    assert "comparison=equal" in result.stdout


def test_compare_command_outputs_all_variants():
    result = run_cli("compare", "--array", "1,2,2,2,5", "--target", "2")
    assert result.returncode == 0
    assert "leftmost" in result.stdout
    assert "rightmost" in result.stdout
    assert "lower_bound" in result.stdout
    assert "upper_bound" in result.stdout


def test_export_and_replay(tmp_path: Path):
    replay = tmp_path / "out.jsonl"
    export = run_cli(
        "step",
        "--array",
        "1,2,3",
        "--target",
        "2",
        "--export",
        str(replay),
        "--renderer",
        "minimal",
    )
    assert export.returncode == 0
    assert replay.exists()

    replayed = run_cli("step", "--replay", str(replay), "--renderer", "minimal")
    assert replayed.returncode == 0
    assert "target=2" in replayed.stdout

