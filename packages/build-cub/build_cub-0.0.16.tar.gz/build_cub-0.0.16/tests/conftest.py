"""Pytest fixtures and configuration for build_cub tests."""

from __future__ import annotations

from importlib import import_module
from pathlib import Path  # noqa: TC003
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel
import pytest

from build_cub.utils import global_config

from . import MAIN_CONFIG_PATH, TEST_TOML_PATH

if TYPE_CHECKING:
    from build_cub.models._build_data import BuildData
    from build_cub.utils import ColorPrinter


@pytest.fixture
def monkey_patch_cwd(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Fixture to monkeypatch CWD to a temporary path."""

    class MockPaths(BaseModel):
        cwd: Path = tmp_path

    class OuterConfig(BaseModel):
        paths: MockPaths = MockPaths()

    temp = import_module("build_cub.models._templates")
    org = getattr(temp, "global_config")  # noqa: B009

    from build_cub.models import _templates as templates

    try:
        monkeypatch.setattr(templates, "global_config", value=OuterConfig())
        yield
    finally:
        monkeypatch.setattr(templates, "global_config", org)


@pytest.fixture
def test_toml_data() -> dict[str, Any]:
    """Load the test fixture TOML as raw dict."""
    from build_cub.utils import load_toml

    return load_toml(TEST_TOML_PATH)


@pytest.fixture
def test_build_data() -> BuildData:
    """Load the test fixture as a validated BuildData model."""
    from build_cub.models._build_data import BuildData
    from build_cub.utils import load_toml

    return BuildData.model_validate(load_toml(TEST_TOML_PATH))


@pytest.fixture
def project_toml_data() -> dict[str, Any]:
    """Load the actual project bear_build.toml as raw dict."""
    from build_cub.utils import load_toml

    return load_toml(MAIN_CONFIG_PATH)


@pytest.fixture
def project_build_data():
    """Load the actual project bear_build.toml as BuildData."""
    from build_cub.models._build_data import BuildData
    from build_cub.utils import load_toml

    return BuildData.model_validate(load_toml(MAIN_CONFIG_PATH))


@pytest.fixture
def color_printer() -> ColorPrinter:
    from build_cub.utils import ColorPrinter

    return ColorPrinter.get_instance()


@pytest.fixture
def default_output_files() -> list[str]:
    """Provide the default output files list."""
    return list(global_config.misc.default_output)
