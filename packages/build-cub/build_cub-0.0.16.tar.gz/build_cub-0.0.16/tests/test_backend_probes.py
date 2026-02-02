"""Smoke tests for backend hook methods."""

from __future__ import annotations

from importlib import import_module

import pytest

from build_cub.plugins import BuildCubHook
from build_cub.validation._models import Artifact

BACKEND_MODULES: list[tuple[str, str]] = [
    ("build_cub.workers.backends.cython", "CythonBackend"),
    ("build_cub.workers.backends.raw_cpp", "RawCppBackend"),
    ("build_cub.workers.backends.pybind11", "Pybind11Backend"),
    ("build_cub.workers.backends.pyo3", "Pyo3Backend"),
]


@pytest.mark.parametrize(("module_path", "cls_name"), BACKEND_MODULES, ids=[name for _, name in BACKEND_MODULES])
def test_backend_pre_post_execute_probe(
    module_path: str,
    cls_name: str,
    test_build_data,
    color_printer,
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Instantiate each backend and call hook methods to ensure they don't crash."""
    module = import_module(module_path)
    backend_cls = getattr(module, cls_name)
    backend = backend_cls(should_run=True, settings=test_build_data, printer=color_printer, hook=BuildCubHook())

    if backend.name == "cython":
        monkeypatch.setattr(module, "cythonize", lambda module_list, **_: module_list)

    backend._pre_execute([])  # Should not raise NotImplementedError.
    backend._post_execute(Artifact(path=tmp_path / "probe.so"))


def test_gperf_plugin_post_execute_probe(
    test_build_data,
    color_printer,
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Ensure gperf plugin can post-process output without crashing."""
    module = import_module("build_cub.workers.plugins.gperf")
    monkeypatch.setattr(module, "find_gperf_binary", lambda _: "/usr/bin/gperf")

    plugin_cls = getattr(module, "GperfPlugin")  # noqa: B009
    plugin = plugin_cls(should_run=True, settings=test_build_data, printer=color_printer, hook=BuildCubHook())

    header = tmp_path / "probe.hpp"
    header.write_text('#line 1 "input"\nregister int value;\nint other;\n')

    plugin._post_execute(header)
    updated = header.read_text()
    assert "#line" not in updated
    assert "register " not in updated
