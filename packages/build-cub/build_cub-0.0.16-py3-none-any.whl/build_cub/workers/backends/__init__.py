"""Build backends for bear-shelf.

Each backend handles a specific compilation technology:
- gperf: GNU perfect hash function generator (preprocessing)
- cython: Cython to C/C++ compilation
- raw_cpp: Raw CPython API C++ extensions
- pybind11: Pybind11 C++ bindings (not yet implemented)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from lazy_bear import lazy

if TYPE_CHECKING:
    from build_cub.models._base import BaseBackendSettings
    from build_cub.models._build_data import BuildData
    from build_cub.plugins import BuildCubHook
    from build_cub.workers._meta import WorkerImport
    from build_cub.workers.backends._base import CompileBackend
else:
    BuildCubHook = lazy("build_cub.plugins", "BuildCubHook")

__all__ = ["run_backends"]

MODULE_PATH_BACKENDS = "build_cub.workers.backends"


def run_backends(build_data: dict[str, Any], data: BuildData, hook: BuildCubHook) -> None:
    """Run all enabled compilation backends in order."""
    from importlib import import_module

    from build_cub.utils import ColorPrinter
    from build_cub.utils._config import global_config
    from build_cub.workers._meta import get_module_map

    _print: ColorPrinter = ColorPrinter.get_instance()
    _print.debug(f"[backends] Discovering backends from: {global_config.all_backends}")

    backend_configs: list[WorkerImport] = get_module_map(
        build_data=data,
        workers=global_config.all_backends,
        suffix="Backend",
    )

    _print.debug(f"[backends] Found {len(backend_configs)} backend configs")

    if not any(settings.enabled for _, _, settings in backend_configs):
        _print.warn("No compilation backends are enabled; skipping backend processing.")
        return

    enabled_count: int = sum(1 for _, _, s in backend_configs if s.enabled and s.targets)
    _print.debug(f"[backends] {enabled_count} backends enabled with targets")

    only_backends: set[str] = global_config.only_backends
    skip_backends: set[str] = global_config.skip_backends

    for backend_name, backend_cls_name, settings in backend_configs:
        settings: BaseBackendSettings  # ty:ignore[invalid-declaration]
        if only_backends and backend_name not in only_backends:
            _print.debug(f"[backends] Skipping {backend_name} (not in only_backends)")
            continue
        if skip_backends and backend_name in skip_backends:
            _print.debug(f"[backends] Skipping {backend_name} (in skip_backends)")
            continue
        if not settings.enabled:
            _print.debug(f"[backends] Skipping {backend_name} (not enabled)")
            continue
        if not settings.targets:
            _print.debug(f"[backends] Skipping {backend_name} (no targets)")
            continue

        module = import_module(f"{MODULE_PATH_BACKENDS}.{backend_name}")
        backend_cls: type[CompileBackend] = getattr(module, backend_cls_name)
        backend: CompileBackend = backend_cls(should_run=True, settings=data, printer=_print, hook=hook)
        if backend.should_run:
            _print.debug(f"Running [cyan]{backend.name}[/] backend...")
            backend.execute(build_data=build_data)
        else:
            _print.debug(f"[backends] {backend.name} declined to run (should_run=False)")
