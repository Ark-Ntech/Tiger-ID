# MCP Servers
## Model Context Protocol Tool Servers for Tiger ID

This document describes the 4 MCP (Model Context Protocol) servers that provide specialized tools for the Investigation 2.0 workflow.

---

## Overview

Tiger ID uses MCP servers to provide modular, tool-based capabilities that integrate into the investigation workflow. Each server provides a set of tools that can be called programmatically.

| Server | Purpose | Key Features |
|--------|---------|--------------|
| `sequential_thinking_server` | Reasoning chains | Track methodology, evidence, conclusions |
| `image_analysis_server` | Image quality | Quality scores, manipulation detection |
| `deep_research_server` | Web research | DuckDuckGo search, multi-query sessions |
| `report_generation_server` | Report writing | Multi-audience reports, PDF export |

---

## 1. Sequential Thinking Server

**File**: `backend/mcp_servers/sequential_thinking_server.py`

### Purpose
Manages reasoning chains throughout investigation workflows, providing methodology transparency and evidence tracking.

### Tools

| Tool | Description |
|------|-------------|
| `start_reasoning_chain` | Initialize a new reasoning chain for an investigation question |
| `add_reasoning_step` | Add a step with evidence, reasoning, and conclusion |
| `finalize_reasoning` | Finalize chain with overall conclusion and confidence |
| `get_reasoning_chain` | Retrieve current state of a chain |
| `list_active_chains` | List all active (non-finalized) chains |

### Data Structures

**ReasoningStep**:
```python
{
    "step": 1,
    "phase": "stripe_analysis",
    "action": "Running 6-model ensemble",
    "evidence": ["4 models returned high confidence", "Wildlife-Tools: 92%"],
    "reasoning": "Multiple models agree on identity...",
    "conclusion": "Tiger identified as T-001 with high confidence",
    "confidence": 87,
    "timestamp": "2026-02-02T14:30:00"
}
```

**ReasoningChain**:
```python
{
    "chain_id": "abc12345",
    "question": "Identify the tiger in the uploaded image",
    "reasoning_type": "identification",
    "steps": [...],
    "status": "finalized",  # active | finalized | abandoned
    "final_conclusion": "Tiger identified as T-001",
    "overall_confidence": 87
}
```

### Reasoning Types
- `identification` - Tiger identity determination
- `location` - Location inference
- `confidence` - Confidence assessment
- `recommendation` - Action recommendations
- `match_selection` - Match ranking decisions
- `quality_assessment` - Image quality evaluation

### Usage Example

```python
from backend.mcp_servers.sequential_thinking_server import get_sequential_thinking_server

server = get_sequential_thinking_server()

# Start chain
result = await server.start_reasoning_chain(
    question="Identify the tiger in this image",
    reasoning_type="identification"
)
chain_id = result["chain_id"]

# Add steps
await server.add_reasoning_step(
    chain_id=chain_id,
    phase="upload_and_parse",
    action="Validated image and extracted EXIF",
    evidence=["Image size: 1920x1080", "EXIF date: 2026-01-15"],
    reasoning="Image meets quality requirements for identification",
    conclusion="Image suitable for analysis",
    confidence=95
)

# Finalize
await server.finalize_reasoning(chain_id)
```

### Workflow Integration
- Chain initialized at investigation start
- Steps added at each workflow phase
- Finalized in report generation phase
- Steps exported to frontend for methodology display

---

## 2. Image Analysis Server

**File**: `backend/mcp_servers/image_analysis_server.py`

### Purpose
Provides image quality assessment and analysis using OpenCV, PIL, and scikit-image. All processing is local.

### Tools

| Tool | Description |
|------|-------------|
| `assess_image_quality` | Assess image quality for tiger identification suitability |
| `analyze_image_features` | Extract visual features (edges, histogram, texture, keypoints) |
| `compare_stripe_patterns` | Compare stripe patterns between two tiger images |
| `detect_image_manipulation` | Detect signs of image tampering using ELA |

### Quality Metrics

```python
{
    "resolution": [1920, 1080],
    "blur_score": 250.5,       # Higher = sharper (>100 good)
    "brightness": 128.0,       # 0-255 (80-180 ideal)
    "contrast": 45.0,          # Standard deviation (>30 good)
    "sharpness": 32.0,         # Gradient magnitude
    "stripe_visibility": 0.75, # 0-1 (>0.5 good)
    "overall_score": 82.0      # 0-100 overall quality
}
```

