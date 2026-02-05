# Skills System
## Claude Code Skills for Tiger ID Investigation

This document describes the Skills system used in Tiger ID for Claude-powered investigation workflows.

---

## Overview

Skills are prompt-based workflows that leverage Claude's reasoning capabilities. They complement MCP servers by handling tasks that require:
- Complex reasoning with Claude's judgment
- Multi-step prompt workflows
- Template-based generation with context
- Natural language understanding

| Skill | Command | Category | Purpose |
|-------|---------|----------|---------|
| Evidence Synthesis | `/synthesize-evidence` | Analysis | Weighted evidence combination |
| Chain-of-Thought Reasoning | `/explain-reasoning` | Reasoning | Transparent decision documentation |
| Facility Investigation | `/investigate-facility` | Research | Deep facility research |
| Report Writer | `/generate-report` | Reporting | Multi-audience reports |
| Image Advisor | `/assess-image` | Quality | Image quality feedback |

---

## Architecture

### BaseSkill Class

All skills inherit from `BaseSkill` (`backend/skills/base_skill.py`):

```python
class BaseSkill(ABC):
    """
    Base class for all Claude Code skills.

    Skills use natural language prompts as templates,
    leverage Claude's judgment, and generate human-readable outputs.
    """

    @abstractmethod
    def get_definition(self) -> SkillDefinition:
        """Return skill definition (name, command, parameters, examples)."""
        pass

    @abstractmethod
    def get_prompt_template(self) -> str:
        """Return the prompt template string with {variable} placeholders."""
        pass

    @abstractmethod
    async def execute(self, context: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Execute the skill with given context."""
        pass
```

### Skill Categories

```python
class SkillCategory(str, Enum):
    ANALYSIS = "analysis"     # Evidence synthesis, data analysis
    RESEARCH = "research"     # Web research, facility investigation
    REPORTING = "reporting"   # Report generation
    REASONING = "reasoning"   # Chain-of-thought, methodology
    QUALITY = "quality"       # Image quality assessment
```

### SkillRegistry

Skills are managed through the `SkillRegistry`:

```python
from backend.skills import SkillRegistry, get_skill

# Register a skill (typically via @SkillRegistry.register decorator)
@SkillRegistry.register
class MySkill(BaseSkill):
    ...

# Get a skill by command
skill = SkillRegistry.get_skill("/synthesize-evidence")

# Execute the skill
result = await skill.execute(context={...})

# List all available skills
skills = SkillRegistry.list_skills()

# List skills by category
analysis_skills = SkillRegistry.list_by_category(SkillCategory.ANALYSIS)
```

---

## 1. Evidence Synthesis Skill

**File**: `backend/skills/evidence_synthesis.py`
**Command**: `/synthesize-evidence`
**Category**: Analysis

### Purpose
Combines evidence from multiple sources with weighted confidence scoring, integrating ML pipeline model weights for accurate confidence calculation.

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `sources` | array | Yes | List of evidence sources to synthesize |
| `model_results` | object | No | Results from ReID models with similarity scores |
| `focus_areas` | array | No | Areas to focus on (default: identification, location, provenance) |
| `synthesis_mode` | string | No | How aggressive (conservative/balanced/aggressive) |

### Evidence Source Reliability

```python
SOURCE_RELIABILITY = {
    "exif_gps": 1.0,        # Highest - direct from image
    "database_match": 0.9,   # High - verified records
    "visual_analysis": 0.8,  # Good - AI analysis
    "user_context": 0.7,     # Moderate - user-provided
    "web_intelligence": 0.6, # Lower - web search
    "external_api": 0.5,     # Variable - external data
}
```

### Model Weights Integration

Uses the 6-model ensemble weights:
```python
MODEL_WEIGHTS = {
    "wildlife_tools": 0.40,  # Best performer
    "cvwc2019_reid": 0.30,   # Part-based
    "transreid": 0.20,       # ViT features
    "tiger_reid": 0.10,      # Baseline
    "rapid_reid": 0.10,      # Edge-optimized
}
```

### Synthesis Modes

| Mode | Behavior |
|------|----------|
| `conservative` | Require corroboration, prefer lower confidence, flag uncertainty |
| `balanced` | Standard weighting, accept single high-reliability sources |
| `aggressive` | Lower threshold, weight web intelligence higher |

### Output Format

```json
{
    "confidence_score": 87,
    "confidence_level": "high",
    "primary_evidence": [...],
    "corroborating_evidence": [...],
    "contradictions": [...],
    "model_consensus": {
        "agreeing_models": 4,
        "total_models": 6,
        "weighted_similarity": 0.85,
        "top_match": {...}
    },
    "reasoning": "Step-by-step justification...",
    "recommendations": [...]
}
```

### Usage Example

