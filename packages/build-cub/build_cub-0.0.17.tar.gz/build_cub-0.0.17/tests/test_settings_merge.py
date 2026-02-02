"""Tests for compiler settings merge behavior (defaults + backend overrides)."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from build_cub.models._build_data import BuildData


class TestSettingsMerge:
    """Tests for the per-field merge behavior between defaults and backend settings."""

    def test_backend_with_no_settings_inherits_all_defaults(self, test_build_data: BuildData) -> None:
        """Backend with no custom settings gets all defaults."""
        # raw_cpp has no [raw_cpp.settings] section in fixture
        raw_cpp_args: list[str] = test_build_data.raw_cpp.settings.extra_compile_args
        default_args: list[str] = test_build_data.defaults.settings.extra_compile_args

        assert raw_cpp_args == default_args
        assert "-std=c++20" in raw_cpp_args

    def test_backend_with_custom_compile_args_merges(self, test_build_data: BuildData) -> None:
        """Backend with custom extra_compile_args merges with defaults (fixture uses merge mode)."""
        # cython has [cython.settings] with extra_compile_args in fixture
        cython_args: list[str] = test_build_data.cython.settings.extra_compile_args

        # In merge mode, both default and backend args are combined
        assert "-std=c++20" in cython_args  # From defaults
        assert "-O3" in cython_args  # From both (deduplicated)
        assert "-ffast-math" in cython_args  # From both (deduplicated)

    def test_backend_with_custom_link_args_merges(self, test_build_data: BuildData) -> None:
        """Backend with custom extra_link_args merges with defaults (fixture uses merge mode)."""
        cython_link_args: list[str] = test_build_data.cython.settings.extra_link_args
        default_link_args: list[str] = test_build_data.defaults.settings.extra_link_args

        # In merge mode, both are combined
        assert "-Wl,-w" in cython_link_args  # Cython's custom arg
        assert "-O3" in cython_link_args  # From defaults

    def test_backend_inherits_unset_fields_from_defaults(self, test_build_data: BuildData) -> None:
        """Backend inherits fields it didn't explicitly set."""
        # cython sets compile/link args but not include_dirs
        cython_include_dirs: list[str] = test_build_data.cython.settings.include_dirs
        default_include_dirs: list[str] = test_build_data.defaults.settings.include_dirs

        # Both are empty in this fixture, but the merge should work
        assert cython_include_dirs == default_include_dirs


class TestSettingsMergeFromDict:
    """Tests for merge behavior when building from raw dicts."""

    def test_partial_settings_merge_correctly(self) -> None:
        """Backend with only some settings inherits the rest from defaults."""
        from build_cub.models._build_data import BuildData

        data = {
            "general": {"name": "test", "enabled": True},
            "defaults": {
                "settings": {
                    "extra_compile_args": ["-O3", "-march=native"],
                    "extra_link_args": ["-flto"],
                    "include_dirs": ["/usr/include/custom"],
                }
            },
            "cython": {
                "enabled": True,
                "targets": [{"name": "test", "sources": "test.pyx"}],
                "settings": {
                    # Only override compile args, should inherit link_args and include_dirs
                    "extra_compile_args": ["-O2"],
                },
            },
        }

        build_data = BuildData.model_validate(data)

        # Cython uses its own compile args
        assert build_data.cython.settings.extra_compile_args == ["-O2"]

        # Cython inherits link_args from defaults
        assert build_data.cython.settings.extra_link_args == ["-flto"]

        # Cython inherits include_dirs from defaults
        assert build_data.cython.settings.include_dirs == ["/usr/include/custom"]

    def test_empty_backend_settings_inherits_all(self) -> None:
        """Backend with empty settings section inherits everything from defaults."""
        from build_cub.models._build_data import BuildData

        data = {
            "general": {"name": "test", "enabled": True},
            "defaults": {
                "settings": {
                    "extra_compile_args": ["-Wall", "-Werror"],
                    "extra_link_args": ["-shared"],
                }
            },
            "raw_cpp": {
                "enabled": True,
                "targets": [{"name": "test", "sources": ["test.cpp"]}],
                # No [raw_cpp.settings] section - should inherit all from defaults
            },
        }

        build_data = BuildData.model_validate(data)

        assert build_data.raw_cpp.settings.extra_compile_args == ["-Wall", "-Werror"]
        assert build_data.raw_cpp.settings.extra_link_args == ["-shared"]


class TestMergeModeReplace:
    """Tests for merge_mode='replace' (default behavior - backend overrides defaults)."""

    def test_replace_mode_backend_args_override_defaults(self) -> None:
        """In replace mode, backend args completely replace defaults."""
        from build_cub.models._build_data import BuildData

        data = {
            "general": {"name": "test", "enabled": True},
            "defaults": {
                "merge_mode": "replace",
                "settings": {
                    "extra_compile_args": ["-O3", "-Wall", "-Werror"],
                    "extra_link_args": ["-flto", "-shared"],
                },
            },
            "cython": {
                "enabled": True,
                "targets": [{"name": "test", "sources": "test.pyx"}],
                "settings": {"extra_compile_args": ["-O2"]},
            },
        }

        build_data = BuildData.model_validate(data)

        # Backend args completely replace defaults (no -O3, -Wall, -Werror)
        assert build_data.cython.settings.extra_compile_args == ["-O2"]
        # Unset fields still inherit
        assert build_data.cython.settings.extra_link_args == ["-flto", "-shared"]

    def test_replace_mode_is_default(self) -> None:
        """Replace mode should be the default when merge_mode is not specified."""
        from build_cub.models._build_data import BuildData

        data = {
            "general": {"name": "test", "enabled": True},
            "defaults": {
                "settings": {"extra_compile_args": ["-O3", "-Wall"]},
            },
            "cython": {
                "enabled": True,
                "targets": [{"name": "test", "sources": "test.pyx"}],
                "settings": {"extra_compile_args": ["-O2"]},
            },
        }

        build_data = BuildData.model_validate(data)

        assert build_data.defaults.merge_mode == "replace"
        assert build_data.cython.settings.extra_compile_args == ["-O2"]


