"""Tests for ImageAdvisorSkill."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.fixture
def skill():
    """Create an ImageAdvisorSkill for testing."""
    with patch('backend.skills.image_advisor.get_logger'):
        with patch('backend.skills.base_skill.get_logger'):
            from backend.skills.image_advisor import ImageAdvisorSkill
            return ImageAdvisorSkill()


@pytest.fixture
def mock_chat_model():
    """Create a mock chat model."""
    mock = MagicMock()
    mock.chat = AsyncMock(return_value={
        "success": True,
        "response": '{"overall_score": 75, "recommendation": "proceed_with_caution", "issues": []}'
    })
    return mock


@pytest.fixture
def sample_quality_metrics():
    """Sample quality metrics."""
    return {
        "resolution": [1024, 768],
        "blur_score": 150,
        "stripe_visibility": 0.8,
        "overall_score": 0.75,
        "brightness": 0.6,
        "contrast": 0.7
    }


@pytest.fixture
def sample_detection_results():
    """Sample detection results."""
    return {
        "detections": [
            {"confidence": 0.95, "bbox": [100, 100, 400, 400], "class": "tiger"}
        ],
        "image_size": [1024, 768]
    }


class TestQualityThresholds:
    """Tests for QUALITY_THRESHOLDS constant."""

    def test_thresholds_defined(self):
        """Test that thresholds are defined."""
        from backend.skills.image_advisor import QUALITY_THRESHOLDS

        assert "resolution_min" in QUALITY_THRESHOLDS
        assert "resolution_good" in QUALITY_THRESHOLDS
        assert "blur_threshold" in QUALITY_THRESHOLDS
        assert "stripe_visibility_min" in QUALITY_THRESHOLDS
        assert "detection_confidence_min" in QUALITY_THRESHOLDS

    def test_threshold_values(self):
        """Test threshold values are reasonable."""
        from backend.skills.image_advisor import QUALITY_THRESHOLDS

        assert QUALITY_THRESHOLDS["resolution_min"] >= 640
        assert QUALITY_THRESHOLDS["resolution_good"] >= QUALITY_THRESHOLDS["resolution_min"]
        assert 0 < QUALITY_THRESHOLDS["stripe_visibility_min"] < 1
        assert 0 < QUALITY_THRESHOLDS["detection_confidence_min"] < 1


class TestSkillDefinition:
    """Tests for skill definition."""

    def test_skill_name(self, skill):
        """Test skill name."""
        definition = skill.get_definition()
        assert definition.name == "Image Quality Advisor"

    def test_skill_command(self, skill):
        """Test skill command."""
        definition = skill.get_definition()
        assert definition.command == "/assess-image"

    def test_skill_category(self, skill):
        """Test skill category."""
        from backend.skills.base_skill import SkillCategory

        definition = skill.get_definition()
        assert definition.category == SkillCategory.QUALITY

    def test_skill_parameters(self, skill):
        """Test skill parameters."""
        definition = skill.get_definition()

        # Check required parameter
        quality_param = next(p for p in definition.parameters if p.name == "quality_metrics")
        assert quality_param.required is True
        assert quality_param.type == "object"

    def test_skill_has_detection_param(self, skill):
        """Test detection_results parameter."""
        definition = skill.get_definition()

        detection_param = next(
            (p for p in definition.parameters if p.name == "detection_results"),
            None
        )
        assert detection_param is not None
        assert detection_param.required is False


class TestPromptTemplate:
    """Tests for prompt template."""

    def test_prompt_template_exists(self, skill):
        """Test prompt template is not empty."""
        template = skill.get_prompt_template()
        assert len(template) > 0

    def test_prompt_template_placeholders(self, skill):
        """Test prompt template has expected placeholders."""
        template = skill.get_prompt_template()

        assert "{quality_metrics_formatted}" in template
        assert "{detection_results_formatted}" in template
        assert "{resolution_min}" in template

    def test_prompt_template_output_format(self, skill):
        """Test prompt template specifies JSON output."""
        template = skill.get_prompt_template()

        assert "JSON" in template or "json" in template
        assert "overall_score" in template


class TestFormatQualityMetrics:
    """Tests for _format_quality_metrics method."""

    def test_format_empty_metrics(self, skill):
        """Test formatting empty metrics."""
        result = skill._format_quality_metrics({})

        assert "No quality metrics" in result

    def test_format_metrics(self, skill, sample_quality_metrics):
        """Test formatting quality metrics."""
        result = skill._format_quality_metrics(sample_quality_metrics)

        assert "Resolution" in result or "resolution" in result.lower()

    def test_format_percentage_values(self, skill):
        """Test formatting percentage values."""
        metrics = {"stripe_visibility": 0.75}

        result = skill._format_quality_metrics(metrics)

        # Should format as percentage (75%)
        assert "75" in result

    def test_format_non_percentage_values(self, skill):
        """Test formatting non-percentage values."""
        metrics = {"blur_score": 150}

        result = skill._format_quality_metrics(metrics)

        assert "150" in result


class TestFormatDetectionResults:
    """Tests for _format_detection_results method."""

    def test_format_empty_detection(self, skill):
        """Test formatting empty detection results."""
        result = skill._format_detection_results({})

        assert "No detection" in result

    def test_format_detection_results(self, skill, sample_detection_results):
        """Test formatting detection results."""
        result = skill._format_detection_results(sample_detection_results)

        assert "1" in result  # 1 tiger detected
        assert "95" in result or "0.95" in result  # confidence

    def test_format_multiple_detections(self, skill):
        """Test formatting multiple detections."""
        results = {
            "detections": [
                {"confidence": 0.95, "bbox": [100, 100, 400, 400]},
                {"confidence": 0.85, "bbox": [500, 100, 800, 400]}
            ]
        }

        result = skill._format_detection_results(results)

        assert "2" in result  # 2 tigers detected


class TestExecute:
    """Tests for execute method."""

    @pytest.mark.asyncio
    async def test_execute_success(self, skill, mock_chat_model, sample_quality_metrics):
        """Test successful execution."""
        skill._chat_model = mock_chat_model

        context = {
            "quality_metrics": sample_quality_metrics
        }

        result = await skill.execute(context)

        assert result["success"] is True
        assert result["output"] is not None

    @pytest.mark.asyncio
    async def test_execute_validation_error(self, skill):
        """Test execution with missing required fields."""
        context = {}  # Missing quality_metrics

        result = await skill.execute(context)

        assert result["success"] is False
        assert "Validation failed" in result.get("error", "")

    @pytest.mark.asyncio
    async def test_execute_with_detection(self, skill, mock_chat_model, sample_quality_metrics, sample_detection_results):
        """Test execution with detection results."""
        skill._chat_model = mock_chat_model

        context = {
            "quality_metrics": sample_quality_metrics,
            "detection_results": sample_detection_results
        }

        result = await skill.execute(context)

        assert result["success"] is True
        assert result["metadata"]["has_detection"] is True

    @pytest.mark.asyncio
    async def test_execute_with_user_context(self, skill, mock_chat_model, sample_quality_metrics):
        """Test execution with user context."""
        skill._chat_model = mock_chat_model

        context = {
            "quality_metrics": sample_quality_metrics,
            "user_context": "Photo taken at night with flash"
        }

        result = await skill.execute(context)

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_execute_chat_model_failure(self, skill, sample_quality_metrics):
        """Test execution when chat model fails."""
        mock_chat = MagicMock()
        mock_chat.chat = AsyncMock(return_value={
            "success": False,
            "error": "API error"
        })
        skill._chat_model = mock_chat

        context = {"quality_metrics": sample_quality_metrics}

        result = await skill.execute(context)

        assert result["success"] is False


class TestComputeBasicQualityScore:
    """Tests for compute_basic_quality_score function."""

    def test_compute_high_quality(self):
        """Test computing score for high quality image."""
        from backend.skills.image_advisor import compute_basic_quality_score

        metrics = {
            "resolution": [1920, 1080],
            "blur_score": 200,
            "detection_confidence": 0.95,
            "stripe_visibility": 0.9
        }

        result = compute_basic_quality_score(metrics)

        assert result["score"] >= 80
        assert result["recommendation"] == "proceed"
        assert len(result["issues"]) == 0

    def test_compute_low_resolution(self):
        """Test computing score for low resolution image."""
        from backend.skills.image_advisor import compute_basic_quality_score

        metrics = {
            "resolution": [320, 240],  # Below minimum
        }

        result = compute_basic_quality_score(metrics)

        assert result["score"] < 80
        assert "Resolution too low" in result["issues"]

    def test_compute_blurry_image(self):
        """Test computing score for blurry image."""
        from backend.skills.image_advisor import compute_basic_quality_score

        metrics = {
            "blur_score": 50,  # Below threshold
        }

        result = compute_basic_quality_score(metrics)

        assert "blurry" in result["issues"][0].lower()

    def test_compute_low_detection_confidence(self):
        """Test computing score for low detection confidence."""
        from backend.skills.image_advisor import compute_basic_quality_score

        metrics = {
            "detection_confidence": 0.5,  # Below threshold
        }

        result = compute_basic_quality_score(metrics)

        assert "detection" in result["issues"][0].lower()

    def test_compute_low_stripe_visibility(self):
        """Test computing score for low stripe visibility."""
        from backend.skills.image_advisor import compute_basic_quality_score

        metrics = {
            "stripe_visibility": 0.3,  # Below threshold
        }

        result = compute_basic_quality_score(metrics)

        assert "stripe" in result["issues"][0].lower()

    def test_compute_multiple_issues(self):
        """Test computing score with multiple issues."""
        from backend.skills.image_advisor import compute_basic_quality_score

        metrics = {
            "resolution": [400, 300],  # Low
            "blur_score": 50,  # Blurry
            "stripe_visibility": 0.3,  # Low visibility
        }

        result = compute_basic_quality_score(metrics)

        assert result["score"] < 50
        assert len(result["issues"]) >= 3
        assert result["recommendation"] == "request_new_image"

    def test_compute_medium_quality(self):
        """Test computing score for medium quality image."""
        from backend.skills.image_advisor import compute_basic_quality_score

        metrics = {
            "resolution": [800, 600],  # Below good, above min
        }

        result = compute_basic_quality_score(metrics)

        assert 50 <= result["score"] <= 90
        assert "below ideal" in result["issues"][0].lower()

    def test_recommendation_thresholds(self):
        """Test recommendation thresholds."""
        from backend.skills.image_advisor import compute_basic_quality_score

        # Score >= 70 -> proceed
        high = compute_basic_quality_score({"resolution": [2000, 2000]})
        assert high["recommendation"] == "proceed"

        # Score 50-69 -> proceed_with_caution
        medium = compute_basic_quality_score({"resolution": [400, 400], "blur_score": 50})
        assert medium["recommendation"] == "proceed_with_caution"

        # Score < 50 -> request_new_image
        low = compute_basic_quality_score({
            "resolution": [200, 200],
            "blur_score": 10,
            "stripe_visibility": 0.1
        })
        assert low["recommendation"] == "request_new_image"


class TestToDict:
    """Tests for to_dict method."""

    def test_to_dict(self, skill):
        """Test converting skill to dictionary."""
        result = skill.to_dict()

        assert result["name"] == "Image Quality Advisor"
        assert result["command"] == "/assess-image"
        assert result["category"] == "quality"
        assert len(result["parameters"]) >= 1