```python
from backend.skills import get_skill

skill = get_skill("/synthesize-evidence")
result = await skill.execute({
    "sources": [
        {"source_type": "database_match", "content": {...}, "confidence": 0.92},
        {"source_type": "web_intelligence", "content": {...}, "confidence": 0.75}
    ],
    "model_results": {
        "wildlife_tools": {"matches": [...]},
        "cvwc2019_reid": {"matches": [...]}
    },
    "synthesis_mode": "balanced"
})
```

---

## 2. Chain-of-Thought Reasoning Skill

**File**: `backend/skills/reasoning_chain.py`
**Command**: `/explain-reasoning`
**Category**: Reasoning

### Purpose
Generates transparent step-by-step reasoning for investigation decisions, creating auditable methodology documentation.

### Decision Types

```python
class DecisionType(str, Enum):
    IDENTIFICATION = "identification"      # Tiger identity
    LOCATION = "location"                  # Location inference
    CONFIDENCE = "confidence"              # Confidence assessment
    RECOMMENDATION = "recommendation"      # Action recommendations
    MATCH_SELECTION = "match_selection"    # Match ranking
    QUALITY_ASSESSMENT = "quality_assessment"  # Image quality
```

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `decision_type` | string | Yes | Type of decision (see DecisionType enum) |
| `context` | object | Yes | Context and data relevant to decision |
| `evidence` | array | No | List of evidence items to consider |
| `require_citations` | boolean | No | Require citations for each step (default: true) |

### Output Format

```json
{
    "decision_type": "identification",
    "question": "Is this tiger T-001?",
    "steps": [
        {
            "step": 1,
            "action": "Analyzed stripe patterns",
            "evidence": ["evidence 1", "evidence 2"],
            "reasoning": "Why this matters...",
            "conclusion": "Patterns match with high similarity",
            "confidence": 85
        }
    ],
    "final_conclusion": "Tiger identified as T-001",
    "overall_confidence": 87,
    "supporting_factors": [...],
    "uncertainty_factors": [...],
    "assumptions_made": [...]
}
```

### Decision-Specific Guidance

Each decision type has specialized guidance:
- **Identification**: Compare stripe patterns, consider viewpoint differences, check distinctive markings
- **Location**: Prioritize EXIF GPS, cross-reference facility locations
- **Confidence**: Consider model consensus, weight by accuracy, factor image quality
- **Recommendation**: Consider urgency, suggest authorities, propose follow-up
- **Match Selection**: Compare scores, apply model weights, verify location consistency
- **Quality Assessment**: Check resolution, assess visibility, evaluate lighting

### Usage Example

```python
skill = get_skill("/explain-reasoning")
result = await skill.execute({
    "decision_type": "identification",
    "context": {
        "tiger_name": "Raja",
        "facility_name": "Big Cat Rescue"
    },
    "evidence": [
        {"type": "stripe_match", "content": "92% similarity", "confidence": 0.92}
    ],
    "require_citations": True
})
```

---

## 3. Facility Investigation Skill

**File**: `backend/skills/facility_investigation.py`
**Command**: `/investigate-facility`
**Category**: Research

### Purpose
Deep research workflow for investigating captive wildlife facilities and exhibitors. Generates structured investigation plans and analyzes web intelligence.

### Risk Levels

```python
class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
```

### Investigation Sections

| Section | Description |
|---------|-------------|
| `identity_verification` | Registrations, aliases, ownership chain |
| `violation_history` | USDA inspections, legal actions, complaints |
| `network_analysis` | Connections to other facilities, dealers |
| `tiger_inventory` | Tigers at facility, acquisitions, dispositions |
| `welfare_assessment` | Care standards, enclosure conditions |

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `facility_name` | string | Yes | Name of facility to investigate |
| `known_info` | object | No | Any known information |
| `investigation_depth` | string | No | quick/standard/deep |
| `focus_sections` | array | No | Specific sections to focus on |
| `web_search_results` | array | No | Pre-fetched search results |

### Investigation Depths

| Depth | Max Queries | Focus |
|-------|-------------|-------|
| `quick` | 4 | Basic: USDA, tiger, violation, owner |
| `standard` | 8 | + animal welfare, lawsuit, big cat, exotic |
| `deep` | 16+ | + CITES, trafficking, death, transfer, breeding, news |

### Output Format

```json
{
    "facility_profile": {
        "name": "Big Cat Rescue",
        "aliases": ["BCR"],
        "location": "Tampa, FL",
        "registration": {...},
        "owner": "Carole Baskin"
    },
    "risk_assessment": {
        "level": "medium",
        "factors": [...],
        "explanation": "..."
    },
    "key_findings": [...],
    "violations": [...],
    "network_connections": [...],
    "tiger_connections": [...],
    "evidence_sources": [...],
    "recommended_actions": [...],
    "investigation_gaps": [...]
}
```

### Search Query Generation

