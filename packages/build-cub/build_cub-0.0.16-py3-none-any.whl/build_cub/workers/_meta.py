from __future__ import annotations

from typing import TYPE_CHECKING, NamedTuple

from lazy_bear import lazy

if TYPE_CHECKING:
    from build_cub.models._base import BaseSettings
    from build_cub.models._build_data import BuildData
else:
    BaseSettings = lazy("build_cub.models._base")
    BuildData = lazy("build_cub.models._build_data")

from build_cub.utils._strings import to_pascal


class WorkerImport(NamedTuple):
    name: str
    class_name: str
    settings: BaseSettings


def get_module_map(
    build_data: BuildData,
    workers: list[str],
    suffix: str,
) -> list[WorkerImport]:
    output: list[WorkerImport] = []
    for worker in workers:
        pascal_name: str = f"{to_pascal(worker)}{suffix}"
        settings: BaseSettings | None = getattr(build_data, worker, None)
        if settings is None:
            continue
        output.append(WorkerImport(name=worker, class_name=pascal_name, settings=settings))
    return output


__all__ = ["get_module_map"]
