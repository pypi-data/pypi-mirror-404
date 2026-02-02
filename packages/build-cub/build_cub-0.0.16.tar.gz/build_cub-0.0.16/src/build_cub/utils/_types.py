from os import PathLike
from pathlib import Path
from typing import Any, Literal

type BinaryExtension = Literal[".so", ".pyd", ".dylib"]
type CompileArgs = Literal["extra_compile_args", "extra_compile_args_windows"]
type LinkArgs = Literal["extra_link_args", "extra_link_args_windows"]
type TomlData = dict[str, Any]
type StrPath = str | Path | PathLike
