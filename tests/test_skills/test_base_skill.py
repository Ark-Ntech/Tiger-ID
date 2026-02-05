"""Tests for BaseSkill abstract base class."""

import pytest
from typing import Any, Dict
from unittest.mock import patch

from backend.skills.base_skill import (
    BaseSkill,
    SkillDefinition,
    SkillParameter,
    SkillCategory
)


class ConcreteSkill(BaseSkill):
    """Concrete implementation for testing."""

    def get_definition(self) -> SkillDefinition:
        return SkillDefinition(
            name="Test Skill",
            description="A test skill for unit testing",
            command="/test-skill",
            category=SkillCategory.ANALYSIS,
            parameters=[
                SkillParameter(
                    name="required_param",
                    description="A required parameter",
                    type="string",
                    required=True
                ),
                SkillParameter(
                    name="optional_param",
                    description="An optional parameter",
                    type="string",
                    required=False,
                    default="default_value"
                ),
                SkillParameter(
                    name="enum_param",
                    description="A parameter with enum values",
                    type="string",
                    required=False,
                    enum=["option_a", "option_b", "option_c"]
                )
            ],
            examples=[
                "/test-skill (with context)",
                "/test-skill --verbose"
            ]
        )

    def get_prompt_template(self) -> str:
        return """Test prompt template.

Required: {required_param}
Optional: {optional_param}
"""

    async def execute(self, context: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        errors = self.validate_context(context)
        if errors:
            return {"success": False, "error": "; ".join(errors), "output": None}

        prompt = self.build_prompt(context)
        return {
            "success": True,
            "output": f"Executed with prompt: {prompt}",
            "metadata": {"test": True}
        }


@pytest.fixture
def skill():
    """Create a concrete skill for testing."""
    with patch('backend.skills.base_skill.get_logger'):
        return ConcreteSkill()


class TestSkillCategory:
    """Tests for SkillCategory enum."""

    def test_analysis_category(self):
        """Test ANALYSIS category."""
        assert SkillCategory.ANALYSIS.value == "analysis"

    def test_research_category(self):
        """Test RESEARCH category."""
        assert SkillCategory.RESEARCH.value == "research"

    def test_reporting_category(self):
        """Test REPORTING category."""
        assert SkillCategory.REPORTING.value == "reporting"

    def test_reasoning_category(self):
        """Test REASONING category."""
        assert SkillCategory.REASONING.value == "reasoning"

    def test_quality_category(self):
        """Test QUALITY category."""
        assert SkillCategory.QUALITY.value == "quality"


class TestSkillParameter:
    """Tests for SkillParameter dataclass."""

    def test_required_parameter(self):
        """Test creating a required parameter."""
        param = SkillParameter(
            name="test",
            description="Test parameter",
            type="string",
            required=True
        )

        assert param.name == "test"
        assert param.description == "Test parameter"
        assert param.type == "string"
        assert param.required is True
        assert param.default is None
        assert param.enum is None

    def test_optional_parameter_with_default(self):
        """Test creating an optional parameter with default."""
        param = SkillParameter(
            name="test",
            description="Test parameter",
            type="number",
            required=False,
            default=42
        )

        assert param.required is False
        assert param.default == 42

    def test_parameter_with_enum(self):
        """Test creating a parameter with enum values."""
        param = SkillParameter(
            name="test",
            description="Test parameter",
            type="string",
            required=True,
            enum=["a", "b", "c"]
        )

        assert param.enum == ["a", "b", "c"]


class TestSkillDefinition:
    """Tests for SkillDefinition dataclass."""

    def test_create_definition(self):
        """Test creating a skill definition."""
        definition = SkillDefinition(
            name="Test Skill",
            description="A test skill",
            command="/test",
            category=SkillCategory.ANALYSIS
        )

        assert definition.name == "Test Skill"
        assert definition.description == "A test skill"
        assert definition.command == "/test"
        assert definition.category == SkillCategory.ANALYSIS
        assert definition.parameters == []
        assert definition.examples == []

    def test_definition_with_parameters(self):
        """Test definition with parameters."""
        params = [
            SkillParameter(name="p1", description="d1", type="string", required=True),
            SkillParameter(name="p2", description="d2", type="number", required=False),
        ]
        definition = SkillDefinition(
            name="Test",
            description="Test",
            command="/test",
            category=SkillCategory.RESEARCH,
            parameters=params
        )

        assert len(definition.parameters) == 2

    def test_definition_with_examples(self):
        """Test definition with examples."""
        definition = SkillDefinition(
            name="Test",
            description="Test",
            command="/test",
            category=SkillCategory.REPORTING,
            examples=["example 1", "example 2"]
        )

        assert definition.examples == ["example 1", "example 2"]


class TestBaseSkillProperties:
    """Tests for BaseSkill properties."""

    def test_name_property(self, skill):
        """Test name property."""
        assert skill.name == "Test Skill"

    def test_command_property(self, skill):
        """Test command property."""
        assert skill.command == "/test-skill"

    def test_category_property(self, skill):
        """Test category property."""
        assert skill.category == SkillCategory.ANALYSIS

    def test_description_property(self, skill):
        """Test description property."""
        assert skill.description == "A test skill for unit testing"


class TestBuildPrompt:
    """Tests for build_prompt method."""

    def test_build_prompt_success(self, skill):
        """Test successful prompt building."""
        context = {
            "required_param": "value1",
            "optional_param": "value2"
        }

        prompt = skill.build_prompt(context)

        assert "value1" in prompt
        assert "value2" in prompt

    def test_build_prompt_missing_key(self, skill):
        """Test prompt building with missing key raises error."""
        context = {"required_param": "value1"}  # missing optional_param

        with pytest.raises(ValueError, match="Missing required context key"):
            skill.build_prompt(context)

    def test_build_prompt_extra_keys_ignored(self, skill):
        """Test that extra context keys are ignored."""
        context = {
            "required_param": "value1",
            "optional_param": "value2",
            "extra_key": "ignored"
        }

        prompt = skill.build_prompt(context)

        assert "ignored" not in prompt


class TestValidateContext:
    """Tests for validate_context method."""

    def test_validate_context_success(self, skill):
        """Test validation with all required params."""
        context = {"required_param": "value"}

        errors = skill.validate_context(context)

        assert errors == []

    def test_validate_context_missing_required(self, skill):
        """Test validation with missing required param."""
        context = {}

        errors = skill.validate_context(context)

        assert len(errors) == 1
        assert "Missing required parameter: required_param" in errors

    def test_validate_context_invalid_enum(self, skill):
        """Test validation with invalid enum value."""
        context = {
            "required_param": "value",
            "enum_param": "invalid_option"
        }

        errors = skill.validate_context(context)

        assert len(errors) == 1
        assert "Invalid value for enum_param" in errors[0]

    def test_validate_context_valid_enum(self, skill):
        """Test validation with valid enum value."""
        context = {
            "required_param": "value",
            "enum_param": "option_a"
        }

        errors = skill.validate_context(context)

        assert errors == []


class TestExecute:
    """Tests for execute method."""

    @pytest.mark.asyncio
    async def test_execute_success(self, skill):
        """Test successful execution."""
        context = {
            "required_param": "test_value",
            "optional_param": "opt_value"
        }

        result = await skill.execute(context)

        assert result["success"] is True
        assert "test_value" in result["output"]
        assert result["metadata"]["test"] is True

    @pytest.mark.asyncio
    async def test_execute_validation_failure(self, skill):
        """Test execution with validation failure."""
        context = {}  # Missing required param

        result = await skill.execute(context)

        assert result["success"] is False
        assert "Missing required parameter" in result["error"]
        assert result["output"] is None


class TestToDict:
    """Tests for to_dict method."""

    def test_to_dict(self, skill):
        """Test converting skill to dictionary."""
        result = skill.to_dict()

        assert result["name"] == "Test Skill"
        assert result["description"] == "A test skill for unit testing"
        assert result["command"] == "/test-skill"
        assert result["category"] == "analysis"
        assert len(result["parameters"]) == 3
        assert result["examples"] == [
            "/test-skill (with context)",
            "/test-skill --verbose"
        ]

    def test_to_dict_parameters(self, skill):
        """Test parameter serialization in to_dict."""
        result = skill.to_dict()

        required_param = next(
            p for p in result["parameters"]
            if p["name"] == "required_param"
        )

        assert required_param["description"] == "A required parameter"
        assert required_param["type"] == "string"
        assert required_param["required"] is True
        assert required_param["default"] is None
        assert required_param["enum"] is None

    def test_to_dict_enum_parameter(self, skill):
        """Test enum parameter serialization."""
        result = skill.to_dict()

        enum_param = next(
            p for p in result["parameters"]
            if p["name"] == "enum_param"
        )

        assert enum_param["enum"] == ["option_a", "option_b", "option_c"]
