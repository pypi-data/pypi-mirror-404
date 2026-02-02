"""Tests for build output validation."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from build_cub.validation._models import ValidationReport, ValidationResult


class TestTemplateValidator:
    """Tests for TemplateValidator class."""

    def test_validates_good_python_file(self, tmp_path: Path) -> None:
        """Test validation passes for well-formed Python output."""
        from build_cub.models._templates import TemplateDefinition
        from build_cub.validation._templates import TemplateValidator

        output_file = tmp_path / "_version.py"
        output_file.write_text('__version__ = "1.2.3"\n__version_tuple__ = (1, 2, 3)\n')

        template = TemplateDefinition(name="test", output=output_file, content="")
        validator = TemplateValidator(template)
        result = validator.validate()

        assert result.success is True

    def test_catches_empty_string_value(self, tmp_path: Path) -> None:
        """Test validation catches empty string assignments."""
        from build_cub.models._templates import TemplateDefinition
        from build_cub.validation._templates import TemplateValidator

        output_file = tmp_path / "_version.py"
        output_file.write_text('__version__ = ""\n')

        template = TemplateDefinition(name="test", output=output_file, content="")
        validator = TemplateValidator(template)
        result: ValidationResult = validator.validate()

        assert result.success is False
        assert "empty or malformed" in result.msg

    def test_catches_broken_tuple(self, tmp_path: Path) -> None:
        """Test validation catches malformed tuple like (,,)."""
        from build_cub.models._templates import TemplateDefinition
        from build_cub.validation._templates import TemplateValidator

        output_file = tmp_path / "_version.py"
        output_file.write_text("__version_tuple__ = (,,)\n")

        template = TemplateDefinition(name="test", output=output_file, content="")
        validator = TemplateValidator(template)
        result = validator.validate()

        assert result.success is False

    def test_catches_python_syntax_error(self, tmp_path: Path) -> None:
        """Test validation catches Python syntax errors."""
        from build_cub.models._templates import TemplateDefinition
        from build_cub.validation._templates import TemplateValidator

        output_file = tmp_path / "_version.py"
        output_file.write_text("__version__ = \n")  # Invalid syntax

        template = TemplateDefinition(name="test", output=output_file, content="")
        validator = TemplateValidator(template)
        result = validator.validate()

        assert result.success is False
        assert "syntax error" in result.msg.lower()

    def test_catches_unrendered_jinja(self, tmp_path: Path) -> None:
        """Test validation catches unrendered Jinja2 variables."""
        from build_cub.models._templates import TemplateDefinition
        from build_cub.validation._templates import TemplateValidator

        output_file = tmp_path / "_version.py"
        output_file.write_text('__version__ = "{{ version.major }}.{{ version.minor }}"\n')

        template = TemplateDefinition(name="test", output=output_file, content="")
        validator = TemplateValidator(template)
        result = validator.validate()

        assert result.success is False
        assert "empty or malformed" in result.msg

    def test_missing_file_fails(self, tmp_path: Path) -> None:
        """Test validation fails when output file doesn't exist."""
        from build_cub.models._templates import TemplateDefinition
        from build_cub.validation._templates import TemplateValidator

        output_file: Path = tmp_path / "nonexistent.py"

        template = TemplateDefinition(name="test", output=output_file, content="")
        validator = TemplateValidator(template)
        result: ValidationResult = validator.validate()

        assert result.success is False
        assert "not found" in result.msg

    def test_provides_helpful_hints(self, tmp_path: Path) -> None:
        """Test validation results include helpful hints."""
        from build_cub.models._templates import TemplateDefinition
        from build_cub.validation._templates import TemplateValidator

        output_file: Path = tmp_path / "_version.py"
        output_file.write_text('__version__ = ""\n')

        template = TemplateDefinition(name="python_version", output=output_file, content="")
        validator = TemplateValidator(template)
        result: ValidationResult = validator.validate()

        assert result.details
        assert any("Hint" in detail for detail in result.details)


