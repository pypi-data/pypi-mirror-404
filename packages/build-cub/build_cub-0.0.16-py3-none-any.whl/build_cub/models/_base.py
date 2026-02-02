from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from ._defaults import CompilerSettings


class BaseSources[T](BaseModel):
    name: str
    sources: T

    model_config = ConfigDict(extra="ignore")


class PathSource(BaseSources[Path]):
    @property
    def module_name(self) -> str:
        from build_cub.utils import get_parts

        return get_parts(self.sources, to_module=True)


class SourcesItem(BaseSources[list[str]]):
    """Model for a source item in backend targets.

    This is typically used when you want to compile multiple source files into a single module.
    """

    @property
    def module_name(self) -> str:
        from build_cub.utils import get_parts

        return get_parts(Path(self.sources[0]), to_module=True)

    def add_to_sources(self, new_sources: list[str] | str) -> None:
        """Add sources to the sources list."""
        if isinstance(new_sources, str):
            new_sources = [new_sources]
        self.sources.extend(new_sources)


class RustSources(BaseSources[str]):
    """Model for a source item with metadata-added sources.

    Used internally to track sources that have had metadata files (e.g., generated headers) added.
    """

    sources: str
    output_path: Path


class BaseSettings[T](BaseModel):
    """Base class for backend settings sections."""

    name: str = Field(default="")
    enabled: bool = Field(default=False)
    cleanup: bool = Field(default=True)
    targets: list[T] = Field(default_factory=list)

    model_config = ConfigDict(extra="ignore")

    @property
    def has_targets(self) -> bool:
        """Check if any targets are specified for this backend."""
        return bool(self.targets)


class BaseBackendSettings[T: BaseSources](BaseSettings[T]):
    """Base class for backend-specific settings in bear_build.toml.

    Each backend section ([cython], [raw_cpp], etc.) maps to a subclass of this.
    """

    settings: CompilerSettings = Field(default_factory=CompilerSettings)

    def get_compiler_settings(self) -> CompilerSettings:
        """Get the compiler settings for this backend."""
        return self.settings

    def get_target(self, name: str) -> T:
        """Get a target by name."""
        for target in self.targets:
            if target.name == name:
                return target
        raise ValueError(f"Target '{name}' not found in backend '{self.name}'.")


__all__ = ["BaseBackendSettings", "BaseSettings", "RustSources", "SourcesItem"]