### Quality Recommendations

The server generates recommendations based on metrics:
- Resolution < 640px: "Use higher resolution image"
- Blur score < 100: "Image appears blurry"
- Brightness < 50: "Image is too dark"
- Contrast < 30: "Low contrast makes stripes hard to detect"
- Stripe visibility < 0.5: "Use flank view with good lighting"

### Manipulation Detection

Uses Error Level Analysis (ELA) to detect tampering:
```python
result = await server.call_tool("detect_image_manipulation", {
    "image_data": base64_image,
    "sensitivity": "medium"  # low | medium | high
})

# Returns:
{
    "manipulation_score": 0.15,  # 0 = authentic, 1 = manipulated
    "verdict": "authentic",      # authentic | possibly_modified | likely_manipulated
    "confidence": "high",
    "findings": [
        {"check": "metadata_analysis", "finding": "...", "severity": "low"}
    ]
}
```

### Usage Example

```python
from backend.mcp_servers.image_analysis_server import get_image_analysis_server

server = get_image_analysis_server()

# Assess quality
quality = await server.assess_image_quality(
    image_data=image_bytes,
    detection_results=megadetector_output
)

if quality["overall_score"] < 60:
    warnings.append(quality["recommendations"])
```

### Dependencies
- **Required**: PIL/Pillow
- **Optional**: OpenCV (`cv2`), scikit-image
- Falls back gracefully if optional deps missing

---

## 3. Deep Research Server

**File**: `backend/mcp_servers/deep_research_server.py`

### Purpose
Provides iterative multi-query web research using DuckDuckGo. No API keys required.

### Tools

| Tool | Description |
|------|-------------|
| `start_research` | Start a new research session on a topic |
| `expand_research` | Follow promising leads with additional queries |
| `synthesize_findings` | Synthesize all findings into coherent summary |
| `get_source_graph` | Get graph of source relationships and credibility |
| `get_session_status` | Get current status of a research session |

### Research Modes

| Mode | Focus | Example Queries |
|------|-------|-----------------|
| `facility_investigation` | Facility research | USDA inspection, exotic animal, owner |
| `tiger_provenance` | Tiger origins | breeding, transfer, born |
| `trafficking_patterns` | Trafficking | seizure, illegal, investigation |
| `regulatory_history` | Compliance | USDA, CITES, violation, license |
| `general` | General | news, information |

### Research Depths

| Depth | Max Queries | Use Case |
|-------|-------------|----------|
| `quick` | 3 | Fast preliminary check |
| `standard` | 10 | Normal investigation |
| `deep` | 25+ | Comprehensive research |

### Source Credibility

Sources are automatically classified:
- **High**: `.gov`, `.edu` domains
- **Medium**: Conservation orgs, major news
- **Low**: General web, social media

### Usage Example

```python
from backend.mcp_servers.deep_research_server import get_deep_research_server

server = get_deep_research_server()

# Start research
result = await server.start_research(
    topic="Big Cat Rescue Tampa",
    mode="facility_investigation",
    depth="standard"
)
session_id = result["session_id"]

# Expand based on findings
await server.call_tool("expand_research", {
    "session_id": session_id,
    "direction": "USDA violations"
})

# Synthesize
synthesis = await server.call_tool("synthesize_findings", {
    "session_id": session_id
})
```

### Session Structure

```python
{
    "session_id": "abc12345",
    "topic": "Big Cat Rescue Tampa",
    "mode": "facility_investigation",
    "depth": "standard",
    "queries_executed": ["...", "..."],
    "results_count": 42,
    "entities_found": ["Carole Baskin", "Howard Baskin"],
    "status": "active"  # active | saturated | completed | failed
}
```

### Dependencies
- **Required**: `duckduckgo-search` package
- Uses Claude for query expansion and synthesis

### Rate Limiting

The Deep Research Server respects the system's per-domain rate limiting:

```python
# Rate limiting is applied to DuckDuckGo API calls
await self._rate_limit("https://duckduckgo.com/")

# On success, backoff is reduced
self.rate_limiter.report_success("https://duckduckgo.com/")

# On failure, backoff increases exponentially
self.rate_limiter.report_error("https://duckduckgo.com/", 500)
```

