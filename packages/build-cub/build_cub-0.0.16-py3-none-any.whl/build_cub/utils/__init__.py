"""Collection of user tools for the entire repo."""

from __future__ import annotations

from ._classes import EMPTY_IMMUTABLE_LIST, IMMUTABLE_DEFAULT_DICT
from ._config import CLOSE_BRACE, OPEN_BRACE, OS, global_config
from ._funcs import (
    NOOP_FUNCTION,
    copy_file_into,
    get_parts,
    item_check,
    load_toml,
    load_toml_section,
    merge_lists,
    path_check,
    pre_allocate_list,
)
from ._printer import ColorPrinter
from ._toml_file import TomlFile
from ._types import CompileArgs, LinkArgs, StrPath, TomlData

__all__ = [
    "CLOSE_BRACE",
    "EMPTY_IMMUTABLE_LIST",
    "IMMUTABLE_DEFAULT_DICT",
    "NOOP_FUNCTION",
    "OPEN_BRACE",
    "OS",
    "ColorPrinter",
    "CompileArgs",
    "LinkArgs",
    "StrPath",
    "TomlData",
    "TomlFile",
    "copy_file_into",
    "get_parts",
    "global_config",
    "item_check",
    "load_toml",
    "load_toml_section",
    "merge_lists",
    "path_check",
    "pre_allocate_list",
]
