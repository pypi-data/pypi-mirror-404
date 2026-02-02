from __future__ import annotations

from build_cub._internal.debug import _ConditionalPrinter
from singleton_base import SingletonBase

from ._config import global_config
from ._funcs import NOOP_FUNCTION

INDENT: str = " " * 4
OPEN_BRACKET = "["
CLOSE_BRACKET = "]"
CBO: str = f"[cyan]{OPEN_BRACKET}[/]"
CBC: str = f"[cyan]{CLOSE_BRACKET}[/]"
ARROW: str = "[red]->[/]"
CHECKMARK: str = "[magenta]✓[/]"
YE: str = "[yellow]"
BM: str = "[bold magenta]"
RED: str = "[red]"


THEME_DICT: dict[str, str] = {
    "info": "dim cyan",
    "warning": "bold yellow",
    "error": "bold red",
    "success": "bold green",
    "debug": "dim magenta",
}


class ColorPrinter(SingletonBase):
    """Simple printer class for console."""

    def __init__(self) -> None:
        self.console: _ConditionalPrinter = _ConditionalPrinter(theme=THEME_DICT, stderr=True)
        setattr(self, "debug", self._debug) if global_config.debug else setattr(self, "debug", NOOP_FUNCTION)

        if global_config.quiet:
            self.quiet_mode()

    def quiet_mode(self) -> None:
        """Will silence everything except for errors and debug msgs if enabled."""
        setattr(self, "update", NOOP_FUNCTION)
        setattr(self, "key_to_value", NOOP_FUNCTION)
        setattr(self, "info", NOOP_FUNCTION)
        setattr(self, "warn", NOOP_FUNCTION)
        setattr(self, "success", NOOP_FUNCTION)

    def update(self, msg: object, indent: bool = False, style: str | None = None) -> None:
        """Print an update message to the console."""
        prefix: str = INDENT if indent else ""
        self.console.print(f"{prefix}{msg}", style=style)

    def key_to_value(self, key: object, value: object, indent: bool = False) -> None:
        ind: str = INDENT if indent else ""
        k_to_v: str = f"{ind}{CBO}{YE}{key}[/]{CBC} {ARROW} {BM}{value}[/]"
        self.update(k_to_v, style="success")

    def info(self, msg: object, indent: bool = False) -> None:
        self.update(msg, indent=indent, style="info")

    def error(self, msg: object, indent: bool = False) -> None:
        self.update(msg, indent=indent, style="error")

    def warn(self, msg: object, indent: bool = False) -> None:
        self.update(msg, indent=indent, style="warning")

    def success(self, msg: object, indent: bool = False) -> None:
        self.update(f"{CHECKMARK} {msg}", indent=indent, style="success")

    def _debug(self, msg: object, indent: bool = False) -> None:
        prefix: str = INDENT if indent else ""
        self.console.print(f"{prefix}{msg}", style="debug")

    def debug(self, msg: object, indent: bool = False) -> None: ...


__all__ = ["ColorPrinter"]

# ruff: noqa: B010
