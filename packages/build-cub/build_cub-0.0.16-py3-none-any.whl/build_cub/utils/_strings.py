from __future__ import annotations

from collections.abc import Iterable, Sequence  # noqa: TC003
from functools import cached_property
import re
from typing import Any, Literal, overload

SPACE = " "
UNDERSCORE = "_"
DASH = "-"
INDENT: str = SPACE * 4
EMPTY_STRING: Literal[""] = ""

CaseChoices = Literal["snake", "kebab", "camel", "pascal", "screaming_snake"]


@overload
def pop_iter[T](seq: Sequence[T], n: int = 0, remainder: Literal[False] = False) -> T: ...
@overload
def pop_iter[T](seq: Sequence[T], n: int, remainder: Literal[True]) -> tuple[T, Iterable[T]]: ...
def pop_iter[T](seq: Sequence[T], n: int = 0, remainder: bool = True) -> tuple[T, Iterable[T]] | T:
    """Pop an item at the nth index from an iterable and return the remainder.

    Args:
        seq: The iterable to pop from.
        n: The index at which to pop the item.
        remainder: Whether to return the remainder of the iterable.

    Returns:
        tuple[Any, Iterable] | Any: The popped item and the remainder of the iterable, or just the popped item if remainder is False.
    """
    if not seq:
        raise IndexError("Cannot pop from an empty sequence")

    if n < 0:
        n = len(seq) + n

    if n < 0 or n >= len(seq):
        raise IndexError("Index out of bounds")

    popped = seq[n]
    if remainder:
        return popped, (item for i, item in enumerate(seq) if i != n)
    return popped


def join(*segments: Any, depth: int | None = None, indent: str | None = None, sep: str = "") -> str:
    """Concatenate segments with indentation at specified depth.

    Args:
        *segments: The string segments to join.
        depth: The indentation depth (number of indents).
        indent: Custom indent string. If None, uses default indent.
        sep: Separator to use between segments.

    Returns:
        The joined string with indentation.
    """
    _indent: str = INDENT * depth if depth is not None else (indent if indent is not None else EMPTY_STRING)
    return f"{_indent}{sep.join(segments)}"


@overload
def pop(s: str, n: int = 0, remainder: Literal[False] = False) -> str: ...
@overload
def pop(s: str, n: int, remainder: Literal[True]) -> tuple[str, str]: ...
def pop(s: str, n: int = 0, remainder: bool = True) -> tuple[str, str] | str:
    """Pop characters at the nth index from a string and return the remainder.

    Args:
        s: The string to pop from.
        n: The index at which to pop characters.
        remainder: Whether to return the remainder of the string.

    Returns:
        A tuple containing the popped character and the remainder of the string.
    """
    if n < 0 or n >= len(s):
        raise ValueError("Invalid index")
    if not remainder:
        return s[n]
    return s[n], join(s[:n], s[n + 1 :])


