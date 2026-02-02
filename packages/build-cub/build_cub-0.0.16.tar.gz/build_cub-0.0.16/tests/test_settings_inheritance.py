"""Tests for the settings inheritance system (defaults -> backend overrides)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from build_cub.models._base import BaseSources
from build_cub.models._build_data import BuildData

if TYPE_CHECKING:
    from build_cub.models._base import BaseBackendSettings


class BasicStr(BaseSources):
    def __init__(self, name: str, sources: list[str] | None = None) -> None:
        """Just allows to pass in a str."""
        super().__init__(name=name, sources=sources or [])


class TestSettingsInheritance:
    """Tests for the defaults + override pattern."""

    def test_backend_has_no_custom_args_flag(self) -> None:
        """Test that backends with no custom args are detected."""
        from build_cub.models._base import BaseBackendSettings

        backend: BaseBackendSettings[BasicStr] = BaseBackendSettings(enabled=True, targets=[BasicStr("test")])
        assert backend.settings.no_custom_args is True

    def test_backend_with_custom_args_detected(self) -> None:
        """Test that backends with custom args are detected."""
        from build_cub.models._base import BaseBackendSettings, CompilerSettings

        backend: BaseBackendSettings[BasicStr] = BaseBackendSettings(
            enabled=True,
            targets=[BasicStr("test")],
            settings=CompilerSettings(extra_compile_args=["-O2"]),
        )
        assert backend.settings.no_custom_args is False
        assert backend.settings.extra_compile_args == ["-O2"]

    def test_cython_merges_with_defaults(self, test_build_data: BuildData) -> None:
        """Test that cython's custom settings merge with defaults (fixture uses merge mode)."""
        cython_args: list[str] = test_build_data.cython.settings.extra_compile_args
        # In merge mode, both default and backend args are combined
        assert "-std=c++20" in cython_args  # From defaults
        assert "-O3" in cython_args  # From both (deduplicated)
        assert "-ffast-math" in cython_args  # From both (deduplicated)

    def test_raw_cpp_inherits_defaults(self, test_build_data: BuildData) -> None:
        """Test that raw_cpp inherits defaults (has -std=c++20)."""
        raw_cpp_args: list[str] = test_build_data.raw_cpp.settings.extra_compile_args
        assert "-std=c++20" in raw_cpp_args

    def test_model_validator_applies_inheritance(self) -> None:
        """Test the model_validator properly copies defaults to backends without custom args."""
        data: dict[str, dict[str, Any]] = {
            "general": {"name": "test", "enabled": True},
            "defaults": {
                "settings": {
                    "extra_compile_args": ["-O3", "-march=native"],
                    "extra_link_args": ["-flto"],
                }
            },
            "pybind11": {"enabled": True, "targets": [{"name": "bindings", "sources": ["bindings.cpp"]}]},
        }
        build_data: BuildData = BuildData.model_validate(data)

        # pybind11 had no custom settings, should inherit defaults
        assert build_data.pybind11.settings.extra_compile_args == ["-O3", "-march=native"]
        assert build_data.pybind11.settings.extra_link_args == ["-flto"]
