"""Shared base class for C++ compilation backends (pybind11, raw_cpp)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from lazy_bear import lazy

from ._base import CompileBackend

if TYPE_CHECKING:
    from setuptools import Extension

    from build_cub.models._base import BaseBackendSettings, CompilerSettings, SourcesItem
else:
    Extension = lazy("setuptools", "Extension")
    SourcesItem = lazy("build_cub.models._base", "SourcesItem")


class CppBackendBase[Settings_T: BaseBackendSettings](CompileBackend[Settings_T, SourcesItem]):
    """Base class for C++ compilation backends.

    Subclasses configure via class attributes:
        - name: Backend name (e.g., "pybind11", "raw_cpp")
        - dependencies: Required packages
        - display_name: Human-readable name for messages
        - language: Extension language param (None to omit)

    Subclasses MAY override:
        - extra_include_dirs property -> add backend-specific includes (e.g., pybind11)
    """

    display_name: str = "C++"
    language: str = ""

    @property
    def compiler_settings(self) -> CompilerSettings:
        """Get the compiler settings for this backend."""
        return self.local_settings.get_compiler_settings()

    def _get_extensions(self, targets: list[SourcesItem]) -> list[Extension]:
        """Build Extension objects from SourcesItem targets."""
        extensions: list[Extension] = []
        compiler_settings: CompilerSettings = self.compiler_settings

        base_include_dirs: list[str] = [
            str(self.settings.pkg_root),
            str(self.settings.pkg_root / self.settings.general.name),
            *self.extra_include_dirs,
        ]
        include_dirs: list[str] = [*base_include_dirs, *compiler_settings.include_dirs]

        for target in targets:
            ext_kwargs: dict[str, Any] = {
                "name": target.module_name,
                "include_dirs": include_dirs,
                "library_dirs": list(compiler_settings.library_dirs),
                "libraries": list(compiler_settings.libraries),
                "sources": target.sources,
                "extra_compile_args": list(compiler_settings.extra_compile_args),
                "extra_link_args": list(compiler_settings.extra_link_args),
            }
            if self.language:
                ext_kwargs["language"] = self.language
            extensions.append(Extension(**ext_kwargs))
        return extensions
