"""Interactive terminal session."""

from __future__ import annotations

import sys

from .algorithms import SearchRegistry
from .ansi import SCHEMES, should_color
from .commands import help_text
from .controller import StepController
from .exceptions import NoStepsAvailableError, VisualizerError
from .input_sources import coerce_target
from .models import Number, SearchState, Variant
from .renderers import Renderer, available_renderers, renderer_for
from .terminal import Display, raw_terminal, read_key


class InteractiveSession:
    """Interactive session."""
    def __init__(
        self,
        *,
        array: tuple[Number, ...],
        target: Number,
        variant: Variant,
        renderer_name: str,
        color_scheme: str,
        no_color: bool,
        speed: float,
    ) -> None:
        self.array = array
        self.target = target
        self.variant = variant
        self.renderer_name = renderer_name
        self.color_scheme = color_scheme
        self.no_color = no_color
        self.speed = max(0.25, speed)
        self.auto = False
        self.show_help = False
        self.controller = self._new_controller()
        self.current: SearchState | None = None

    def _new_controller(self) -> StepController:
        return StepController(
            lambda: SearchRegistry.get(self.variant).search(self.array, self.target)
        )

    def _renderer(self) -> Renderer:
        scheme = SCHEMES[self.color_scheme]
        return renderer_for(self.renderer_name, scheme, should_color(self.no_color))

    def frame(self) -> str:
        if self.current is None:
            self.current = self.controller.next()
        body = self._renderer().render(self.current)
        status = (
            f"\n\nmode={'auto' if self.auto else 'manual'} "
            f"speed={self.speed:.2f}Hz  renderer={self.renderer_name} "
            "press ? for keys"
        )
        if self.show_help:
            status += "\n\n" + help_text()
        return body + status

    def next(self) -> None:
        try:
            self.current = self.controller.next()
        except NoStepsAvailableError:
            pass

    def previous(self) -> None:
        try:
            self.current = self.controller.back()
        except NoStepsAvailableError:
            pass

    def reset(self) -> None:
        self.controller.reset()
        self.current = self.controller.next()

    def end(self) -> None:
        self.current = self.controller.run_to_end()

    def cycle_variant(self) -> None:
        variants = SearchRegistry.variants()
        index = variants.index(self.variant)
        self.variant = variants[(index + 1) % len(variants)]
        self.reset()

    def cycle_renderer(self) -> None:
        renderers = available_renderers()
        index = renderers.index(self.renderer_name)
        self.renderer_name = renderers[(index + 1) % len(renderers)]

    def cycle_colors(self) -> None:
        names = tuple(SCHEMES)
        index = names.index(self.color_scheme)
        self.color_scheme = names[(index + 1) % len(names)]

    def prompt_target(self, display: Display) -> None:
        display.close()
        raw = input("target: ")
        self.target = coerce_target(raw, self.array)
        self.controller = self._new_controller()
        self.current = self.controller.next()


def run_interactive(session: InteractiveSession) -> int:
    """Run the interactive session."""
    display = Display()
    try:
        with raw_terminal():
            while True:
                display.draw(session.frame())
                timeout = 1.0 / session.speed if session.auto else 0.1
                key = read_key(timeout)
                if key is None:
                    if session.auto:
                        session.next()
                    continue
                if key in ("q", "\x03"):
                    break
                _handle_key(session, key, display)
    except (KeyboardInterrupt, EOFError):
        pass
    except VisualizerError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    finally:
        display.close()
    if session.current is not None:
        print(
            f"{session.current.outcome.value}: result={session.current.result_index} "
            f"comparisons={session.current.comparisons}"
        )
    return 0


def _handle_key(session: InteractiveSession, key: str, display: Display) -> None:
    """Handle a keyboard key press."""
    if key in ("space", "right"):
        session.next()
    elif key == "left":
        session.previous()
    elif key == "r":
        session.reset()
    elif key == "g":
        session.end()
    elif key == "a":
        session.auto = not session.auto
    elif key == "+":
        session.speed = min(20.0, session.speed * 1.25)
    elif key == "-":
        session.speed = max(0.25, session.speed / 1.25)
    elif key == "v":
        session.cycle_variant()
    elif key == "m":
        session.cycle_renderer()
    elif key == "c":
        session.cycle_colors()
    elif key == "?":
        session.show_help = not session.show_help
    elif key == "t":
        session.prompt_target(display)
    elif key == "j":
        display.close()
        raw = input("step: ")
        try:
            step_number = int(raw)
        except ValueError:
            return
        try:
            session.current = session.controller.jump_to(step_number)
        except NoStepsAvailableError:
            return