class TestValidationReport:
    """Tests for ValidationReport aggregation."""

    def test_all_passed_when_all_succeed(self, tmp_path: Path) -> None:
        """Test all_passed is True when all validations succeed."""
        from build_cub.models._templates import TemplateDefinition, VersioningSettings
        from build_cub.validation._templates import validate_templates

        file1: Path = tmp_path / "a.py"
        file2: Path = tmp_path / "b.py"
        file1.write_text("x = 1\n")
        file2.write_text("y = 2\n")
        temps = VersioningSettings()
        temps.templates.append(TemplateDefinition(name="a", output=file1, content=""))
        temps.templates.append(TemplateDefinition(name="b", output=file2, content=""))

        report: ValidationReport = validate_templates(temps)
        assert report.all_passed is True
        assert len(report.failed_jobs) == 0

    def test_failures_collected(self, tmp_path: Path) -> None:
        """Test failures are collected in report."""
        from build_cub.models._templates import TemplateDefinition, VersioningSettings
        from build_cub.validation._templates import validate_templates

        good_file: Path = tmp_path / "good.py"
        bad_file: Path = tmp_path / "bad.py"
        good_file.write_text("x = 1\n")
        bad_file.write_text('x = ""\n')

        temps = VersioningSettings()
        temps.templates.append(TemplateDefinition(name="good", output=good_file, content=""))
        temps.templates.append(TemplateDefinition(name="bad", output=bad_file, content=""))

        report = validate_templates(temps)
        assert report.all_passed is False
        assert len(report.failed_jobs) == 1
        assert report.failed_jobs[0].path == bad_file


