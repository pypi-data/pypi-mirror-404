"""Models for [versioning] section in bear_build.toml.

Supports flexible template rendering with user-defined variables.
All variables are passed to all templates, allowing maximum flexibility.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from jinja2 import Template
from pydantic import BaseModel, Field, field_validator

from build_cub.utils import global_config

if TYPE_CHECKING:
    from build_cub.validation._models import ValidationResult


class TemplateValidation(BaseModel):
    """Validation configuration for a template.

    Example TOML:
        validation = { type = "python", expression = "len(__version_tuple__) == 3" }
    """

    type: str = Field(default="python", description="Validation type: 'python' for now")
    expression: str = Field(
        default="", description="Python expression to evaluate against the generated file's namespace"
    )


class TemplateDefinition(BaseModel):
    """A single template definition with output path and content.

    Used in [[versioning.templates]] array of tables.
    """

    name: str = Field(default="", description="Optional name for the template")
    output: Path = Field(description="Output file path for the rendered template")
    content: str = Field(default="", description="Jinja2 template content")
    validation: TemplateValidation | None = Field(default=None, description="Optional validation config")

    @field_validator("output", mode="before")
    @classmethod
    def validate_output_path(cls, value: Path) -> Path:
        return Path(value)

    def render(self, variables: dict[str, Any]) -> str:
        """Render this template with the provided variables."""
        return Template(self.content).render(**variables)

    def write(self, variables: dict[str, Any]) -> ValidationResult:
        """Render and write template to output path.

        Args:
            variables: Variables to use for rendering.

        Returns:
            TemplateValidator result after writing the file.
        """
        from build_cub.validation._templates import TemplateValidator

        project_root: Path = global_config.paths.cwd.resolve()
        output_path: Path = Path(self.output).resolve()
        if not str(output_path).startswith(str(project_root)):  # Trying to add safeguard
            raise ValueError(f"Template output path {output_path} is outside the project root {project_root}")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(self.render(variables))
        return TemplateValidator(self).validate()


class VersioningSettings(BaseModel):
    """Maps to [versioning] section.

    Supports flexible template system:
    - variables: User-defined dicts passed to all templates (version is auto-injected)
    - templates: List of TemplateDefinition with output path and content

    Example TOML:
        [versioning.variables]
        database = { major = 2, minor = 0, patch = 0 }

        [[versioning.templates]]
        output = "src/pkg/_version.py"
        content = '''
        __version__ = "{{ version.major }}.{{ version.minor }}.{{ version.patch }}"
        __db_version__ = "{{ database.major }}.{{ database.minor }}"
        '''
    """

    variables: dict[str, Any] = Field(default_factory=dict)  # User-defined variables - all get passed to all templates
    templates: list[TemplateDefinition] = Field(default_factory=list)

    @property
    def has_templates(self) -> bool:
        """Check if any templates are defined."""
        return bool(self.templates)


__all__ = ["TemplateDefinition", "TemplateValidation", "VersioningSettings"]
