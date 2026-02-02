"""Tests for the hatch version source plugin and related hooks."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess

import pytest

from build_cub.models._misc import BuildConfig  # noqa: TC001
from build_cub.utils import global_config


class TestVersionModel:
    """Tests for Version model parsing."""

    def test_version_from_dunamai_valid(self) -> None:
        """Test parsing a valid semver version from Dunamai."""
        from dunamai import Version as DunamaiVersion

        from build_cub.models._version import Version

        v = Version.from_version(DunamaiVersion("1.2.3"))
        assert v.major == 1
        assert v.minor == 2
        assert v.patch == 3

    def test_version_from_dunamai_with_prerelease(self) -> None:
        """Test parsing version with prerelease suffix falls back to default."""
        from dunamai import Version as DunamaiVersion

        from build_cub.models._version import Version

        v = Version.from_version(DunamaiVersion("1.2.3-beta.1"))
        # The regex only matches clean semver, so this should return default
        assert v.major == 0
        assert v.minor == 0
        assert v.patch == 0

    def test_version_str(self) -> None:
        """Test Version __str__ returns dotted format."""
        from build_cub.models._version import Version

        v = Version(major=3, minor=14, patch=159)
        assert str(v) == "3.14.159"

    def test_version_bool_nonzero(self) -> None:
        """Test Version is truthy when non-zero."""
        from build_cub.models._version import Version

        v = Version(major=1, minor=0, patch=0)
        assert bool(v) is True

    def test_version_bool_zero(self) -> None:
        """Test Version is falsy when all zeros."""
        from build_cub.models._version import Version

        v = Version(major=0, minor=0, patch=0)
        assert bool(v) is False


class TestDynamicVersioningSrc:
    """Tests for the DynamicVersioningSrc plugin class."""

    def test_plugin_instantiates(self, tmp_path: Path) -> None:
        """Test that the plugin can be instantiated with root and config."""
        from build_cub.hooks import DynamicVersioningSrc

        plugin = DynamicVersioningSrc(root=str(tmp_path), config={})
        # Plugin instantiated without error - that's the test
        assert plugin is not None
        assert plugin.PLUGIN_NAME == "build-cub"

    def test_plugin_has_correct_name(self, tmp_path: Path) -> None:
        """Test the plugin reports the correct PLUGIN_NAME."""
        from build_cub.hooks import DynamicVersioningSrc

        plugin = DynamicVersioningSrc(root=str(tmp_path), config={})
        assert plugin.PLUGIN_NAME == "build-cub"

    def test_get_version_data_returns_dict(self) -> None:
        """Test get_version_data returns dict with version key."""
        from build_cub.hooks import DynamicVersioningSrc

        plugin = DynamicVersioningSrc(root=".", config={})
        result: dict[str, str] = plugin.get_version_data()
        assert isinstance(result, dict)
        assert "version" in result
        assert isinstance(result["version"], str)

    def test_get_version_data_format(self) -> None:
        """Test version string matches semver format."""
        import re

        from build_cub.hooks import DynamicVersioningSrc

        plugin = DynamicVersioningSrc(root=".", config={})
        result: dict[str, str] = plugin.get_version_data()
        # Should be semver-ish (at least major.minor.patch)
        assert re.match(r"^\d+\.\d+\.\d+", result["version"])


class TestVersionFromGit:
    """Integration tests for version detection from git tags."""

    def test_version_from_git_tag(self, tmp_path: Path) -> None:
        """Test that version is correctly read from a git tag."""
        # Create a mini git repo with a tag
        subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=tmp_path,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test"],
            cwd=tmp_path,
            check=True,
            capture_output=True,
        )
        (tmp_path / "file.txt").write_text("hello")
        subprocess.run(["git", "add", "."], cwd=tmp_path, check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "init"],
            cwd=tmp_path,
            check=True,
            capture_output=True,
        )
        subprocess.run(["git", "tag", "v2.5.0"], cwd=tmp_path, check=True, capture_output=True)

        # Test version detection from that repo
        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            from dunamai import Vcs, Version as DunamaiVersion

            v: DunamaiVersion = DunamaiVersion.from_vcs(Vcs.Git)
            assert v.base == "2.5.0"
        finally:
            os.chdir(old_cwd)

    def test_version_model_from_git_tag(self, tmp_path: Path) -> None:
        """Test Version.from_version correctly parses a git-derived version."""
        subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=tmp_path,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test"],
            cwd=tmp_path,
            check=True,
            capture_output=True,
        )
        (tmp_path / "file.txt").write_text("hello")
        subprocess.run(["git", "add", "."], cwd=tmp_path, check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "init"],
            cwd=tmp_path,
            check=True,
            capture_output=True,
        )
        subprocess.run(["git", "tag", "v7.8.9"], cwd=tmp_path, check=True, capture_output=True)

        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            from dunamai import Vcs, Version as DunamaiVersion

            from build_cub.models._version import Version

            v = Version.from_version(DunamaiVersion.from_vcs(Vcs.Git))
            assert v.major == 7
            assert v.minor == 8
            assert v.patch == 9
        finally:
            os.chdir(old_cwd)


class TestBuildConfig:
    """Tests for BuildConfig loading."""

    def test_build_config_loads_from_pyproject(self) -> None:
        """Test BuildConfig can load from the project's pyproject.toml."""
        from build_cub.models._misc import BuildConfig

        config: BuildConfig = BuildConfig.load_from_file(global_config.paths.pyproject_toml)
        assert config.vcs == "git"
        assert config.fallback_version is not None

    def test_build_config_has_required_fields(self) -> None:
        """Test BuildConfig has all required fields after loading."""
        from build_cub.models._misc import BuildConfig

        config = BuildConfig.load_from_file(global_config.paths.pyproject_toml)
        assert hasattr(config, "vcs")
        assert hasattr(config, "style")
        assert hasattr(config, "metadata")
        assert hasattr(config, "fallback_version")


