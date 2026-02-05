"""
Image Quality Advisor Skill

Advises users on image quality and suggests improvements for tiger identification.
"""

from typing import Any, Dict, List

from backend.skills.base_skill import (
    BaseSkill,
    SkillDefinition,
    SkillParameter,
    SkillCategory
)
from backend.skills import SkillRegistry
from backend.models.anthropic_chat import AnthropicChatModel
from backend.utils.logging import get_logger

logger = get_logger(__name__)


# Quality thresholds
QUALITY_THRESHOLDS = {
    "resolution_min": 640,  # Minimum dimension
    "resolution_good": 1024,
    "blur_threshold": 100,  # Laplacian variance
    "stripe_visibility_min": 0.5,
    "detection_confidence_min": 0.7,
}


@SkillRegistry.register
class ImageAdvisorSkill(BaseSkill):
    """
    Skill for advising users on image quality for tiger identification.

    Provides user-friendly feedback on:
    - Resolution and clarity
    - Stripe pattern visibility
    - Pose angle suitability
    - Lighting conditions
    - Suggestions for better images

    Command: /assess-image
    """

    def __init__(self):
        """Initialize the image advisor skill."""
        super().__init__()
        self._chat_model = None

    def get_definition(self) -> SkillDefinition:
        """Return skill definition."""
        return SkillDefinition(
            name="Image Quality Advisor",
            description="Advise on image quality and suggest improvements",
            command="/assess-image",
            category=SkillCategory.QUALITY,
            parameters=[
                SkillParameter(
                    name="quality_metrics",
                    description="Computed quality metrics from image analysis",
                    type="object",
                    required=True
                ),
                SkillParameter(
                    name="detection_results",
                    description="Tiger detection results if available",
                    type="object",
                    required=False,
                    default={}
                ),
                SkillParameter(
                    name="user_context",
                    description="Any context provided by the user",
                    type="string",
                    required=False,
                    default=""
                )
            ],
            examples=[
                "/assess-image (after image analysis)",
                "/assess-image --context 'photo taken at night'"
            ]
        )

    def get_prompt_template(self) -> str:
        """Return the prompt template."""
        return """You are advising a user on their tiger image quality for identification.

## Image Analysis Results
{quality_metrics_formatted}

## Detection Results
{detection_results_formatted}

## User Context
{user_context}

## Quality Thresholds Reference
- Minimum resolution: {resolution_min}px (shorter dimension)
- Good resolution: {resolution_good}px+
- Minimum detection confidence: {detection_min:.0%}
- Stripe visibility minimum: {stripe_min:.0%}

## Your Task
Provide helpful, constructive feedback on:

1. **Overall Suitability** (0-100%)
   - Can this image produce reliable identification?
   - If not, why not?

2. **Specific Issues Found**
   - Resolution problems
   - Lighting issues
   - Unfavorable angle/pose
   - Stripe pattern visibility
   - Motion blur or focus problems
   - Potential image manipulation

3. **Impact on Accuracy**
   - How do these issues affect identification reliability?
   - Which issues are most critical?

4. **Actionable Suggestions**
   - Specific tips for getting better images
   - What would make this image usable?

5. **Recommendation**
   - Proceed with current image?
   - Request a new image?
   - Proceed with warnings?

## Response Style
- Be helpful and constructive, not discouraging
- Explain WHY certain issues matter for tiger ID
- Provide specific, actionable tips
- Acknowledge what IS good about the image
- Use simple, non-technical language where possible

## Output Format
Respond in JSON:

```json
{{
    "overall_score": <0-100>,
    "recommendation": "<proceed|proceed_with_caution|request_new_image>",
    "issues": [
        {{
            "issue": "<issue name>",
            "severity": "<low|medium|high|critical>",
            "impact": "<how this affects identification>",
            "suggestion": "<how to fix or work around>"
        }}
    ],
    "strengths": ["<positive aspect 1>", "<positive aspect 2>"],
    "tips_for_better_images": ["<tip 1>", "<tip 2>"],
    "user_message": "<friendly summary message to display to user>"
}}
```"""

    async def execute(
        self,
        context: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute the image advisor skill.

        Args:
            context: Dictionary containing:
                - quality_metrics: Computed quality metrics
                - detection_results: Optional detection results
                - user_context: Optional user-provided context

        Returns:
            Dictionary with image quality advice
        """
        errors = self.validate_context(context)
        if errors:
            return {
                "success": False,
                "error": f"Validation failed: {'; '.join(errors)}",
                "output": None
            }

        try:
            quality_metrics = context.get("quality_metrics", {})
            detection_results = context.get("detection_results", {})
            user_context = context.get("user_context", "")

            # Format inputs
            quality_metrics_formatted = self._format_quality_metrics(quality_metrics)
            detection_results_formatted = self._format_detection_results(detection_results)

            # Build prompt
            prompt = self.build_prompt({
                "quality_metrics_formatted": quality_metrics_formatted,
                "detection_results_formatted": detection_results_formatted,
                "user_context": user_context or "None provided",
                "resolution_min": QUALITY_THRESHOLDS["resolution_min"],
                "resolution_good": QUALITY_THRESHOLDS["resolution_good"],
                "detection_min": QUALITY_THRESHOLDS["detection_confidence_min"],
                "stripe_min": QUALITY_THRESHOLDS["stripe_visibility_min"]
            })

            if not self._chat_model:
                self._chat_model = AnthropicChatModel(model_name="claude-sonnet-4-5-20250929")

            logger.info("Generating image quality advice")
            response = await self._chat_model.chat(
                message=prompt,
                system_prompt="You are a helpful image quality advisor. Be constructive and encouraging. Respond only with valid JSON."
            )

            if not response.get("success"):
                return {
                    "success": False,
                    "error": response.get("error", "Unknown error"),
                    "output": None
                }

            return {
                "success": True,
                "output": response.get("response", ""),
                "metadata": {
                    "quality_metrics": quality_metrics,
                    "has_detection": bool(detection_results)
                }
            }

        except Exception as e:
            logger.error(f"Image advisor failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "output": None
            }

    def _format_quality_metrics(self, metrics: Dict) -> str:
        """Format quality metrics for the prompt."""
        if not metrics:
            return "No quality metrics available."

        formatted = []
        for key, value in metrics.items():
            label = key.replace("_", " ").title()
            if isinstance(value, float) and 0 <= value <= 1:
                formatted.append(f"- {label}: {value:.1%}")
            else:
                formatted.append(f"- {label}: {value}")

        return "\n".join(formatted)

    def _format_detection_results(self, results: Dict) -> str:
        """Format detection results for the prompt."""
        if not results:
            return "No detection performed yet."

        formatted = []
        if "detections" in results:
            formatted.append(f"Tigers detected: {len(results['detections'])}")
            for i, det in enumerate(results["detections"], 1):
                formatted.append(f"  Detection {i}:")
                formatted.append(f"    - Confidence: {det.get('confidence', 0):.1%}")
                formatted.append(f"    - Bounding box: {det.get('bbox', 'N/A')}")

        if "image_size" in results:
            formatted.append(f"Image size: {results['image_size']}")

        return "\n".join(formatted) if formatted else "Detection results empty."


def compute_basic_quality_score(metrics: Dict) -> Dict[str, Any]:
    """
    Compute a basic quality score from metrics without Claude.

    This can be used for quick filtering before full analysis.
    """
    score = 100
    issues = []

    # Resolution check
    if "resolution" in metrics:
        res = min(metrics["resolution"]) if isinstance(metrics["resolution"], (list, tuple)) else metrics["resolution"]
        if res < QUALITY_THRESHOLDS["resolution_min"]:
            score -= 30
            issues.append("Resolution too low")
        elif res < QUALITY_THRESHOLDS["resolution_good"]:
            score -= 10
            issues.append("Resolution below ideal")

    # Blur check
    if "blur_score" in metrics:
        if metrics["blur_score"] < QUALITY_THRESHOLDS["blur_threshold"]:
            score -= 25
            issues.append("Image appears blurry")

    # Detection confidence
    if "detection_confidence" in metrics:
        if metrics["detection_confidence"] < QUALITY_THRESHOLDS["detection_confidence_min"]:
            score -= 20
            issues.append("Low detection confidence")

    # Stripe visibility
    if "stripe_visibility" in metrics:
        if metrics["stripe_visibility"] < QUALITY_THRESHOLDS["stripe_visibility_min"]:
            score -= 20
            issues.append("Stripe pattern not clearly visible")

    return {
        "score": max(0, score),
        "issues": issues,
        "recommendation": "proceed" if score >= 70 else "proceed_with_caution" if score >= 50 else "request_new_image"
    }
