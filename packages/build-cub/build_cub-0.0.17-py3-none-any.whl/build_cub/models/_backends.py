"""Models for build backend settings in bear_build.toml."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from build_cub.utils import global_config

from ._base import BaseBackendSettings, BaseSettings, PathSource, RustSources, SourcesItem


class GperfSettings(BaseSettings[Path]):
    """Maps to [gperf] section."""

    binary: str = Field(default="")
    language: str = Field(default="C++")
    options: list[str] = Field(default_factory=list)
    target_ext: str = Field(default="")

    @property
    def cmd(self) -> list[str]:
        """Command snippet for subprocess."""
        from build_cub.utils import pre_allocate_list

        pre_allocated_list: list[str] = pre_allocate_list(
            5,
            "",
            self.binary,
            "-L",
            self.language if self.language else "ANSI-C",
        )
        return pre_allocated_list


class CompilerDirectives(BaseModel):
    """Maps to [cython.compiler_directives] - Cython-specific compiler options."""

    language_level: str = "3"
    embedsignature: bool = Field(default=True)
    boundscheck: bool = Field(default=False)
    wraparound: bool = Field(default=False)
    nonecheck: bool = Field(default=False)
    cdivision: bool = Field(default=True)
    initializedcheck: bool = Field(default=False)
    freethreading_compatible: bool | None = None
    overflowcheck: bool | None = None
    profile: bool | None = None
    linetrace: bool | None = None
    generate_cleanup_code: bool | None = None
    cimport_from_pyx: bool | None = None

    model_config = ConfigDict(extra="ignore")


class CythonSettings(BaseBackendSettings[PathSource]):
    """Maps to [cython] section."""

    name: str = "cython"
    annotate: bool = Field(default=False)
    quiet: bool = Field(default=True)
    compiler_directives: CompilerDirectives = Field(default_factory=CompilerDirectives)


class Pybind11Settings(BaseBackendSettings[SourcesItem]):
    """Maps to [pybind11] section."""

    name: str = "pybind11"


class RawCppSettings(BaseBackendSettings[SourcesItem]):
    """Maps to [raw_cpp] section."""

    name: str = "raw_cpp"


class Pyo3Settings(BaseBackendSettings[RustSources]):
    """Maps to [pyo3] section for Rust/PyO3 extensions."""

    cargo_path: Path = Field(default=global_config.paths.cargo_toml, description="Path to Cargo.toml")
    output_path: Path = Field(default=global_config.paths.cwd, description="Where should artifacts end up")
    quiet: bool = Field(default=False, description="Suppress cargo build output")
    cleanup: bool = Field(default=True, description="Remove target/ directory after build")
    release: bool = Field(default=True, description="Build in release mode (optimized)")
    features: list[str] = Field(default_factory=list, description="Cargo features to enable")

    @property
    def cmd(self) -> list[str]:
        """Base cargo build command."""
        cmd: list[str] = list(global_config.misc.rust_cmd)
        if self.release:
            cmd.append("--release")
        if self.features:
            cmd.extend(["--features", ",".join(self.features)])
        return cmd


__all__ = [
    "CompilerDirectives",
    "CythonSettings",
    "GperfSettings",
    "Pybind11Settings",
    "Pyo3Settings",
    "RawCppSettings",
]
