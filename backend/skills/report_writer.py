"""
Multi-Audience Report Writer Skill

Generates investigation reports tailored to different audiences:
- Law Enforcement: Formal, citations, legal focus
- Conservation: Welfare-focused, actionable
- Internal: Technical, debug-level details
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

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


class ReportAudience(str, Enum):
    """Target audience for reports."""
    LAW_ENFORCEMENT = "law_enforcement"
    CONSERVATION = "conservation"
    INTERNAL = "internal"
    PUBLIC = "public"


class ReportFormat(str, Enum):
    """Output format for reports."""
    MARKDOWN = "markdown"
    JSON = "json"
    PDF = "pdf"


@dataclass
class ReportSection:
    """Definition of a report section."""
    name: str
    required: bool
    description: str


# Section requirements by audience
AUDIENCE_SECTIONS: Dict[ReportAudience, List[ReportSection]] = {
    ReportAudience.LAW_ENFORCEMENT: [
        ReportSection("Executive Summary", True, "Brief overview of findings"),
        ReportSection("Subject Identification", True, "Tiger details and confidence"),
        ReportSection("Evidence Chain", True, "Numbered evidence with citations"),
        ReportSection("Methodology", True, "How identification was made"),
        ReportSection("Location Intelligence", True, "Where tiger is/was located"),
        ReportSection("Facility Information", False, "Owner/facility details if applicable"),
        ReportSection("Potential Violations", True, "Specific laws/regulations"),
        ReportSection("Recommended Actions", True, "Suggested next steps"),
        ReportSection("Appendices", False, "Supporting images and data"),
    ],
    ReportAudience.CONSERVATION: [
        ReportSection("Tiger Overview", True, "Identity and history"),
        ReportSection("Current Status", True, "Welfare and conditions"),
        ReportSection("Facility Assessment", True, "Care standards evaluation"),
        ReportSection("Historical Context", True, "Previous locations, transfers"),
        ReportSection("Conservation Implications", True, "Species impact"),
        ReportSection("Recommendations", True, "Welfare-focused actions"),
        ReportSection("Urgency Assessment", True, "Priority level"),
    ],
    ReportAudience.INTERNAL: [
        ReportSection("Investigation Summary", True, "Overview of results"),
        ReportSection("Model Performance", True, "Which models matched, scores"),
        ReportSection("Data Quality", True, "Image quality, metadata completeness"),
        ReportSection("Pipeline Details", True, "Execution steps, timing"),
        ReportSection("Reasoning Chain", True, "Full methodology documentation"),
        ReportSection("Errors and Warnings", False, "Any issues encountered"),
        ReportSection("System Recommendations", False, "Improvement suggestions"),
    ],
    ReportAudience.PUBLIC: [
        ReportSection("Summary", True, "Non-technical overview"),
        ReportSection("Key Findings", True, "Main discoveries"),
        ReportSection("About the Tiger", False, "Background if known"),
        ReportSection("What This Means", True, "Plain-language explanation"),
    ],
}


@SkillRegistry.register
class ReportWriterSkill(BaseSkill):
    """
    Skill for generating audience-specific investigation reports.

    Produces professional reports tailored to:
    - Law Enforcement: Formal, evidential, legal citations
    - Conservation: Welfare-focused, conservation impact
    - Internal: Technical details, system performance
    - Public: Non-technical summary

    Command: /generate-report <audience>
    """

    def __init__(self):
        """Initialize the report writer skill."""
        super().__init__()
        self._chat_model = None

    def get_definition(self) -> SkillDefinition:
        """Return skill definition."""
        return SkillDefinition(
            name="Expert Report Writer",
            description="Generate audience-specific investigation reports",
            command="/generate-report",
            category=SkillCategory.REPORTING,
            parameters=[
                SkillParameter(
                    name="audience",
                    description="Target audience for the report",
                    type="string",
                    required=True,
                    enum=[a.value for a in ReportAudience]
                ),
                SkillParameter(
                    name="investigation_data",
                    description="Complete investigation data to report on",
                    type="object",
                    required=True
                ),
                SkillParameter(
                    name="format",
                    description="Output format",
                    type="string",
                    required=False,
                    default="markdown",
                    enum=[f.value for f in ReportFormat]
                ),
                SkillParameter(
                    name="include_appendices",
                    description="Whether to include appendices",
                    type="boolean",
                    required=False,
                    default=True
                ),
                SkillParameter(
                    name="classification",
                    description="Report classification level",
                    type="string",
                    required=False,
                    default="restricted",
                    enum=["public", "restricted", "confidential"]
                )
            ],
            examples=[
                "/generate-report law_enforcement",
                "/generate-report conservation --format pdf",
                "/generate-report internal --include-appendices false"
            ]
        )

    def get_prompt_template(self) -> str:
        """Return the base prompt template."""
        return """You are an expert report writer for wildlife trafficking investigations.

