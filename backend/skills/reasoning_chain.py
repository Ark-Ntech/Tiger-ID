"""
Chain-of-Thought Reasoning Skill

Exposes Claude's reasoning process for investigation decisions.
Generates transparent, step-by-step reasoning with evidence citations.
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum
import json

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


class DecisionType(str, Enum):
    """Types of decisions that can be explained."""
    IDENTIFICATION = "identification"
    LOCATION = "location"
    CONFIDENCE = "confidence"
    RECOMMENDATION = "recommendation"
    MATCH_SELECTION = "match_selection"
    QUALITY_ASSESSMENT = "quality_assessment"


@dataclass
class ReasoningStep:
    """A single step in the reasoning chain."""
    step_number: int
    action: str
    evidence: List[str]
    reasoning: str
    conclusion: str
    confidence: int  # 0-100

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "step": self.step_number,
            "action": self.action,
            "evidence": self.evidence,
            "reasoning": self.reasoning,
            "conclusion": self.conclusion,
            "confidence": self.confidence
        }


@dataclass
class ReasoningChain:
    """Complete reasoning chain for a decision."""
    decision_type: DecisionType
    question: str
    steps: List[ReasoningStep] = field(default_factory=list)
    final_conclusion: str = ""
    overall_confidence: int = 0

    def add_step(self, step: ReasoningStep):
        """Add a step to the chain."""
        self.steps.append(step)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "decision_type": self.decision_type.value,
            "question": self.question,
            "steps": [s.to_dict() for s in self.steps],
            "final_conclusion": self.final_conclusion,
            "overall_confidence": self.overall_confidence,
            "step_count": len(self.steps)
        }


@SkillRegistry.register
class ReasoningChainSkill(BaseSkill):
    """
    Skill for generating transparent chain-of-thought reasoning.

    Exposes Claude's decision process for investigation decisions,
    creating auditable methodology documentation.

    Command: /explain-reasoning
    """

    def __init__(self):
        """Initialize the reasoning chain skill."""
        super().__init__()
        self._chat_model = None

    def get_definition(self) -> SkillDefinition:
        """Return skill definition."""
        return SkillDefinition(
            name="Chain-of-Thought Reasoning",
            description="Generate transparent step-by-step reasoning for investigation decisions",
            command="/explain-reasoning",
            category=SkillCategory.REASONING,
            parameters=[
                SkillParameter(
                    name="decision_type",
                    description="Type of decision being made",
                    type="string",
                    required=True,
                    enum=[d.value for d in DecisionType]
                ),
                SkillParameter(
                    name="context",
                    description="Context and data relevant to the decision",
                    type="object",
                    required=True
                ),
                SkillParameter(
                    name="evidence",
                    description="List of evidence items to consider",
                    type="array",
                    required=False,
                    default=[]
                ),
                SkillParameter(
                    name="require_citations",
                    description="Whether to require citations for each step",
                    type="boolean",
                    required=False,
                    default=True
                )
            ],
            examples=[
                "/explain-reasoning identification --context {...}",
                "/explain-reasoning match_selection --evidence [...]"
            ]
        )

    def get_prompt_template(self) -> str:
        """Return the prompt template."""
        return """You are documenting your reasoning process for a tiger identification investigation.

## Decision Being Made
**Type:** {decision_type}
**Question:** {question}

## Available Evidence
{evidence_formatted}

## Context
{context_formatted}

## Reasoning Requirements
Generate a transparent chain of reasoning following this exact structure:

For each step, address:
1. What evidence supports the conclusion?
2. What evidence contradicts the conclusion?
3. How was conflicting evidence resolved?
4. What assumptions were made?
5. What is the confidence level and why?

## Citation Requirements
{citation_requirements}

## Output Format
Provide your reasoning chain in the following JSON structure:

```json
{{
    "decision_type": "{decision_type}",
    "question": "{question}",
    "steps": [
        {{
            "step": 1,
            "action": "<What was done in this step>",
            "evidence": ["<evidence item 1>", "<evidence item 2>"],
            "reasoning": "<Why this matters and how it was interpreted>",
            "conclusion": "<What was determined from this step>",
            "confidence": <0-100>
        }}
    ],
    "final_conclusion": "<Overall conclusion reached>",
    "overall_confidence": <0-100>,
    "supporting_factors": ["<factor 1>", "<factor 2>"],
    "uncertainty_factors": ["<uncertainty 1>", "<uncertainty 2>"],
    "assumptions_made": ["<assumption 1>", "<assumption 2>"]
}}
```

## Decision-Specific Guidance
{decision_guidance}

