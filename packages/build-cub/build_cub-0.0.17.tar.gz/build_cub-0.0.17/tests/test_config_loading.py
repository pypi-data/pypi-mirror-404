"""Tests for TOML loading and BuildData validation.

Uses the test fixture for specific value assertions.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from build_cub.models._build_data import BuildData


class TestFixtureLoading:
    """Tests against the stable test fixture - tests specific expected values."""

    def test_general_section(self, test_build_data: BuildData) -> None:
        """Test [general] section loads with expected values."""
        assert test_build_data.general.name == "test_project"
        assert test_build_data.general.enabled is True
        assert test_build_data.general.debug_symbols is False

    def test_defaults_section(self, test_build_data: BuildData, default_output_files: list[str]) -> None:
        """Test [defaults] section loads correctly."""
        for file in default_output_files:
            assert file in test_build_data.defaults.lib_files
        assert "-std=c++20" in test_build_data.defaults.settings.extra_compile_args
        assert "-O3" in test_build_data.defaults.settings.extra_link_args

    def test_cython_backend_enabled(self, test_build_data: BuildData) -> None:
        """Test [cython] section loads with targets."""
        assert test_build_data.cython.enabled is True
        assert len(test_build_data.cython.targets) == 2
        assert test_build_data.cython.quiet is True

    def test_raw_cpp_backend_enabled(self, test_build_data: BuildData) -> None:
        """Test [raw_cpp] section loads with SourcesItem targets."""
        assert test_build_data.raw_cpp.enabled is True
        assert len(test_build_data.raw_cpp.targets) == 1
        assert test_build_data.raw_cpp.targets[0].name == "bindings"

    def test_disabled_backends(self, test_build_data: BuildData) -> None:
        """Test disabled backends load correctly."""
        assert test_build_data.pybind11.enabled is False
        assert test_build_data.gperf.enabled is False

    def test_versioning_section(self, test_build_data: BuildData) -> None:
        """Test [versioning] section loads with variables and templates."""
        variables: dict[str, Any] = test_build_data.versioning.variables
        assert variables["united_data"]["major"] == 2
        assert variables["united_data"]["minor"] == 1
        assert variables["schema"]["major"] == 1
        assert variables["schema"]["patch"] == 3
        assert test_build_data.versioning.has_templates is True
        assert len(test_build_data.versioning.templates) == 2


class TestProjectConfigLoading:
    """Tests against the actual project bear_build.toml - config-agnostic checks."""

    def test_project_toml_loads(self, project_toml_data: dict[str, Any]) -> None:
        """Verify bear_build.toml exists and has required sections."""
        assert project_toml_data is not None
        assert "general" in project_toml_data
        assert "defaults" in project_toml_data

    def test_project_build_data_validates(self, project_build_data: BuildData) -> None:
        """Test that BuildData can validate the project TOML."""
        assert project_build_data.general.name == "build_cub"

    def test_defaults_has_output_files(self, project_build_data: BuildData, default_output_files: list[str]) -> None:
        """Test defaults section has lib_files configured."""
        for file in default_output_files:
            assert file in project_build_data.defaults.lib_files
