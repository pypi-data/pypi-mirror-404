"""Tests for model helper/mutator methods."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from build_cub.models._base import SourcesItem
from build_cub.models._defaults import CompilerSettings

if TYPE_CHECKING:
    from build_cub.models._build_data import BuildData


TMP_INCLUDE = "/tmp/include"  # noqa: S108
TMP_LIB = "/tmp/lib"  # noqa: S108


class TestBuildDataGetBackend:
    """Tests for BuildData.get_backend."""

    def test_get_backend_returns_backend(self, test_build_data: BuildData) -> None:
        """Get backend returns the matching backend settings object."""
        backend = test_build_data.get_backend("cython")

        assert backend is test_build_data.cython
        assert backend.name == "cython"

    def test_get_backend_raises_for_unknown(self, test_build_data: BuildData) -> None:
        """Get backend raises for unrecognized backend names."""
        with pytest.raises(ValueError, match="not a recognized backend"):
            test_build_data.get_backend("not_real")


class TestBaseBackendSettingsGetTarget:
    """Tests for BaseBackendSettings.get_target."""

    def test_get_target_returns_named_target(self, test_build_data: BuildData) -> None:
        """Get target returns the correct target for its name."""
        target = test_build_data.raw_cpp.get_target("bindings")

        assert target.name == "bindings"
        assert "bindings.cpp" in target.sources[0]

    def test_get_target_raises_for_unknown(self, test_build_data: BuildData) -> None:
        """Get target raises for missing target names."""
        with pytest.raises(ValueError, match="Target 'missing' not found"):
            test_build_data.raw_cpp.get_target("missing")


class TestCompilerSettingsAdders:
    """Tests for CompilerSettings add_to_* helpers."""

    def test_add_to_compile_args_appends(self) -> None:
        """Compile args accept both strings and lists."""
        settings = CompilerSettings()

        settings.add_to_compile_args("-O2")
        settings.add_to_compile_args(["-Wall", "-Wextra"])

        assert settings.extra_compile_args == ["-O2", "-Wall", "-Wextra"]

    def test_add_to_link_args_appends(self) -> None:
        """Link args accept both strings and lists."""
        settings = CompilerSettings()

        settings.add_to_link_args("-Wl,-rpath,/usr/lib")
        settings.add_to_link_args(["-Wl,-s", "-Wl,-dead_strip"])

        assert settings.extra_link_args == ["-Wl,-rpath,/usr/lib", "-Wl,-s", "-Wl,-dead_strip"]

    def test_add_to_include_dirs_appends(self) -> None:
        """Include dirs accept both strings and lists."""
        settings = CompilerSettings()

        settings.add_to_include_dirs("/usr/include")
        settings.add_to_include_dirs(["/opt/local/include", TMP_INCLUDE])

        assert settings.include_dirs == ["/usr/include", "/opt/local/include", TMP_INCLUDE]

    def test_add_to_library_dirs_appends(self) -> None:
        """Library dirs accept both strings and lists."""
        settings = CompilerSettings()

        settings.add_to_library_dirs("/usr/lib")
        settings.add_to_library_dirs(["/opt/local/lib", TMP_LIB])

        assert settings.library_dirs == ["/usr/lib", "/opt/local/lib", TMP_LIB]

    def test_add_to_libraries_appends(self) -> None:
        """Libraries accept both strings and lists."""
        settings = CompilerSettings()

        settings.add_to_libraries("m")
        settings.add_to_libraries(["z", "ssl"])

        assert settings.libraries == ["m", "z", "ssl"]


class TestSourcesItemAddToSources:
    """Tests for SourcesItem.add_to_sources."""

    def test_add_to_sources_appends(self) -> None:
        """Sources can be added via string or list."""
        target = SourcesItem(name="bindings", sources=["src/test_project/_cpp/bindings.cpp"])

        target.add_to_sources("src/test_project/_cpp/helpers.cpp")
        target.add_to_sources(["src/test_project/_cpp/extra.cpp", "src/test_project/_cpp/more.cpp"])

        assert target.sources == [
            "src/test_project/_cpp/bindings.cpp",
            "src/test_project/_cpp/helpers.cpp",
            "src/test_project/_cpp/extra.cpp",
            "src/test_project/_cpp/more.cpp",
        ]


class TestFullFlowMutations:
    """Tests a full flow of fetching a backend and mutating settings/targets."""

    def test_full_flow_backend_settings_and_targets(self) -> None:
        """End-to-end style test for backend settings and target mutations."""
        from build_cub.models._build_data import BuildData

        data = {
            "general": {"name": "test_project", "enabled": True},
            "defaults": {"settings": {"extra_compile_args": ["-O3"]}},
            "pybind11": {
                "enabled": True,
                "targets": [{"name": "core", "sources": ["src/test_project/_cpp/core.cpp"]}],
            },
        }

        build_data = BuildData.model_validate(data)
        backend = build_data.get_backend("pybind11")

        settings = backend.get_compiler_settings()
        settings.add_to_compile_args("-O2")
        settings.add_to_link_args("-Wl,-s")
        settings.add_to_include_dirs("/usr/include")
        settings.add_to_library_dirs("/usr/lib")
        settings.add_to_libraries(["m", "z"])

        core_target = backend.get_target("core")
        core_target.add_to_sources("src/test_project/_cpp/helpers.cpp")
        backend.targets.append(SourcesItem(name="extra", sources=["src/test_project/_cpp/extra.cpp"]))

        assert settings.extra_compile_args == ["-O3", "-O2"]
        assert settings.extra_link_args == ["-Wl,-s"]
        assert settings.include_dirs == ["/usr/include"]
        assert settings.library_dirs == ["/usr/lib"]
        assert settings.libraries == ["m", "z"]
        assert core_target.sources == [
            "src/test_project/_cpp/core.cpp",
            "src/test_project/_cpp/helpers.cpp",
        ]
        assert backend.get_target("extra").sources == ["src/test_project/_cpp/extra.cpp"]
