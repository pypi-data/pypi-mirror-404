from __future__ import annotations

from operator import attrgetter, eq, ge, gt, le, lt
from pathlib import Path  # noqa: TC003
from typing import TYPE_CHECKING, Any, Literal, Self

from pydantic import BaseModel, Field, model_validator

from build_cub.utils import OS, global_config

if TYPE_CHECKING:
    from collections.abc import Callable


type ConditionType = Literal["platform", "env_var", "python_version"]
type ComparisonType = Literal["==", "<", "<=", ">", ">="]
type ProcedureType = Literal["append", "replace"]

COMP_OPS: dict[str, Callable[..., bool]] = {
    "==": eq,
    "<": lt,
    "<=": le,
    ">": gt,
    ">=": ge,
}


def append_to(obj: object, path: str, value: Any) -> None:
    if (_obj := attrgetter(path)(obj)) is not None:
        _obj(value)


def replace_with(obj: object, path: str, value: Any) -> None:
    if (_obj := attrgetter(path)(obj)) is not None:
        _obj(value)


class BaseProcedure(BaseModel):
    op: ProcedureType
    target: str
    value: Any

    def execute(self, obj: object) -> None:
        if self.op == "append":
            return append_to(obj, self.target, self.value)
        if self.op == "replace":
            return replace_with(obj, self.target, self.value)
        raise ValueError(f"Unknown procedure operation: {self.op}")


class BaseConditional(BaseModel):
    """A base class for build conditional."""

    proc: list[BaseProcedure] = Field(default_factory=list)

    def execute_all(self, obj: object) -> None:
        for procedure in self.proc:
            procedure.execute(obj)

    def __bool__(self) -> bool:
        return False


class EnvVarConditional(BaseConditional):
    """Environment variable-specific build conditional."""

    var: str = ""
    value: Any | None = None
    override: bool = False

    def __bool__(self) -> bool:
        from os import getenv

        from build_cub.utils._funcs import env_bool

        if self.override:
            return True

        return env_bool(self.var) if self.value is None else getenv(self.var) == self.value


class PlatformConditional(BaseConditional):
    """Platform-specific build conditional."""

    value: OS = Field(default=global_config.platform.os)
    target: str = "darwin"

    def __bool__(self) -> bool:
        return self.value.lower() == self.target.lower()


class PythonVersionConditional(BaseConditional):
    """Python version-specific build conditional."""

    value: tuple[int, ...] = Field(default=global_config.python_ver)
    target: tuple[int, ...] = (0, 0, 0)
    operator: ComparisonType = "=="

    def __bool__(self) -> bool:
        return COMP_OPS.get(self.operator, eq)(self.value, self.target)


class Conditionals(BaseModel):
    platform: dict[OS, PlatformConditional] = Field(default_factory=dict)
    env_var: dict[str, EnvVarConditional] = Field(default_factory=dict)
    py_ver: dict[str, PythonVersionConditional] = Field(default_factory=dict)

    @property
    def not_empty(self) -> bool:
        return bool(self.platform or self.env_var or self.py_ver)

    @model_validator(mode="after")
    def insert_var(self) -> Self:
        """Insert the key as the var for env_var conditionals."""
        for key, cond in self.env_var.items():
            cond.var = key
        for key, cond in self.platform.items():
            cond.target = key
        return self


class BuildConfig(BaseModel):
    """Build configuration settings loaded from bear_build.toml."""

    config_path: Path
    vcs: str
    style: str
    metadata: bool
    fallback_version: str

    @classmethod
    def load_from_file(cls, path: Path = global_config.paths.pyproject_toml) -> BuildConfig:
        """Load build settings from a TOML file.

        This will drill down to the ``[tool.hatch.build.hooks.custom]`` section.
        """
        from build_cub.utils import TomlFile, global_config

        return TomlFile(path).load_and().navigate(global_config.misc.path_to_custom).model_validate(BuildConfig)
