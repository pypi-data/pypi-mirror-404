"""Build output validation utilities.

Provides verification that templates rendered correctly and build outputs exist.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from lazy_bear import lazy

from ._base import BaseValidator
from ._constants import EMPTY_PATTERNS, SAFE_BUILTINS
from ._helpers import extract_assignments, syntax_error_result
from ._models import ValidationResult as Result

if TYPE_CHECKING:
    import ast
    from pathlib import Path

    from build_cub.models._templates import TemplateDefinition, VersioningSettings

    from ._models import ValidationReport
else:
    ast = lazy("ast")
    Path = lazy("pathlib", "Path")
    TemplateDefinition = lazy("build_cub.models._templates", "TemplateDefinition")


def _check_output_path(artifact: TemplateDefinition) -> Result:
    """Check that the output path exists."""
    if not artifact.output.exists():
        return Result.with_path(path=artifact.output).failed(msg="Template output file not found")
    return Result.with_path(path=artifact.output).succeeded(msg="Template output file exists")


def default_checks(artifact: TemplateDefinition) -> Result:
    """Basic built-in checks for templates."""
    output_path: Path = artifact.output
    content: str = output_path.read_text()
    issues: list[str] = [f"Found malformed pattern: {p.pattern!r}" for p in EMPTY_PATTERNS if p.search(content)]
    result: Result = Result.with_path(path=output_path)
    msg: str = ""
    if issues:
        msg = f"Template '{artifact.name or 'unknown'}' appears to have empty or malformed values"
        details: list[str] = [*issues, "Hint: Check that your variable names match those in [versioning.variables]"]
        return result.failed(msg, details=details)
    if output_path.suffix == ".py":
        try:
            ast.parse(content)
        except SyntaxError as e:
            return syntax_error_result(e, output_path)
    return result.succeeded(msg=f"Template '{artifact.name or output_path.name}' validated successfully")


def check_python_expression(artifact: TemplateDefinition) -> Result:
    """Validate using AST parsing and safe eval of user expression."""
    job: Result = Result.with_path(path=artifact.output)
    content: str = artifact.output.read_text()
    output_path: Path = artifact.output
    if artifact.validation is None:
        return job.failed(msg="No validation configuration provided")
    expr: str = artifact.validation.expression
    try:
        tree: ast.Module = ast.parse(content)
    except SyntaxError as e:
        return syntax_error_result(e, output_path)
    namespace: dict[str, object] = extract_assignments(tree)
    msg: str = ""
    try:
        result: Any = eval(expr, {"__builtins__": SAFE_BUILTINS}, namespace)  # noqa: S307
    except NameError as e:
        msg = f"Validation expression references undefined variable: {e!s}"
        details: list[str] = [f"Expression: {expr}", f"Available variables: {', '.join(namespace.keys())}"]
        return job.failed(msg=msg, details=details, exception=e)
    except Exception as e:
        msg = f"Error evaluating validation expression: {e!s}"
        return job.failed(msg=msg, details=[f"Expression: {expr}"], exception=e)

    if result:
        msg = f"Template '{artifact.name or output_path.name}' passed validation"
        return job.succeeded(msg=msg, details=[f"Expression '{expr}' evaluated to True"])

    msg = f"Template '{artifact.name or output_path.name}' failed validation"
    details = [
        f"Expression '{expr}' evaluated to False",
        f"Namespace values: {namespace}",
        "Hint: Check that your template variables are rendering correctly",
    ]
    return job.failed(msg=msg, details=details)


class TemplateValidator(BaseValidator[TemplateDefinition]):
    """Validates rendered template output."""

    def __init__(self, template: TemplateDefinition) -> None:
        """Create the validator."""
        super().__init__(template, template.output)
        self.register_test(_check_output_path)
        if self.artifact.validation is not None and self.artifact.validation.expression:
            self.register_test(check_python_expression)
        else:
            self.register_test(default_checks)


def validate_templates(template_struct: VersioningSettings) -> ValidationReport:
    """Validate multiple rendered templates."""
    from ._models import ValidationReport

    report = ValidationReport()
    for template in template_struct.templates:
        report.add(TemplateValidator(template).validate())
    return report


__all__ = ["TemplateValidator", "validate_templates"]
