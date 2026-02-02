"""A custom build hook that handles the build process."""  # noqa: INP001

from __future__ import annotations

from typing import Any

from hatchling.builders.hooks.plugin.interface import BuildHookInterface

from build_cub.plugins import BuildCubHook


class CustomBuildHook(BuildHookInterface):
    PLUGIN_NAME = "custom"

    def initialize(self, version: Any, build_data: dict[str, Any]) -> None:  # noqa: ARG002
        """Initialize the build hook."""
        with BuildCubHook() as hook:
            hook.printer.info("Starting custom build hook...")
            hook.render_template()
            hook.run_backends(build_data)