## Report Parameters
**Audience:** {audience}
**Format:** {format}
**Classification:** {classification}
**Date:** {report_date}

## Investigation Data
{investigation_data_formatted}

## Required Sections
{required_sections}

## Audience-Specific Guidelines
{audience_guidelines}

## Writing Guidelines
- Use formal, professional language
- Be precise and factual
- Cite sources for all claims
- Include confidence levels where applicable
- Organize information logically
- Use clear headings and structure

## Output Format
{format_instructions}"""

    async def execute(
        self,
        context: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute the report writer skill.

        Args:
            context: Dictionary containing:
                - audience: Target audience
                - investigation_data: Data to report on
                - format: Output format
                - include_appendices: Whether to include appendices
                - classification: Report classification

        Returns:
            Dictionary with generated report
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
            audience = ReportAudience(context.get("audience", "internal"))
            investigation_data = context.get("investigation_data", {})
            format_type = context.get("format", "markdown")
            include_appendices = context.get("include_appendices", True)
            classification = context.get("classification", "restricted")

            # Get audience-specific content
            required_sections = self._get_required_sections(audience, include_appendices)
            audience_guidelines = self._get_audience_guidelines(audience)
            format_instructions = self._get_format_instructions(format_type)

            # Format investigation data
            investigation_data_formatted = self._format_investigation_data(
                investigation_data, audience
            )

            # Build the prompt
            prompt = self.build_prompt({
                "audience": audience.value.replace("_", " ").title(),
                "format": format_type,
                "classification": classification.upper(),
                "report_date": datetime.now().strftime("%Y-%m-%d"),
                "investigation_data_formatted": investigation_data_formatted,
                "required_sections": required_sections,
                "audience_guidelines": audience_guidelines,
                "format_instructions": format_instructions
            })

            # Get or create chat model (use quality model for reports)
            if not self._chat_model:
                self._chat_model = AnthropicChatModel(model_name="claude-opus-4-5-20251101")

            # Execute with Claude
            logger.info(f"Generating {audience.value} report in {format_type} format")
            response = await self._chat_model.chat(
                message=prompt,
                system_prompt=f"You are a professional report writer. Generate a formal {audience.value.replace('_', ' ')} report."
            )

            if not response.get("success"):
                return {
                    "success": False,
                    "error": response.get("error", "Unknown error from Claude"),
                    "output": None
                }

            output = response.get("response", "")

            return {
                "success": True,
                "output": output,
                "metadata": {
                    "audience": audience.value,
                    "format": format_type,
                    "classification": classification,
                    "generated_at": datetime.now().isoformat(),
                    "sections_included": [s.name for s in AUDIENCE_SECTIONS[audience]]
                }
            }

        except Exception as e:
            logger.error(f"Report generation failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "output": None
            }

    def _get_required_sections(
        self,
        audience: ReportAudience,
        include_appendices: bool
    ) -> str:
        """Get required sections for audience."""
        sections = AUDIENCE_SECTIONS.get(audience, [])

        formatted = []
        for section in sections:
            if section.name == "Appendices" and not include_appendices:
                continue

            req_text = "REQUIRED" if section.required else "OPTIONAL"
            formatted.append(f"- **{section.name}** ({req_text}): {section.description}")

        return "\n".join(formatted)

    def _get_audience_guidelines(self, audience: ReportAudience) -> str:
        """Get audience-specific writing guidelines."""
        guidelines = {
            ReportAudience.LAW_ENFORCEMENT: """
