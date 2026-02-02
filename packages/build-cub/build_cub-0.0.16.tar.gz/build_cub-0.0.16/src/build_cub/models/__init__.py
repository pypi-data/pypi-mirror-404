"""A set of models that represent the various compilation backends supported by Build Cub."""

from pydantic import BaseModel as _BaseModel, ConfigDict as _ConfigDict

from build_cub.models._version import DEFAULT_VERSION, Version


class IgnoredModel(_BaseModel):  # noqa: D101
    model_config = _ConfigDict(extra="ignore")


__all__ = ["DEFAULT_VERSION", "IgnoredModel", "Version"]
