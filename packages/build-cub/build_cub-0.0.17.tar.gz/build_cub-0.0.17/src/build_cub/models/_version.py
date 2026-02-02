from __future__ import annotations

import re
from typing import TYPE_CHECKING, Self

from dunamai import Vcs, Version as DunamaiVersion
from pydantic import BaseModel, computed_field

from build_cub.utils import item_check

if TYPE_CHECKING:
    from build_cub.models._misc import BuildConfig

STR_REGEX = r"^(\d+)\.(\d+)\.(\d+)$"
_pattern: re.Pattern[str] | None = None


def get_version_pattern() -> re.Pattern[str]:
    """Get or compile the version regex pattern."""
    global _pattern  # noqa: PLW0603
    if _pattern is None:
        _pattern = re.compile(STR_REGEX)
    return _pattern


class VersionNumbers(BaseModel):
    """Simple major.minor.patch version - used for user-defined version variables."""

    major: int = 0
    minor: int = 0
    patch: int = 0


class Version(VersionNumbers):
    """A pydantic model to store version information."""

    @computed_field
    def version_str(self) -> str:
        return str(self)

    def __bool__(self) -> bool:
        """Check if version is non-zero."""
        return any((self.major, self.minor, self.patch))

    def __str__(self) -> str:
        """Get the version as a string."""
        return f"{self.major}.{self.minor}.{self.patch}"

    @classmethod
    def from_version(cls, version: DunamaiVersion) -> Self:
        """Create a Version instance from a DunamaiVersion."""
        regex: re.Pattern[str] = get_version_pattern()
        match: re.Match[str] | None = regex.match(version.base)
        if match:
            vals: tuple[int, ...] = item_check(n=3, data=match.groups(), expected_type=int)
            return cls(major=vals[0], minor=vals[1], patch=vals[2])
        return cls()

    @classmethod
    def get_version(cls, build_settings: BuildConfig) -> Self:
        """Get version information from VCS or fallback."""
        try:
            return cls.from_version(DunamaiVersion.from_vcs(Vcs[build_settings.vcs.capitalize()]))
        except RuntimeError:
            return cls.from_version(DunamaiVersion(build_settings.fallback_version))


DEFAULT_VERSION = Version()