**Rate Limit Settings:**
- Base interval: 2 seconds between requests
- Max backoff: 60 seconds
- Backoff doubles on errors (429, 503, 520-524)
- Backoff reduces by 0.9x on success

This prevents overwhelming DuckDuckGo and ensures reliable research sessions.

---

## 4. Report Generation Server

**File**: `backend/mcp_servers/report_generation_server.py`

### Purpose
Generates investigation reports tailored to different audiences with multiple output formats.

### Tools

| Tool | Description |
|------|-------------|
| `generate_report` | Generate report for specific audience and format |
| `get_report_template` | Get template structure for an audience |
| `validate_report_completeness` | Validate report has required sections |
| `export_to_pdf` | Export markdown report to PDF |
| `get_report` | Retrieve previously generated report |

### Report Audiences

| Audience | Focus | Key Sections |
|----------|-------|--------------|
| `law_enforcement` | Legal/investigation | Evidence chain, violations, recommended actions |
| `conservation` | Wildlife welfare | Welfare status, conservation implications, urgency |
| `internal` | Technical details | Model performance, reasoning chain, errors |
| `public` | General information | Summary, key findings |

### Audience-Specific Sections

**Law Enforcement**:
- Executive Summary
- Subject Identification
- Evidence Chain
- Methodology
- Potential Violations
- Recommended Actions

**Conservation**:
- Tiger Overview
- Current Welfare Status
- Facility Assessment
- Conservation Implications
- Urgency Assessment

**Internal**:
- Investigation Summary
- Model Performance
- Reasoning Chain
- Data Quality
- Errors/Warnings

**Public**:
- Summary
- Key Findings

### Output Formats

- `markdown` - Default, human-readable
- `json` - Structured data
- `pdf` - Formatted document (requires reportlab)
- `html` - Web-compatible

### Usage Example

```python
from backend.mcp_servers.report_generation_server import get_report_generation_server

server = get_report_generation_server()

# Generate report
report = await server.generate_report(
    investigation_id="inv_123",
    audience="law_enforcement",
    format="markdown",
    investigation_data={
        "identification": {"tiger_id": "T-001", "confidence": 0.87},
        "reasoning_steps": [...],
        "evidence": [...]
    }
)

# Export to PDF
await server.call_tool("export_to_pdf", {
    "report_content": report["content"],
    "output_path": "/path/to/report.pdf",
    "title": "Tiger Investigation Report"
})
```

### Dependencies
- **Optional**: `reportlab` for PDF export

---

## Workflow Integration

All MCP servers are integrated into the Investigation 2.0 workflow:

```
1. Upload & Parse
   └── Image Analysis: assess_image_quality
   └── Sequential Thinking: start_reasoning_chain + add_step

2. Reverse Image Search
   └── Deep Research: start_research, expand_research
   └── Sequential Thinking: add_step

3. Tiger Detection
   └── Sequential Thinking: add_step

4. Stripe Analysis
   └── Sequential Thinking: add_step

5. Report Generation
   └── Report Generation: generate_report
   └── Sequential Thinking: finalize_reasoning

6. Complete
   └── Report Generation: export_to_pdf (optional)
```

### State Fields

The workflow state includes:
- `reasoning_chain_id` - From Sequential Thinking
- `image_quality` - From Image Analysis
- `deep_research_session_id` - From Deep Research
- `report_audience` - For Report Generation

---

## Creating New MCP Servers

To create a new MCP server:

1. Create file in `backend/mcp_servers/`
2. Inherit from `MCPServerBase`
3. Register tools with `MCPTool`
4. Implement `list_tools`, `call_tool`, `list_resources`
5. Add singleton getter function

```python
from backend.mcp_servers.base_mcp_server import MCPServerBase, MCPTool

class MyMCPServer(MCPServerBase):
    def __init__(self):
        super().__init__("my_server")
        self._register_tools()

    def _register_tools(self):
        self.tools = {
            "my_tool": MCPTool(
                name="my_tool",
                description="...",
                parameters={...},
                handler=self._handle_my_tool
            )
        }

    async def _handle_my_tool(self, **kwargs):
        return {"success": True, ...}

# Singleton
_instance = None

def get_my_server():
    global _instance
    if _instance is None:
        _instance = MyMCPServer()
    return _instance
```

---

*Last Updated: February 2026*