The skill can generate DuckDuckGo queries for the Deep Research MCP:

```python
skill = get_skill("/investigate-facility")
queries = skill.generate_search_queries("Big Cat Rescue", "standard")
# Returns: ['"Big Cat Rescue" USDA inspection', '"Big Cat Rescue" tiger', ...]
```

### Usage Example

```python
skill = get_skill("/investigate-facility")
result = await skill.execute({
    "facility_name": "Dade City Wild Things",
    "investigation_depth": "deep",
    "focus_sections": ["violations", "network"],
    "web_search_results": [
        {"title": "USDA Report", "url": "...", "content": "..."}
    ]
})
```

---

## 4. Report Writer Skill

**File**: `backend/skills/report_writer.py`
**Command**: `/generate-report`
**Category**: Reporting

### Purpose
Generates investigation reports tailored to different audiences with specific sections, tone, and focus areas.

### Report Audiences

| Audience | Focus | Tone |
|----------|-------|------|
| `law_enforcement` | Legal, evidential | Formal, citations |
| `conservation` | Welfare, conservation impact | Accessible, actionable |
| `internal` | Technical, debugging | Detailed, metrics |
| `public` | General information | Plain language |

### Audience-Specific Sections

**Law Enforcement:**
- Executive Summary
- Subject Identification
- Evidence Chain (numbered, cited)
- Methodology
- Location Intelligence
- Potential Violations (ESA, Lacey Act, CITES)
- Recommended Actions

**Conservation:**
- Tiger Overview
- Current Welfare Status
- Facility Assessment
- Historical Context
- Conservation Implications
- Urgency Assessment

**Internal:**
- Investigation Summary
- Model Performance (scores, calibration)
- Data Quality
- Pipeline Details
- Reasoning Chain
- Errors and Warnings

**Public:**
- Summary
- Key Findings
- About the Tiger
- What This Means

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `audience` | string | Yes | Target audience |
| `investigation_data` | object | Yes | Complete investigation data |
| `format` | string | No | markdown/json/pdf |
| `include_appendices` | boolean | No | Include appendices (default: true) |
| `classification` | string | No | public/restricted/confidential |

### Output Formats

- **markdown**: Clean markdown with headers, tables, callouts
- **json**: Structured JSON with sections array
- **pdf**: Markdown formatted for PDF conversion

### Usage Example

```python
skill = get_skill("/generate-report")
result = await skill.execute({
    "audience": "law_enforcement",
    "investigation_data": {
        "identification": {"tiger_id": "T-001", "confidence": 0.87},
        "model_results": {...},
        "location": {...},
        "evidence": [...]
    },
    "format": "markdown",
    "classification": "restricted"
})
```

### Template Functions

The skill provides template getters for external use:

```python
from backend.skills.report_writer import (
    get_law_enforcement_template,
    get_conservation_template
)

template = get_law_enforcement_template()
```

---

## 5. Image Quality Advisor Skill

**File**: `backend/skills/image_advisor.py`
**Command**: `/assess-image`
**Category**: Quality

### Purpose
Advises users on image quality for tiger identification with constructive feedback and actionable suggestions.

### Quality Thresholds

```python
QUALITY_THRESHOLDS = {
    "resolution_min": 640,        # Minimum dimension
    "resolution_good": 1024,      # Good resolution
    "blur_threshold": 100,        # Laplacian variance
    "stripe_visibility_min": 0.5, # 0-1 visibility score
    "detection_confidence_min": 0.7,
}
```

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `quality_metrics` | object | Yes | Computed quality metrics |
| `detection_results` | object | No | Tiger detection results |
| `user_context` | string | No | User-provided context |

### Quality Assessment Areas

1. **Resolution and Clarity** - Pixel dimensions, sharpness
2. **Stripe Pattern Visibility** - Visibility score from Image Analysis MCP
3. **Pose Angle Suitability** - Flank views preferred
4. **Lighting Conditions** - Brightness, contrast
5. **Motion Blur/Focus** - Blur detection score
6. **Potential Manipulation** - ELA analysis results

### Output Format

```json
{
    "overall_score": 75,
    "recommendation": "proceed_with_caution",
    "issues": [
        {
            "issue": "Low resolution",
            "severity": "medium",
            "impact": "May reduce matching accuracy",
            "suggestion": "Use higher resolution image if available"
        }
    ],
    "strengths": ["Good stripe visibility", "Clear flank view"],
    "tips_for_better_images": [
        "Capture tiger from side profile",
        "Ensure adequate lighting"
    ],
    "user_message": "This image can be used but may have reduced accuracy..."
}
```

### Recommendations

| Score | Recommendation |
|-------|----------------|
| >= 70 | `proceed` |
| 50-69 | `proceed_with_caution` |
| < 50 | `request_new_image` |

### Quick Quality Check

A helper function provides fast scoring without Claude:

