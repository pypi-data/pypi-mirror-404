"""Tests for the CLI."""

from __future__ import annotations

from unittest import mock

import pytest

from build_cub import METADATA, main


@mock.patch("sys.argv", new=["build_cub"])
def test_main() -> None:
    """Basic CLI test."""
    with pytest.raises(SystemExit):
        assert main([]) == 0


@mock.patch("sys.argv", new=["build_cub", "--help"])
def test_show_help(capsys: pytest.CaptureFixture) -> None:
    """Show help.

    Parameters:
        capsys: Pytest fixture to capture output.
    """
    with pytest.raises(SystemExit):
        main()
    captured = capsys.readouterr()
    assert "build_cub" in captured.out


@mock.patch("sys.argv", new=["build_cub", "version"])
def test_show_version(capsys: pytest.CaptureFixture) -> None:
    """Show version.

    Parameters:
        capsys: Pytest fixture to capture output.
    """
    main()
    captured = capsys.readouterr()
    assert METADATA.version in captured.out


@mock.patch("sys.argv", new=["build_cub", "debug", "-n"])
def test_show_debug_info(capsys: pytest.CaptureFixture) -> None:
    """Show debug information.

    Parameters:
        capsys: Pytest fixture to capture output.
    """
    main()
    captured = capsys.readouterr().out.lower()
    assert "python" in captured
    assert "system" in captured
    assert "environment" in captured
    assert "packages" in captured
