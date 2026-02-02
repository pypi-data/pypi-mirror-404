"""Pybind11 compilation backend."""

from __future__ import annotations

from typing import TYPE_CHECKING

from lazy_bear import lazy

from ._cpp_base import CppBackendBase

if TYPE_CHECKING:
    import pybind11

    from build_cub.models._backends import Pybind11Settings
    from build_cub.models._build_data import BuildData
    from build_cub.plugins import BuildCubHook
    from build_cub.utils._printer import ColorPrinter
else:
    Pybind11Settings = lazy("build_cub.models._backends", "Pybind11Settings")
    pybind11 = lazy("pybind11")
    BuildCubHook = lazy("build_cub.plugins", "BuildCubHook")


class Pybind11Backend(CppBackendBase[Pybind11Settings]):
    """Pybind11 compilation backend."""

    name: str = "pybind11"
    dependencies: tuple[str, ...] = ("pybind11", "setuptools")
    display_name: str = "pybind11"
    language: str = "c++"

    def __init__(self, should_run: bool, settings: BuildData, printer: ColorPrinter, hook: BuildCubHook) -> None:
        """Initialize the Pybind11 backend."""
        super().__init__(should_run, settings, printer, hook)

    @property
    def extra_include_dirs(self) -> list[str]:
        """Add pybind11's include directory."""
        return [pybind11.get_include()]
