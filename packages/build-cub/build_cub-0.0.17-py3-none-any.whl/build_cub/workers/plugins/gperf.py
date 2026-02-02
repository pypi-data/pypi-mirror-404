"""A Plugin for processing GNU gperf files.

Gperf is a perfect hash function generator used to create efficient lookup tables.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from lazy_bear import lazy

from build_cub.models._base import PathSource
from build_cub.workers._base_worker import BaseWorker

if TYPE_CHECKING:
    import subprocess

    from build_cub.models._backends import GperfSettings
    from build_cub.models._build_data import BuildData
    from build_cub.plugins import BuildCubHook
    from build_cub.utils._funcs import search_paths
    from build_cub.utils._printer import ColorPrinter
else:
    GperfSettings = lazy("build_cub.models._backends", "GperfSettings")
    subprocess = lazy("subprocess")
    BuildCubHook = lazy("build_cub.plugins", "BuildCubHook")
    search_paths = lazy("build_cub.utils._funcs", "search_paths")


def get_paths() -> list[str]:
    """Derive the possible paths for gperf."""
    from build_cub.utils import EMPTY_IMMUTABLE_LIST, global_config

    if global_config.platform.is_macos:
        return ["/opt/homebrew/bin/gperf", "/usr/local/bin/gperf", "/usr/bin/gperf"]
    if global_config.platform.is_linux:
        return ["/usr/bin/gperf", "/usr/local/bin/gperf"]
    if global_config.platform.is_windows:
        return [r"C:\Program Files\gperf\gperf.exe", r"C:\msys64\usr\bin\gperf.exe"]
    return EMPTY_IMMUTABLE_LIST


def which(cmd: str) -> str | None:
    """Locate a command in the system PATH."""
    from shutil import which as shutil_which

    return shutil_which(cmd)


def find_gperf_binary(configured_binary: str) -> str | None:
    """Find gperf binary with platform-specific fallbacks.

    Tries in order:
    1. The configured binary (if specified and found)
    2. 'gperf' in PATH
    3. Platform-specific fallback paths
    """
    if configured_binary and which(configured_binary):
        return configured_binary

    if which("gperf"):
        return "gperf"
    paths: list[str] = get_paths()
    for path in paths:
        if Path(path).exists():
            return path

    return None


class GperfPlugin(BaseWorker[GperfSettings, PathSource]):
    """GNU perfect hash function generator plugin."""

    name: str = "gperf"
    ext: tuple[str] = (".gperf",)

    def __init__(self, should_run: bool, settings: BuildData, printer: ColorPrinter, hook: BuildCubHook) -> None:
        """Initialize the Gperf plugin."""
        super().__init__(should_run, settings, printer, hook)

    def _verify_dependencies(self) -> None:
        configured_binary: str = self.settings.gperf.binary
        self.printer.debug(f"[{self.name}] Looking for gperf binary (configured: {configured_binary})")
        found_binary: str | None = find_gperf_binary(configured_binary)

        if found_binary is None:
            self.should_run = False
            self.printer.warn("Gperf binary not found. Please install gperf to proceed.")
            return
        if found_binary != configured_binary:
            self.settings.gperf.binary = found_binary
            self.printer.info(f"Using gperf binary: {found_binary}", indent=True)
        self.printer.debug(f"[{self.name}] Found gperf at: {found_binary}", indent=True)

    def _post_execute(self, header_file: Path) -> None:
        """Remove #line directives and 'register' keyword from gperf output."""
        if not header_file:
            return
        new_lines: list[str] = [line for line in header_file.read_text().splitlines() if not line.startswith("#line")]
        output: str = "\n".join(new_lines) + "\n"
        header_file.write_text(output.replace("register ", ""))

    def _pre_check(self, gperf_files: list[Path], ext: str) -> list[Path]:
        """Pre-compilation check for .gperf files."""
        files_to_keep = []
        for gperf_file in gperf_files:
            expected_header: Path = gperf_file.with_suffix(ext)
            if expected_header.exists():
                if gperf_file.stat().st_mtime < expected_header.stat().st_mtime:
                    self.printer.key_to_value(f"Skipping {gperf_file.name}", "(up to date)", indent=True)
                else:
                    files_to_keep.append(gperf_file)
                    expected_header.unlink()
        return files_to_keep

    def execute(self, *, build_data: dict[str, Any]) -> None:  # noqa: ARG002
        """Process .gperf files to generate header files."""
        if not self.should_run:
            self.printer.debug(f"[{self.name}] Skipping (should_run=False)")
            return

        gperf_files: list[Path] = search_paths(self.settings.pkg_root, exts=self.ext)
        self.printer.debug(f"[{self.name}] Found {len(gperf_files)} .gperf files in {self.settings.pkg_root}")

        if not gperf_files:
            self.printer.warn("No .gperf files found to process.", indent=True)
            return

        cmd: list[str] = self.local_settings.cmd
        self.printer.debug(f"[{self.name}] Base command: {cmd}")
        gperf_files: list[Path] = self._pre_check(gperf_files=gperf_files, ext=self.local_settings.target_ext)
        self.printer.debug(f"[{self.name}] After pre-check: {len(gperf_files)} files need processing")

        for gperf_file in gperf_files:
            header_file: Path = gperf_file.with_suffix(suffix=self.local_settings.target_ext)
            cmd[3] = str(gperf_file)
            cmd[4] = f"--output-file={header_file}"

            self.printer.debug(f"[{self.name}] Running: {' '.join(cmd)}", indent=True)
            subprocess.run(cmd, check=True)

            if header_file.exists():
                self.printer.key_to_value(f"Generated {gperf_file.name}", header_file.name, indent=True)
                self._post_execute(header_file)
