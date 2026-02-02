"""Raw CPython API C++ compilation backend."""

from __future__ import annotations

from typing import TYPE_CHECKING

from lazy_bear import lazy

from ._cpp_base import CppBackendBase

if TYPE_CHECKING:
    from build_cub.models._backends import RawCppSettings
    from build_cub.models._build_data import BuildData
    from build_cub.plugins import BuildCubHook
    from build_cub.utils._printer import ColorPrinter
else:
    RawCppSettings = lazy("build_cub.models._backends", "RawCppSettings")
    BuildCubHook = lazy("build_cub.plugins", "BuildCubHook")


class RawCppBackend(CppBackendBase[RawCppSettings]):
    """Raw CPython API C++ compilation backend."""

    name: str = "raw_cpp"
    dependencies: tuple[str, ...] = ("setuptools",)
    display_name: str = "C++"
    language: str = "c++"

    def __init__(self, should_run: bool, settings: BuildData, printer: ColorPrinter, hook: BuildCubHook) -> None:
        """Initialize the Raw C++ backend."""
        super().__init__(should_run, settings, printer, hook)
