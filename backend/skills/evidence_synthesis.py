"""
Evidence Synthesis Skill

Combines evidence from multiple sources with weighted confidence scoring.
Integrates with ML pipeline model weights for accurate confidence calculation.
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass

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


# Model weights from ML pipeline (coordinates with ML improvement plan)
MODEL_WEIGHTS = {
    "wildlife_tools": 0.40,    # Best individual performer
    "cvwc2019_reid": 0.30,     # Part-based (after fix)
    "transreid": 0.20,         # ViT features (new)
    "tiger_reid": 0.10,        # Baseline
    "rapid_reid": 0.10,        # Edge-optimized (fallback)
}

# Source reliability hierarchy
SOURCE_RELIABILITY = {
    "exif_gps": 1.0,           # Most reliable - direct from image
    "database_match": 0.9,      # High - verified database records
    "visual_analysis": 0.8,     # Good - Claude/model analysis
    "user_context": 0.7,        # Moderate - user-provided info
    "web_intelligence": 0.6,    # Lower - web search results
    "external_api": 0.5,        # Variable - external data sources
}


@dataclass
class EvidenceSource:
    """Represents a single piece of evidence."""
    source_type: str
    content: Dict[str, Any]
    confidence: float
    url: Optional[str] = None
    timestamp: Optional[str] = None


@SkillRegistry.register
class EvidenceSynthesisSkill(BaseSkill):
    """
    Skill for synthesizing evidence from multiple sources.

    Combines evidence with weighted confidence scoring based on:
    1. Source reliability (EXIF GPS > Database > Visual Analysis > Web)
    2. Model weights (wildlife_tools > cvwc2019 > transreid > tiger_reid)
    3. Corroboration across sources
    4. Contradiction detection

    Command: /synthesize-evidence
    """

    def __init__(self):
        """Initialize the evidence synthesis skill."""
        super().__init__()
        self._chat_model = None

    def get_definition(self) -> SkillDefinition:
        """Return skill definition."""
        return SkillDefinition(
            name="Evidence Synthesis",
            description="Combine evidence from multiple sources with weighted confidence scoring",
            command="/synthesize-evidence",
            category=SkillCategory.ANALYSIS,
            parameters=[
                SkillParameter(
                    name="sources",
                    description="List of evidence sources to synthesize",
                    type="array",
                    required=True
                ),
                SkillParameter(
                    name="model_results",
                    description="Results from ReID models with similarity scores",
                    type="object",
                    required=False
                ),
                SkillParameter(
                    name="focus_areas",
                    description="Specific areas to focus synthesis on",
                    type="array",
                    required=False,
                    default=["identification", "location", "provenance"]
                ),
                SkillParameter(
                    name="synthesis_mode",
                    description="How aggressive to be in combining evidence",
                    type="string",
                    required=False,
                    default="balanced",
                    enum=["conservative", "balanced", "aggressive"]
                )
            ],
            examples=[
                "/synthesize-evidence (with investigation context)",
                "/synthesize-evidence --mode conservative"
            ]
        )

    def get_prompt_template(self) -> str:
        """Return the prompt template."""
        return """You are an expert wildlife forensics analyst specializing in tiger identification and trafficking investigations.

## Task
Synthesize the following evidence sources into a coherent assessment of tiger identification confidence.

## Evidence Sources
{sources_formatted}

## Model Matching Results
{model_results_formatted}

## Source Reliability Hierarchy
- EXIF GPS data: Highest reliability (direct from image metadata)
- Database matches: High reliability (verified records)
- Visual analysis: Good reliability (AI model analysis)
- User-provided context: Moderate reliability
- Web intelligence: Lower reliability (requires verification)

## Model Weight Distribution
{model_weights_formatted}

## Synthesis Mode: {synthesis_mode}
{synthesis_mode_instructions}

## Synthesis Requirements
1. Weight each source by reliability using the hierarchy above
2. Apply model weights to ReID matching results
3. Identify corroborating evidence across sources
4. Flag any contradictions or inconsistencies
5. Calculate an overall confidence score (0-100%)
6. Provide clear reasoning for the confidence assessment

## Focus Areas
{focus_areas}

## Output Format
Provide your synthesis in the following JSON structure:

```json
{{
    "confidence_score": <0-100>,
    "confidence_level": "<low|medium|high|very_high>",
    "primary_evidence": [
        {{
            "source_type": "<type>",
            "key_finding": "<finding>",
            "reliability": <0-1>
        }}
    ],
    "corroborating_evidence": [
        {{
            "finding": "<what was corroborated>",
            "sources": ["<source1>", "<source2>"]
        }}
    ],
    "contradictions": [
        {{
            "issue": "<what contradicts>",
            "sources": ["<source1>", "<source2>"],
            "resolution": "<how resolved or why unresolved>"
        }}
    ],
    "model_consensus": {{
        "agreeing_models": <count>,
        "total_models": <count>,
        "weighted_similarity": <0-1>,
        "top_match": {{
            "tiger_id": "<id>",
            "tiger_name": "<name>",
            "confidence": <0-1>
        }}
    }},
    "reasoning": "<step-by-step justification for confidence score>",
    "recommendations": ["<action1>", "<action2>"]
}}
```"""

    async def execute(
        self,
        context: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute the evidence synthesis skill.

        Args:
            context: Dictionary containing:
                - sources: List of evidence sources
                - model_results: Optional ReID model results
                - focus_areas: Optional list of focus areas
                - synthesis_mode: Optional mode (conservative/balanced/aggressive)

        Returns:
            Dictionary with synthesis results
        """
        # Validate context
        errors = self.validate_context(context)
        if errors:
            return {
                "success": False,
                "error": f"Validation failed: {'; '.join(errors)}",
                "output": None
            }

        try:
            # Extract parameters
            sources = context.get("sources", [])
            model_results = context.get("model_results", {})
            focus_areas = context.get("focus_areas", ["identification", "location", "provenance"])
            synthesis_mode = context.get("synthesis_mode", "balanced")

            # Format sources for prompt
            sources_formatted = self._format_sources(sources)
            model_results_formatted = self._format_model_results(model_results)
            model_weights_formatted = self._format_model_weights()
            synthesis_mode_instructions = self._get_synthesis_instructions(synthesis_mode)

            # Build the prompt
            prompt = self.build_prompt({
                "sources_formatted": sources_formatted,
                "model_results_formatted": model_results_formatted,
                "model_weights_formatted": model_weights_formatted,
                "synthesis_mode": synthesis_mode,
                "synthesis_mode_instructions": synthesis_mode_instructions,
                "focus_areas": ", ".join(focus_areas)
            })

            # Get or create chat model
            if not self._chat_model:
                self._chat_model = AnthropicChatModel(model_name="claude-sonnet-4-5-20250929")

            # Execute with Claude
            logger.info(f"Executing evidence synthesis with {len(sources)} sources")
            response = await self._chat_model.chat(
                message=prompt,
                system_prompt="You are an expert wildlife forensics analyst. Respond only with valid JSON."
            )

            if not response.get("success"):
                return {
                    "success": False,
                    "error": response.get("error", "Unknown error from Claude"),
                    "output": None
                }

            # Parse response
            output = response.get("response", "")

            # Calculate pre-computed metrics for validation
            pre_computed = self._compute_metrics(sources, model_results)

            return {
                "success": True,
                "output": output,
                "metadata": {
                    "sources_count": len(sources),
                    "models_used": list(model_results.keys()),
                    "synthesis_mode": synthesis_mode,
                    "pre_computed_metrics": pre_computed
                }
            }

        except Exception as e:
            logger.error(f"Evidence synthesis failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "output": None
            }

    def _format_sources(self, sources: List[Dict]) -> str:
        """Format evidence sources for the prompt."""
        if not sources:
            return "No evidence sources provided."

        formatted = []
        for i, source in enumerate(sources, 1):
            source_type = source.get("source_type", "unknown")
            reliability = SOURCE_RELIABILITY.get(source_type, 0.5)

            formatted.append(f"""
### Source {i}: {source_type.replace('_', ' ').title()}
- Reliability Weight: {reliability:.1%}
- Content: {source.get('content', 'N/A')}
- Confidence: {source.get('confidence', 'N/A')}
- URL/Reference: {source.get('url', 'N/A')}
""")

        return "\n".join(formatted)

    def _format_model_results(self, model_results: Dict) -> str:
        """Format ReID model results for the prompt."""
        if not model_results:
            return "No model matching results available."

        formatted = []
        for model_name, results in model_results.items():
            weight = MODEL_WEIGHTS.get(model_name, 0.1)
            matches = results.get("matches", [])

            formatted.append(f"""
### {model_name.replace('_', ' ').title()}
- Weight: {weight:.0%}
- Top Matches:""")

            for match in matches[:3]:  # Top 3 matches
                formatted.append(f"""
  - Tiger: {match.get('tiger_name', 'Unknown')} (ID: {match.get('tiger_id', 'N/A')})
  - Similarity: {match.get('similarity', 0):.2%}
  - Facility: {match.get('facility_name', 'Unknown')}
""")

        return "\n".join(formatted)

    def _format_model_weights(self) -> str:
        """Format model weights for the prompt."""
        lines = ["(Weights sum to 1.0 for weighted ensemble)"]
        for model, weight in sorted(MODEL_WEIGHTS.items(), key=lambda x: -x[1]):
            lines.append(f"- {model}: {weight:.0%}")
        return "\n".join(lines)

    def _get_synthesis_instructions(self, mode: str) -> str:
        """Get synthesis mode-specific instructions."""
        instructions = {
            "conservative": """
Conservative mode: Be very cautious with conclusions.
- Require corroboration from multiple high-reliability sources
- Flag any uncertainty prominently
- Prefer lower confidence scores when evidence is ambiguous
- Recommend additional investigation for uncertain findings
""",
            "balanced": """
Balanced mode: Standard evidence weighting.
- Use reliability hierarchy as defined
- Accept single high-reliability sources for key findings
- Weight contradictions appropriately
- Provide nuanced confidence assessment
""",
            "aggressive": """
Aggressive mode: Accept weaker evidence for faster conclusions.
- Lower threshold for accepting evidence
- Weight web intelligence higher
- Accept single-source findings more readily
- Provide action-oriented recommendations
"""
        }
        return instructions.get(mode, instructions["balanced"])

    def _compute_metrics(
        self,
        sources: List[Dict],
        model_results: Dict
    ) -> Dict[str, Any]:
        """Pre-compute metrics for validation."""
        # Count sources by type
        source_counts = {}
        for source in sources:
            stype = source.get("source_type", "unknown")
            source_counts[stype] = source_counts.get(stype, 0) + 1

        # Calculate weighted similarity from models
        weighted_sim = 0.0
        total_weight = 0.0
        agreeing_models = 0

        for model_name, results in model_results.items():
            weight = MODEL_WEIGHTS.get(model_name, 0.1)
            matches = results.get("matches", [])

            if matches:
                top_sim = matches[0].get("similarity", 0)
                weighted_sim += weight * top_sim
                total_weight += weight

                if top_sim >= 0.8:  # Agreement threshold
                    agreeing_models += 1

        if total_weight > 0:
            weighted_sim /= total_weight

        return {
            "source_counts": source_counts,
            "total_sources": len(sources),
            "models_count": len(model_results),
            "agreeing_models": agreeing_models,
            "weighted_similarity": weighted_sim
        }