class TestPartCheck:
    """Tests for the part_check utility function."""

    def test_part_check_valid_input(self) -> None:
        """Test part_check with valid 3-part version."""
        from build_cub.utils import item_check

        result: tuple[int, ...] = item_check(3, ("1", "2", "3"), int)
        assert result == (1, 2, 3)

    def test_part_check_wrong_count_raises(self) -> None:
        """Test part_check raises ValueError with wrong part count."""
        from build_cub.utils import item_check

        with pytest.raises(ValueError, match="must have 3 parts"):
            item_check(3, ("1", "2"), int)

    def test_part_check_invalid_type_raises(self) -> None:
        """Test part_check raises TypeError for non-convertible values."""
        from build_cub.utils import item_check

        with pytest.raises(TypeError, match="must be of type int"):
            item_check(3, ("1", "two", "3"), int)


class TestVersionEdgeCases:
    """Edge case tests for Version model."""

    def test_version_with_leading_zeros(self) -> None:
        """Test version parsing handles leading zeros."""
        from dunamai import Version as DunamaiVersion

        from build_cub.models._version import Version

        v = Version.from_version(DunamaiVersion("01.02.03"))
        # Leading zeros should still parse as integers
        assert v.major == 1
        assert v.minor == 2
        assert v.patch == 3

    def test_version_large_numbers(self) -> None:
        """Test version handles large version numbers."""
        from dunamai import Version as DunamaiVersion

        from build_cub.models._version import Version

        v = Version.from_version(DunamaiVersion("100.200.300"))
        assert v.major == 100
        assert v.minor == 200
        assert v.patch == 300

    def test_default_version_is_zero(self) -> None:
        """Test DEFAULT_VERSION is all zeros."""
        from build_cub.models._version import DEFAULT_VERSION

        assert DEFAULT_VERSION.major == 0
        assert DEFAULT_VERSION.minor == 0
        assert DEFAULT_VERSION.patch == 0
        assert bool(DEFAULT_VERSION) is False

    def test_version_model_dump(self) -> None:
        """Test Version can be dumped to dict for template rendering."""
        from build_cub.models._version import Version

        v = Version(major=1, minor=2, patch=3)
        dumped = v.model_dump()
        assert dumped == {"major": 1, "minor": 2, "patch": 3, "version_str": "1.2.3"}


