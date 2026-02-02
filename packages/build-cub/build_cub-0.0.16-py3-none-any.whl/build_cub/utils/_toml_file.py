"""TOML file representation."""

from __future__ import annotations

from collections.abc import Callable, Generator  # noqa: TC003
from contextlib import contextmanager
from pathlib import Path
import tomllib
from typing import IO, TYPE_CHECKING, Any, Literal, Self, overload

from lazy_bear import lazy
from pydantic import BaseModel

if TYPE_CHECKING:
    from functools import reduce
    from operator import getitem

    from build_cub.utils._funcs import path_check, sh_lock, unlock
    from build_cub.utils._types import TomlData

    from ._types import StrPath
else:
    reduce = lazy("functools", "reduce")
    getitem = lazy("operator", "getitem")
    path_check, sh_lock, unlock = lazy("build_cub.utils._funcs", "path_check", "sh_lock", "unlock")


class TomlFile:
    """Representation of TOML file."""

    def __init__(self, file: StrPath) -> None:
        self.file: Path = Path(file)
        path_check(self.file)
        self._data: TomlData | None = None
        self._current_data: TomlData | None = None

    @property
    def data(self) -> TomlData:
        if self._data is None:
            self._data = self.load()
        return self._data

    @property
    def current_data(self) -> TomlData:
        if self._current_data is None:
            self._current_data = self.data
        return self._current_data

    @contextmanager
    def handle(self, mode: str = "r+") -> Generator[IO[Any], Any]:
        handle: IO[Any] = open(self.file, mode)  # noqa: SIM115
        try:
            sh_lock(handle)
            handle.seek(0)
            yield handle
        finally:
            unlock(handle)
            handle.close()

    def reset(self) -> Self:
        """Reset current_data to the root data."""
        self._current_data = self.data
        return self

    def load(self) -> TomlData:
        with self.handle() as handle:
            data: str = handle.read()
            if data.strip():
                return tomllib.loads(data)
        return {}

    def load_and(self) -> Self:
        self.load()
        return self

    @overload
    def get[T](self, item: Any = None, typed: Callable[..., T] = ...) -> T: ...  # pyright: ignore[reportInvalidTypeVarUse]

    @overload
    def get[T](self, item: None) -> TomlData: ...

    @overload
    def get[T](self, item: Any) -> Any: ...

    def get[T](self, item: Any = None, typed: Callable[..., T] | None = None) -> Any:
        if item is None:
            return typed(self.current_data) if typed is not None else self.current_data
        return self.current_data.get(item)

    def _get_section(self, section: str) -> Any:
        current = self.data
        for key in section.split("."):
            if not isinstance(current, dict) or key not in current:
                return {}
            if isinstance(current, dict) and key in current:
                current: Any = current[key]
        return current

    @overload
    def navigate(self, path: str | tuple[str, ...], reset: bool = False, get_value: Literal[False] = False) -> Self: ...
    @overload
    def navigate(self, path: str | tuple[str, ...], reset: bool = False, get_value: Literal[True] = True) -> Any: ...
    def navigate(self, path: str | tuple[str, ...], reset: bool = False, get_value: bool = False) -> Self | Any:
        """Get a particular section from the Toml file using a tuple or dot dontation string.

        Args:
            path (str | tuple[str, ...]): Input to access particular path within TOML
            reset (bool): Whether to reset current_data to the root data before navigation.
             Defaults to False.
            get_value (bool): Whether to return the value at the path instead of TomlFile.
        """
        if reset:
            self._current_data = self.data
        try:
            if isinstance(path, str):
                value: TomlData = self._get_section(path)
            else:
                value = reduce(getitem, path, self.current_data)
            self._current_data = value
            if get_value:
                return value
            return self
        except tomllib.TOMLDecodeError as e:
            raise RuntimeError(f"Failed to load from {self.file}") from e

    def model_validate[T: BaseModel](self, model: type[T]) -> T:
        return model.model_validate(self.current_data)

    def __str__(self) -> str:
        return str(self.current_data)


__all__ = ["TomlFile"]

# if __name__ == "__main__":
#     toml = TomlFile("pyproject.toml")

#     print(toml.load_and().load_section("tool.hatch.build.hooks.custom"))
