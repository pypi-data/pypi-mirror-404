from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Generic, TypeVar

from ._models import Artifact, ValidationResult as Result

if TYPE_CHECKING:
    from pathlib import Path

T_contra = TypeVar("T_contra", contravariant=True)

ResultCallable = Callable[[T_contra], Result]


class BaseValidator(Generic[T_contra]):  # noqa: UP046
    __slots__ = ("artifact", "output_path", "tests_to_run")

    output_path: Path
    tests_to_run: list[ResultCallable]
    artifact: T_contra

    def __init__(self, artifact: T_contra, output_path: Path) -> None:
        """Create the validator."""
        self.artifact = artifact
        self.output_path: Path = output_path
        self.tests_to_run = []

    def register_test(self, test: ResultCallable) -> None:
        """Add to the tests to be run."""
        self.tests_to_run.append(test)

    def _validate(self) -> Result:
        artifact: Artifact = Artifact(path=self.output_path)
        artifact.extra.empty = True
        for test in self.tests_to_run:
            result: Result = test(self.artifact)
            if not result.success:
                return result
            if artifact.get("empty", False):
                artifact: Artifact = result.obj
        return Result(obj=artifact).succeeded("Passed all validation tests")

    def validate(self) -> Result:
        return self._validate()