class TestHookRegistration:
    """Tests for hatch hook registration."""

    def test_hatch_register_version_source_returns_class(self) -> None:
        """Test the hookimpl function returns the plugin class."""
        from build_cub.hooks import DynamicVersioningSrc, hatch_register_version_source

        result = hatch_register_version_source()
        assert result is DynamicVersioningSrc

    def test_plugin_inherits_from_version_source_interface(self) -> None:
        """Test DynamicVersioningSrc inherits from VersionSourceInterface."""
        from hatchling.version.source.plugin.interface import VersionSourceInterface

        from build_cub.hooks import DynamicVersioningSrc

        assert issubclass(DynamicVersioningSrc, VersionSourceInterface)


class TestTemplatePathSecurity:
    """Tests for template output path security."""

    def test_template_rejects_path_traversal(self, tmp_path: Path) -> None:
        """Test template write rejects paths outside project root."""
        from build_cub.models._templates import TemplateDefinition

        template = TemplateDefinition(
            output=Path("../../../etc/evil.py"),
            content="malicious = True",
        )

        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            with pytest.raises(ValueError, match="outside the project root"):
                template.write({"version": {"major": 1, "minor": 0, "patch": 0}})
        finally:
            os.chdir(old_cwd)

    def test_template_allows_nested_paths(self, tmp_path: Path, monkey_patch_cwd: None) -> None:  # noqa: ARG002
        """Test template write allows deeply nested paths within project."""
        from build_cub.models._templates import TemplateDefinition

        output_file = tmp_path / "src" / "pkg" / "subpkg" / "_version.py"
        template = TemplateDefinition(
            output=output_file,
            content="__version__ = '{{ version.major }}'",
        )

        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            result = template.write({"version": {"major": 5, "minor": 0, "patch": 0}})
            assert result.exists()
            assert result.read_text() == "__version__ = '5'"
        finally:
            os.chdir(old_cwd)


class TestTemplateRendering:
    """Tests for template rendering with version variables."""

    def test_template_renders_version(self, tmp_path: Path) -> None:
        """Test TemplateDefinition renders version variables correctly."""
        from build_cub.models._templates import TemplateDefinition

        template = TemplateDefinition(
            output=tmp_path / "test.py",
            content="__version__ = '{{ version.major }}.{{ version.minor }}.{{ version.patch }}'",
        )
        result = template.render({"version": {"major": 1, "minor": 2, "patch": 3}})
        assert result == "__version__ = '1.2.3'"

    def test_template_writes_file(self, tmp_path: Path, monkey_patch_cwd: None) -> None:  # noqa: ARG002
        """Test TemplateDefinition.write creates the output file."""
        output_file = tmp_path / "generated" / "_version.py"
        from build_cub.models._templates import TemplateDefinition

        template = TemplateDefinition(
            output=output_file,
            content="VERSION = ({{ version.major }}, {{ version.minor }}, {{ version.patch }})",
        )

        # Need to be in the tmp_path for the security check to pass
        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            written_path = template.write({"version": {"major": 4, "minor": 5, "patch": 6}})
            assert written_path.exists()
            assert written_path.read_text() == "VERSION = (4, 5, 6)"
        finally:
            os.chdir(old_cwd)

    def test_template_with_custom_variables(self, tmp_path: Path) -> None:
        """Test templates can use custom user-defined variables."""
        output_file = tmp_path / "_version.py"
        from build_cub.models._templates import TemplateDefinition

        template = TemplateDefinition(
            output=output_file,
            content="DB_VERSION = '{{ database.major }}.{{ database.minor }}'",
        )

        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            result = template.render({"database": {"major": 2, "minor": 0}})
            assert result == "DB_VERSION = '2.0'"
        finally:
            os.chdir(old_cwd)


# ruff: noqa: S607
