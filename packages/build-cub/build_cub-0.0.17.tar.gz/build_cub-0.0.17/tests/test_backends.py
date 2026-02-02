"""Tests for backend initialization and behavior."""

from __future__ import annotations

from typing import Any, cast

import pytest

# ruff: noqa: TC001
from build_cub.models._backends import CythonSettings, RawCppSettings
from build_cub.models._build_data import BuildData
from build_cub.plugins import BuildCubHook
from build_cub.utils import ColorPrinter


class TestWorkerDiscovery:
    """Tests for auto-discovery of backends and plugins."""

    def test_backend_discovery(self) -> None:
        """Test that backends are auto-discovered from the backends directory."""
        from build_cub.utils import global_config

        assert "cython" in global_config.all_backends
        assert "raw_cpp" in global_config.all_backends
        assert "pybind11" in global_config.all_backends
        assert "pyo3" in global_config.all_backends

    def test_plugin_discovery(self) -> None:
        """Test that plugins are auto-discovered from the plugins directory."""
        from build_cub.utils import global_config

        assert "gperf" in global_config.all_plugins

    def test_get_module_map_creates_correct_imports(self, test_build_data: BuildData) -> None:
        """Test get_module_map generates correct class names with suffix."""
        from build_cub.workers._meta import get_module_map

        backend_imports = get_module_map(test_build_data, ["cython", "raw_cpp"], suffix="Backend")

        names = {imp.name for imp in backend_imports}
        class_names = {imp.class_name for imp in backend_imports}

        assert "cython" in names
        assert "raw_cpp" in names
        assert "CythonBackend" in class_names
        assert "RawCppBackend" in class_names

    def test_get_module_map_with_plugin_suffix(self, test_build_data: BuildData) -> None:
        """Test get_module_map works with Plugin suffix."""
        from build_cub.workers._meta import get_module_map

        plugin_imports = get_module_map(test_build_data, ["gperf"], suffix="Plugin")

        assert len(plugin_imports) == 1
        assert plugin_imports[0].name == "gperf"
        assert plugin_imports[0].class_name == "GperfPlugin"


class MockHook:
    """Mock BuildCubHook for testing."""

    def register_validation(self, name: str, worker: str, callback: Any, report: Any) -> None:
        """Mock method to register validation."""


@pytest.fixture
def mock_hook() -> BuildCubHook:
    """Fixture for MockHook."""
    return cast("BuildCubHook", MockHook())


class TestBackendInitialization:
    """Tests for backend class initialization."""

    def test_cython_backend_init(
        self,
        test_build_data: BuildData,
        color_printer: ColorPrinter,
        mock_hook: BuildCubHook,
    ) -> None:
        """Test CythonBackend initializes correctly."""
        from build_cub.workers.backends.cython import CythonBackend

        backend = CythonBackend(should_run=True, settings=test_build_data, printer=color_printer, hook=mock_hook)
        assert backend.name == "cython"
        assert backend.should_run is True
        assert backend.settings is test_build_data

    def test_raw_cpp_backend_init(
        self, test_build_data: BuildData, color_printer: ColorPrinter, mock_hook: BuildCubHook
    ) -> None:
        """Test RawCppBackend initializes correctly."""
        from build_cub.workers.backends.raw_cpp import RawCppBackend

        backend = RawCppBackend(should_run=True, settings=test_build_data, printer=color_printer, hook=mock_hook)
        assert backend.name == "raw_cpp"
        assert backend.should_run is True

    def test_pybind11_backend_init(
        self,
        test_build_data: BuildData,
        color_printer: ColorPrinter,
        mock_hook: BuildCubHook,
    ) -> None:
        """Test Pybind11Backend initializes correctly."""
        from build_cub.workers.backends.pybind11 import Pybind11Backend

        backend = Pybind11Backend(should_run=True, settings=test_build_data, printer=color_printer, hook=mock_hook)
        assert backend.name == "pybind11"
        assert backend.should_run is True

    def test_gperf_plugin_init(
        self, test_build_data: BuildData, color_printer: ColorPrinter, mock_hook: BuildCubHook
    ) -> None:
        """Test GperfPlugin initializes correctly."""
        from build_cub.workers.plugins.gperf import GperfPlugin

        plugin = GperfPlugin(should_run=True, settings=test_build_data, printer=color_printer, hook=mock_hook)
        assert plugin.name == "gperf"


class TestGperfDependencyVerification:
    """Tests for gperf binary dependency checking."""

    def test_gperf_uses_fallback_when_configured_binary_missing(
        self,
        test_toml_data: dict[str, Any],
        mock_hook: BuildCubHook,
    ) -> None:
        """Test GperfPlugin uses fallback when configured binary not found."""
        from build_cub.models._build_data import BuildData
        from build_cub.utils import ColorPrinter
        from build_cub.workers.plugins.gperf import GperfPlugin, find_gperf_binary

        test_toml_data["gperf"]["binary"] = "/nonexistent/path/to/gperf"

        build_data: BuildData = BuildData.model_validate(test_toml_data)
        printer = ColorPrinter()
        plugin = GperfPlugin(should_run=True, settings=build_data, printer=printer, hook=mock_hook)

        # If gperf exists on system, fallback should find it and update the binary path
        # If gperf doesn't exist, should_run should be False
        system_gperf: str | None = find_gperf_binary("")
        if system_gperf:
            assert plugin.should_run is True
            assert build_data.gperf.binary == system_gperf
        else:
            assert plugin.should_run is False

    def test_find_gperf_binary_returns_none_when_not_installed(self) -> None:
        """Test find_gperf_binary returns None when gperf isn't installed anywhere."""
        from unittest.mock import patch

        from build_cub.workers.plugins.gperf import find_gperf_binary

        with (
            patch("build_cub.workers.plugins.gperf.which", return_value=None),
            patch("pathlib.Path.exists", return_value=False),
        ):
            result: str | None = find_gperf_binary("/fake/binary")
            assert result is None

    def test_find_gperf_binary_prefers_configured(self) -> None:
        """Test find_gperf_binary returns configured binary if it exists."""
        from unittest.mock import patch

        from build_cub.workers.plugins.gperf import find_gperf_binary

        def mock_which(cmd: str) -> str | None:
            if cmd == "/my/custom/gperf":
                return "/my/custom/gperf"
            return None

        with patch("build_cub.workers.plugins.gperf.which", side_effect=mock_which):
            result: str | None = find_gperf_binary("/my/custom/gperf")
            assert result == "/my/custom/gperf"


class TestBackendLocalSettings:
    """Tests for backend local_settings property."""

    def test_cython_local_settings(
        self, test_build_data: BuildData, color_printer: ColorPrinter, mock_hook: BuildCubHook
    ) -> None:
        """Test CythonBackend.local_settings returns CythonSettings."""
        from build_cub.workers.backends.cython import CythonBackend

        backend = CythonBackend(should_run=True, settings=test_build_data, printer=color_printer, hook=mock_hook)
        local: CythonSettings = backend.local_settings
        assert local.enabled is True
        assert len(local.targets) == 2

    def test_raw_cpp_local_settings(
        self, test_build_data: BuildData, color_printer: ColorPrinter, mock_hook: BuildCubHook
    ) -> None:
        """Test RawCppBackend.local_settings returns RawCppSettings."""
        from build_cub.workers.backends.raw_cpp import RawCppBackend

        backend = RawCppBackend(should_run=True, settings=test_build_data, printer=color_printer, hook=mock_hook)
        local: RawCppSettings = backend.local_settings
        assert local.enabled is True
        assert len(local.targets) == 1
