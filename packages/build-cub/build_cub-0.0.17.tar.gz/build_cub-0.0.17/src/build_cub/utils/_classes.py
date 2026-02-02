from __future__ import annotations

from collections.abc import Callable  # noqa: TC003
from types import MappingProxyType
from typing import NoReturn


def _immutable(self, *args, **kwargs) -> NoReturn:  # noqa: ANN001, ARG001
    raise TypeError("This list is immutable and cannot be modified.")


_SENTINEL = object()


class ImmutableList[T](list):
    """An immutable list that prevents modification."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.__sentinel__: bool = super().__len__() == 1 and self[0] is _SENTINEL

    __setitem__: Callable[..., NoReturn] = _immutable
    __delitem__: Callable[..., NoReturn] = _immutable
    append: Callable[..., NoReturn] = _immutable
    extend: Callable[..., NoReturn] = _immutable
    insert: Callable[..., NoReturn] = _immutable
    remove: Callable[..., NoReturn] = _immutable
    pop: Callable[..., NoReturn] = _immutable
    clear: Callable[..., NoReturn] = _immutable

    def __len__(self) -> int:
        if self.__sentinel__:
            return 0
        return super().__len__()

    def __bool__(self) -> bool:
        if self.__sentinel__:
            return False
        return super().__len__() > 0

    def __hash__(self) -> int:
        if self.__sentinel__:
            return hash("__sentinel__")
        return hash(tuple(self))

    def __eq__(self, other: object) -> bool:
        if self.__sentinel__:
            return other == []
        if not isinstance(other, list):
            return False
        return list(self) == other

    def __ne__(self, other: object) -> bool:
        return not self.__eq__(other)


EMPTY_IMMUTABLE_LIST: ImmutableList[object] = ImmutableList([_SENTINEL])
IMMUTABLE_DEFAULT_DICT: MappingProxyType = MappingProxyType({})
"""Whenever we need to use a default data structure in a non-dataclass."""
