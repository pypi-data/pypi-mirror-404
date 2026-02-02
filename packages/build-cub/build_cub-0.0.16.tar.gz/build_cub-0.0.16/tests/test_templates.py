"""Tests for flexible template rendering system."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from build_cub.models._build_data import BuildData


class TestTemplateVariables:
    """Tests for template_variables property structure."""

    def test_template_variables_has_version(self, test_build_data: BuildData) -> None:
        """Test template_variables always contains version dict (auto-injected)."""
        variables: dict[str, Any] = test_build_data.template_variables
        assert "version" in variables
        assert "major" in variables["version"]
        assert "minor" in variables["version"]
        assert "patch" in variables["version"]

    def test_template_variables_has_user_defined(self, test_build_data: BuildData) -> None:
        """Test template_variables contains user-defined variables from [versioning.variables]."""
        variables: dict[str, Any] = test_build_data.template_variables
        # From fixture: united_data and schema are user-defined
        assert "united_data" in variables
        assert variables["united_data"]["major"] == 2
        assert variables["united_data"]["minor"] == 1

        assert "schema" in variables
        assert variables["schema"]["major"] == 1
        assert variables["schema"]["patch"] == 3


class TestTemplateDefinitions:
    """Tests for template definitions list."""

    def test_has_templates_flag(self, test_build_data: BuildData) -> None:
        """Test has_templates returns True when templates are defined."""
        assert test_build_data.versioning.has_templates is True

    def test_template_count(self, test_build_data: BuildData) -> None:
        """Test correct number of templates loaded."""
        # Fixture has 2 templates: Python and C++
        assert len(test_build_data.versioning.templates) == 2

    def test_template_outputs(self, test_build_data: BuildData) -> None:
        """Test template output paths are correct."""
        outputs = [str(t.output) for t in test_build_data.versioning.templates]
        assert "src/test_project/_version.py" in outputs
        assert "src/test_project/_cpp/_version.hpp" in outputs


class TestTemplateRendering:
    """Tests for template rendering."""

    def test_python_template_renders(self, test_build_data: BuildData) -> None:
        """Test Python template renders with expected variables."""
        python_template = test_build_data.versioning.templates[0]
        rendered: str = python_template.render(test_build_data.template_variables)
        assert "__version__" in rendered
        assert "__united_data_version__" in rendered
        assert "__schema_version__" in rendered

    def test_python_template_interpolates_values(self, test_build_data: BuildData) -> None:
        """Test template actually interpolates version numbers."""
        python_template = test_build_data.versioning.templates[0]
        rendered: str = python_template.render(test_build_data.template_variables)
        # united_data is 2.1.0 in fixture
        assert '"2.1.0"' in rendered
        # schema is 1.5.3 in fixture
        assert '"1.5.3"' in rendered

    def test_cpp_template_renders(self, test_build_data: BuildData) -> None:
        """Test C++ template renders with expected content."""
        cpp_template = test_build_data.versioning.templates[1]
        rendered: str = cpp_template.render(test_build_data.template_variables)
        assert "namespace test_project" in rendered
        assert "UNITED_DATA_VERSION" in rendered
        assert "SCHEMA_VERSION" in rendered


class TestNoTemplates:
    """Tests for when no templates are configured."""

    def test_has_templates_false_when_empty(self) -> None:
        """Test has_templates returns False when no templates defined."""
        from build_cub.models._build_data import BuildData

        data: dict[str, Any] = {
            "general": {"name": "test"},
        }
        build_data: BuildData = BuildData.model_validate(data)
        assert build_data.versioning.has_templates is False

    def test_render_templates_returns_empty_report(self) -> None:
        """Test render_templates returns empty report when no templates."""
        from build_cub.models._build_data import BuildData
        from build_cub.validation._models import EMPTY_REPORT

        data: dict[str, Any] = {
            "general": {"name": "test"},
        }
        build_data: BuildData = BuildData.model_validate(data)
        assert build_data.render_templates() is EMPTY_REPORT


class TestFlexibleVariables:
    """Tests for user-defined variable flexibility."""

    def test_arbitrary_variables_work(self) -> None:
        """Test that users can define any variables they want."""
        from build_cub.models._build_data import BuildData

        data: dict[str, Any] = {
            "general": {"name": "test"},
            "versioning": {
                "variables": {
                    "my_custom_var": {"foo": "bar", "count": 42},
                    "another": {"x": 1, "y": 2},
                },
                "templates": [
                    {"output": "test.txt", "content": "{{ my_custom_var.foo }} - {{ another.x }}"},
                ],
            },
        }
        build_data: BuildData = BuildData.model_validate(data)

        variables = build_data.template_variables
        assert "my_custom_var" in variables
        assert variables["my_custom_var"]["foo"] == "bar"
        assert variables["another"]["x"] == 1

        # Version is always injected
        assert "version" in variables
