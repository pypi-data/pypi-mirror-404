"""Tests for helper functions in _helpers.py."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel
import pytest

from build_cub.utils._funcs import search_paths


class TestPlatformDetection:
    """Tests for platform-specific settings selection."""

    def test_compiler_args_key_matches_platform(self) -> None:
        """Test correct compiler args key is selected based on platform."""
        from build_cub.utils import global_config

        if global_config.platform.is_windows:
            assert global_config.keys.compiler_args == "extra_compile_args_windows"
            assert global_config.keys.link_args == "extra_link_args_windows"
        else:
            assert global_config.keys.compiler_args == "extra_compile_args"
            assert global_config.keys.link_args == "extra_link_args"


class TestCompilerSettingsValidationAlias:
    """Tests for CompilerSettings platform-specific arg selection."""

    def test_picks_correct_args_via_alias(self) -> None:
        """Test CompilerSettings uses validation_alias for platform detection."""
        from build_cub.models._defaults import CompilerSettings

        data: dict[str, list[str]] = {
            "extra_compile_args": ["-O3"],
            "extra_compile_args_windows": ["/O2"],
            "extra_link_args": ["-Wl,-w"],
            "extra_link_args_windows": ["/IGNORE:4099"],
        }

        settings = CompilerSettings.model_validate(data)
        assert len(settings.extra_compile_args) > 0
        assert len(settings.extra_link_args) > 0


class MockPlatformNotMacOS(BaseModel):
    @property
    def is_macos(self):
        """MacOS."""
        return False

    @property
    def not_macos(self):
        """Not MacOS."""
        return True


class MockPlatformMacOS(BaseModel):
    @property
    def is_macos(self):
        """MacOS."""
        return True

    @property
    def not_macos(self):
        """Not MacOS."""
        return False


class MockGlobalConfigNotMacOS(BaseModel):
    platform: MockPlatformNotMacOS = MockPlatformNotMacOS()


class MockGlobalConfigMacOS(BaseModel):
    platform: MockPlatformMacOS = MockPlatformMacOS()


class TestCompilerSettingsMacosArgs:
    """Tests for CompilerSettings removal of MacOS-specific args."""

    def test_removes_macos_args_on_non_macos(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """MacOS-specific args are removed when NOT_MACOS is True."""
        from build_cub.models import _defaults as defaults

        monkeypatch.setattr(defaults, "global_config", MockGlobalConfigNotMacOS())

        settings = defaults.CompilerSettings.model_validate(
            {"extra_compile_args": ["-O2", "-mmacos-version-min=10.15", "-Wall"]}
        )

        assert settings.extra_compile_args == ["-O2", "-Wall"]

    def test_keeps_macos_args_on_macos(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """MacOS-specific args are kept when NOT_MACOS is False."""
        from build_cub.models import _defaults as defaults

        monkeypatch.setattr(defaults, "global_config", MockGlobalConfigMacOS())

        settings = defaults.CompilerSettings.model_validate(
            {"extra_compile_args": ["-O2", "-mmacos-version-min=10.15", "-Wall"]}
        )
        assert settings.extra_compile_args == ["-O2", "-mmacos-version-min=10.15", "-Wall"]


class TestGetFiles:
    """Tests for get_files utility function."""

    def test_finds_files_by_extension(self, tmp_path: Path) -> None:
        """Test get_files finds files matching extensions."""
        (tmp_path / "test.pyx").touch()
        (tmp_path / "other.py").touch()
        (tmp_path / "subdir").mkdir()
        (tmp_path / "subdir" / "nested.pyx").touch()

        files = search_paths(tmp_path, [".pyx"])
        print(files)
        assert len(files) == 2
        assert all(f.suffix == ".pyx" for f in files)

    def test_finds_multiple_extensions(self, tmp_path: Path) -> None:
        """Test get_files can match multiple extensions."""
        (tmp_path / "a.so").touch()
        (tmp_path / "b.pyd").touch()
        (tmp_path / "c.txt").touch()

        files = search_paths(tmp_path, [".pyd", ".so"])
        assert len(files) == 2


class TestGetParts:
    """Tests for get_parts path parsing."""

    def test_extracts_module_parts(self) -> None:
        """Test get_parts extracts module path components."""
        from build_cub.utils import get_parts

        path = Path("src/my_project/submodule/file.pyx")
        parts: tuple[str, ...] = get_parts(path)
        assert parts == ("my_project", "submodule", "file")

    def test_strips_src_prefix(self) -> None:
        """Test get_parts removes 'src' from path."""
        from build_cub.utils import get_parts

        path = Path("src/pkg/module.py")
        parts: tuple[str, ...] = get_parts(path)
        assert parts[0] != "src"
        assert parts == ("pkg", "module")

    def test_to_module_returns_dotted_string(self) -> None:
        """Test get_parts with to_module=True returns dotted module path."""
        from build_cub.utils import get_parts

        path = Path("src/pkg/sub/mod.py")
        module: str = get_parts(path, to_module=True)
        assert module == "pkg.sub.mod"


class TestImmutableList:
    """Tests for ImmutableList sentinel class."""

    def test_raises_on_append(self) -> None:
        """Test ImmutableList raises on append."""
        from build_cub.utils._classes import ImmutableList

        immutable = ImmutableList([1, 2, 3])  # We will never use the ImmutableList like this lol
        with pytest.raises(TypeError, match="immutable"):
            immutable.append(4)

    def test_raises_on_setitem(self) -> None:
        """Test ImmutableList raises on item assignment."""
        from build_cub.utils._classes import ImmutableList

        immutable = ImmutableList([1, 2, 3])
        with pytest.raises(TypeError, match="immutable"):
            immutable[0] = 99

    def test_raises_on_extend(self) -> None:
        """Test ImmutableList raises on extend."""
        from build_cub.utils._classes import ImmutableList

        immutable = ImmutableList([1, 2, 3])
        with pytest.raises(TypeError, match="immutable"):
            immutable.extend([4, 5])

    def test_bool_is_false(self) -> None:
        """Test ImmutableList is falsy (used as empty sentinel)."""
        from build_cub.utils import EMPTY_IMMUTABLE_LIST

        assert bool(EMPTY_IMMUTABLE_LIST) is False

    def test_len_is_zero(self) -> None:
        """Test ImmutableList reports length as 0 (sentinel behavior)."""
        from build_cub.utils import EMPTY_IMMUTABLE_LIST

        assert len(EMPTY_IMMUTABLE_LIST) == 0