**Law Enforcement Report Guidelines:**
- Use formal, objective language suitable for legal proceedings
- Cite all evidence sources with URLs and access dates
- Include confidence levels for all assertions (percentage)
- Reference specific regulations: Endangered Species Act (ESA), Lacey Act, CITES
- Structure evidence chain with numbered items
- Avoid speculation; distinguish facts from allegations
- Include chain of custody considerations
- Note any limitations in the evidence
- Provide specific, actionable recommendations
- Format for potential court submission
""",
            ReportAudience.CONSERVATION: """
**Conservation Report Guidelines:**
- Focus on animal welfare implications
- Use accessible language (avoid excessive jargon)
- Emphasize conservation impact and urgency
- Include historical context for the tiger
- Assess facility conditions objectively
- Recommend welfare-focused interventions
- Consider species-level implications
- Note positive findings as well as concerns
- Suggest monitoring or follow-up needs
- Avoid legal terminology (redirect to law enforcement if needed)
""",
            ReportAudience.INTERNAL: """
**Internal Technical Report Guidelines:**
- Include full technical details
- Document all model performance metrics
- Show confidence scores for each matching model
- Include weighted ensemble calculations
- Document any calibration applied
- Note k-reciprocal re-ranking effects if used
- Include timing/performance data
- Log any errors or warnings
- Suggest system improvements
- Include raw data references for debugging
""",
            ReportAudience.PUBLIC: """
**Public Report Guidelines:**
- Use plain, accessible language
- Avoid technical jargon
- Focus on key takeaways
- Do not include sensitive location data
- Protect individual privacy where applicable
- Emphasize positive conservation outcomes
- Be educational about tiger conservation
- Avoid inflammatory language
- Include general background on tiger trafficking
"""
        }

        return guidelines.get(audience, "Use appropriate professional standards.")

    def _get_format_instructions(self, format_type: str) -> str:
        """Get format-specific output instructions."""
        instructions = {
            "markdown": """
Output the report in clean Markdown format:
- Use # for main title, ## for sections, ### for subsections
- Use **bold** for emphasis
- Use bullet points for lists
- Use > for important callouts
- Use tables where appropriate for data
- Include horizontal rules (---) between major sections
""",
            "json": """
Output the report as a JSON object:
```json
{
    "title": "Investigation Report",
    "audience": "<audience>",
    "classification": "<level>",
    "generated_at": "<ISO timestamp>",
    "sections": [
        {
            "name": "<section name>",
            "content": "<section content>",
            "subsections": [...]
        }
    ],
    "metadata": {
        "investigation_id": "<id>",
        "confidence_level": "<level>",
        "word_count": <count>
    }
}
```
""",
            "pdf": """
Output in Markdown format (will be converted to PDF):
- Include a title page section with report metadata
- Use clear section breaks
- Ensure tables are properly formatted
- Include figure captions for any images
- Add page break hints with <!-- pagebreak --> where appropriate
"""
        }

        return instructions.get(format_type, instructions["markdown"])

    def _format_investigation_data(
        self,
        data: Dict[str, Any],
        audience: ReportAudience
    ) -> str:
        """Format investigation data for the prompt."""
        formatted = []

        # Core identification data
        if "identification" in data:
            id_data = data["identification"]
            formatted.append(f"""
