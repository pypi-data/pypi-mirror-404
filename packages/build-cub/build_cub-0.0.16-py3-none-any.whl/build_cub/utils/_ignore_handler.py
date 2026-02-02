"""Python module to handle ignore patterns for file paths in a directory tree."""

from __future__ import annotations

from pathlib import Path
import re
from typing import TYPE_CHECKING

from lazy_bear import lazy
from pathspec import GitIgnoreSpec

from singleton_base import SingletonBase

if TYPE_CHECKING:
    from collections.abc import Iterable

    from build_cub.utils import global_config
else:
    global_config = lazy("build_cub.utils._config", "global_config")

IGNORE_PATTERNS: tuple[str, ...] = (
    "**/__pycache__",
    "**/*.pyc",
    "**/*.pyo",
    "**/.mypy_cache",
    "**/.pytest_cache",
    "**/.tox",
    "**/.git",
    "**/.venv",
    "**/.env",
    ".vscode",
    ".idea",
    "*.DS_Store*",
    "**/__pypackages__",
    "**/.coverage",
    ".*.swp",
    ".*.swo",
    "*.lock",
    "**/.nox",
    "**/.ruff_cache",
    "**/.pytest_cache",
)

PROTECTED_RE: re.Pattern[str] = re.compile(
    r"^[!*\/]*(?:build|dist|target)[\/]*$"
    r"|\.(?:so|dylib|py[cod])$"
)

OVERRIDES: list[str] = [
    "!**/*.so",
    "!**/*.py[cod]",
    "!**/*.dylib",
    "!**/build",
    "!**/dist",
    "!**/target",
]


def filtered_patterns(patterns: Iterable[str]) -> list[str]:
    """Filter out protected patterns from a list of patterns.

    Args:
        patterns: Sequence of ignore patterns
    Returns:
        List of filtered ignore patterns
    """
    return [p for p in patterns if not PROTECTED_RE.match(p)]


class IgnoreHandler(SingletonBase):
    """Class to handle ignore patterns for file paths."""

    def __init__(self, gitignore_file: Path | None = None, patterns: Iterable[str] | None = None) -> None:
        """Initialize the IgnoreHandler with default and optional gitignore patterns."""
        local_patterns: list[str] = list(IGNORE_PATTERNS)
        if gitignore_file is None:
            gitignore_file = global_config.paths.cwd / ".gitignore"
        if gitignore_file and gitignore_file.exists():
            git_lines: list[str] = self.parse_gitignore(gitignore_file)
            self.update(local_patterns, git_lines)
        if patterns:
            local_patterns.extend(patterns)
        local_patterns.extend(OVERRIDES)
        if global_config.env == "test":
            local_patterns.append("!**/var")
        self.patterns: list[str] = list(dict.fromkeys(filtered_patterns(local_patterns)))
        self.spec: GitIgnoreSpec = self._create_spec(self.patterns)

    @staticmethod
    def update(base_patterns: list[str], patterns: Iterable[str] | str) -> None:
        if isinstance(patterns, str):
            patterns = [patterns]
        base_patterns.extend(filtered_patterns(patterns))

    @staticmethod
    def parse_gitignore(gitignore_file: Path) -> list[str]:
        """Parse a .gitignore file and return a list of ignore patterns.

        Args:
            gitignore_file (Path): Path to the .gitignore file

        Returns:
            List of ignore patterns
        """
        if not gitignore_file.exists():
            return []
        return [
            line.strip()
            for line in gitignore_file.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.startswith("#")
        ]

    @staticmethod
    def _create_spec(patterns: list[str]) -> GitIgnoreSpec:
        """Create a pathspec from the given patterns.

        Args:
            patterns: Set of ignore patterns

        Returns:
            A pathspec object
        """
        return GitIgnoreSpec.from_lines("gitignore", patterns)

    def should_ignore(self, path: Path | str) -> bool:
        """Check if a given path should be ignored based on the ignore patterns.

        Args:
            path (Path): The path to check
        Returns:
            bool: True if the path should be ignored, False otherwise
        """
        if isinstance(path, str):
            path = path.replace("\\", "/")

        path_obj: Path = Path(path).expanduser()
        path_str: str = path_obj.as_posix()

        if path_obj.is_dir() and not path_str.endswith("/"):
            path_str += "/"

        return self.spec.match_file(path_str)

    def add_patterns(self, patterns: Iterable[str]) -> None:
        """Add a new pattern to the ignore list.

        Args:
            pattern (str): The pattern to add
        """
        self.update(base_patterns=self.patterns, patterns=patterns)
        self.spec = self._create_spec(self.patterns)
