"""Tests for ReasoningChainSkill."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime


@pytest.fixture
def skill():
    """Create a ReasoningChainSkill for testing."""
    with patch('backend.skills.reasoning_chain.get_logger'):
        with patch('backend.skills.base_skill.get_logger'):
            from backend.skills.reasoning_chain import ReasoningChainSkill
            return ReasoningChainSkill()


@pytest.fixture
def mock_chat_model():
    """Create a mock chat model."""
    mock = MagicMock()
    mock.chat = AsyncMock(return_value={
        "success": True,
        "response": '{"reasoning_step": "Analysis complete", "confidence": 0.85}'
    })
    return mock


class TestDecisionType:
    """Tests for DecisionType enum."""

    def test_decision_type_values(self):
        """Test DecisionType enum values."""
        from backend.skills.reasoning_chain import DecisionType

        assert DecisionType.IDENTIFICATION.value == "identification"
        assert DecisionType.VERIFICATION.value == "verification"
        assert DecisionType.LOCATION.value == "location"
        assert DecisionType.TIMELINE.value == "timeline"
        assert DecisionType.CONFIDENCE.value == "confidence"

    def test_all_decision_types(self):
        """Test all decision types are defined."""
        from backend.skills.reasoning_chain import DecisionType

        types = list(DecisionType)

        assert len(types) >= 5


class TestReasoningStep:
    """Tests for ReasoningStep dataclass."""

    def test_create_reasoning_step(self):
        """Test creating a reasoning step."""
        from backend.skills.reasoning_chain import ReasoningStep

        step = ReasoningStep(
            step_number=1,
            description="Analyzing stripe patterns",
            evidence=["Pattern match found", "92% similarity"],
            confidence=0.92,
            decision_type="identification"
        )

        assert step.step_number == 1
        assert "stripe patterns" in step.description
        assert len(step.evidence) == 2
        assert step.confidence == 0.92

    def test_reasoning_step_with_optional_fields(self):
        """Test reasoning step with optional fields."""
        from backend.skills.reasoning_chain import ReasoningStep

        step = ReasoningStep(
            step_number=2,
            description="Location analysis",
            evidence=["GPS data extracted"],
            confidence=0.8,
            decision_type="location",
            alternatives=["Could be Zoo B instead of Zoo A"],
            notes="EXIF data partially corrupted"
        )

        assert step.alternatives is not None
        assert step.notes is not None


class TestSkillDefinition:
    """Tests for skill definition."""

    def test_skill_name(self, skill):
        """Test skill name."""
        assert skill.name == "Reasoning Chain"

    def test_skill_command(self, skill):
        """Test skill command."""
        assert skill.command == "/explain-reasoning"

    def test_skill_category(self, skill):
        """Test skill category."""
        from backend.skills.base_skill import SkillCategory

        assert skill.category == SkillCategory.ANALYSIS

    def test_skill_description(self, skill):
        """Test skill description."""
        assert "reasoning" in skill.description.lower()

    def test_skill_parameters(self, skill):
        """Test skill parameters."""
        definition = skill.get_definition()

        # Check required parameters
        assert any(p.name == "decision" for p in definition.parameters)
        assert any(p.name == "evidence" for p in definition.parameters)

    def test_skill_has_decision_type_param(self, skill):
        """Test decision_type parameter."""
        definition = skill.get_definition()

        decision_param = next(
            (p for p in definition.parameters if p.name == "decision_type"),
            None
        )

        assert decision_param is not None
        assert "identification" in decision_param.enum


class TestPromptTemplate:
    """Tests for prompt template."""

    def test_prompt_template_exists(self, skill):
        """Test prompt template is not empty."""
        template = skill.get_prompt_template()

        assert len(template) > 0

    def test_prompt_template_placeholders(self, skill):
        """Test prompt template has expected placeholders."""
        template = skill.get_prompt_template()

        assert "{decision}" in template
        assert "{evidence_formatted}" in template
        assert "{decision_type}" in template


class TestFormatEvidence:
    """Tests for _format_evidence method."""

    def test_format_evidence_empty(self, skill):
        """Test formatting empty evidence."""
        result = skill._format_evidence([])

        assert result == "No evidence provided."

    def test_format_evidence_single(self, skill):
        """Test formatting single evidence item."""
        evidence = [
            {"type": "stripe_match", "value": "92% similarity to Raja"}
        ]

        result = skill._format_evidence(evidence)

        assert "stripe_match" in result.lower() or "92%" in result

    def test_format_evidence_multiple(self, skill):
        """Test formatting multiple evidence items."""
        evidence = [
            {"type": "stripe_match", "value": "92% similarity"},
            {"type": "location", "value": "GPS: Zoo A"},
            {"type": "timestamp", "value": "2024-01-01"}
        ]

        result = skill._format_evidence(evidence)

        # All evidence should be included
        lines = result.split('\n')
        assert len(lines) >= 3

    def test_format_evidence_with_confidence(self, skill):
        """Test formatting evidence with confidence scores."""
        evidence = [
            {"type": "model_match", "value": "Match found", "confidence": 0.95}
        ]

        result = skill._format_evidence(evidence)

        assert "95" in result or "0.95" in result


class TestBuildReasoningChain:
    """Tests for _build_reasoning_chain method."""

    def test_build_chain_basic(self, skill):
        """Test building basic reasoning chain."""
        decision = "This tiger is Raja"
        evidence = [
            {"type": "stripe_match", "value": "92% similarity"}
        ]

        chain = skill._build_reasoning_chain(decision, evidence)

        assert len(chain) >= 1

    def test_build_chain_multiple_evidence(self, skill):
        """Test building chain with multiple evidence types."""
        decision = "Tiger identified as Raja at Zoo A"
        evidence = [
            {"type": "stripe_match", "value": "92% match"},
            {"type": "location", "value": "GPS matches Zoo A"},
            {"type": "timeline", "value": "Consistent with known movements"}
        ]

        chain = skill._build_reasoning_chain(decision, evidence)

        # Should have steps for each evidence type
        assert len(chain) >= 2

    def test_chain_has_confidence(self, skill):
        """Test that chain steps have confidence."""
        decision = "Match confirmed"
        evidence = [{"type": "test", "value": "data", "confidence": 0.9}]

        chain = skill._build_reasoning_chain(decision, evidence)

        for step in chain:
            assert "confidence" in step or hasattr(step, "confidence")


class TestReasoningStepGeneration:
    """Tests for reasoning step generation."""

    def test_generate_identification_step(self, skill):
        """Test generating identification reasoning step."""
        from backend.skills.reasoning_chain import DecisionType

        step = skill._generate_step(
            step_number=1,
            decision_type=DecisionType.IDENTIFICATION,
            evidence={"type": "stripe_match", "value": "High similarity"}
        )

        assert step["step_number"] == 1
        assert "identification" in step["decision_type"].lower() or step["decision_type"] == "identification"

    def test_generate_verification_step(self, skill):
        """Test generating verification reasoning step."""
        from backend.skills.reasoning_chain import DecisionType

        step = skill._generate_step(
            step_number=2,
            decision_type=DecisionType.VERIFICATION,
            evidence={"type": "keypoint_match", "value": "45 matches"}
        )

        assert step["step_number"] == 2

    def test_generate_location_step(self, skill):
        """Test generating location reasoning step."""
        from backend.skills.reasoning_chain import DecisionType

        step = skill._generate_step(
            step_number=3,
            decision_type=DecisionType.LOCATION,
            evidence={"type": "gps", "value": "Coordinates: 28.5, 77.2"}
        )

        assert step is not None


class TestAlternativeConsideration:
    """Tests for alternative consideration."""

    def test_generate_alternatives(self, skill):
        """Test generating alternative explanations."""
        decision = "This is Raja"
        evidence = [
            {"type": "stripe_match", "value": "88% similarity"}
        ]

        alternatives = skill._generate_alternatives(decision, evidence)

        # Should suggest alternatives for non-certain matches
        assert isinstance(alternatives, list)

    def test_no_alternatives_high_confidence(self, skill):
        """Test no alternatives for very high confidence."""
        decision = "Definite match to Raja"
        evidence = [
            {"type": "stripe_match", "value": "99% similarity", "confidence": 0.99}
        ]

        alternatives = skill._generate_alternatives(decision, evidence)

        # High confidence should have few or no alternatives
        assert len(alternatives) <= 2


class TestConfidenceCalculation:
    """Tests for confidence calculation."""

    def test_calculate_chain_confidence(self, skill):
        """Test calculating overall chain confidence."""
        steps = [
            {"confidence": 0.95},
            {"confidence": 0.90},
            {"confidence": 0.85}
        ]

        confidence = skill._calculate_chain_confidence(steps)

        # Should be weighted average or minimum
        assert 0.8 <= confidence <= 0.95

    def test_confidence_with_low_step(self, skill):
        """Test confidence with one low step."""
        steps = [
            {"confidence": 0.95},
            {"confidence": 0.50},  # Low confidence step
            {"confidence": 0.90}
        ]

        confidence = skill._calculate_chain_confidence(steps)

        # Should be pulled down by low step
        assert confidence < 0.9

    def test_confidence_range(self, skill):
        """Test confidence is in valid range."""
        for conf_values in [[0.1], [0.5, 0.5], [0.9, 0.9, 0.9], [1.0]]:
            steps = [{"confidence": c} for c in conf_values]
            result = skill._calculate_chain_confidence(steps)
            assert 0 <= result <= 1


class TestExecute:
    """Tests for execute method."""

    @pytest.mark.asyncio
    async def test_execute_success(self, skill, mock_chat_model):
        """Test successful execution."""
        skill._chat_model = mock_chat_model

        context = {
            "decision": "Tiger identified as Raja",
            "evidence": [
                {"type": "stripe_match", "value": "92% similarity", "confidence": 0.92}
            ],
            "decision_type": "identification"
        }

        result = await skill.execute(context)

        assert result["success"] is True
        assert result["output"] is not None
        assert "reasoning_chain" in result or "chain" in str(result).lower()

    @pytest.mark.asyncio
    async def test_execute_validation_error(self, skill):
        """Test execution with missing required fields."""
        context = {}  # Missing decision and evidence

        result = await skill.execute(context)

        assert result["success"] is False
        assert "Validation failed" in result.get("error", "")

    @pytest.mark.asyncio
    async def test_execute_uses_decision_type(self, skill, mock_chat_model):
        """Test execution uses decision type."""
        skill._chat_model = mock_chat_model

        for decision_type in ["identification", "verification", "location"]:
            context = {
                "decision": "Test decision",
                "evidence": [{"type": "test", "value": "test"}],
                "decision_type": decision_type
            }

            result = await skill.execute(context)
            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_execute_returns_steps(self, skill, mock_chat_model):
        """Test execution returns reasoning steps."""
        skill._chat_model = mock_chat_model

        context = {
            "decision": "Match confirmed",
            "evidence": [
                {"type": "stripe_match", "value": "95%"},
                {"type": "keypoint", "value": "50 matches"}
            ],
            "decision_type": "verification"
        }

        result = await skill.execute(context)

        assert result["success"] is True
        # Should have reasoning steps in output

    @pytest.mark.asyncio
    async def test_execute_chat_model_failure(self, skill):
        """Test execution when chat model fails."""
        mock_chat = MagicMock()
        mock_chat.chat = AsyncMock(return_value={
            "success": False,
            "error": "API error"
        })
        skill._chat_model = mock_chat

        context = {
            "decision": "Test",
            "evidence": [{"type": "test", "value": "test"}]
        }

        result = await skill.execute(context)

        assert result["success"] is False


class TestOutputFormatting:
    """Tests for output formatting."""

    def test_format_chain_for_display(self, skill):
        """Test formatting chain for display."""
        chain = [
            {
                "step_number": 1,
                "description": "Stripe pattern analysis",
                "confidence": 0.92
            },
            {
                "step_number": 2,
                "description": "Location verification",
                "confidence": 0.85
            }
        ]

        formatted = skill._format_chain_output(chain)

        assert "Step 1" in formatted or "1." in formatted
        assert "Step 2" in formatted or "2." in formatted

    def test_format_includes_confidence(self, skill):
        """Test formatting includes confidence indicators."""
        chain = [
            {"step_number": 1, "description": "Test", "confidence": 0.95}
        ]

        formatted = skill._format_chain_output(chain)

        # Should include confidence indication
        assert "95" in formatted or "high" in formatted.lower() or "confident" in formatted.lower()


class TestToDict:
    """Tests for to_dict method."""

    def test_to_dict(self, skill):
        """Test converting skill to dictionary."""
        result = skill.to_dict()

        assert result["name"] == "Reasoning Chain"
        assert result["command"] == "/explain-reasoning"
        assert result["category"] == "analysis"
        assert len(result["parameters"]) >= 2


class TestIntegration:
    """Integration tests for reasoning chain in investigation workflow."""

    @pytest.mark.asyncio
    async def test_integration_with_investigation(self, skill, mock_chat_model):
        """Test integration with investigation context."""
        skill._chat_model = mock_chat_model

        # Simulate investigation result
        context = {
            "decision": "Tiger identified as Raja (ID: t123) currently at Zoo A",
            "evidence": [
                {
                    "type": "reid_ensemble",
                    "value": "6 models agree with weighted score 0.91",
                    "confidence": 0.91
                },
                {
                    "type": "keypoint_verification",
                    "value": "MatchAnything: 48 keypoint matches",
                    "confidence": 0.94
                },
                {
                    "type": "location",
                    "value": "EXIF GPS: 28.5673, 77.2134 (matches Zoo A)",
                    "confidence": 1.0
                },
                {
                    "type": "historical",
                    "value": "Last seen at Zoo A on 2024-01-01",
                    "confidence": 0.85
                }
            ],
            "decision_type": "identification"
        }

        result = await skill.execute(context)

        assert result["success"] is True
        assert result["metadata"]["evidence_count"] == 4
