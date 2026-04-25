"""Tests for the interactive module."""

from __future__ import annotations

from bsviz.interactive import InteractiveSession, _handle_key
from bsviz.models import Variant


class DummyDisplay:
    def __init__(self) -> None:
        self.close_calls = 0

    def close(self) -> None:
        self.close_calls += 1


def make_session() -> InteractiveSession:
    return InteractiveSession(
        array=(1, 3, 5, 7, 9),
        target=7,
        variant=Variant.CLASSIC,
        renderer_name="minimal",
        color_scheme="classic",
        no_color=True,
        speed=2.0,
    )


def test_jump_key_accepts_valid_step(monkeypatch):
    session = make_session()
    display = DummyDisplay()
    monkeypatch.setattr("builtins.input", lambda _: "1")

    _handle_key(session, "j", display)

    assert session.current is not None
    assert session.current.step == 1
    assert display.close_calls == 1


def test_jump_key_ignores_non_integer_input(monkeypatch):
    session = make_session()
    display = DummyDisplay()
    session.current = session.controller.next()
    previous = session.current
    monkeypatch.setattr("builtins.input", lambda _: "abc")

    _handle_key(session, "j", display)

    assert session.current == previous
    assert display.close_calls == 1


def test_jump_key_ignores_out_of_range_step(monkeypatch):
    session = make_session()
    display = DummyDisplay()
    session.current = session.controller.next()
    previous = session.current
    monkeypatch.setattr("builtins.input", lambda _: "99")

    _handle_key(session, "j", display)

    assert session.current == previous
    assert display.close_calls == 1
