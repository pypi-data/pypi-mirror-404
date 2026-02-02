from __future__ import annotations

from typing import TYPE_CHECKING

from lazy_bear import lazy

from ._base import BaseValidator

if TYPE_CHECKING:
    from ._models import Artifact, ValidationReport, ValidationResult
else:
    Artifact = lazy("build_cub.validation._models", "Artifact")


def _validate_existence(artifact: Artifact) -> ValidationResult:
    from ._models import ValidationResult

    name: str = artifact.get("name", "Unknown")
    if not artifact.path.exists():
        return ValidationResult(obj=artifact).failed(msg=f"{name} not found")
    return ValidationResult(obj=artifact).succeeded(msg=name)


class ArtifactValidator(BaseValidator[Artifact]):
    def __init__(self, artifact: Artifact) -> None:
        super().__init__(artifact, artifact.path)
        self.register_test(_validate_existence)


def validate_artifacts(name: str, copied: list[Artifact]) -> ValidationReport:
    """Validate that all expected artifacts were produced.

    Args:
        name: The name of the job
        copied: List of artifact paths that were copied

    Returns:
        ValidationReport with results for each artifact
    """
    from ._models import ValidationReport

    report: ValidationReport = ValidationReport(name=name)
    for dest in copied:
        report.add(ArtifactValidator(dest).validate())
    return report