class TestPythonExpressionValidation:
    """Tests for Python expression-based validation."""

    def test_expression_validation_passes(self, tmp_path: Path) -> None:
        """Test validation passes when expression evaluates to True."""
        from build_cub.models._templates import TemplateDefinition, TemplateValidation
        from build_cub.validation._templates import TemplateValidator

        output_file = tmp_path / "_version.py"
        output_file.write_text('__version__ = "1.2.3"\n__version_tuple__ = (1, 2, 3)\n')

        template = TemplateDefinition(
            name="test",
            output=output_file,
            content="",
            validation=TemplateValidation(type="python", expression="len(__version_tuple__) == 3"),
        )
        validator = TemplateValidator(template)
        result = validator.validate()

        assert result.success is True
        assert "Passed all validation tests" in result.msg

    def test_expression_validation_fails(self, tmp_path: Path) -> None:
        """Test validation fails when expression evaluates to False."""
        from build_cub.models._templates import TemplateDefinition, TemplateValidation
        from build_cub.validation._templates import TemplateValidator

        output_file = tmp_path / "_version.py"
        output_file.write_text('__version__ = "1.2.3"\n__version_tuple__ = (1, 2)\n')  # Only 2 elements

        template = TemplateDefinition(
            name="test",
            output=output_file,
            content="",
            validation=TemplateValidation(type="python", expression="len(__version_tuple__) == 3"),
        )
        validator = TemplateValidator(template)
        result = validator.validate()

        assert result.success is False
        assert "failed validation" in result.msg
        assert "evaluated to False" in result.details[0]

    def test_expression_catches_empty_version(self, tmp_path: Path) -> None:
        """Test expression can catch empty string values."""
        from build_cub.models._templates import TemplateDefinition, TemplateValidation
        from build_cub.validation._templates import TemplateValidator

        output_file = tmp_path / "_version.py"
        output_file.write_text('__version__ = ""\n')

        template = TemplateDefinition(
            name="test",
            output=output_file,
            content="",
            validation=TemplateValidation(type="python", expression="__version__ != ''"),
        )
        validator = TemplateValidator(template)
        result = validator.validate()

        assert result.success is False

    def test_expression_with_multiple_conditions(self, tmp_path: Path) -> None:
        """Test complex validation expressions with multiple conditions."""
        from build_cub.models._templates import TemplateDefinition, TemplateValidation
        from build_cub.validation._templates import TemplateValidator

        output_file = tmp_path / "_version.py"
        output_file.write_text('__version__ = "1.2.3"\n__version_tuple__ = (1, 2, 3)\n')

        template = TemplateDefinition(
            name="test",
            output=output_file,
            content="",
            validation=TemplateValidation(
                type="python",
                expression="len(__version_tuple__) == 3 and __version__ != '' and isinstance(__version__, str)",
            ),
        )
        validator = TemplateValidator(template)
        result = validator.validate()

        assert result.success is True

    def test_expression_catches_syntax_error(self, tmp_path: Path) -> None:
        """Test expression validation catches syntax errors in generated file."""
        from build_cub.models._templates import TemplateDefinition, TemplateValidation
        from build_cub.validation._templates import TemplateValidator

        output_file = tmp_path / "_version.py"
        output_file.write_text("__version__ = \n")  # Syntax error

        template = TemplateDefinition(
            name="test",
            output=output_file,
            content="",
            validation=TemplateValidation(type="python", expression="len(__version__) > 0"),
        )
        validator = TemplateValidator(template)
        result = validator.validate()

        assert result.success is False
        assert "syntax error" in result.msg.lower()

    def test_expression_catches_undefined_variable(self, tmp_path: Path) -> None:
        """Test expression validation catches references to undefined variables."""
        from build_cub.models._templates import TemplateDefinition, TemplateValidation
        from build_cub.validation._templates import TemplateValidator

        output_file = tmp_path / "_version.py"
        output_file.write_text('__version__ = "1.2.3"\n')

        template = TemplateDefinition(
            name="test",
            output=output_file,
            content="",
            validation=TemplateValidation(type="python", expression="len(__nonexistent__) > 0"),
        )
        validator = TemplateValidator(template)
        result = validator.validate()

        assert result.success is False
        assert "undefined variable" in result.msg.lower()

    def test_expression_cannot_access_os_or_imports(self, tmp_path: Path) -> None:
        """Test that expression validation is sandboxed - no access to dangerous builtins."""
        from build_cub.models._templates import TemplateDefinition, TemplateValidation
        from build_cub.validation._templates import TemplateValidator

        output_file = tmp_path / "_version.py"
        output_file.write_text('__version__ = "1.2.3"\n')

        # Try to use __import__ which should not be available
        template = TemplateDefinition(
            name="test",
            output=output_file,
            content="",
            validation=TemplateValidation(type="python", expression="__import__('os').system('echo pwned')"),
        )
        validator = TemplateValidator(template)
        result = validator.validate()

        # Should fail because __import__ is not in SAFE_BUILTINS
        assert result.success is False


