from __future__ import annotations

from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from build_cub.models import DEFAULT_VERSION, Version
from build_cub.utils import global_config, merge_lists

type MergeMode = Literal["replace", "merge"]


def to_list(args: list[str] | str) -> list[str]:
    if isinstance(args, str):
        args = [args]
    return args


class CompilerSettings(BaseModel):
    """Maps to [defaults.settings] or [backend.settings] - compiler/linker configuration.

    Uses validation_alias to automatically pick the correct platform-specific args
    (extra_compile_args vs extra_compile_args_windows) based on IS_WINDOWS.
    """

    extra_compile_args: list[str] = Field(default_factory=list)
    extra_link_args: list[str] = Field(default_factory=list)
    include_dirs: list[str] = Field(default_factory=list)
    library_dirs: list[str] = Field(default_factory=list)
    libraries: list[str] = Field(default_factory=list)
    lib_files: list[str] = Field(default=list(global_config.misc.default_output))

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    @model_validator(mode="after")
    def validate_args(self) -> Self:
        """Ensure that any MacOS specific args are removed on non-MacOS systems."""
        if global_config.platform.not_macos:
            self.extra_compile_args = [arg for arg in self.extra_compile_args if not arg.startswith("-mmacos-version")]
        return self

    # TODO: Make it easier to hook into the hook so I can hook while I hook
    # For now we will allow the user to reach in and manually add values to the settings here before compilation

    def add_to_compile_args(self, args: list[str] | str) -> None:
        self.extra_compile_args = merge_lists(self.extra_compile_args, to_list(args))

    def replace_compile_args(self, args: list[str] | str) -> None:
        self.extra_compile_args = to_list(args)

    def add_to_link_args(self, args: list[str] | str) -> None:
        self.extra_link_args = merge_lists(self.extra_link_args, to_list(args))

    def replace_link_args(self, args: list[str] | str) -> None:
        self.extra_link_args = to_list(args)

    def add_to_include_dirs(self, dirs: list[str] | str) -> None:
        self.include_dirs = merge_lists(self.include_dirs, to_list(dirs))

    def replace_include_dirs(self, dirs: list[str] | str) -> None:
        self.include_dirs = to_list(dirs)

    def add_to_library_dirs(self, dirs: list[str] | str) -> None:
        self.library_dirs = merge_lists(self.library_dirs, to_list(dirs))

    def replace_library_dirs(self, dirs: list[str] | str) -> None:
        self.library_dirs = to_list(dirs)

    def add_to_libraries(self, libs: list[str] | str) -> None:
        self.libraries = merge_lists(self.libraries, to_list(libs))

    def replace_libraries(self, libs: list[str] | str) -> None:
        self.libraries = to_list(libs)

    @property
    def no_custom_args(self) -> bool:
        return not bool(
            self.extra_compile_args or self.extra_link_args or self.include_dirs or self.library_dirs or self.libraries
        )

    def merge_with_defaults(self, defaults: CompilerSettings, merge_mode: MergeMode = "replace") -> None:
        """Merge this settings with defaults - only inheriting fields we didn't customize."""
        d = defaults
        if merge_mode == "replace":
            self.extra_compile_args = self.extra_compile_args or d.extra_compile_args
            self.extra_link_args = self.extra_link_args or d.extra_link_args
            self.include_dirs = self.include_dirs or d.include_dirs
            self.library_dirs = self.library_dirs or d.library_dirs
            self.libraries = self.libraries or d.libraries
        else:
            self.extra_compile_args = merge_lists(d.extra_compile_args, self.extra_compile_args)
            self.extra_link_args = merge_lists(d.extra_link_args, self.extra_link_args)
            self.include_dirs = merge_lists(d.include_dirs, self.include_dirs)
            self.library_dirs = merge_lists(d.library_dirs, self.library_dirs)
            self.libraries = merge_lists(d.libraries, self.libraries)


class GeneralSettings(BaseModel):
    """Maps to [general] in bear_build.toml."""

    name: str = Field(default="")
    enabled: bool = Field(default=False)
    debug_symbols: bool = Field(default=False)
    version: Version = Field(default=DEFAULT_VERSION)


class DefaultSettings(BaseModel):
    """Maps to [defaults] section - base settings inherited by all backends."""

    merge_mode: MergeMode = Field(default="replace")
    settings: CompilerSettings = Field(default_factory=CompilerSettings)

    @property
    def lib_files(self) -> list[str]:
        return self.settings.lib_files


__all__ = [
    "CompilerSettings",
    "DefaultSettings",
    "GeneralSettings",
]
