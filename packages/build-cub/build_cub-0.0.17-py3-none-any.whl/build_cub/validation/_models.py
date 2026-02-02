from __future__ import annotations

from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path
from types import SimpleNamespace as Namespace
from typing import TYPE_CHECKING, Any, Self

from build_cub.utils import EMPTY_IMMUTABLE_LIST

if TYPE_CHECKING:
    from pathlib import Path


@dataclass(slots=True)
class Artifact:
    path: Path
    extra: Namespace = field(default_factory=Namespace)

    def get[D](self, name: str, default: D) -> Any | D:
        return getattr(self.extra, name, default)

    def set(self, name: str, value: Any) -> Self:
        setattr(self.extra, name, value)
        return self

    def update(self, **kwargs: Any) -> Self:
        for key, value in kwargs.items():
            if key == "path":
                self.path = value
            else:
                setattr(self.extra, key, value)
        return self

    def exists(self) -> bool:
        return bool(self.path.exists() if self.path is not None else False)


@dataclass(slots=True)
class ValidationResult[T: Artifact]:
    obj: Artifact
    msg: str = ""
    success: bool = True
    details: list[str] = field(default_factory=list)
    exception: Exception | None = field(default=None)

    @classmethod
    def with_path(cls, path: Path, **kwargs) -> Self:
        return cls(obj=Artifact(path=path), **kwargs)

    def __bool__(self) -> bool:
        return self.success

    @property
    def path(self) -> Path:
        return self.obj.path

    def exists(self) -> bool:
        return bool(self.path.exists() if self.path is not None else False)

    def read_text(self) -> str:
        return self.path.read_text() if self.path is not None else ""

    def succeeded(
        self,
        msg: str,
        details: list[str] = EMPTY_IMMUTABLE_LIST,
        exception: Exception | None = None,
    ) -> Self:
        self.success = True
        self.msg = msg
        if details:
            self.details = details
        if exception:
            self.exception = exception
        return self

    def failed(
        self,
        msg: str,
        details: list[str] = EMPTY_IMMUTABLE_LIST,
        exception: Exception | None = None,
    ) -> Self:
        self.success = False
        self.msg = msg
        if details:
            self.details = details
        if exception:
            self.exception = exception
        return self


@dataclass
class ValidationReport:
    """Collection of validation results."""

    name: str = ""
    results: list[ValidationResult[Artifact]] = field(default_factory=list)

    def add(self, result: ValidationResult[Artifact]) -> None:
        """Add a result to the list of results."""
        self.results.append(result)

    @property
    def all_passed(self) -> bool:
        """Check if all validations passed."""
        return all(result.success for result in self.results)

    @cached_property
    def passed_jobs(self) -> list[Path]:
        """Paths of passed validations."""
        return [r.obj.path for r in self.results if r.success and r.obj.path is not None]

    @cached_property
    def failed_jobs(self) -> list[ValidationResult[Artifact]]:
        """Failed validation results."""
        return [r for r in self.results if not r.success]

    @property
    def count(self) -> int:
        """Total number of validation results."""
        return len(self.results)

    @property
    def failure_count(self) -> int:
        """Total number of failed validation results."""
        return len(self.failed_jobs)

    @property
    def fail_percent(self) -> float:
        """Percentage of failed validation results."""
        if self.count == 0:
            return 0.0
        return (self.failure_count / self.count) * 100.0

    def __str__(self) -> str:
        """Generate a single-line summary report."""
        twenty_five = 25
        fail_count: int = self.failure_count
        color = "red" if fail_count > twenty_five else "yellow" if fail_count > 0 else "green"
        fail_percent_colored: str = f"[{color}]{self.fail_percent:.2f}%[/{color}]"
        return f"{self.name.title()} Jobs: [green]{self.count} total[/], [red]{fail_count}[/] failed ({fail_percent_colored})"


EMPTY_REPORT = ValidationReport()
