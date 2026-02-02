"""A custom version source plugin for Hatchling using Dunamai."""

from __future__ import annotations

from collections.abc import Callable  # noqa: TC003
from dataclasses import dataclass, field
from time import perf_counter
from typing import TYPE_CHECKING, Any, Literal, Self

if TYPE_CHECKING:
    from build_cub.models._build_data import BuildData
    from build_cub.models._misc import BuildConfig
    from build_cub.models._version import Version
    from build_cub.utils import ColorPrinter
    from build_cub.validation._models import ValidationReport

type WorkerTypeLiteral = Literal["backend", "plugin"]


class QuickTimer:
    __slots__ = ("_elapsed", "_end", "_start")

    _start: float
    _end: float
    _elapsed: float

    def __init__(self) -> None:
        self._start = 0.0
        self._end = 0.0
        self._elapsed = 0.0

    def start(self) -> None:
        self._start = perf_counter()

    def stop(self) -> None:
        self._end = perf_counter()
        self._elapsed = self._end - self._start

    def above_one(self) -> bool:
        return self._elapsed >= 1.0

    @property
    def elapsed(self) -> float:
        return self._elapsed

    @property
    def elapsed_ms(self) -> float:
        return self._elapsed * 1000.0


class BaseCustomPlugin:
    """Base class for custom build hooks."""

    _build_config: BuildConfig | None
    _printer: ColorPrinter | None
    _build_data: BuildData | None
    _version: Version | None

    __slots__ = ("_build_config", "_build_data", "_printer", "_version")

    def __init__(self, build_data: BuildData | None = None, *args, **kwargs) -> None:  # noqa: ARG002
        """Initialize the VersionBasePlugin."""
        self._build_config = None
        self._build_data = build_data
        self._version: Version | None = None
        self._printer = None

    @property
    def printer(self) -> ColorPrinter:
        """Lazy loaded print helper."""
        if self._printer is None:
            from build_cub.utils import ColorPrinter

            self._printer = ColorPrinter.get_instance()
        return self._printer

    @property
    def build_config(self) -> BuildConfig:
        """Lazily loaded ``pyproject.toml`` options extraction."""
        if self._build_config is None:
            from build_cub.models._misc import BuildConfig

            self._build_config = BuildConfig.load_from_file()
        return self._build_config

    @property
    def build_data(self) -> BuildData:
        """Get the build data, loading it if necessary."""
        if self._build_data is None:
            from build_cub.models._build_data import BuildData

            self._build_data = BuildData.load_from_file(self.build_config.config_path, self.version)
        return self._build_data

    @property
    def version(self) -> Version:
        """Get the current version information."""
        if self._version is None:
            from build_cub.models._version import Version

            self._version = Version.get_version(self.build_config)
        return self._version


@dataclass(slots=True)
class ResolutionCallback:
    """A callback for if a validator record is successful."""

    name: str
    num_targets: int
    callback: Callable
    validation: ValidationReport
    messages: dict[str, str] = field(default_factory=dict)

    def add_msg(self, key: str, value: str) -> None:
        """Add a message to the callback."""
        self.messages[key] = value


class BuildCubHook(BaseCustomPlugin):
    """A custom version source plugin for Hatchling using Dunamai."""

    def __init__(self, build_data: BuildData | None = None, *args, **kwargs) -> None:
        """Initialize the BuildCubHook."""
        super().__init__(build_data, *args, **kwargs)
        from build_cub.utils import global_config

        self.show_time: bool = global_config.print_time_to_build
        self.timer = QuickTimer()
        if self.build_data.general.enabled:
            self.backend_validations: dict[str, ResolutionCallback] = {}
            self.plugin_validations: dict[str, ResolutionCallback] = {}

    def register_validation(
        self,
        name: str,
        num_targets: int,
        worker: WorkerTypeLiteral,
        report: ValidationReport,
        callback: Callable,
    ) -> None:
        """Register a validation report for final summary."""
        if worker == "backend":
            self.backend_validations[name] = ResolutionCallback(name, num_targets, callback, report)
        else:
            self.plugin_validations[name] = ResolutionCallback(name, num_targets, callback, report)

    def register_message(
        self,
        name: str,
        key: str,
        value: str,
        worker: WorkerTypeLiteral,
    ):
        """Register a message for final summary."""
        if worker == "backend" and name in self.backend_validations:
            self.backend_validations[name].add_msg(key, value)
        elif worker == "plugin" and name in self.plugin_validations:
            self.plugin_validations[name].add_msg(key, value)

    def run_backends(self, plugin_build_data: dict[str, Any]) -> None:
        """Utility method to easily expose running backends."""
        if self.build_data.general.enabled:
            from build_cub.utils import OPEN_BRACE
            from build_cub.workers.backends import run_backends

            run_backends(build_data=plugin_build_data, data=self.build_data, hook=self)

            for name, v in self.backend_validations.items():
                self.printer.key_to_value(
                    f"Compiling [red]{v.num_targets}[/] {v.name} {'files' if v.num_targets > 1 else 'file'}",
                    value=f"{OPEN_BRACE}",
                )
                for key, msg in v.messages.items():
                    self.printer.key_to_value(key, msg, indent=True)
                self.printer.key_to_value(name, f"{v.validation}", indent=True)
                for dest in v.validation.passed_jobs:
                    self.printer.key_to_value("New Artifact", dest.name, indent=True)
                    self.printer.key_to_value(dest.name, f"{dest.parent}/", indent=True)
                if v.validation.all_passed:
                    v.callback()
                    continue
                if not v.validation.all_passed:
                    for result in v.validation.failed_jobs:
                        self.printer.error(f"Artifact validation failed: {result.msg}", indent=True)

    def run_plugins(self, plugin_build_data: dict[str, Any]) -> None:
        """Utility method to easily expose running plugins."""
        if self.build_data.general.enabled:
            from build_cub.workers.plugins import run_plugins

            run_plugins(build_data=plugin_build_data, data=self.build_data)

    def render_template(self) -> None:
        """Render the template with the given variables."""
        from build_cub.utils import CLOSE_BRACE, OPEN_BRACE

        jobs: ValidationReport = self.build_data.render_templates()
        self.printer.key_to_value(f"{jobs} ", value=f"{OPEN_BRACE}")
        for path in jobs.passed_jobs:
            self.printer.key_to_value("Generated Template", f"{path!s}\n{CLOSE_BRACE}", indent=True)
        for failed_job in jobs.failed_jobs:
            self.printer.error(
                f"Failed to generate template: {failed_job.msg}: {failed_job.path}\n{CLOSE_BRACE}", indent=True
            )
            for detail in failed_job.details:
                self.printer.warn(detail, indent=True)

    def __enter__(self) -> Self:
        """Start timing the build hook."""
        self.timer.start()
        return self

    def __exit__(self, exc_type: object, exc_value: object, traceback: object) -> None:
        """End timing the build hook and print the elapsed time."""
        self.timer.stop()
        if self.timer.above_one() and self.show_time:
            self.printer.success(f"Build hook completed in {self.timer.elapsed:.2f} seconds.")
        elif self.show_time:
            self.printer.success(f"Build hook completed in {self.timer.elapsed_ms:.2f} ms.")


__all__ = ["BuildCubHook"]
