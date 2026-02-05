"""
Facility Investigation Skill

Deep research workflow for investigating wildlife facilities/exhibitors.
Integrates with Deep Research MCP for iterative DuckDuckGo queries.
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum

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


class RiskLevel(str, Enum):
    """Risk assessment levels for facilities."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class InvestigationSection(str, Enum):
    """Sections of a facility investigation."""
    IDENTITY = "identity_verification"
    VIOLATIONS = "violation_history"
    NETWORK = "network_analysis"
    INVENTORY = "tiger_inventory"
    WELFARE = "welfare_assessment"


@dataclass
class FacilityProfile:
    """Profile of an investigated facility."""
    name: str
    aliases: List[str] = field(default_factory=list)
    location: Optional[str] = None
    registration: Optional[Dict[str, str]] = None  # USDA, CITES registrations
    owner: Optional[str] = None
    risk_level: RiskLevel = RiskLevel.MEDIUM
    key_findings: List[str] = field(default_factory=list)
    evidence_sources: List[Dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "aliases": self.aliases,
            "location": self.location,
            "registration": self.registration,
            "owner": self.owner,
            "risk_level": self.risk_level.value,
            "key_findings": self.key_findings,
            "evidence_sources": self.evidence_sources
        }


@SkillRegistry.register
class FacilityInvestigationSkill(BaseSkill):
    """
    Skill for deep investigation of captive wildlife facilities.

    Generates structured research workflow for investigating facilities/exhibitors
    potentially involved in tiger trafficking.

    Command: /investigate-facility <facility_name>
    """

    def __init__(self):
        """Initialize the facility investigation skill."""
        super().__init__()
        self._chat_model = None

    def get_definition(self) -> SkillDefinition:
        """Return skill definition."""
        return SkillDefinition(
            name="Facility Investigation",
            description="Deep research workflow for investigating facilities/exhibitors",
            command="/investigate-facility",
            category=SkillCategory.RESEARCH,
            parameters=[
                SkillParameter(
                    name="facility_name",
                    description="Name of the facility to investigate",
                    type="string",
                    required=True
                ),
                SkillParameter(
                    name="known_info",
                    description="Any known information about the facility",
                    type="object",
                    required=False,
                    default={}
                ),
                SkillParameter(
                    name="investigation_depth",
                    description="How deep to investigate",
                    type="string",
                    required=False,
                    default="standard",
                    enum=["quick", "standard", "deep"]
                ),
                SkillParameter(
                    name="focus_sections",
                    description="Specific sections to focus on",
                    type="array",
                    required=False,
                    default=None
                ),
                SkillParameter(
                    name="web_search_results",
                    description="Pre-fetched web search results to analyze",
                    type="array",
                    required=False,
                    default=[]
                )
            ],
            examples=[
                "/investigate-facility Big Cat Rescue",
                "/investigate-facility \"G.W. Exotic Animal Park\" --depth deep",
                "/investigate-facility Dade City Wild Things --focus violations,network"
            ]
        )

    def get_prompt_template(self) -> str:
        """Return the prompt template."""
        return """You are a wildlife trafficking investigator specializing in captive tiger facilities.

## Investigation Target
**Facility:** {facility_name}
**Known Information:** {known_info_formatted}
**Investigation Depth:** {investigation_depth}

## Web Intelligence
{web_results_formatted}

## Investigation Workflow

### 1. Identity Verification
Research and document:
- Official registrations (USDA exhibitor license, CITES permits)
- Alternative names, DBAs, or related entities
- Ownership chain (current and historical owners)
- Corporate structure if applicable
- Physical address and contact information

### 2. Violation History
Search for and document:
- USDA Animal Welfare Act inspection reports
- State wildlife agency violations
- News articles about violations or incidents
- Legal actions (lawsuits, criminal charges)
- Social media complaints or exposés

### 3. Network Analysis
Map connections to:
- Other known facilities (breeding, sales, transfers)
- Individual breeders or dealers
- Transport companies
- Business relationships
- Personnel who have worked at multiple facilities

### 4. Tiger Inventory
Cross-reference:
- Known tigers at this facility (from database)
- Acquisition sources (where tigers came from)
- Disposition records (where tigers went)
- Breeding activity
- Deaths and their circumstances

### 5. Welfare Assessment (if applicable)
Evaluate:
- Care standards based on available information
- Enclosure conditions (photos, videos, reports)
- Veterinary care evidence
- Staff qualifications
- Public safety incidents

## Focus Sections
{focus_sections}

## Output Format
Provide your investigation report in the following JSON structure:

```json
{{
    "facility_profile": {{
        "name": "{facility_name}",
        "aliases": ["<alias 1>", "<alias 2>"],
        "location": "<address or location>",
        "registration": {{
            "usda_license": "<license number or 'Unknown'>",
            "cites_registration": "<registration or 'Unknown'>",
            "state_permits": "<permits or 'Unknown'>"
        }},
        "owner": "<current owner name>",
        "ownership_history": ["<previous owners>"]
    }},
    "risk_assessment": {{
        "level": "<low|medium|high|critical>",
        "factors": ["<factor 1>", "<factor 2>"],
        "explanation": "<why this risk level>"
    }},
    "key_findings": [
        {{
            "finding": "<finding description>",
            "significance": "<why this matters>",
            "evidence_quality": "<strong|moderate|weak>",
            "source": "<source URL or description>"
        }}
    ],
    "violations": [
        {{
            "date": "<date if known>",
            "type": "<violation type>",
            "description": "<what happened>",
            "outcome": "<fine, warning, etc.>",
            "source": "<source URL>"
        }}
    ],
    "network_connections": [
        {{
            "entity": "<connected entity name>",
            "relationship": "<type of connection>",
            "significance": "<why this connection matters>"
        }}
    ],
    "tiger_connections": [
        {{
            "tiger_id": "<ID if known>",
            "tiger_name": "<name if known>",
            "relationship": "<acquired from|transferred to|bred at|died at>",
            "date": "<date if known>"
        }}
    ],
    "evidence_sources": [
        {{
            "url": "<source URL>",
            "title": "<source title>",
            "type": "<news|government|social_media|database>",
            "reliability": "<high|medium|low>",
            "access_date": "<when accessed>"
        }}
    ],
    "recommended_actions": [
        {{
            "action": "<recommended action>",
            "priority": "<high|medium|low>",
            "rationale": "<why this action>"
        }}
    ],
    "investigation_gaps": ["<what needs more research>"],
    "confidence_notes": "<overall assessment of evidence quality>"
}}
```

## Important Guidelines
- Be thorough but stick to facts from the provided web results
- Clearly distinguish between confirmed facts and allegations
- Note the source and reliability of each finding
- Flag any potential legal sensitivities
- Recommend follow-up actions based on findings"""

    async def execute(
        self,
        context: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute the facility investigation skill.

        Args:
            context: Dictionary containing:
                - facility_name: Name of facility
                - known_info: Known information about facility
                - investigation_depth: How deep to investigate
                - focus_sections: Optional sections to focus on
                - web_search_results: Pre-fetched search results

        Returns:
            Dictionary with investigation report
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
            facility_name = context.get("facility_name", "Unknown Facility")
            known_info = context.get("known_info", {})
            investigation_depth = context.get("investigation_depth", "standard")
            focus_sections = context.get("focus_sections")
            web_results = context.get("web_search_results", [])

            # Format inputs
            known_info_formatted = self._format_known_info(known_info)
            web_results_formatted = self._format_web_results(web_results)
            focus_sections_formatted = self._format_focus_sections(focus_sections)

            # Build the prompt
            prompt = self.build_prompt({
                "facility_name": facility_name,
                "known_info_formatted": known_info_formatted,
                "investigation_depth": investigation_depth,
                "web_results_formatted": web_results_formatted,
                "focus_sections": focus_sections_formatted
            })

            # Get or create chat model (use quality model for investigations)
            if not self._chat_model:
                self._chat_model = AnthropicChatModel(model_name="claude-opus-4-5-20251101")

            # Execute with Claude
            logger.info(f"Investigating facility: {facility_name} (depth: {investigation_depth})")
            response = await self._chat_model.chat(
                message=prompt,
                system_prompt="You are an expert wildlife trafficking investigator. Be thorough, factual, and cite sources. Respond only with valid JSON."
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
                    "facility_name": facility_name,
                    "investigation_depth": investigation_depth,
                    "web_sources_count": len(web_results),
                    "focus_sections": focus_sections
                }
            }

        except Exception as e:
            logger.error(f"Facility investigation failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "output": None
            }

    def _format_known_info(self, known_info: Dict) -> str:
        """Format known information about the facility."""
        if not known_info:
            return "No prior information available."

        formatted = []
        for key, value in known_info.items():
            formatted.append(f"- {key.replace('_', ' ').title()}: {value}")

        return "\n".join(formatted)

    def _format_web_results(self, results: List[Dict]) -> str:
        """Format web search results for analysis."""
        if not results:
            return "No web search results provided. Generate investigation plan only."

        formatted = ["The following web intelligence has been gathered:"]

        for i, result in enumerate(results, 1):
            formatted.append(f"""
### Source {i}: {result.get('title', 'Untitled')}
**URL:** {result.get('url', 'N/A')}
**Type:** {result.get('type', 'Unknown')}
**Content:**
{result.get('content', result.get('snippet', 'No content available'))}
""")

        return "\n".join(formatted)

    def _format_focus_sections(self, sections: Optional[List[str]]) -> str:
        """Format focus sections instruction."""
        if not sections:
            return "Investigate all sections comprehensively."

        section_names = {
            "identity": "Identity Verification",
            "violations": "Violation History",
            "network": "Network Analysis",
            "inventory": "Tiger Inventory",
            "welfare": "Welfare Assessment"
        }

        focused = [section_names.get(s, s) for s in sections]
        return f"Focus primarily on: {', '.join(focused)}"

    def generate_search_queries(
        self,
        facility_name: str,
        investigation_depth: str = "standard"
    ) -> List[str]:
        """
        Generate search queries for the Deep Research MCP.

        Args:
            facility_name: Name of the facility
            investigation_depth: How deep to investigate

        Returns:
            List of search queries
        """
        base_queries = [
            f'"{facility_name}" USDA inspection',
            f'"{facility_name}" tiger',
            f'"{facility_name}" violation',
            f'"{facility_name}" owner',
        ]

        standard_queries = base_queries + [
            f'"{facility_name}" animal welfare',
            f'"{facility_name}" lawsuit',
            f'"{facility_name}" big cat',
            f'"{facility_name}" exotic animal',
        ]

        deep_queries = standard_queries + [
            f'"{facility_name}" CITES',
            f'"{facility_name}" trafficking',
            f'"{facility_name}" death',
            f'"{facility_name}" transfer',
            f'"{facility_name}" breeding',
            f'"{facility_name}" news',
            f'"{facility_name}" facebook',
            f'"{facility_name}" review complaint',
        ]

        if investigation_depth == "quick":
            return base_queries
        elif investigation_depth == "deep":
            return deep_queries
        else:
            return standard_queries