### Identification Results
- Tiger ID: {id_data.get('tiger_id', 'Unknown')}
- Tiger Name: {id_data.get('tiger_name', 'Unknown')}
- Confidence: {id_data.get('confidence', 0):.1%}
- Primary Model: {id_data.get('model', 'Unknown')}
""")

        # Model results (detailed for internal, summary for others)
        if "model_results" in data:
            formatted.append("### Model Matching Results")
            for model, results in data["model_results"].items():
                if audience == ReportAudience.INTERNAL:
                    formatted.append(f"""
**{model}:**
- Top Match: {results.get('top_match', 'None')}
- Similarity: {results.get('similarity', 0):.4f}
- Calibrated: {results.get('calibrated_similarity', 0):.4f}
- Time: {results.get('inference_time', 'N/A')}ms
""")
                else:
                    formatted.append(f"- {model}: {results.get('similarity', 0):.1%}")

        # Location data
        if "location" in data:
            loc = data["location"]
            formatted.append(f"""
### Location Intelligence
- Primary Location: {loc.get('primary', 'Unknown')}
- Source: {loc.get('source', 'Unknown')}
- Confidence: {loc.get('confidence', 0):.1%}
- Coordinates: {loc.get('coordinates', 'N/A')}
""")

        # Facility data
        if "facility" in data:
            fac = data["facility"]
            formatted.append(f"""
### Facility Information
- Name: {fac.get('name', 'Unknown')}
- Location: {fac.get('location', 'Unknown')}
- Owner: {fac.get('owner', 'Unknown')}
- USDA License: {fac.get('usda_license', 'Unknown')}
""")

        # Evidence
        if "evidence" in data:
            formatted.append("### Evidence Summary")
            for i, ev in enumerate(data["evidence"], 1):
                formatted.append(f"{i}. {ev.get('type', 'Unknown')}: {ev.get('summary', 'N/A')}")

        # Methodology (for internal reports)
        if "reasoning_steps" in data and audience == ReportAudience.INTERNAL:
            formatted.append("### Methodology/Reasoning Chain")
            for step in data["reasoning_steps"]:
                formatted.append(f"""
**Step {step.get('step', '?')}:** {step.get('action', 'Unknown')}
- Conclusion: {step.get('conclusion', 'N/A')}
- Confidence: {step.get('confidence', 0)}%
""")

        return "\n".join(formatted) if formatted else "No investigation data provided."


# Template getters for external use

def get_law_enforcement_template() -> str:
    """Get the law enforcement report template."""
    return """# Tiger Investigation Report
## Case Reference: {case_id}

**Classification:** {classification}
**Date:** {date}
**Investigator:** Tiger ID System

---

## 1. Executive Summary

{executive_summary}

---

## 2. Subject Identification

**Tiger ID:** {tiger_id}
**Name:** {tiger_name}
**Identification Confidence:** {confidence}%

{identification_details}

---

## 3. Evidence Chain

{evidence_chain}

---

## 4. Methodology

{methodology}

---

## 5. Location Intelligence

{location_intelligence}

---

## 6. Facility/Owner Information

{facility_information}

---

## 7. Potential Violations

{potential_violations}

---

## 8. Recommended Actions

{recommended_actions}

---

## Appendices

{appendices}

---

*Report generated by Tiger ID Investigation System*
*This report is intended for law enforcement use only*
"""


def get_conservation_template() -> str:
    """Get the conservation report template."""
    return """# Tiger Welfare Assessment Report

**Date:** {date}
**Urgency Level:** {urgency}

---

## Tiger Overview

{tiger_overview}

---

## Current Welfare Status

{welfare_status}

---

## Facility Assessment

{facility_assessment}

---

## Historical Context

{historical_context}

---

## Conservation Implications

{conservation_implications}

---

## Recommendations

{recommendations}

---

*Report generated by Tiger ID Investigation System*
"""