```python
from backend.skills.image_advisor import compute_basic_quality_score

quick_result = compute_basic_quality_score({
    "resolution": [1920, 1080],
    "blur_score": 150,
    "stripe_visibility": 0.8
})
# Returns: {"score": 90, "issues": [], "recommendation": "proceed"}
```

### Usage Example

```python
skill = get_skill("/assess-image")
result = await skill.execute({
    "quality_metrics": {
        "resolution": [1920, 1080],
        "blur_score": 250.5,
        "brightness": 128.0,
        "contrast": 45.0,
        "stripe_visibility": 0.75
    },
    "detection_results": {
        "detections": [{"confidence": 0.95, "bbox": [100, 100, 500, 400]}],
        "image_size": [1920, 1080]
    },
    "user_context": "Photo taken through glass enclosure"
})
```

---

## Workflow Integration

Skills are integrated into the Investigation 2.0 workflow:

```
1. Upload & Parse
   └── /assess-image - Quality feedback to user

2. Reverse Image Search
   └── /investigate-facility - Deep research on facilities found

3. Tiger Detection
   └── (MegaDetector - no skill)

4. Stripe Analysis
   └── /synthesize-evidence - Combine model results

5. Report Generation
   └── /generate-report - Multi-audience reports
   └── /explain-reasoning - Methodology documentation

6. Complete
   └── (Results returned)
```

### State Integration

Skills contribute to workflow state:
- `evidence_synthesis` - From /synthesize-evidence
- `reasoning_chain` - From /explain-reasoning
- `facility_profile` - From /investigate-facility
- `report_content` - From /generate-report
- `image_quality_advice` - From /assess-image

---

## Creating New Skills

To create a new skill:

1. Create file in `backend/skills/`
2. Inherit from `BaseSkill`
3. Add `@SkillRegistry.register` decorator
4. Implement required methods

```python
from backend.skills.base_skill import (
    BaseSkill, SkillDefinition, SkillParameter, SkillCategory
)
from backend.skills import SkillRegistry

@SkillRegistry.register
class MyNewSkill(BaseSkill):
    def get_definition(self) -> SkillDefinition:
        return SkillDefinition(
            name="My New Skill",
            description="Description of what it does",
            command="/my-command",
            category=SkillCategory.ANALYSIS,
            parameters=[
                SkillParameter(
                    name="input_data",
                    description="Data to process",
                    type="object",
                    required=True
                )
            ],
            examples=["/my-command --input {...}"]
        )

    def get_prompt_template(self) -> str:
        return """Your task is to...

## Input Data
{input_data_formatted}

## Output Format
Respond in JSON:
```json
{{
    "result": "..."
}}
```"""

    async def execute(self, context: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        # Validate
        errors = self.validate_context(context)
        if errors:
            return {"success": False, "error": str(errors), "output": None}

        # Build prompt
        prompt = self.build_prompt({
            "input_data_formatted": str(context.get("input_data", {}))
        })

        # Execute with Claude
        response = await self._chat_model.chat(message=prompt)

        return {
            "success": True,
            "output": response.get("response", ""),
            "metadata": {...}
        }
```

---

## Skills vs MCP Servers

Understanding when to use Skills vs MCP Servers is key to effective workflow design.

### Comparison Table

| Aspect | Skills | MCP Servers |
|--------|--------|-------------|
| **Invocation** | Slash commands (`/synthesize-evidence`) | Programmatic tool calls (`server.call_tool()`) |
| **Execution** | Claude prompt + reasoning | Deterministic Python functions |
| **Output** | Natural language / structured JSON | Raw structured data |
| **Best For** | Complex judgment, synthesis, explanation | Data retrieval, computation, external APIs |
| **Latency** | Higher (requires LLM call) | Lower (direct execution) |
| **Determinism** | Non-deterministic (LLM reasoning) | Deterministic (same input → same output) |

### When to Use Skills

- **Reasoning required**: Weighing evidence, making judgments
- **Synthesis needed**: Combining multiple data sources
- **Explanation expected**: Documenting methodology, chain-of-thought
- **User-facing output**: Reports, recommendations, feedback

### When to Use MCP Servers

- **Data retrieval**: Image analysis, web search, database queries
- **Computation**: Quality metrics, similarity scores
- **External APIs**: DuckDuckGo search, file operations
- **Fast responses**: Operations where latency matters

### Complementary Usage

Skills and MCP tools work together in the investigation workflow:

1. **MCP Server** gathers raw data (Image Analysis → quality metrics)
2. **Skill** interprets results (`/assess-image` → user-friendly feedback)
3. **MCP Server** performs search (Deep Research → web results)
4. **Skill** synthesizes findings (`/investigate-facility` → structured analysis)
5. **Skill** generates output (`/generate-report` → audience-specific report)

---

*Last Updated: February 2026*