class CaseConverter:
    """String casing utilities."""

    @cached_property
    def _cts_pattern(self) -> re.Pattern[str]:
        """Regex pattern to convert camelCase to snake_case.

        Returns:
            Compiled regex pattern for camelCase to snake_case conversion.
        """
        return re.compile(
            r"""
                (?<=[a-z])      # preceded by lowercase
                (?=[A-Z])       # followed by uppercase
                |               # OR
                (?<=[A-Z])      # preceded by lowercase
                (?=[A-Z][a-z])  # followed by uppercase, then lowercase
            """,
            re.X,
        )

    def camel_to_snake(self, value: str) -> str:
        """Convert a camelCase string to snake_case.

        Args:
            value: The camelCase string to convert.

        Returns:
            The converted snake_case string.
        """
        return self._cts_pattern.sub("_", value).lower()

    def snake_to_pascal(self, value: str) -> str:
        """Convert a snake_case string to PascalCase.

        Args:
            value: The snake_case string to convert.

        Returns:
            The converted PascalCase string.
        """
        return "".join(word.capitalize() for word in value.split(UNDERSCORE))

    def snake_to_kebab(self, value: str) -> str:
        """Convert a snake_case string to kebab-case.

        Args:
            value: The snake_case string to convert.

        Returns:
            The converted kebab-case string.
        """
        return value.replace(UNDERSCORE, DASH)

    def _normalized_case(self, value: str) -> str:
        current_case: str = detect_case(value)
        if current_case in {"camel", "pascal"}:
            return self.camel_to_snake(value)
        if current_case == "kebab":
            return value.replace(DASH, UNDERSCORE)
        if current_case == "screaming_snake":
            return value.lower()
        if current_case == "snake":
            return value
        return value

    def convert_to(self, value: str, target_case: CaseChoices) -> str:
        """Convert a string to the target case format, auto-detecting the source format.

        Args:
            value: The string to convert.
            target_case: The target case format ('snake', 'kebab', 'camel', 'pascal').

        Returns:
            The converted string.

        Raises:
            ValueError: If the target case is not supported.
        """
        normalized: str = self._normalized_case(value)
        match target_case:
            case "snake":
                return normalized
            case "kebab":
                return normalized.replace(UNDERSCORE, DASH)
            case "camel":
                words: list[str] = normalized.split(UNDERSCORE)
                first, rest = pop_iter(words)
                return first + "".join(word.capitalize() for word in rest)
            case "pascal":
                return self.snake_to_pascal(normalized)
            case "screaming_snake":
                return normalized.upper()
            case _:
                raise ValueError(f"Unsupported target case: {target_case}")


def detect_case(value: str) -> str:
    """Detect the casing format of a string.

    Args:
        value: The string to analyze.

    Returns:
        The detected case format: 'snake', 'kebab', 'camel', 'pascal', 'screaming_snake', or 'unknown'.
    """
    if not value:
        return "unknown"
    has_underscores: bool = UNDERSCORE in value
    has_dashes: bool = DASH in value
    has_uppercase: bool = any(c.isupper() for c in value)
    has_lowercase: bool = any(c.islower() for c in value)
    starts_with_upper: bool = value[0].isupper()
    has_spaces: bool = SPACE in value
    if has_spaces:
        return "unknown"
    if has_underscores and has_uppercase and not has_lowercase:
        return "screaming_snake"
    if has_underscores and not has_uppercase:
        return "snake"
    if has_dashes and not has_uppercase:
        return "kebab"
    if starts_with_upper and has_uppercase and has_lowercase and not has_underscores and not has_dashes:
        return "pascal"
    if not starts_with_upper and has_uppercase and has_lowercase and not has_underscores and not has_dashes:
        return "camel"
    return "unknown"


def to_snake(value: str) -> str:
    """Convert a string to snake_case.

    Args:
        value: The string to convert.

    Returns:
        The converted snake_case string.
    """
    return CaseConverter().convert_to(value, "snake")


def to_kebab(value: str) -> str:
    """Convert a string to kebab-case.

    Args:
        value: The string to convert.

    Returns:
        The converted kebab-case string.
    """
    return CaseConverter().convert_to(value, "kebab")


def to_camel(value: str) -> str:
    """Convert a string to camelCase.

    Args:
        value: The string to convert.

    Returns:
        The converted camelCase string.
    """
    return CaseConverter().convert_to(value, "camel")


def to_pascal(value: str) -> str:
    """Convert a string to PascalCase.

    Args:
        value: The string to convert.

    Returns:
        The converted PascalCase string.
    """
    return CaseConverter().convert_to(value, "pascal")


def to_screaming_snake(value: str) -> str:
    """Convert a string to SCREAMING_SNAKE_CASE.

    Args:
        value: The string to convert.

    Returns:
        The converted SCREAMING_SNAKE_CASE string.
    """
    return CaseConverter().convert_to(value, "screaming_snake")


def convert_case(value: str, target_case: CaseChoices) -> str:
    """Convert a string to the target case format, auto-detecting the source format.

    Args:
        value: The string to convert.
        target_case: The target case format ('snake', 'kebab', 'camel', 'pascal', 'screaming_snake').

    Returns:
        The converted string.
    """
    return CaseConverter().convert_to(value, target_case)
