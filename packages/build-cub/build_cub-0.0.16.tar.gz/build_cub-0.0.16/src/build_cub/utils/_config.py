"""Configuration management for Build Cub.

Runtime configuration that can be overridden via environment variables.
All settings use the BUILD_CUB_ prefix (e.g., BUILD_CUB_ONLY_BACKENDS=pybind11).
"""

from __future__ import annotations

from enum import StrEnum
from functools import cached_property
from os import getenv
from pathlib import Path
import sys
from typing import Any, Final, cast

from bear_config.manager import ConfigManager
from pydantic import BaseModel, ConfigDict, Field, field_validator

from build_cub.utils._types import BinaryExtension, CompileArgs, LinkArgs  # noqa: TC001
from singleton_base import SingletonWrap

VERSION_INFO = cast("tuple", sys.version_info)


def get_names(path: Path) -> list[str]:
    """Get the names of all backend modules in the specified directory."""
    return [file.stem for file in path.glob("*.py") if not file.name.startswith("_")]


class OS(StrEnum):
    """Enum for operating system platforms."""

    WINDOWS = "windows"
    LINUX = "linux"
    DARWIN = "darwin"
    UNKNOWN = "unknown"

    @classmethod
    def get_platform(cls) -> OS:
        platform_str: str = sys.platform.lower()
        if platform_str.startswith("win"):
            return OS.WINDOWS
        if platform_str.startswith("linux"):
            return OS.LINUX
        if platform_str.startswith("darwin"):
            return OS.DARWIN
        return OS.UNKNOWN


_CURRENT_PLATFORM: OS = OS.get_platform()
_IS_WINDOWS: bool = _CURRENT_PLATFORM == OS.WINDOWS
_IS_MACOS: bool = _CURRENT_PLATFORM == OS.DARWIN
_IS_LINUX: bool = _CURRENT_PLATFORM == OS.LINUX

_CUSTOM_PATH: Final = ("tool", "hatch", "build", "hooks", "custom")
"""Toml path to where the settings are within ``pyproject.toml``."""

_CWD: Final[Path] = Path.cwd()
"""The current working directory.

This current working directory HAS to be the directory that has the ``pyproject.toml``
else ``uv build`` will not work and thus not call this code.

If you try to call uv build from another cwd you'll get:
``does not appear to be a Python project, as neither `pyproject.toml` nor `setup.py` are present in the directory``.

Thus, this is inherently not dangerous since UV will just not run if we are in ANY other directory other than the user's
specified Python directory.
"""

OPEN_BRACE = "{"
CLOSE_BRACE = "}"


class Paths(BaseModel):
    """Paths for important files."""

    cwd: Path = Field(default=_CWD)
    cargo_toml: Path = Field(default=_CWD / "Cargo.toml")
    pyproject_toml: Path = Field(default=_CWD / "pyproject.toml")
    backend_path: Path = Field(default=Path(__file__).parent.parent / "workers" / "backends")
    plugin_path: Path = Field(default=Path(__file__).parent.parent / "workers" / "plugins")


class Platform(BaseModel):
    """Platform information."""

    os: OS = Field(default=_CURRENT_PLATFORM)
    is_windows: bool = Field(default=_IS_WINDOWS)
    is_macos: bool = Field(default=_IS_MACOS)
    is_linux: bool = Field(default=_IS_LINUX)
    not_macos: bool = Field(default=not _IS_MACOS)


class Keys(BaseModel):
    """Keys for configuration."""

    compiler_args: CompileArgs = Field(default="extra_compile_args_windows" if _IS_WINDOWS else "extra_compile_args")
    link_args: LinkArgs = Field(default="extra_link_args_windows" if _IS_WINDOWS else "extra_link_args")


class Misc(BaseModel):
    """Miscellaneous configuration."""

    path_to_custom: tuple[str, ...] = Field(default=_CUSTOM_PATH, description="Path to custom build in pyproject.toml")
    default_output: set[BinaryExtension] = {".so", ".pyd", ".dylib"}
    rust_cmd: tuple[str, ...] = ("cargo", "build")

    @cached_property
    def lib_ext(self) -> BinaryExtension:
        return ".pyd" if _IS_WINDOWS else ".so"


class BuildCubConfig(BaseModel):
    """Configuration for Build Cub runtime behavior.

    These settings control how build-cub runs and can be overridden via
    environment variables with the BUILD_CUB_ prefix.
    """

    env: str = Field(default="prod", description="Environment name (prod, dev, test)")
    debug: bool = False
    # verbose: bool = False  # PLACEHOLDER, NOT YET ENABLED.
    quiet: bool = Field(default=False, description="Suppress all non-error output")
    only_backends: set[str] = Field(
        default_factory=set,
        description="Only run these backends (e.g., ['pybind11']). Empty means run all enabled.",
    )
    skip_backends: set[str] = Field(
        default_factory=set, description="Skip these backends. Applied after only_backends."
    )

    print_time_to_build: bool = Field(default=True, description="Print time taken to build each backend")
    debug_symbols: bool = Field(default=False, description="Override [general].debug_symbols at runtime")

    model_config = ConfigDict(extra="ignore", frozen=True)

    platform: Platform = Platform()
    keys: Keys = Keys()
    paths: Paths = Paths()
    misc: Misc = Misc()

    @field_validator("only_backends", "skip_backends", mode="before")
    @classmethod
    def validate_backends(cls, obj: Any) -> set[str]:
        if isinstance(obj, set):
            return obj
        if isinstance(obj, (list | tuple)):
            return set(obj)
        raise ValueError(f"Invalid type for backend list: {type(obj)}. Must be set of strings.")

    @cached_property
    def all_backends(self) -> list[str]:
        """Get all available backend names."""
        return get_names(self.paths.backend_path)

    @cached_property
    def all_plugins(self) -> list[str]:
        """Get all available plugin names."""
        return get_names(self.paths.plugin_path)

    @property
    def python_ver(self) -> tuple[int, ...]:
        """Get the current Python version as a tuple."""
        return VERSION_INFO

    @cached_property
    def python_314_or_newer(self) -> bool:
        """Check if the Python version is 3.14 or newer."""
        return self.python_ver >= (3, 14)


_config_singleton: SingletonWrap[ConfigManager[BuildCubConfig]] | None = None


def get_config_manager(env: str) -> ConfigManager[BuildCubConfig]:
    """Get the configuration manager for Build Cub.

    Args:
        env: Optional environment name to load specific configurations.

    Returns:
        ConfigManager[BuildCubConfig]: The configuration manager instance.
    """
    global _config_singleton  # noqa: PLW0603
    if _config_singleton is None:
        _config_singleton = SingletonWrap(
            ConfigManager,
            config_model=BuildCubConfig,
            program_name="build_cub",
            env=env,
        )
    return _config_singleton.get_instance()


config_manager: ConfigManager[BuildCubConfig] = get_config_manager(getenv("BUILD_CUB_ENV", "prod"))
"""Config Manager is mostly useless by itself but can be used for debugging purposes."""
global_config: BuildCubConfig = config_manager.config
"""Global configuration instance for Build Cub."""


__all__ = ["CLOSE_BRACE", "OPEN_BRACE", "BuildCubConfig", "config_manager", "global_config"]
