from __future__ import annotations

from functools import cached_property
from pathlib import Path
from typing import TYPE_CHECKING, Any, Self

from pydantic import model_validator

from . import IgnoredModel
from ._backends import CythonSettings, GperfSettings, Pybind11Settings, Pyo3Settings, RawCppSettings
from ._defaults import DefaultSettings, GeneralSettings
from ._misc import Conditionals
from ._templates import VersioningSettings

if TYPE_CHECKING:
    from build_cub.models._misc import BaseConditional
    from build_cub.utils import ColorPrinter
    from build_cub.validation._models import ValidationReport

    from ._base import BaseBackendSettings, BaseSettings
    from ._version import Version


def _get_base_backend(base_setting: BaseSettings) -> BaseBackendSettings:
    """A very naughty way to tell type checker to take a hike."""
    return base_setting  # type: ignore[return-value]


class BuildData(IgnoredModel):
    """Root model that maps to the entire bear_build.toml file."""

    general: GeneralSettings = GeneralSettings()
    defaults: DefaultSettings = DefaultSettings()

    gperf: GperfSettings = GperfSettings()
    cython: CythonSettings = CythonSettings()
    pybind11: Pybind11Settings = Pybind11Settings()
    raw_cpp: RawCppSettings = RawCppSettings()
    pyo3: Pyo3Settings = Pyo3Settings()

    conditionals: Conditionals = Conditionals()
    versioning: VersioningSettings = VersioningSettings()

    def parse_conditionals(self, _print: ColorPrinter) -> None:
        """Parse and apply conditionals to the build data."""
        all_conditions: list[BaseConditional] = [
            *self.conditionals.env_var.values(),
            *self.conditionals.platform.values(),
            *self.conditionals.py_ver.values(),
        ]

        for cond in all_conditions:
            if cond:
                _print.debug(f"Applying conditional for '{cond}'...")
                cond.execute_all(self)

    @model_validator(mode="after")
    def post_init_work(self) -> Self:
        """Post-initialization to set up compiler settings inheritance."""
        if not self.general.enabled:
            return self

        from build_cub.utils import ColorPrinter, global_config

        _print: ColorPrinter = ColorPrinter.get_instance()
        if self.conditionals.not_empty:
            self.parse_conditionals(_print)

        for backend_name in global_config.all_backends:
            backend: BaseSettings
            backend = getattr(self, backend_name)
            if not hasattr(backend, "settings"):
                _print.debug(f"Backend '{backend_name}' does not have 'settings' attribute; skipping...")
                continue
            if not backend.enabled:
                _print.debug(f"Backend '{backend_name}' is not enabled; skipping...")
                continue
            if not backend.has_targets:
                _print.debug(f"Backend '{backend_name}' has no targets; skipping...")
                continue
            base_backend: BaseBackendSettings = _get_base_backend(backend)
            base_backend.settings.merge_with_defaults(self.defaults.settings, self.defaults.merge_mode)
        return self

    def get_backend(self, name: str) -> BaseBackendSettings:
        """Get backend settings by name."""
        from build_cub.utils import global_config

        if name not in global_config.all_backends:
            raise ValueError(f"Backend '{name}' is not a recognized backend.")
        backend: BaseBackendSettings = getattr(self, name)
        return backend

    @property
    def lib_files(self) -> list[str]:
        """Get the list of library files to include in build."""
        return self.defaults.lib_files

    @cached_property
    def pkg_root(self) -> Path:
        """Find package root - handles both src layout and flat layout (from sdist)."""
        src_layout = Path(f"src/{self.general.name}")
        flat_layout = Path(self.general.name)
        if src_layout.exists():
            return Path("src")
        if flat_layout.exists():
            return Path(".")
        raise FileNotFoundError(
            f"Cannot find package directory for '{self.general.name}'. "
            f"Checked: {src_layout} (src layout), {flat_layout} (flat layout)"
        )

    @cached_property
    def template_variables(self) -> dict[str, Any]:
        """Get all variables for template rendering.

        Combines:
        - version: Auto-injected from VCS (always available)
        - User-defined variables from [versioning.variables]
        """
        variables: dict[str, Any] = {"version": self.general.version.model_dump()}
        for key, value in self.versioning.variables.items():
            if hasattr(value, "model_dump"):
                variables[key] = value.model_dump()
            else:
                variables[key] = value
        return variables

    def render_templates(self) -> ValidationReport:
        """Render all templates and write to their output paths.

        Returns:
            List of output paths that were written.
        """
        from build_cub.validation._models import EMPTY_REPORT, ValidationReport

        if not self.versioning.has_templates:
            return EMPTY_REPORT

        jobs: ValidationReport = ValidationReport("templates")

        for template in self.versioning.templates:
            if template.content and template.output:
                jobs.add(template.write(self.template_variables))
        return jobs

    @classmethod
    def load_from_file(cls, path: Path | str, version: Version) -> BuildData:
        """Load build configuration from a TOML file.

        Error handling should be added to the calling code.
        """
        from build_cub.utils import TomlFile

        validated: BuildData = TomlFile(file=path).load_and().model_validate(BuildData)
        validated.general.version = version
        return validated
