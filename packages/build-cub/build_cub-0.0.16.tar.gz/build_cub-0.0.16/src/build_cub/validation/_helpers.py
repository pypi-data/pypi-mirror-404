from __future__ import annotations

import ast
from contextlib import suppress
from typing import TYPE_CHECKING

from ._models import ValidationResult

if TYPE_CHECKING:
    from pathlib import Path


def syntax_error_result(e: SyntaxError, path: Path) -> ValidationResult:
    """Create ValidationResult from a SyntaxError."""
    return ValidationResult.with_path(
        path=path,
        success=False,
        msg="Python syntax error in generated file",
        details=[
            f"Line {e.lineno}: {e.msg}",
            f"Text: {e.text.strip() if e.text else 'N/A'}",
            "Hint: This usually means a template variable didn't render correctly",
        ],
        exception=e,
    )


def extract_assignments(tree: ast.Module) -> dict[str, object]:
    """Extract top-level assignments from AST as name->value dict."""
    namespace: dict[str, object] = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if not isinstance(target, ast.Name):
                continue
            with suppress(ValueError, TypeError):
                namespace[target.id] = ast.literal_eval(node.value)
    return namespace
