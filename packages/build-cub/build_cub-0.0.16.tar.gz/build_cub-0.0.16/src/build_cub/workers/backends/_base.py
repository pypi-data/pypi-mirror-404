"""Base class for compilation backends with shared execute() logic."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, cast

from lazy_bear import lazy

from build_cub.workers._base_worker import BaseWorker

if TYPE_CHECKING:
    from importlib.util import find_spec
    from pathlib import Path

    from setuptools import Distribution, Extension
    from setuptools.command.build_ext import build_ext

    from build_cub.models._base import BaseSettings, BaseSources
    from build_cub.models._build_data import BuildData
    from build_cub.plugins import BuildCubHook
    from build_cub.utils import copy_file_into
    from build_cub.utils._funcs import search_paths
    from build_cub.utils._printer import ColorPrinter
    from build_cub.validation._backends import validate_artifacts
    from build_cub.validation._models import Artifact, ValidationReport
else:
    Path = lazy("pathlib", "Path")
    copy_file_into = lazy("build_cub.utils", "copy_file_into")
    find_spec = lazy("importlib.util", "find_spec")
    Distribution = lazy("setuptools", "Distribution")
    build_ext = lazy("setuptools.command.build_ext", "build_ext")
    validate_artifacts = lazy("build_cub.validation._backends", "validate_artifacts")
    ValidationReport, Artifact = lazy("build_cub.validation._models", "ValidationReport", "Artifact")
    BuildCubHook = lazy("build_cub.plugins", "BuildCubHook")
    Extension = lazy("setuptools", "Extension")
    ColorPrinter = lazy("build_cub.utils._printer", "ColorPrinter")
    search_paths = lazy("build_cub.utils._funcs", "search_paths")


def _success(build_data: dict[str, Any], display_name: str, printer: ColorPrinter) -> None:
    from build_cub.utils import CLOSE_BRACE

    printer.key_to_value(key=f"{display_name}", value=f"Compilation successful!\n{CLOSE_BRACE}", indent=True)
    build_data["pure_python"] = False
    build_data["infer_tag"] = True


class CompileBackend[Settings_T: BaseSettings, Target_T: BaseSources](BaseWorker[Settings_T, Target_T], ABC):
    """Base class for compilation backends.

    Subclasses configure via class attributes:
        - name: Backend name matching the settings section (e.g., "cython", "pybind11")
        - _dependencies: Required packages to verify before running
        - _display_name: Human-readable name for log messages

    Subclasses MUST implement:
        - _get_targets() -> list of targets to compile
        - _get_extensions(targets) -> list[Extension] for setuptools
        - _get_target_names(targets) -> set[str] for artifact matching

    Subclasses MAY override hooks:
        - _pre_execute(extensions) -> wrap/transform extensions (e.g., cythonize)
        - _post_artifact_copy(dest) -> cleanup after each artifact copy
        - extra_include_dirs property -> add backend-specific include paths
    """

    name: str
    display_name: str = "extension"

    def __init__(self, should_run: bool, settings: BuildData, printer: ColorPrinter, hook: BuildCubHook) -> None:
        """Initialize the backend."""
        super().__init__(should_run=should_run, settings=settings, printer=printer, hook=hook)

    @property
    def extra_include_dirs(self) -> list[str]:
        """Override to add backend-specific include directories."""
        return []

    def _verify_dependencies(self) -> None:
        """Check that all required packages are available."""
        self.printer.debug(f"[{self.name}] Checking dependencies: {self.dependencies}")
        missing: list[str] = []

        for package in self.dependencies:
            if find_spec(package) is None:
                missing.append(package)
        if missing:
            self.should_run = False
            self.printer.warn(
                f"Missing dependencies for {self.name}: {', '.join(missing)}. Please install them to proceed."
            )
        else:
            self.printer.debug(f"[{self.name}] All dependencies satisfied", indent=True)

    def _get_targets(self) -> list[Target_T]:
        """Return the list of targets to compile.

        Returns:
            List of targets (Path for Cython, SourcesItem for C++ backends)
        """
        return self.local_settings.targets

    def _pre_execute(self, data: list[Any]) -> list[Any]:
        """Hook called before execute."""
        return data

    def _post_execute(self, data: Artifact) -> None:  # noqa: ARG002
        """Optional post-execution hook."""
        return

    @abstractmethod
    def _get_extensions(self, targets: list[Target_T]) -> list[Any]:
        """Build Extension objects from targets.

        Args:
            targets: The list from _get_targets()

        Returns:
            List of setuptools Extension objects ready for compilation
        """

    def _add_artifact(self, bd: dict[str, Any], v: Any) -> None:
        if not isinstance(v, str):
            v = str(v)
        cast("list", bd["artifacts"]).append(v)

    def _copy_artifacts(
        self,
        build_lib: Path,
        build_data: dict[str, Any],
        target_names: set[str],
        expected: dict[str, Artifact],
    ) -> list[Artifact]:
        """Copy compiled artifacts from build_lib to pkg_root.

        Only copies files whose stem (without platform suffix) matches one of the target_names.
        This prevents double-copying artifacts from previous backends.

        When a match is found, the corresponding expected artifact's path is updated
        to the real destination so validation can verify existence.

        Args:
            build_lib: The setuptools build directory
            build_data: The hatch build_data dict to append artifacts to
            target_names: Set of base names (e.g. {"core", "record"}) to copy
            expected: Dict of target name -> Artifact (sentinel paths, updated in-place on success)

        Returns:
            List of destination paths that were copied (for cleanup hooks)
        """
        files: list[Path] = search_paths(build_lib, self.settings.lib_files)
        self.printer.debug(f"[{self.name}] Found {len(files)} lib files in {build_lib}")
        copied: list[Artifact] = []

        for src in files:
            base_name: str = self._get_base_name(src)
            if base_name not in target_names:
                self.printer.debug(f"[{self.name}] Skipping {src.name} (not in target set)", indent=True)
                continue
            relative: Path = src.relative_to(build_lib)
            dest: Path = self.settings.pkg_root / relative
            self.printer.debug(f"[{self.name}] Copying: {src} -> {dest}", indent=True)
            copy_file_into(file=src, dest=dest, mkdir=True)
            self._add_artifact(build_data, dest)

            if base_name in expected:
                expected[base_name].update(path=dest, src=src)
                copied.append(expected[base_name])
            else:
                copied.append(Artifact(path=dest).set("src", src))

        self.printer.debug(f"[{self.name}] Copied {len(copied)} artifacts to {self.settings.pkg_root}")
        return copied

    def execute[T](self, *, build_data: dict[str, Any]) -> None:
        """Run compilation for this backend.

        This method orchestrates the full compilation pipeline:
        1. Get targets and validate
        2. Inject debug symbols if enabled
        3. Build extensions
        4. Apply pre-compile hook (e.g., cythonize)
        5. Run setuptools compilation
        6. Copy artifacts and run post-copy hooks
        7. Update build_data flags
        """
        if not self.should_run:
            self.printer.debug(f"[{self.name}] Skipping (should_run=False)")
            return

        targets: list[Target_T] = self._get_targets()
        num_targets: int = len(targets)
        self.printer.debug(f"[{self.name}] Found {num_targets} targets: {[str(t) for t in targets]}")

        if num_targets == 0:
            self.printer.warn(f"No {self.display_name} files configured to compile.")
            return
        from functools import partial

        # TODO: Too many data structures being created around here?
        expected: dict[str, Artifact] = {t.name: Artifact(path=Path(t.name)).set("name", t.name) for t in targets}
        self.printer.debug(f"[{self.name}] Registered {len(expected)} expected artifacts")

        extensions: list[Extension] = self._get_extensions(targets)
        self.printer.debug(f"[{self.name}] Built {len(extensions)} extensions")
        extensions: list[Extension] = self._pre_execute(extensions)

        dist = Distribution({"ext_modules": extensions})
        cmd = build_ext(dist)
        cmd.ensure_finalized()
        self.printer.debug(f"[{self.name}] Running setuptools build_ext...")
        cmd.run()

        build_lib = Path(cmd.build_lib)
        self.printer.debug(f"[{self.name}] Build complete, artifacts in: {build_lib}")
        target_names: set[str] = self._target_names
        copied: list[Artifact] = self._copy_artifacts(build_lib, build_data, target_names, expected)

        self.hook.register_validation(
            name=self.display_name,
            worker="backend",
            num_targets=num_targets,
            report=validate_artifacts("", list(expected.values())),
            callback=partial(_success, build_data, self.display_name, self.printer),
        )

        for dest in copied:
            self._post_execute(dest)
