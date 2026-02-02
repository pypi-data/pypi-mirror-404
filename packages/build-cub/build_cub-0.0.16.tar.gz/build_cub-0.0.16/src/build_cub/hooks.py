"""Module defining a custom version source plugin for Hatchling using Dunamai."""

from hatchling.plugin import hookimpl
from hatchling.version.source.plugin.interface import VersionSourceInterface

from .plugins import BaseCustomPlugin


class DynamicVersioningSrc(BaseCustomPlugin, VersionSourceInterface):
    """A custom version source plugin for Hatchling using Dunamai."""

    PLUGIN_NAME = "build-cub"

    def get_version_data(self) -> dict[str, str]:
        """Get version data for the build process."""
        return {"version": str(self.version)}


@hookimpl
def hatch_register_version_source() -> type[DynamicVersioningSrc]:
    """Register the custom version source plugin."""
    return DynamicVersioningSrc
