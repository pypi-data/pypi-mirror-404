from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, Any

from lazy_bear import lazy

if TYPE_CHECKING:
    from build_cub.models._base import BaseSettings, BaseSources
    from build_cub.models._build_data import BuildData
    from build_cub.plugins import BuildCubHook
    from build_cub.utils import ColorPrinter
else:
    BuildCubHook = lazy("build_cub.plugins", "BuildCubHook")
    ColorPrinter = lazy("build_cub.utils._printer", "ColorPrinter")


class BaseWorker[Settings_T: BaseSettings, Target_T: BaseSources](ABC):
    name: str
    display_name: str = "worker"
    should_run: bool
    printer: ColorPrinter
    settings: BuildData
    local_settings: Settings_T
    dependencies: tuple[str, ...] = ()

    def __init__(self, should_run: bool, settings: BuildData, printer: ColorPrinter, hook: BuildCubHook) -> None:
        """Initialize the worker."""
        self.should_run: bool = should_run
        self.printer: ColorPrinter = printer
        self.settings: BuildData = settings
        self.local_settings: Settings_T = getattr(settings, self.name)
        self.hook: BuildCubHook = hook
        self._verify_dependencies()

    @abstractmethod
    def _verify_dependencies(self) -> None: ...

    @abstractmethod
    def execute(self, *, build_data: dict[str, Any]) -> None: ...

    @property
    def _target_names(self) -> set[str]:
        """Extract target names for artifact matching.

        Args:
            targets: The list from _get_targets()

        Returns:
            Set of base names (e.g., {"core", "record"}) used to filter artifacts
        """
        target_names: set[str] = set()
        for target in self.local_settings.targets:
            if isinstance(target, Path):
                target_names.add(target.stem)
            else:
                target_names.add(target.name)
        return target_names

    @staticmethod
    def _to_module_name(file: Path, remove_src: bool = True) -> str:
        """Convert a file path to a dotted module name."""
        parts: tuple[str, ...] = Path(file).with_suffix(suffix="").parts
        if remove_src and parts[0] == "src":
            parts = parts[1:]
        return ".".join(parts)

    @staticmethod
    def _get_base_name(file: Path) -> str:
        """Extract base module name from compiled artifact (strips platform suffix)."""
        return file.stem.split(".")[0]

    def _get_targets(self) -> list[Target_T]:
        """Return the list of targets to compile.

        Returns:
            List of targets (Path for Cython, SourcesItem for C++ backends)
        """
        return self.local_settings.targets
