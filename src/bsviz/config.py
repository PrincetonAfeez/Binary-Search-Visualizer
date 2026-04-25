"""Configuration loading from ~/.bsviz/config.toml."""

from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    tomllib = None  # type: ignore[assignment]

DEFAULTS: dict[str, Any] = {
    "variant": "classic",
    "renderer": "bar",
    "colors": "classic",
    "speed": 2.0,
    "seed": None,
}


def config_path() -> Path:
    return Path.home() / ".bsviz" / "config.toml"


def load_config(path: Path | None = None) -> dict[str, Any]:
    target = path or config_path()
    if not target.exists() or tomllib is None:
        return {}
    with target.open("rb") as handle:
        payload = tomllib.load(handle)
    if not isinstance(payload, dict):
        return {}
    return payload


def effective_settings(args: object) -> dict[str, Any]:
    config = load_config()
    settings = DEFAULTS | {key: value for key, value in config.items() if key in DEFAULTS}
    for key in DEFAULTS:
        value = getattr(args, key, None)
        if value is not None:
            settings[key] = value
    return settings

