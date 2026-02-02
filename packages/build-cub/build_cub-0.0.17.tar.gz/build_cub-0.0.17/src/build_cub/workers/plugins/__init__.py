"""Preprocessing plugins for build-cub.

Plugins run before compilation backends:
- gperf: GNU perfect hash function generator (generates headers)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from build_cub.models._base import BaseSettings
    from build_cub.models._build_data import BuildData
    from build_cub.workers._base_worker import BaseWorker
    from build_cub.workers._meta import WorkerImport

__all__ = ["run_plugins"]

MODULE_PATH_PLUGINS = "build_cub.workers.plugins"


def run_plugins(build_data: dict[str, Any], data: BuildData) -> None:
    """Run all enabled preprocessing plugins in order."""
    from importlib import import_module

    from build_cub.utils import ColorPrinter, global_config
    from build_cub.workers._meta import get_module_map

    _print: ColorPrinter = ColorPrinter.get_instance()
    _print.debug(f"[plugins] Discovering plugins from: {global_config.all_plugins}")

    plugin_configs: list[WorkerImport] = get_module_map(
        data,
        global_config.all_plugins,
        suffix="Plugin",
    )

    if not plugin_configs:
        _print.debug("[plugins] No plugin configs found")
        return

    _print.debug(f"[plugins] Found {len(plugin_configs)} plugin configs")

    for plugin_name, plugin_cls_name, settings in plugin_configs:
        settings: BaseSettings
        if not settings.enabled:
            _print.debug(f"[plugins] Skipping {plugin_name} (not enabled)")
            continue

        module = import_module(f"{MODULE_PATH_PLUGINS}.{plugin_name}")
        plugin_cls: type[BaseWorker] | None = getattr(module, plugin_cls_name, None)
        if plugin_cls is None:
            _print.debug(f"Plugin class {plugin_cls_name} not found in module {module}.")
            continue
        plugin: BaseWorker = plugin_cls(should_run=True, settings=data, printer=_print)

        if plugin.should_run:
            _print.debug(f"Running [cyan]{plugin.name}[/] plugin...")
            plugin.execute(build_data=build_data)
        else:
            _print.debug(f"[plugins] {plugin.name} declined to run (should_run=False)")
