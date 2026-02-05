"""Tests for FacilityInvestigationSkill."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.fixture
def skill():
    """Create a FacilityInvestigationSkill for testing."""
    with patch('backend.skills.facility_investigation.get_logger'):
        with patch('backend.skills.base_skill.get_logger'):
            from backend.skills.facility_investigation import FacilityInvestigationSkill
            return FacilityInvestigationSkill()


@pytest.fixture
def mock_chat_model():
    """Create a mock chat model."""
    mock = MagicMock()
    mock.chat = AsyncMock(return_value={
        "success": True,
        "response": '{"facility_profile": {"name": "Test Zoo"}, "risk_assessment": {"level": "medium"}}'
    })
    return mock


@pytest.fixture
def sample_known_info():
    """Sample known information about a facility."""
    return {
        "usda_license": "12-A-0123",
        "owner": "John Doe",
        "location": "City, State"
    }


@pytest.fixture
def sample_web_results():
    """Sample web search results."""
    return [
        {
            "title": "Zoo Inspection Report",
            "url": "https://example.com/report",
            "type": "government",
            "content": "USDA inspection found minor violations..."
        },
        {
            "title": "News Article About Zoo",
            "url": "https://news.example.com/article",
            "type": "news",
            "snippet": "Zoo owner faces allegations..."
        }
    ]


class TestRiskLevel:
    """Tests for RiskLevel enum."""

    def test_risk_level_values(self):
        """Test RiskLevel enum values."""
        from backend.skills.facility_investigation import RiskLevel

        assert RiskLevel.LOW.value == "low"
        assert RiskLevel.MEDIUM.value == "medium"
        assert RiskLevel.HIGH.value == "high"
        assert RiskLevel.CRITICAL.value == "critical"


class TestInvestigationSection:
    """Tests for InvestigationSection enum."""

    def test_section_values(self):
        """Test InvestigationSection enum values."""
        from backend.skills.facility_investigation import InvestigationSection

        assert InvestigationSection.IDENTITY.value == "identity_verification"
        assert InvestigationSection.VIOLATIONS.value == "violation_history"
        assert InvestigationSection.NETWORK.value == "network_analysis"
        assert InvestigationSection.INVENTORY.value == "tiger_inventory"
        assert InvestigationSection.WELFARE.value == "welfare_assessment"


class TestFacilityProfile:
    """Tests for FacilityProfile dataclass."""

    def test_create_facility_profile(self):
        """Test creating a facility profile."""
        from backend.skills.facility_investigation import FacilityProfile, RiskLevel

        profile = FacilityProfile(
            name="Test Zoo",
            aliases=["Test Animal Park"],
            location="City, State",
            owner="John Doe",
            risk_level=RiskLevel.HIGH
        )

        assert profile.name == "Test Zoo"
        assert len(profile.aliases) == 1
        assert profile.risk_level == RiskLevel.HIGH

    def test_facility_profile_to_dict(self):
        """Test converting profile to dictionary."""
        from backend.skills.facility_investigation import FacilityProfile, RiskLevel

        profile = FacilityProfile(
            name="Test Zoo",
            risk_level=RiskLevel.MEDIUM,
            key_findings=["Finding 1", "Finding 2"]
        )

        result = profile.to_dict()

        assert result["name"] == "Test Zoo"
        assert result["risk_level"] == "medium"
        assert len(result["key_findings"]) == 2

    def test_facility_profile_defaults(self):
        """Test facility profile default values."""
        from backend.skills.facility_investigation import FacilityProfile, RiskLevel

        profile = FacilityProfile(name="Test")

        assert profile.aliases == []
        assert profile.location is None
        assert profile.risk_level == RiskLevel.MEDIUM


class TestSkillDefinition:
    """Tests for skill definition."""

    def test_skill_name(self, skill):
        """Test skill name."""
        definition = skill.get_definition()
        assert definition.name == "Facility Investigation"

    def test_skill_command(self, skill):
        """Test skill command."""
        definition = skill.get_definition()
        assert definition.command == "/investigate-facility"

    def test_skill_category(self, skill):
        """Test skill category."""
        from backend.skills.base_skill import SkillCategory

        definition = skill.get_definition()
        assert definition.category == SkillCategory.RESEARCH

    def test_skill_parameters(self, skill):
        """Test skill parameters."""
        definition = skill.get_definition()

        # Check required parameter
        facility_param = next(p for p in definition.parameters if p.name == "facility_name")
        assert facility_param.required is True
        assert facility_param.type == "string"

    def test_skill_has_depth_param(self, skill):
        """Test investigation_depth parameter."""
        definition = skill.get_definition()

        depth_param = next(
            (p for p in definition.parameters if p.name == "investigation_depth"),
            None
        )
        assert depth_param is not None
        assert depth_param.default == "standard"
        assert "quick" in depth_param.enum
        assert "deep" in depth_param.enum


class TestPromptTemplate:
    """Tests for prompt template."""

    def test_prompt_template_exists(self, skill):
        """Test prompt template is not empty."""
        template = skill.get_prompt_template()
        assert len(template) > 0

    def test_prompt_template_placeholders(self, skill):
        """Test prompt template has expected placeholders."""
        template = skill.get_prompt_template()

        assert "{facility_name}" in template
        assert "{known_info_formatted}" in template
        assert "{investigation_depth}" in template
        assert "{web_results_formatted}" in template

    def test_prompt_template_sections(self, skill):
        """Test prompt template has investigation sections."""
        template = skill.get_prompt_template()

        assert "Identity Verification" in template
        assert "Violation History" in template
        assert "Network Analysis" in template
        assert "Tiger Inventory" in template


class TestFormatKnownInfo:
    """Tests for _format_known_info method."""

    def test_format_empty_info(self, skill):
        """Test formatting empty known info."""
        result = skill._format_known_info({})

        assert "No prior information" in result

    def test_format_known_info(self, skill, sample_known_info):
        """Test formatting known info."""
        result = skill._format_known_info(sample_known_info)

        assert "12-A-0123" in result
        assert "John Doe" in result


class TestFormatWebResults:
    """Tests for _format_web_results method."""

    def test_format_empty_results(self, skill):
        """Test formatting empty web results."""
        result = skill._format_web_results([])

        assert "No web search results" in result

    def test_format_web_results(self, skill, sample_web_results):
        """Test formatting web results."""
        result = skill._format_web_results(sample_web_results)

        assert "Source 1" in result
        assert "Source 2" in result
        assert "Zoo Inspection Report" in result
        assert "example.com" in result

    def test_format_web_results_with_snippet(self, skill):
        """Test formatting results with snippet fallback."""
        results = [
            {"title": "Article", "url": "http://example.com", "snippet": "Some snippet text"}
        ]

        result = skill._format_web_results(results)

        assert "Some snippet text" in result


class TestFormatFocusSections:
    """Tests for _format_focus_sections method."""

    def test_format_no_focus(self, skill):
        """Test formatting with no focus sections."""
        result = skill._format_focus_sections(None)

        assert "all sections" in result.lower()

    def test_format_focus_sections(self, skill):
        """Test formatting focus sections."""
        result = skill._format_focus_sections(["violations", "network"])

        assert "Violation History" in result
        assert "Network Analysis" in result

    def test_format_unknown_section(self, skill):
        """Test formatting unknown section."""
        result = skill._format_focus_sections(["unknown_section"])

        assert "unknown_section" in result


class TestGenerateSearchQueries:
    """Tests for generate_search_queries method."""

    def test_generate_quick_queries(self, skill):
        """Test generating quick search queries."""
        queries = skill.generate_search_queries("Test Zoo", "quick")

        assert len(queries) >= 4
        assert any("USDA" in q for q in queries)
        assert any("tiger" in q.lower() for q in queries)

    def test_generate_standard_queries(self, skill):
        """Test generating standard search queries."""
        queries = skill.generate_search_queries("Test Zoo", "standard")

        assert len(queries) > 4
        assert any("lawsuit" in q.lower() for q in queries)
        assert any("welfare" in q.lower() for q in queries)

    def test_generate_deep_queries(self, skill):
        """Test generating deep search queries."""
        queries = skill.generate_search_queries("Test Zoo", "deep")

        assert len(queries) > 8
        assert any("CITES" in q for q in queries)
        assert any("trafficking" in q.lower() for q in queries)
        assert any("breeding" in q.lower() for q in queries)

    def test_queries_contain_facility_name(self, skill):
        """Test that queries contain facility name."""
        queries = skill.generate_search_queries("Big Cat Rescue", "standard")

        for query in queries:
            assert "Big Cat Rescue" in query


class TestExecute:
    """Tests for execute method."""

    @pytest.mark.asyncio
    async def test_execute_success(self, skill, mock_chat_model, sample_known_info):
        """Test successful execution."""
        skill._chat_model = mock_chat_model

        context = {
            "facility_name": "Test Zoo",
            "known_info": sample_known_info
        }

        result = await skill.execute(context)

        assert result["success"] is True
        assert result["output"] is not None
        assert result["metadata"]["facility_name"] == "Test Zoo"

    @pytest.mark.asyncio
    async def test_execute_validation_error(self, skill):
        """Test execution with missing required fields."""
        context = {}  # Missing facility_name

        result = await skill.execute(context)

        assert result["success"] is False
        assert "Validation failed" in result.get("error", "")

    @pytest.mark.asyncio
    async def test_execute_with_web_results(self, skill, mock_chat_model, sample_web_results):
        """Test execution with web search results."""
        skill._chat_model = mock_chat_model

        context = {
            "facility_name": "Test Zoo",
            "web_search_results": sample_web_results
        }

        result = await skill.execute(context)

        assert result["success"] is True
        assert result["metadata"]["web_sources_count"] == 2

    @pytest.mark.asyncio
    async def test_execute_all_depths(self, skill, mock_chat_model):
        """Test execution for all investigation depths."""
        skill._chat_model = mock_chat_model

        for depth in ["quick", "standard", "deep"]:
            context = {
                "facility_name": "Test Zoo",
                "investigation_depth": depth
            }

            result = await skill.execute(context)
            assert result["success"] is True
            assert result["metadata"]["investigation_depth"] == depth

    @pytest.mark.asyncio
    async def test_execute_with_focus_sections(self, skill, mock_chat_model):
        """Test execution with focus sections."""
        skill._chat_model = mock_chat_model

        context = {
            "facility_name": "Test Zoo",
            "focus_sections": ["violations", "network"]
        }

        result = await skill.execute(context)

        assert result["success"] is True
        assert result["metadata"]["focus_sections"] == ["violations", "network"]

    @pytest.mark.asyncio
    async def test_execute_chat_model_failure(self, skill):
        """Test execution when chat model fails."""
        mock_chat = MagicMock()
        mock_chat.chat = AsyncMock(return_value={
            "success": False,
            "error": "API error"
        })
        skill._chat_model = mock_chat

        context = {"facility_name": "Test Zoo"}

        result = await skill.execute(context)

        assert result["success"] is False


class TestToDict:
    """Tests for to_dict method."""

    def test_to_dict(self, skill):
        """Test converting skill to dictionary."""
        result = skill.to_dict()

        assert result["name"] == "Facility Investigation"
        assert result["command"] == "/investigate-facility"
        assert result["category"] == "research"
        assert len(result["parameters"]) >= 1


class TestIntegration:
    """Integration tests for facility investigation workflow."""

    @pytest.mark.asyncio
    async def test_investigation_workflow(self, skill, mock_chat_model, sample_known_info, sample_web_results):
        """Test complete investigation workflow."""
        skill._chat_model = mock_chat_model

        # Step 1: Generate search queries
        queries = skill.generate_search_queries("Big Cat Rescue", "standard")
        assert len(queries) > 0

        # Step 2: Execute investigation with web results
        context = {
            "facility_name": "Big Cat Rescue",
            "known_info": sample_known_info,
            "investigation_depth": "standard",
            "web_search_results": sample_web_results
        }

        result = await skill.execute(context)

        assert result["success"] is True
        assert result["output"] is not None