class TestMergeModeMerge:
    """Tests for merge_mode='merge' (backend args combined with defaults)."""

    def test_merge_mode_combines_compile_args(self) -> None:
        """In merge mode, backend compile args are combined with defaults."""
        from build_cub.models._build_data import BuildData

        data = {
            "general": {"name": "test", "enabled": True},
            "defaults": {
                "merge_mode": "merge",
                "settings": {"extra_compile_args": ["-O3", "-Wall"]},
            },
            "cython": {
                "enabled": True,
                "targets": [{"name": "test", "sources": "test.pyx"}],
                "settings": {"extra_compile_args": ["-ffast-math", "-Wextra"]},
            },
        }

        build_data = BuildData.model_validate(data)

        # Both default and backend args should be present
        args = build_data.cython.settings.extra_compile_args
        assert "-O3" in args
        assert "-Wall" in args
        assert "-ffast-math" in args
        assert "-Wextra" in args

    def test_merge_mode_combines_link_args(self) -> None:
        """In merge mode, backend link args are combined with defaults."""
        from build_cub.models._build_data import BuildData

        data = {
            "general": {"name": "test", "enabled": True},
            "defaults": {
                "merge_mode": "merge",
                "settings": {"extra_link_args": ["-flto"]},
            },
            "raw_cpp": {
                "enabled": True,
                "targets": [{"name": "test", "sources": ["test.cpp"]}],
                "settings": {"extra_link_args": ["-shared"]},
            },
        }

        build_data = BuildData.model_validate(data)

        args = build_data.raw_cpp.settings.extra_link_args
        assert "-flto" in args
        assert "-shared" in args

    def test_merge_mode_combines_include_dirs(self) -> None:
        """In merge mode, include_dirs from both sources are combined."""
        from build_cub.models._build_data import BuildData

        data = {
            "general": {"name": "test", "enabled": True},
            "defaults": {
                "merge_mode": "merge",
                "settings": {"include_dirs": ["/usr/include", "/opt/include"]},
            },
            "pybind11": {
                "enabled": True,
                "targets": [{"name": "test", "sources": ["test.cpp"]}],
                "settings": {"include_dirs": ["/custom/include"]},
            },
        }

        build_data = BuildData.model_validate(data)

        dirs = build_data.pybind11.settings.include_dirs
        assert "/usr/include" in dirs
        assert "/opt/include" in dirs
        assert "/custom/include" in dirs

    def test_merge_mode_deduplicates_args(self) -> None:
        """In merge mode, duplicate args are removed while preserving order."""
        from build_cub.models._build_data import BuildData

        data = {
            "general": {"name": "test", "enabled": True},
            "defaults": {
                "merge_mode": "merge",
                "settings": {"extra_compile_args": ["-O3", "-Wall", "-ffast-math"]},
            },
            "cython": {
                "enabled": True,
                "targets": [{"name": "test", "sources": "test.pyx"}],
                "settings": {"extra_compile_args": ["-O3", "-Wextra"]},  # -O3 is duplicate
            },
        }

        build_data = BuildData.model_validate(data)

        args = build_data.cython.settings.extra_compile_args
        # -O3 should appear only once
        assert args.count("-O3") == 1
        # Order: defaults first, then backend additions
        assert args == ["-O3", "-Wall", "-ffast-math", "-Wextra"]

    def test_merge_mode_preserves_order_defaults_first(self) -> None:
        """In merge mode, default args come first, then backend args."""
        from build_cub.models._defaults import merge_lists

        defaults = ["-O3", "-Wall"]
        backend = ["-ffast-math", "-Wextra"]

        result = merge_lists(defaults, backend)

        assert result == ["-O3", "-Wall", "-ffast-math", "-Wextra"]


class TestMergeListsFunction:
    """Unit tests for the merge_lists helper function."""

    def test_merge_lists_empty_inputs(self) -> None:
        """Merging empty lists returns empty list."""
        from build_cub.models._defaults import merge_lists

        assert merge_lists([], []) == []

    def test_merge_lists_one_empty(self) -> None:
        """Merging with one empty list returns the other."""
        from build_cub.models._defaults import merge_lists

        assert merge_lists(["-O3"], []) == ["-O3"]
        assert merge_lists([], ["-O3"]) == ["-O3"]

    def test_merge_lists_no_overlap(self) -> None:
        """Merging non-overlapping lists concatenates them."""
        from build_cub.models._defaults import merge_lists

        result = merge_lists(["-O3", "-Wall"], ["-ffast-math"])
        assert result == ["-O3", "-Wall", "-ffast-math"]

    def test_merge_lists_full_overlap(self) -> None:
        """Merging identical lists returns single copy."""
        from build_cub.models._defaults import merge_lists

        result = merge_lists(["-O3", "-Wall"], ["-O3", "-Wall"])
        assert result == ["-O3", "-Wall"]

    def test_merge_lists_partial_overlap(self) -> None:
        """Merging partially overlapping lists deduplicates correctly."""
        from build_cub.models._defaults import merge_lists

        result = merge_lists(["-O3", "-Wall"], ["-Wall", "-Wextra"])
        assert result == ["-O3", "-Wall", "-Wextra"]
