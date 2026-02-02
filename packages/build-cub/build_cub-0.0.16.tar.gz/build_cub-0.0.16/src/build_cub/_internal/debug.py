from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Any, Literal, NamedTuple, Protocol, TextIO

if TYPE_CHECKING:
    import re

    from .info import _Package


class _Variable(NamedTuple):
    """Dataclass describing an environment variable."""

    name: str
    """Variable name."""
    value: str
    """Variable value."""


class _Environment(NamedTuple):
    """Dataclass to store environment information."""

    interpreter_info: _Variable
    """Python interpreter information."""
    interpreter_path: str
    """Path to Python executable."""
    platform: str
    """Operating System."""
    packages: list[Any]
    """Installed packages."""
    variables: list[_Variable]
    """Environment variables."""


def _interpreter_name_version() -> _Variable:
    if hasattr(sys, "implementation"):
        impl: sys._version_info = sys.implementation.version
        version: str = f"{impl.major}.{impl.minor}.{impl.micro}"
        kind: Literal["alpha", "beta", "candidate", "final"] = impl.releaselevel
        if kind != "final":
            version += kind[0] + str(impl.serial)
        return _Variable(sys.implementation.name, version)
    return _Variable("", "0.0.0")


def _get_debug_info() -> _Environment:
    """Get debug/environment information.

    Returns:
        Environment information.
    """
    from os import environ, getenv
    import platform

    from .info import METADATA

    py: _Variable = _interpreter_name_version()
    environ[f"{METADATA.name_upper}_DEBUG"] = "1"
    variables: list[str] = [
        "PYTHONPATH",
        *[var for var in environ if var.startswith(METADATA.name_upper)],
    ]
    return _Environment(
        interpreter_info=py,
        interpreter_path=sys.executable,
        platform=platform.platform(),
        variables=[_Variable(var, val) for var in variables if (val := getenv(var))],
        packages=_get_installed_packages(),
    )


def _get_installed_packages() -> list[_Package]:
    """Get all installed packages in current environment"""
    from importlib.metadata import distributions

    from .info import _Package

    packages: list[_Package] = []
    for dist in distributions():
        packages.append(_Package.new(name=dist.metadata["Name"]))
    return packages


class FunctionPointer(Protocol):
    def __call__(self, msg: object, indent: bool = False) -> None: ...


class _ConditionalPrinter:
    def __init__(
        self,
        no_color: bool = False,
        in_workflow: bool = False,
        theme: dict[str, str] | None = None,
        stderr: bool = False,
    ) -> None:
        from importlib.util import find_spec
        import os

        self.no_color: bool = no_color
        self._pattern: Any | None = None
        self._file: TextIO | Any = sys.stderr if stderr else sys.stdout
        self._rich_mode: bool = find_spec("rich") is not None
        self._ci_cd_mode: bool = os.environ.get("NOT_IN_WORKFLOW") != "true" and in_workflow
        self._printer: Any = self._get_printer(theme or {})
        self._set_function_pointer()

    def compiled_pattern(self) -> re.Pattern[str]:
        from re import compile as _compile

        return _compile(r"\[([^\]]+)\](.*?)\[/\]")

    @property
    def pattern(self) -> Any:
        if self._pattern is None:
            self._pattern = self.compiled_pattern() if not self._rich_mode else ""
        return self._pattern

    def _set_function_pointer(self) -> None:
        setattr(self, "print", self._regular_print) if not self._rich_mode else setattr(self, "print", self._rich_print)

    def _get_printer(self, theme: dict[str, str]) -> Any:
        if self._rich_mode:
            from rich.console import Console
            from rich.theme import Theme

            stderr: bool = self._file == sys.stderr
            if self._ci_cd_mode or self.no_color:
                # CI/CD environment or no color

                return Console(stderr=stderr, highlight=False, markup=True, force_terminal=False, no_color=True)
            return Console(stderr=stderr, highlight=True, markup=True, force_terminal=True, theme=Theme(theme))
        return print  # fallback to regular print

    def _rich_print(self, msg: object = "", **kwargs: object) -> None:
        """Print using rich console, only enabled if rich is available."""
        self._printer.print(msg, **kwargs)

    def _regular_print(self, msg: object = "", **kwargs: object) -> None:
        """Print using regular print, with simple markup removal."""
        kwargs.pop("style", None)
        msg = self.pattern.sub(r"\2", str(msg))
        self._printer(msg, file=self._file, **kwargs)

    def print(self, msg: object = "", **kwargs: object) -> None:
        """Will dynamically be replaced."""


def _print_debug_info(no_color: bool = False) -> None:
    """Print debug/environment information with minimal clean formatting."""
    info: _Environment = _get_debug_info()
    sections: list[tuple[str, list[tuple[str, str]]]] = [
        (
            "SYSTEM",
            [
                ("Platform", info.platform),
                ("Python", f"{info.interpreter_info.name} {info.interpreter_info.value}"),
                ("Location", info.interpreter_path),
            ],
        ),
        ("ENVIRONMENT", [(var.name, var.value) for var in info.variables]),
        ("PACKAGES", [(pkg.name, f"v{pkg.version}") for pkg in info.packages]),
    ]

    output: _ConditionalPrinter = _ConditionalPrinter(no_color=no_color)

    for i, (section_name, items) in enumerate(sections):
        if items:
            output.print(f"{section_name}", style="bold red")
            for key, value in items:
                output.print(key, style="bold blue", end=": ")
                output.print(value, style="bold green")
            if i < len(sections) - 1:
                output.print()


if __name__ == "__main__":
    _print_debug_info()
