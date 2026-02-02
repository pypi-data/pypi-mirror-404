from __future__ import annotations

from collections.abc import Callable  # noqa: TC003
import fcntl
from os import walk
from pathlib import Path
from typing import IO, TYPE_CHECKING, Any, Literal, overload

from lazy_bear import lazy

from build_cub.utils._config import global_config

from ._ignore_handler import IgnoreHandler

if TYPE_CHECKING:
    from collections.abc import Sequence
    from functools import reduce
    from operator import getitem
    from shutil import copy2
    import tomllib

    from build_cub.utils import StrPath, TomlData
else:
    tomllib = lazy("tomllib")
    reduce = lazy("functools", "reduce")
    getitem = lazy("operator", "getitem")
    copy2 = lazy("shutil", "copy2")


ignore_handler = IgnoreHandler.get_instance()


def NOOP_FUNCTION(*args, **kwargs) -> None:  # noqa: N802
    """A no operation function that does nothing."""


def path_check(path: Path) -> None:
    # TODO: Make locating this more dynamic with fallbacks
    from ._exec import CannotLocatePyProjectError

    if not path.exists():
        raise CannotLocatePyProjectError


def load_toml(path: StrPath = "bear_build.toml") -> TomlData:
    """Load and parse a TOML file.

    Caller needs to handle exceptions.
    """
    with Path(path).open("rb") as f:
        return tomllib.load(f)


def load_toml_section(
    path_to_reduce: tuple[str, ...] = global_config.misc.path_to_custom,
    path: Path = global_config.paths.pyproject_toml,
) -> TomlData:
    path_check(path)
    try:
        data: TomlData = load_toml(path)
        return reduce(getitem, path_to_reduce, data)
    except tomllib.TOMLDecodeError as e:
        raise RuntimeError(f"Failed to load build settings from {path}") from e


@overload
def get_parts(file: Path | str, to_module: Literal[True]) -> str: ...


@overload
def get_parts(file: Path | str, to_module: Literal[False] = False) -> tuple[str, ...]: ...


def get_parts(file: Path | str, to_module: bool = False) -> tuple[str, ...] | str:
    parts: tuple[str, ...] = Path(file).with_suffix(suffix="").parts
    if parts[0] == "src":
        parts = parts[1:]
    if to_module:
        return ".".join(parts)
    return parts


def item_check[T](n: int, data: tuple[str, ...], expected_type: Callable[[str], T]) -> tuple[T, ...]:
    if len(data) != n:
        raise ValueError(f"Version string must have {n} parts: {data!r}")
    values = []
    for i, part in enumerate(data):
        try:
            values.append(expected_type(part))
        except ValueError as e:
            raise TypeError(f"Part {i} must be of type {expected_type.__name__}: {part}") from e  # ty:ignore[unresolved-attribute]
    return tuple(values)


def pre_allocate_list[T](size: int, default: T, *values: T) -> list[T]:
    """Pre-allocate a list of given size with a default value, then fill with provided values."""
    pre_allocated_list: list[T] = [default] * size
    if not values:
        return pre_allocated_list
    for i, value in enumerate(values):
        pre_allocated_list[i] = value
    return pre_allocated_list


def copy_file_into(file: Path, dest: Path, mkdir: bool = False, file_name: bool = False) -> None: ...


if global_config.python_314_or_newer:

    def _314_copy_file(file: Path, dest: Path, mkdir: bool = False, file_name: bool = False) -> None:
        if mkdir:
            dest.parent.mkdir(parents=True, exist_ok=True)
        if file_name:
            file.copy(dest, preserve_metadata=True)  # ty:ignore[unresolved-attribute] (method exists in 3.14+)  # ty:ignore[unused-ignore-comment]
        else:
            file.copy_into(dest.parent, preserve_metadata=True)  # ty:ignore[unresolved-attribute] (method exists in 3.14+)  # ty:ignore[unused-ignore-comment]

    globals()["copy_file_into"] = _314_copy_file
    # copy_file_into = _314_copy_file
else:

    def _pre_314_copy_file(file: Path, dest: Path, mkdir: bool = False, file_name: bool = False) -> None:  # noqa: ARG001
        if mkdir:
            dest.parent.mkdir(parents=True, exist_ok=True)
        copy2(file, dest)

    globals()["copy_file_into"] = _pre_314_copy_file
    # copy_file_into = _pre_314_copy_file


SHARED_LOCK: int = fcntl.LOCK_SH
UNLOCK: int = fcntl.LOCK_UN


def flock(handle: IO[Any], operation: int) -> None:
    """Apply a file lock operation on the given file handle."""
    fcntl.flock(handle.fileno(), operation)


def sh_lock(handle: IO[Any]) -> None:
    """Apply a shared lock on the given file handle."""
    flock(handle=handle, operation=SHARED_LOCK)


def unlock(handle: IO[Any]) -> None:
    """Unlock the given file handle."""
    flock(handle=handle, operation=UNLOCK)


def search_paths(pkg_root: Path, exts: Sequence[str]) -> list[Path]:
    """Recursively find files in the given package root, respecting ignore patterns."""
    files: list[Path] = []
    for dirpath, dirs, filenames in walk(str(pkg_root)):
        for filename in filenames:
            dir_path: Path = Path(dirpath) / filename
            if not any(dir_path.suffix == ext for ext in exts):
                continue
            if ignore_handler.should_ignore(str(dir_path.relative_to(pkg_root))):
                continue
            files.append(dir_path)
        for dirname in list(dirs):
            dir_str = str(Path(pkg_root) / dirname) + "/"
            if ignore_handler.should_ignore(dir_str):
                dirs.remove(dirname)
    return files


def env_bool(var: str, default: bool = False) -> bool:
    """Get a boolean value from an environment variable."""
    from os import getenv

    val: str | None = getenv(var, None)
    if val is None:
        return default
    return val.lower() in ("1", "true", "yes", "on")


def merge_lists(a: list[str], b: list[str]) -> list[str]:
    """Merge two lists, removing duplicates while preserving order."""
    return list(dict.fromkeys(a + b))
