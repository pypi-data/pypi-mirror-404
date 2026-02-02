"""A backend for compiling Rust/PyO3 extensions.

PyO3 allows writing Python extensions in Rust. This backend uses setuptools-rust
to compile Rust code and produce properly-named Python extension modules.

We are living our best crab life! 🦀
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

from lazy_bear import lazy

from build_cub.utils import CLOSE_BRACE, global_config

from ._base import CompileBackend

if TYPE_CHECKING:
    from shutil import which as shutil_which

    from setuptools_rust import RustExtension

    from build_cub.models._backends import Pyo3Settings
    from build_cub.models._base import RustSources
    from build_cub.models._build_data import BuildData
    from build_cub.plugins import BuildCubHook
    from build_cub.utils._funcs import search_paths
    from build_cub.utils._printer import ColorPrinter
    from build_cub.validation._models import ValidationReport
else:
    Pyo3Settings = lazy("build_cub.models._backends", "Pyo3Settings")
    RustExtension = lazy("setuptools_rust", "RustExtension")
    shutil_which = lazy("shutil", "which")
    ValidationReport = lazy("build_cub.validation._models", "ValidationReport")
    RustSources = lazy("build_cub.models._base", "RustSources")
    BuildCubHook = lazy("build_cub.plugins", "BuildCubHook")
    search_paths = lazy("build_cub.utils._funcs", "search_paths")


def _success(build_data: dict[str, Any], display_name: str, printer: ColorPrinter) -> None:
    printer.key_to_value(key=f"{display_name}", value=f"Compilation successful!\n{CLOSE_BRACE}", indent=True)
    build_data["pure_python"] = False
    build_data["infer_tag"] = True


class Pyo3Backend(CompileBackend[Pyo3Settings, RustSources]):
    """Rust/PyO3 extension backend using setuptools-rust.

    Uses RustExtension from setuptools-rust which handles:
    - Proper Python extension naming (e.g., _lib.cpython-314-darwin.so)
    - Cargo build invocation
    - Cross-platform compatibility
    """

    name: str = "pyo3"
    display_name: str = "Rust/PyO3"
    dependencies: tuple[str, ...] = ("setuptools_rust",)

    def __init__(self, should_run: bool, settings: BuildData, printer: ColorPrinter, hook: BuildCubHook) -> None:
        """Initialize the PyO3 backend."""
        super().__init__(should_run, settings, printer, hook)

    def _verify_dependencies(self) -> None:
        """Check that cargo is available in addition to setuptools-rust."""
        super()._verify_dependencies()
        if self.should_run and shutil_which("cargo") is None:
            self.should_run = False
            self.printer.warn("Cargo not found. Please install Rust toolchain to compile PyO3 extensions.")
        elif self.should_run:
            self.printer.debug(f"[{self.name}] Cargo found in PATH", indent=True)

    def _get_extensions(self, targets: list[RustSources]) -> list[RustExtension]:
        """Build RustExtension objects from Cargo.toml paths."""
        extensions: list[RustExtension] = []

        for target in targets:
            extensions.append(
                RustExtension(
                    target=self._to_module_name(target.output_path, remove_src=False),
                    path=str(target.sources),
                    features=self.local_settings.features,
                    debug=not self.local_settings.release,
                    quiet=self.local_settings.quiet,
                )
            )
        return extensions

    def execute(self, *, build_data: dict[str, Any]) -> None:
        """Run Rust/PyO3 compilation using setuptools-rust."""
        if not self.should_run:
            self.printer.debug(f"[{self.name}] Skipping (should_run=False)")
            return
        from setuptools import Distribution
        from setuptools_rust.build import build_rust

        from build_cub.validation._backends import validate_artifacts
        from build_cub.validation._models import Artifact

        targets: list[RustSources] = self._get_targets()
        num_targets: int = len(targets)
        self.printer.debug(f"[{self.name}] Found {num_targets} Cargo.toml targets")

        if num_targets == 0:
            self.printer.warn("No Cargo.toml files configured to compile.")
            return
        expected: dict[str, Artifact] = {t.name: Artifact(path=Path(t.name)).update(name=t.name) for t in targets}
        self.printer.debug(f"[{self.name}] Registered {len(expected)} expected artifacts")

        self.printer.debug(f"[{self.name}] Release mode: {self.local_settings.release}")
        self.printer.debug(f"[{self.name}] Features: {self.local_settings.features}")
        self.printer.debug(f"[{self.name}] Quiet: {self.local_settings.quiet}")

        extensions: list[RustExtension] = self._get_extensions(targets)
        self.printer.debug(f"[{self.name}] Built {len(extensions)} RustExtension objects")

        dist = Distribution({"rust_extensions": extensions})
        dist.packages = []

        cmd = build_rust(dist)
        cmd.inplace = True
        cmd.ensure_finalized()
        self.printer.debug(f"[{self.name}] Running cargo build (inplace=True)...")
        cmd.run()

        output_path: Path = self.local_settings.output_path
        self.printer.debug(f"[{self.name}] Build complete, looking for artifacts in: {output_path}")

        files: list[Path] = search_paths(output_path, exts=[global_config.misc.lib_ext])
        self.printer.debug(f"[{self.name}] Found {len(files)} lib files")

        for ext in extensions:
            ext_name: str = cast("str", ext.name).split(".")[-1]
            for file in files:
                if ext_name in file.stem:
                    self.printer.debug(f"[{self.name}] Matched artifact: {file}", indent=True)
                    rel_path: Path = file.relative_to(global_config.paths.cwd)
                    if ext_name in expected:
                        expected[ext_name].update(path=rel_path, src=file)
                    self._add_artifact(build_data, file)
                    break

        self.printer.debug(f"[{self.name}] Registered {len(expected)} expected artifacts")

        from functools import partial

        self.hook.register_validation(
            name=self.display_name,
            worker="backend",
            num_targets=num_targets,
            callback=partial(_success, build_data, self.display_name, self.printer),
            report=validate_artifacts("", list(expected.values())),
        )
