"""Tests for the renderers module."""

from __future__ import annotations

from bsviz.algorithms import run_search
from bsviz.ansi import SCHEMES
from bsviz.models import Variant
from bsviz.renderers import BarRenderer, MinimalRenderer, TableRenderer, TreeRenderer, renderer_for


def test_minimal_renderer_is_single_line():
    state = run_search(Variant.CLASSIC, [1, 2, 3], 2)[0]
    output = MinimalRenderer().render(state)
    assert "\n" not in output
    assert "comparison=equal" in output


def test_visual_renderers_return_strings():
    state = run_search(Variant.LEFTMOST, [1, 2, 2, 3], 2)[0]
    for renderer in (
        BarRenderer(SCHEMES["classic"], use_color=False),
        TableRenderer(SCHEMES["classic"], use_color=False),
        TreeRenderer(SCHEMES["classic"], use_color=False),
    ):
        output = renderer.render(state)
        assert isinstance(output, str)
        assert output


def test_renderer_factory_wraps_composite_renderer():
    state = run_search(Variant.CLASSIC, [1, 2, 3], 4)[-1]
    output = renderer_for("bar", SCHEMES["classic"], use_color=False).render(state)
    assert "variant:" in output
    assert "log" in output

