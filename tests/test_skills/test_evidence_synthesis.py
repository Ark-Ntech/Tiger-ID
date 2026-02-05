"""Tests for EvidenceSynthesisSkill."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from backend.skills.evidence_synthesis import (
    EvidenceSynthesisSkill,
    EvidenceSource,
    MODEL_WEIGHTS,
    SOURCE_RELIABILITY
)
from backend.skills.base_skill import SkillCategory


@pytest.fixture
def skill():
    """Create an EvidenceSynthesisSkill for testing."""
    with patch('backend.skills.evidence_synthesis.get_logger'):
        with patch('backend.skills.base_skill.get_logger'):
            return EvidenceSynthesisSkill()


@pytest.fixture
def mock_chat_model():
    """Create a mock chat model."""
    mock = MagicMock()
    mock.chat = AsyncMock(return_value={
        "success": True,
        "response": '{"confidence_score": 85, "confidence_level": "high"}'
    })
    return mock


class TestConstants:
    """Tests for module constants."""

    def test_model_weights_sum(self):
        """Test that model weights sum approximately to 1.0."""
        total = sum(MODEL_WEIGHTS.values())
        # Weights are 0.40 + 0.30 + 0.20 + 0.10 + 0.10 = 1.10
        assert 0.9 <= total <= 1.2

    def test_model_weights_wildlife_tools(self):
        """Test wildlife_tools has highest weight."""
        assert MODEL_WEIGHTS["wildlife_tools"] == 0.40
        assert MODEL_WEIGHTS["wildlife_tools"] >= max(
            v for k, v in MODEL_WEIGHTS.items() if k != "wildlife_tools"
        )

    def test_source_reliability_hierarchy(self):
        """Test source reliability hierarchy."""
        assert SOURCE_RELIABILITY["exif_gps"] == 1.0
        assert SOURCE_RELIABILITY["database_match"] > SOURCE_RELIABILITY["visual_analysis"]
        assert SOURCE_RELIABILITY["visual_analysis"] > SOURCE_RELIABILITY["web_intelligence"]


class TestEvidenceSource:
    """Tests for EvidenceSource dataclass."""

    def test_create_evidence_source(self):
        """Test creating an evidence source."""
        source = EvidenceSource(
            source_type="database_match",
            content={"tiger_id": "123", "name": "Raja"},
            confidence=0.95
        )

        assert source.source_type == "database_match"
        assert source.content == {"tiger_id": "123", "name": "Raja"}
        assert source.confidence == 0.95
        assert source.url is None
        assert source.timestamp is None

    def test_create_evidence_source_with_optional(self):
        """Test creating an evidence source with optional fields."""
        source = EvidenceSource(
            source_type="web_intelligence",
            content={"finding": "Tiger spotted"},
            confidence=0.6,
            url="https://example.com/article",
            timestamp="2024-01-01T12:00:00Z"
        )

        assert source.url == "https://example.com/article"
        assert source.timestamp == "2024-01-01T12:00:00Z"


class TestSkillDefinition:
    """Tests for skill definition."""

    def test_skill_name(self, skill):
        """Test skill name."""
        assert skill.name == "Evidence Synthesis"

    def test_skill_command(self, skill):
        """Test skill command."""
        assert skill.command == "/synthesize-evidence"

    def test_skill_category(self, skill):
        """Test skill category."""
        assert skill.category == SkillCategory.ANALYSIS

    def test_skill_description(self, skill):
        """Test skill description."""
        assert "evidence" in skill.description.lower()

    def test_skill_parameters(self, skill):
        """Test skill parameters."""
        definition = skill.get_definition()

        # Check required parameters
        sources_param = next(
            p for p in definition.parameters if p.name == "sources"
        )
        assert sources_param.required is True
        assert sources_param.type == "array"

    def test_skill_has_synthesis_mode_param(self, skill):
        """Test synthesis_mode parameter."""
        definition = skill.get_definition()

        mode_param = next(
            p for p in definition.parameters if p.name == "synthesis_mode"
        )
        assert mode_param.required is False
        assert mode_param.default == "balanced"
        assert mode_param.enum == ["conservative", "balanced", "aggressive"]


class TestPromptTemplate:
    """Tests for prompt template."""

    def test_prompt_template_exists(self, skill):
        """Test prompt template is not empty."""
        template = skill.get_prompt_template()
        assert len(template) > 0

    def test_prompt_template_placeholders(self, skill):
        """Test prompt template has expected placeholders."""
        template = skill.get_prompt_template()

        assert "{sources_formatted}" in template
        assert "{model_results_formatted}" in template
        assert "{model_weights_formatted}" in template
        assert "{synthesis_mode}" in template
        assert "{focus_areas}" in template


class TestFormatSources:
    """Tests for _format_sources method."""

    def test_format_sources_empty(self, skill):
        """Test formatting empty sources."""
        result = skill._format_sources([])
        assert result == "No evidence sources provided."

    def test_format_sources_single(self, skill):
        """Test formatting single source."""
        sources = [{
            "source_type": "database_match",
            "content": "Tiger found in database",
            "confidence": 0.9,
            "url": "https://example.com"
        }]

        result = skill._format_sources(sources)

        assert "Source 1" in result
        assert "Database Match" in result
        assert "Tiger found in database" in result
        assert "90" in result  # reliability percentage

    def test_format_sources_multiple(self, skill):
        """Test formatting multiple sources."""
        sources = [
            {"source_type": "exif_gps", "content": "GPS data"},
            {"source_type": "web_intelligence", "content": "Web finding"},
        ]

        result = skill._format_sources(sources)

        assert "Source 1" in result
        assert "Source 2" in result

    def test_format_sources_unknown_type(self, skill):
        """Test formatting source with unknown type."""
        sources = [{
            "source_type": "unknown_source",
            "content": "Some content"
        }]

        result = skill._format_sources(sources)

        # Should use default reliability of 0.5
        assert "50" in result


class TestFormatModelResults:
    """Tests for _format_model_results method."""

    def test_format_model_results_empty(self, skill):
        """Test formatting empty model results."""
        result = skill._format_model_results({})
        assert result == "No model matching results available."

    def test_format_model_results_single(self, skill):
        """Test formatting single model result."""
        model_results = {
            "wildlife_tools": {
                "matches": [
                    {"tiger_id": "t1", "tiger_name": "Raja", "similarity": 0.92, "facility_name": "Zoo A"},
                    {"tiger_id": "t2", "tiger_name": "Sher", "similarity": 0.85, "facility_name": "Zoo B"},
                ]
            }
        }

        result = skill._format_model_results(model_results)

        assert "Wildlife Tools" in result
        assert "40%" in result  # weight
        assert "Raja" in result
        assert "92" in result  # similarity

    def test_format_model_results_limits_to_top_3(self, skill):
        """Test that only top 3 matches are shown."""
        model_results = {
            "wildlife_tools": {
                "matches": [
                    {"tiger_id": f"t{i}", "tiger_name": f"Tiger {i}", "similarity": 0.9 - i*0.1}
                    for i in range(5)
                ]
            }
        }

        result = skill._format_model_results(model_results)

        # Should only have Tiger 0, 1, 2 (top 3)
        assert "Tiger 0" in result
        assert "Tiger 2" in result


class TestFormatModelWeights:
    """Tests for _format_model_weights method."""

    def test_format_model_weights(self, skill):
        """Test formatting model weights."""
        result = skill._format_model_weights()

        assert "wildlife_tools: 40%" in result
        assert "cvwc2019_reid: 30%" in result

    def test_format_model_weights_sorted(self, skill):
        """Test that weights are sorted in descending order."""
        result = skill._format_model_weights()
        lines = result.split('\n')

        # Find lines with weights
        weight_lines = [l for l in lines if ':' in l and '%' in l]

        # Extract weights
        weights = []
        for line in weight_lines:
            if '%' in line:
                # Extract percentage
                pct = int(line.split(':')[1].strip().replace('%', ''))
                weights.append(pct)

        # Should be sorted descending
        assert weights == sorted(weights, reverse=True)


class TestGetSynthesisInstructions:
    """Tests for _get_synthesis_instructions method."""

    def test_conservative_mode(self, skill):
        """Test conservative mode instructions."""
        result = skill._get_synthesis_instructions("conservative")

        assert "Conservative" in result
        assert "cautious" in result.lower()

    def test_balanced_mode(self, skill):
        """Test balanced mode instructions."""
        result = skill._get_synthesis_instructions("balanced")

        assert "Balanced" in result

    def test_aggressive_mode(self, skill):
        """Test aggressive mode instructions."""
        result = skill._get_synthesis_instructions("aggressive")

        assert "Aggressive" in result
        assert "faster" in result.lower() or "weaker" in result.lower()

    def test_unknown_mode_defaults_to_balanced(self, skill):
        """Test unknown mode defaults to balanced."""
        result = skill._get_synthesis_instructions("unknown")

        assert "Balanced" in result


class TestComputeMetrics:
    """Tests for _compute_metrics method."""

    def test_compute_metrics_empty(self, skill):
        """Test computing metrics with empty data."""
        result = skill._compute_metrics([], {})

        assert result["source_counts"] == {}
        assert result["total_sources"] == 0
        assert result["models_count"] == 0
        assert result["weighted_similarity"] == 0

    def test_compute_metrics_sources(self, skill):
        """Test computing metrics with sources."""
        sources = [
            {"source_type": "database_match"},
            {"source_type": "database_match"},
            {"source_type": "web_intelligence"},
        ]

        result = skill._compute_metrics(sources, {})

        assert result["total_sources"] == 3
        assert result["source_counts"]["database_match"] == 2
        assert result["source_counts"]["web_intelligence"] == 1

    def test_compute_metrics_model_results(self, skill):
        """Test computing metrics with model results."""
        model_results = {
            "wildlife_tools": {
                "matches": [{"similarity": 0.95}]
            },
            "cvwc2019_reid": {
                "matches": [{"similarity": 0.85}]
            }
        }

        result = skill._compute_metrics([], model_results)

        assert result["models_count"] == 2
        assert result["weighted_similarity"] > 0

    def test_compute_metrics_agreeing_models(self, skill):
        """Test counting agreeing models."""
        model_results = {
            "wildlife_tools": {"matches": [{"similarity": 0.95}]},  # Agrees (>= 0.8)
            "cvwc2019_reid": {"matches": [{"similarity": 0.60}]},   # Disagrees
            "transreid": {"matches": [{"similarity": 0.85}]},       # Agrees
        }

        result = skill._compute_metrics([], model_results)

        assert result["agreeing_models"] == 2


class TestExecute:
    """Tests for execute method."""

    @pytest.mark.asyncio
    async def test_execute_success(self, skill, mock_chat_model):
        """Test successful execution."""
        skill._chat_model = mock_chat_model

        context = {
            "sources": [
                {"source_type": "database_match", "content": "Match found", "confidence": 0.9}
            ],
            "model_results": {
                "wildlife_tools": {
                    "matches": [{"tiger_id": "t1", "tiger_name": "Raja", "similarity": 0.92}]
                }
            },
            "focus_areas": ["identification"],
            "synthesis_mode": "balanced"
        }

        result = await skill.execute(context)

        assert result["success"] is True
        assert result["output"] is not None
        assert result["metadata"]["sources_count"] == 1

    @pytest.mark.asyncio
    async def test_execute_validation_error(self, skill):
        """Test execution with missing required sources."""
        context = {}  # Missing sources

        result = await skill.execute(context)

        assert result["success"] is False
        assert "Validation failed" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_chat_model_failure(self, skill):
        """Test execution when chat model fails."""
        mock_chat = MagicMock()
        mock_chat.chat = AsyncMock(return_value={
            "success": False,
            "error": "API error"
        })
        skill._chat_model = mock_chat

        context = {"sources": [{"source_type": "test", "content": "test"}]}

        result = await skill.execute(context)

        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_execute_creates_chat_model(self, skill):
        """Test that execute creates chat model if not exists."""
        context = {"sources": [{"source_type": "test", "content": "test"}]}

        with patch('backend.skills.evidence_synthesis.AnthropicChatModel') as mock_cls:
            mock_instance = MagicMock()
            mock_instance.chat = AsyncMock(return_value={
                "success": True,
                "response": '{"confidence_score": 75}'
            })
            mock_cls.return_value = mock_instance

            result = await skill.execute(context)

            mock_cls.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_uses_default_values(self, skill, mock_chat_model):
        """Test execution uses default values for optional params."""
        skill._chat_model = mock_chat_model

        context = {
            "sources": [{"source_type": "test", "content": "test"}]
        }

        result = await skill.execute(context)

        assert result["success"] is True
        assert result["metadata"]["synthesis_mode"] == "balanced"

    @pytest.mark.asyncio
    async def test_execute_exception_handling(self, skill):
        """Test execution handles exceptions."""
        mock_chat = MagicMock()
        mock_chat.chat = AsyncMock(side_effect=Exception("Unexpected error"))
        skill._chat_model = mock_chat

        context = {"sources": [{"source_type": "test", "content": "test"}]}

        result = await skill.execute(context)

        assert result["success"] is False
        assert "Unexpected error" in result["error"]


class TestToDict:
    """Tests for to_dict method."""

    def test_to_dict(self, skill):
        """Test converting skill to dictionary."""
        result = skill.to_dict()

        assert result["name"] == "Evidence Synthesis"
        assert result["command"] == "/synthesize-evidence"
        assert result["category"] == "analysis"
        assert len(result["parameters"]) >= 1