Generate a thorough reasoning chain with at least 3-5 steps for non-trivial decisions."""

    async def execute(
        self,
        context: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute the reasoning chain skill.

        Args:
            context: Dictionary containing:
                - decision_type: Type of decision
                - context: Decision context data
                - evidence: List of evidence items
                - require_citations: Whether to require citations

        Returns:
            Dictionary with reasoning chain
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
            decision_type = context.get("decision_type", "identification")
            decision_context = context.get("context", {})
            evidence = context.get("evidence", [])
            require_citations = context.get("require_citations", True)

            # Generate question from decision type
            question = self._generate_question(decision_type, decision_context)

            # Format inputs
            evidence_formatted = self._format_evidence(evidence)
            context_formatted = self._format_context(decision_context)
            citation_requirements = self._get_citation_requirements(require_citations)
            decision_guidance = self._get_decision_guidance(decision_type)

            # Build the prompt
            prompt = self.build_prompt({
                "decision_type": decision_type,
                "question": question,
                "evidence_formatted": evidence_formatted,
                "context_formatted": context_formatted,
                "citation_requirements": citation_requirements,
                "decision_guidance": decision_guidance
            })

            # Get or create chat model
            if not self._chat_model:
                self._chat_model = AnthropicChatModel(model_name="claude-sonnet-4-5-20250929")

            # Execute with Claude
            logger.info(f"Generating reasoning chain for {decision_type} decision")
            response = await self._chat_model.chat(
                message=prompt,
                system_prompt="You are a methodical forensic analyst. Generate detailed reasoning chains. Respond only with valid JSON."
            )

            if not response.get("success"):
                return {
                    "success": False,
                    "error": response.get("error", "Unknown error from Claude"),
                    "output": None
                }

            # Parse and validate response
            output = response.get("response", "")

            return {
                "success": True,
                "output": output,
                "metadata": {
                    "decision_type": decision_type,
                    "question": question,
                    "evidence_count": len(evidence),
                    "citations_required": require_citations
                }
            }

        except Exception as e:
            logger.error(f"Reasoning chain generation failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "output": None
            }

    def _generate_question(self, decision_type: str, context: Dict) -> str:
        """Generate a question based on decision type and context."""
        questions = {
            "identification": "Is this tiger the same individual as the database match?",
            "location": "Where is this tiger most likely located?",
            "confidence": "How confident can we be in this identification?",
            "recommendation": "What actions should be taken based on these findings?",
            "match_selection": "Which database match is the most likely true match?",
            "quality_assessment": "Is this image suitable for reliable identification?"
        }

        base_question = questions.get(decision_type, "What conclusion should be drawn?")

        # Customize based on context
        if "tiger_name" in context:
            base_question = base_question.replace("this tiger", f"{context['tiger_name']}")
        if "facility_name" in context:
            base_question += f" (Facility: {context['facility_name']})"

        return base_question

    def _format_evidence(self, evidence: List) -> str:
        """Format evidence items for the prompt."""
        if not evidence:
            return "No specific evidence items provided. Use context data."

        formatted = []
        for i, item in enumerate(evidence, 1):
            if isinstance(item, dict):
                formatted.append(f"""
**Evidence {i}:** {item.get('type', 'Unknown type')}
- Source: {item.get('source', 'Unknown')}
- Content: {item.get('content', 'N/A')}
- Confidence: {item.get('confidence', 'N/A')}
""")
            else:
                formatted.append(f"**Evidence {i}:** {item}")

        return "\n".join(formatted)

    def _format_context(self, context: Dict) -> str:
        """Format context data for the prompt."""
        if not context:
            return "No additional context provided."

        formatted = []
        for key, value in context.items():
            if isinstance(value, dict):
                formatted.append(f"**{key.replace('_', ' ').title()}:**")
                for k, v in value.items():
                    formatted.append(f"  - {k}: {v}")
            elif isinstance(value, list):
                formatted.append(f"**{key.replace('_', ' ').title()}:** {', '.join(str(v) for v in value)}")
            else:
                formatted.append(f"**{key.replace('_', ' ').title()}:** {value}")

        return "\n".join(formatted)

    def _get_citation_requirements(self, require_citations: bool) -> str:
        """Get citation requirement instructions."""
        if require_citations:
            return """
**Citations Required:** Each reasoning step must cite specific evidence.
- Reference evidence by number (e.g., "Evidence 1")
- Include source URLs where available
- Note confidence level of cited evidence
"""
        else:
            return """
**Citations Optional:** Evidence references are helpful but not required.
Focus on clear logical reasoning.
"""

    def _get_decision_guidance(self, decision_type: str) -> str:
        """Get decision-specific guidance."""
        guidance = {
            "identification": """
**Identification Decision Guidance:**
- Compare stripe patterns systematically
- Consider viewpoint/pose differences
- Account for lighting and image quality
- Check for distinctive markings (scars, ear notches)
- Consider temporal changes if dates differ significantly
""",
            "location": """
**Location Decision Guidance:**
- Prioritize EXIF GPS data if available
- Cross-reference with known facility locations
- Consider web intelligence sources
- Account for user-provided context
- Note confidence hierarchy (EXIF > Database > User > Web)
""",
            "confidence": """
**Confidence Assessment Guidance:**
- Consider model consensus (how many models agree)
- Weight by model accuracy (wildlife_tools > cvwc2019 > transreid > tiger_reid)
- Factor in image quality
- Account for corroborating evidence
- Note any contradictions that reduce confidence
""",
            "recommendation": """
**Recommendation Decision Guidance:**
- Consider urgency based on welfare concerns
- Suggest appropriate authorities (USFWS, state wildlife agency)
- Recommend evidence preservation steps
- Propose follow-up investigation actions
- Consider legal implications
""",
            "match_selection": """
**Match Selection Guidance:**
- Compare similarity scores across models
- Consider model weights in ensemble
- Check for k-reciprocal re-ranking effects
- Verify location consistency
- Look for temporal patterns
""",
            "quality_assessment": """
**Quality Assessment Guidance:**
- Check resolution and clarity
- Assess stripe pattern visibility
- Consider pose angle (flank views preferred)
- Evaluate lighting conditions
- Detect potential image manipulation
"""
        }

        return guidance.get(decision_type, "Apply standard analytical reasoning.")


# Helper functions for external use

async def generate_reasoning_step(
    phase: str,
    action: str,
    evidence: List[str],
    conclusion: str,
    confidence: int
) -> Dict[str, Any]:
    """
    Helper to generate a single reasoning step.

    This can be called from workflow nodes to add methodology tracking.
    """
    return {
        "step": 0,  # Will be numbered by caller
        "phase": phase,
        "action": action,
        "evidence": evidence,
        "reasoning": f"Based on {len(evidence)} piece(s) of evidence from {phase}",
        "conclusion": conclusion,
        "confidence": confidence
    }
