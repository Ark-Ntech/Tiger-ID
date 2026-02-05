"""Tests for ReportWriterSkill."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime


@pytest.fixture
def skill():
    """Create a ReportWriterSkill for testing."""
    with patch('backend.skills.report_writer.get_logger'):
        with patch('backend.skills.base_skill.get_logger'):
            from backend.skills.report_writer import ReportWriterSkill
            return ReportWriterSkill()


@pytest.fixture
def mock_chat_model():
    """Create a mock chat model."""
    mock = MagicMock()
    mock.chat = AsyncMock(return_value={
        "success": True,
        "response": "# Investigation Report\n\n## Executive Summary\n\nTiger identified as Raja..."
    })
    return mock


@pytest.fixture
def sample_investigation_data():
    """Sample investigation data for reports."""
    return {
        "identification": {
            "tiger_id": "t123",
            "tiger_name": "Raja",
            "confidence": 0.92,
            "model": "wildlife_tools"
        },
        "model_results": {
            "wildlife_tools": {"top_match": "Raja", "similarity": 0.92},
            "cvwc2019_reid": {"top_match": "Raja", "similarity": 0.88}
        },
        "location": {
            "primary": "Zoo A",
            "source": "EXIF GPS",
            "confidence": 1.0,
            "coordinates": "28.5, 77.2"
        },
        "facility": {
            "name": "Zoo A",
            "location": "City, State",
            "owner": "John Doe",
            "usda_license": "12-A-0123"
        },
        "evidence": [
            {"type": "stripe_match", "summary": "92% similarity match"},
            {"type": "location", "summary": "GPS confirmed at Zoo A"}
        ]
    }


class TestReportAudience:
    """Tests for ReportAudience enum."""

    def test_audience_values(self):
        """Test ReportAudience enum values."""
        from backend.skills.report_writer import ReportAudience

        assert ReportAudience.LAW_ENFORCEMENT.value == "law_enforcement"
        assert ReportAudience.CONSERVATION.value == "conservation"
        assert ReportAudience.INTERNAL.value == "internal"
        assert ReportAudience.PUBLIC.value == "public"

    def test_all_audiences(self):
        """Test all audiences are defined."""
        from backend.skills.report_writer import ReportAudience

        audiences = list(ReportAudience)
        assert len(audiences) == 4


class TestReportFormat:
    """Tests for ReportFormat enum."""

    def test_format_values(self):
        """Test ReportFormat enum values."""
        from backend.skills.report_writer import ReportFormat

        assert ReportFormat.MARKDOWN.value == "markdown"
        assert ReportFormat.JSON.value == "json"
        assert ReportFormat.PDF.value == "pdf"


class TestReportSection:
    """Tests for ReportSection dataclass."""

    def test_create_report_section(self):
        """Test creating a report section."""
        from backend.skills.report_writer import ReportSection

        section = ReportSection(
            name="Executive Summary",
            required=True,
            description="Brief overview of findings"
        )

        assert section.name == "Executive Summary"
        assert section.required is True
        assert "overview" in section.description.lower()


class TestAudienceSections:
    """Tests for AUDIENCE_SECTIONS constant."""

    def test_law_enforcement_sections(self):
        """Test law enforcement report sections."""
        from backend.skills.report_writer import AUDIENCE_SECTIONS, ReportAudience

        sections = AUDIENCE_SECTIONS[ReportAudience.LAW_ENFORCEMENT]

        section_names = [s.name for s in sections]
        assert "Executive Summary" in section_names
        assert "Evidence Chain" in section_names
        assert "Potential Violations" in section_names

    def test_conservation_sections(self):
        """Test conservation report sections."""
        from backend.skills.report_writer import AUDIENCE_SECTIONS, ReportAudience

        sections = AUDIENCE_SECTIONS[ReportAudience.CONSERVATION]

        section_names = [s.name for s in sections]
        assert "Tiger Overview" in section_names
        assert "Welfare Assessment" in section_names or "Current Status" in section_names

    def test_internal_sections(self):
        """Test internal report sections."""
        from backend.skills.report_writer import AUDIENCE_SECTIONS, ReportAudience

        sections = AUDIENCE_SECTIONS[ReportAudience.INTERNAL]

        section_names = [s.name for s in sections]
        assert "Model Performance" in section_names
        assert "Pipeline Details" in section_names

    def test_public_sections(self):
        """Test public report sections."""
        from backend.skills.report_writer import AUDIENCE_SECTIONS, ReportAudience

        sections = AUDIENCE_SECTIONS[ReportAudience.PUBLIC]

        section_names = [s.name for s in sections]
        assert "Summary" in section_names
        assert "Key Findings" in section_names


class TestSkillDefinition:
    """Tests for skill definition."""

    def test_skill_name(self, skill):
        """Test skill name."""
        definition = skill.get_definition()
        assert definition.name == "Expert Report Writer"

    def test_skill_command(self, skill):
        """Test skill command."""
        definition = skill.get_definition()
        assert definition.command == "/generate-report"

    def test_skill_category(self, skill):
        """Test skill category."""
        from backend.skills.base_skill import SkillCategory

        definition = skill.get_definition()
        assert definition.category == SkillCategory.REPORTING

    def test_skill_parameters(self, skill):
        """Test skill parameters."""
        definition = skill.get_definition()

        # Check required parameters
        audience_param = next(p for p in definition.parameters if p.name == "audience")
        assert audience_param.required is True
        assert "law_enforcement" in audience_param.enum

        investigation_data_param = next(p for p in definition.parameters if p.name == "investigation_data")
        assert investigation_data_param.required is True

    def test_skill_has_format_param(self, skill):
        """Test format parameter."""
        definition = skill.get_definition()

        format_param = next(p for p in definition.parameters if p.name == "format")
        assert format_param.required is False
        assert format_param.default == "markdown"
        assert "json" in format_param.enum


class TestPromptTemplate:
    """Tests for prompt template."""

    def test_prompt_template_exists(self, skill):
        """Test prompt template is not empty."""
        template = skill.get_prompt_template()
        assert len(template) > 0

    def test_prompt_template_placeholders(self, skill):
        """Test prompt template has expected placeholders."""
        template = skill.get_prompt_template()

        assert "{audience}" in template
        assert "{investigation_data_formatted}" in template
        assert "{required_sections}" in template
        assert "{audience_guidelines}" in template


class TestGetRequiredSections:
    """Tests for _get_required_sections method."""

    def test_get_law_enforcement_sections(self, skill):
        """Test getting law enforcement sections."""
        from backend.skills.report_writer import ReportAudience

        result = skill._get_required_sections(ReportAudience.LAW_ENFORCEMENT, True)

        assert "Executive Summary" in result
        assert "REQUIRED" in result

    def test_get_sections_without_appendices(self, skill):
        """Test getting sections without appendices."""
        from backend.skills.report_writer import ReportAudience

        result = skill._get_required_sections(ReportAudience.LAW_ENFORCEMENT, False)

        # Appendices should be excluded
        assert "Appendices" not in result

    def test_get_sections_all_audiences(self, skill):
        """Test getting sections for all audiences."""
        from backend.skills.report_writer import ReportAudience

        for audience in ReportAudience:
            result = skill._get_required_sections(audience, True)
            assert len(result) > 0


class TestGetAudienceGuidelines:
    """Tests for _get_audience_guidelines method."""

    def test_law_enforcement_guidelines(self, skill):
        """Test law enforcement guidelines."""
        from backend.skills.report_writer import ReportAudience

        guidelines = skill._get_audience_guidelines(ReportAudience.LAW_ENFORCEMENT)

        assert "formal" in guidelines.lower() or "legal" in guidelines.lower()
        assert "ESA" in guidelines or "Endangered Species" in guidelines

    def test_conservation_guidelines(self, skill):
        """Test conservation guidelines."""
        from backend.skills.report_writer import ReportAudience

        guidelines = skill._get_audience_guidelines(ReportAudience.CONSERVATION)

        assert "welfare" in guidelines.lower()

    def test_internal_guidelines(self, skill):
        """Test internal guidelines."""
        from backend.skills.report_writer import ReportAudience

        guidelines = skill._get_audience_guidelines(ReportAudience.INTERNAL)

        assert "technical" in guidelines.lower()

    def test_public_guidelines(self, skill):
        """Test public guidelines."""
        from backend.skills.report_writer import ReportAudience

        guidelines = skill._get_audience_guidelines(ReportAudience.PUBLIC)

        assert "plain" in guidelines.lower() or "accessible" in guidelines.lower()


class TestGetFormatInstructions:
    """Tests for _get_format_instructions method."""

    def test_markdown_instructions(self, skill):
        """Test markdown format instructions."""
        instructions = skill._get_format_instructions("markdown")

        assert "Markdown" in instructions
        assert "#" in instructions

    def test_json_instructions(self, skill):
        """Test JSON format instructions."""
        instructions = skill._get_format_instructions("json")

        assert "JSON" in instructions
        assert "sections" in instructions.lower()

    def test_pdf_instructions(self, skill):
        """Test PDF format instructions."""
        instructions = skill._get_format_instructions("pdf")

        assert "PDF" in instructions or "Markdown" in instructions


class TestFormatInvestigationData:
    """Tests for _format_investigation_data method."""

    def test_format_with_identification(self, skill, sample_investigation_data):
        """Test formatting identification data."""
        from backend.skills.report_writer import ReportAudience

        result = skill._format_investigation_data(
            sample_investigation_data,
            ReportAudience.LAW_ENFORCEMENT
        )

        assert "Raja" in result
        assert "t123" in result

    def test_format_with_model_results_internal(self, skill, sample_investigation_data):
        """Test formatting model results for internal audience."""
        from backend.skills.report_writer import ReportAudience

        result = skill._format_investigation_data(
            sample_investigation_data,
            ReportAudience.INTERNAL
        )

        # Internal reports should have detailed model info
        assert "wildlife_tools" in result

    def test_format_with_location(self, skill, sample_investigation_data):
        """Test formatting location data."""
        from backend.skills.report_writer import ReportAudience

        result = skill._format_investigation_data(
            sample_investigation_data,
            ReportAudience.LAW_ENFORCEMENT
        )

        assert "Zoo A" in result

    def test_format_empty_data(self, skill):
        """Test formatting empty data."""
        from backend.skills.report_writer import ReportAudience

        result = skill._format_investigation_data({}, ReportAudience.INTERNAL)

        assert "No investigation data" in result


class TestExecute:
    """Tests for execute method."""

    @pytest.mark.asyncio
    async def test_execute_success(self, skill, mock_chat_model, sample_investigation_data):
        """Test successful execution."""
        skill._chat_model = mock_chat_model

        context = {
            "audience": "law_enforcement",
            "investigation_data": sample_investigation_data,
            "format": "markdown"
        }

        result = await skill.execute(context)

        assert result["success"] is True
        assert result["output"] is not None
        assert result["metadata"]["audience"] == "law_enforcement"

    @pytest.mark.asyncio
    async def test_execute_validation_error(self, skill):
        """Test execution with missing required fields."""
        context = {}  # Missing audience and investigation_data

        result = await skill.execute(context)

        assert result["success"] is False
        assert "Validation failed" in result.get("error", "")

    @pytest.mark.asyncio
    async def test_execute_all_audiences(self, skill, mock_chat_model, sample_investigation_data):
        """Test execution for all audiences."""
        skill._chat_model = mock_chat_model

        for audience in ["law_enforcement", "conservation", "internal", "public"]:
            context = {
                "audience": audience,
                "investigation_data": sample_investigation_data,
                "format": "markdown"
            }

            result = await skill.execute(context)
            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_execute_all_formats(self, skill, mock_chat_model, sample_investigation_data):
        """Test execution for all formats."""
        skill._chat_model = mock_chat_model

        for format_type in ["markdown", "json", "pdf"]:
            context = {
                "audience": "internal",
                "investigation_data": sample_investigation_data,
                "format": format_type
            }

            result = await skill.execute(context)
            assert result["success"] is True
            assert result["metadata"]["format"] == format_type

    @pytest.mark.asyncio
    async def test_execute_with_classification(self, skill, mock_chat_model, sample_investigation_data):
        """Test execution with classification level."""
        skill._chat_model = mock_chat_model

        context = {
            "audience": "law_enforcement",
            "investigation_data": sample_investigation_data,
            "classification": "confidential"
        }

        result = await skill.execute(context)

        assert result["success"] is True
        assert result["metadata"]["classification"] == "confidential"

    @pytest.mark.asyncio
    async def test_execute_chat_model_failure(self, skill, sample_investigation_data):
        """Test execution when chat model fails."""
        mock_chat = MagicMock()
        mock_chat.chat = AsyncMock(return_value={
            "success": False,
            "error": "API error"
        })
        skill._chat_model = mock_chat

        context = {
            "audience": "internal",
            "investigation_data": sample_investigation_data
        }

        result = await skill.execute(context)

        assert result["success"] is False


class TestReportTemplates:
    """Tests for report template functions."""

    def test_get_law_enforcement_template(self):
        """Test law enforcement template."""
        from backend.skills.report_writer import get_law_enforcement_template

        template = get_law_enforcement_template()

        assert "Case Reference" in template
        assert "Evidence Chain" in template
        assert "Potential Violations" in template

    def test_get_conservation_template(self):
        """Test conservation template."""
        from backend.skills.report_writer import get_conservation_template

        template = get_conservation_template()

        assert "Welfare" in template
        assert "Conservation" in template


class TestToDict:
    """Tests for to_dict method."""

    def test_to_dict(self, skill):
        """Test converting skill to dictionary."""
        result = skill.to_dict()

        assert result["name"] == "Expert Report Writer"
        assert result["command"] == "/generate-report"
        assert result["category"] == "reporting"
        assert len(result["parameters"]) >= 2