class TestArtifactValidation:
    """Tests for artifact validation with upfront expected artifacts."""

    def test_all_artifacts_found(self, tmp_path: Path) -> None:
        """When all expected artifacts exist on disk, all pass."""
        from build_cub.validation._backends import validate_artifacts
        from build_cub.validation._models import Artifact

        art_a = tmp_path / "core.cpython-314-darwin.so"
        art_b = tmp_path / "record.cpython-314-darwin.so"
        art_a.write_bytes(b"fake")
        art_b.write_bytes(b"fake")

        artifacts = [
            Artifact(path=art_a).update(name="core"),
            Artifact(path=art_b).update(name="record"),
        ]

        report = validate_artifacts("test", artifacts)

        assert report.count == 2
        assert report.failure_count == 0
        assert report.all_passed is True

    def test_missing_artifacts_reported_as_failed(self, tmp_path: Path) -> None:
        """Artifacts with sentinel paths (non-existent) are reported as failed."""
        from build_cub.validation._backends import validate_artifacts
        from build_cub.validation._models import Artifact

        real_file = tmp_path / "core.cpython-314-darwin.so"
        real_file.write_bytes(b"fake")

        artifacts = [
            Artifact(path=real_file).update(name="core"),
            Artifact(path=Path("record")).update(name="record"),  # sentinel - never compiled
            Artifact(path=Path("utils")).update(name="utils"),  # sentinel - never compiled
        ]

        report = validate_artifacts("test", artifacts)

        assert report.count == 3
        assert report.failure_count == 2
        assert report.all_passed is False
        failed_names = {r.obj.get("name", "") for r in report.failed_jobs}
        assert "record" in failed_names
        assert "utils" in failed_names

    def test_all_artifacts_missing(self) -> None:
        """When no artifacts were compiled, all are reported as failed."""
        from build_cub.validation._backends import validate_artifacts
        from build_cub.validation._models import Artifact

        artifacts = [
            Artifact(path=Path("core")).update(name="core"),
            Artifact(path=Path("record")).update(name="record"),
        ]

        report = validate_artifacts("test", artifacts)

        assert report.count == 2
        assert report.failure_count == 2
        assert report.all_passed is False

    def test_empty_artifacts_list(self) -> None:
        """Empty artifact list produces empty report."""
        from build_cub.validation._backends import validate_artifacts

        report = validate_artifacts("test", [])

        assert report.count == 0
        assert report.failure_count == 0
        assert report.all_passed is True

    def test_sentinel_path_updated_to_real_path(self, tmp_path: Path) -> None:
        """Simulates the full flow: sentinel created, then updated after successful copy."""
        from build_cub.validation._backends import validate_artifacts
        from build_cub.validation._models import Artifact

        expected: dict[str, Artifact] = {
            "core": Artifact(path=Path("core")).update(name="core"),
            "record": Artifact(path=Path("record")).update(name="record"),
        }

        # Simulate successful copy for "core" only
        real_core = tmp_path / "core.cpython-314-darwin.so"
        real_core.write_bytes(b"fake")
        expected["core"].path = real_core

        report = validate_artifacts("test", list(expected.values()))

        assert report.count == 2
        assert report.failure_count == 1
        assert len(report.passed_jobs) == 1
        assert report.passed_jobs[0] == real_core

    def test_report_string_output(self, tmp_path: Path) -> None:
        """Report __str__ shows correct counts."""
        from build_cub.validation._backends import validate_artifacts
        from build_cub.validation._models import Artifact

        real_file = tmp_path / "core.so"
        real_file.write_bytes(b"fake")

        artifacts = [
            Artifact(path=real_file).update(name="core"),
            Artifact(path=Path("missing")).update(name="missing"),
        ]

        report = validate_artifacts("pybind11", artifacts)
        report_str = str(report)

        assert "2 total" in report_str
        assert "1" in report_str  # 1 failed


class TestNonPythonFiles:
    """Tests for non-Python template validation."""

    def test_validates_header_file(self, tmp_path: Path) -> None:
        """Test validation works for C++ header files."""
        from build_cub.models._templates import TemplateDefinition
        from build_cub.validation._templates import TemplateValidator

        output_file = tmp_path / "version.hpp"
        output_file.write_text("#define VERSION_MAJOR 1\n#define VERSION_MINOR 2\n")

        template = TemplateDefinition(name="cpp_version", output=output_file, content="")
        validator = TemplateValidator(template)
        result = validator.validate()

        assert result.success is True

    def test_catches_empty_in_header(self, tmp_path: Path) -> None:
        """Test validation catches empty values in non-Python files."""
        from build_cub.models._templates import TemplateDefinition
        from build_cub.validation._templates import TemplateValidator

        output_file = tmp_path / "version.hpp"
        output_file.write_text('#define VERSION ""\n')

        template = TemplateDefinition(name="cpp_version", output=output_file, content="")
        validator = TemplateValidator(template)
        result = validator.validate()

        assert result.success is False
