"""
Report Generation MCP Server

Provides report generation tools that integrate with the Report Writer skill.
Handles structured data preparation and PDF export.
"""

from typing import Any, Dict, List, Optional
import json
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from backend.mcp_servers.base_mcp_server import MCPServerBase, MCPTool
from backend.utils.logging import get_logger

logger = get_logger(__name__)

# Try to import PDF generation library
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
    from reportlab.lib.styles import getSampleStyleSheet
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False
    logger.warning("reportlab not available, PDF export will be limited")


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
    HTML = "html"


@dataclass
class ReportMetadata:
    """Metadata for a generated report."""
    report_id: str
    investigation_id: str
    audience: ReportAudience
    format: ReportFormat
    generated_at: str
    classification: str
    word_count: int
    sections: List[str]


class ReportGenerationMCPServer(MCPServerBase):
    """
    MCP server for generating investigation reports.

    Provides tools for:
    - Generating reports in different formats
    - Getting audience-specific templates
    - Validating report completeness
    - Exporting to PDF

    Integrates with the Report Writer skill for content generation.
    """

    def __init__(self):
        """Initialize the Report Generation MCP server."""
        super().__init__("report_generation")

        # Store generated reports
        self._reports: Dict[str, Dict[str, Any]] = {}

        self._register_tools()
        logger.info("ReportGenerationMCPServer initialized")

    def _register_tools(self):
        """Register available tools."""
        self.tools = {
            "generate_report": MCPTool(
                name="generate_report",
                description="Generate an investigation report for a specific audience and format.",
                parameters={
                    "type": "object",
                    "properties": {
                        "investigation_id": {
                            "type": "string",
                            "description": "The investigation ID to generate report for"
                        },
                        "investigation_data": {
                            "type": "object",
                            "description": "Complete investigation data to include in report"
                        },
                        "audience": {
                            "type": "string",
                            "enum": [a.value for a in ReportAudience],
                            "description": "Target audience for the report",
                            "default": "internal"
                        },
                        "format": {
                            "type": "string",
                            "enum": [f.value for f in ReportFormat],
                            "description": "Output format for the report",
                            "default": "markdown"
                        },
                        "classification": {
                            "type": "string",
                            "enum": ["public", "restricted", "confidential"],
                            "description": "Classification level for the report",
                            "default": "restricted"
                        },
                        "include_methodology": {
                            "type": "boolean",
                            "description": "Whether to include full methodology chain",
                            "default": True
                        }
                    },
                    "required": ["investigation_id", "investigation_data", "audience"]
                },
                handler=self._handle_generate_report
            ),
            "get_report_template": MCPTool(
                name="get_report_template",
                description="Get the template structure for a specific audience report.",
                parameters={
                    "type": "object",
                    "properties": {
                        "audience": {
                            "type": "string",
                            "enum": [a.value for a in ReportAudience],
                            "description": "Target audience"
                        }
                    },
                    "required": ["audience"]
                },
                handler=self._handle_get_template
            ),
            "validate_report_completeness": MCPTool(
                name="validate_report_completeness",
                description="Validate that a report has all required sections for its audience.",
                parameters={
                    "type": "object",
                    "properties": {
                        "report_content": {
                            "type": "string",
                            "description": "The report content to validate"
                        },
                        "audience": {
                            "type": "string",
                            "enum": [a.value for a in ReportAudience],
                            "description": "Target audience"
                        }
                    },
                    "required": ["report_content", "audience"]
                },
                handler=self._handle_validate_completeness
            ),
            "export_to_pdf": MCPTool(
                name="export_to_pdf",
                description="Export a markdown report to PDF format.",
                parameters={
                    "type": "object",
                    "properties": {
                        "report_content": {
                            "type": "string",
                            "description": "Markdown content to export"
                        },
                        "output_path": {
                            "type": "string",
                            "description": "Path to save the PDF file"
                        },
                        "title": {
                            "type": "string",
                            "description": "Report title",
                            "default": "Investigation Report"
                        }
                    },
                    "required": ["report_content", "output_path"]
                },
                handler=self._handle_export_pdf
            ),
            "get_report": MCPTool(
                name="get_report",
                description="Retrieve a previously generated report by ID.",
                parameters={
                    "type": "object",
                    "properties": {
                        "report_id": {
                            "type": "string",
                            "description": "The report ID to retrieve"
                        }
                    },
                    "required": ["report_id"]
                },
                handler=self._handle_get_report
            )
        }

    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools."""
        return [tool.to_dict() for tool in self.tools.values()]

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool."""
        if tool_name not in self.tools:
            return {"error": f"Tool {tool_name} not found"}

        try:
            return await self.tools[tool_name].call(arguments)
        except Exception as e:
            logger.error(f"Tool call failed: {tool_name}", error=str(e), exc_info=True)
            return {"error": str(e)}

    async def list_resources(self) -> List[Dict[str, Any]]:
        """List available resources."""
        return []

    def _get_audience_sections(self, audience: ReportAudience) -> Dict[str, bool]:
        """Get required sections for each audience."""
        sections = {
            ReportAudience.LAW_ENFORCEMENT: {
                "executive_summary": True,
                "subject_identification": True,
                "evidence_chain": True,
                "methodology": True,
                "location_intelligence": True,
                "facility_information": False,
                "potential_violations": True,
                "recommended_actions": True,
                "appendices": False
            },
            ReportAudience.CONSERVATION: {
                "tiger_overview": True,
                "current_status": True,
                "facility_assessment": True,
                "historical_context": True,
                "conservation_implications": True,
                "recommendations": True,
                "urgency_assessment": True
            },
            ReportAudience.INTERNAL: {
                "investigation_summary": True,
                "model_performance": True,
                "data_quality": True,
                "pipeline_details": True,
                "reasoning_chain": True,
                "errors_warnings": False,
                "system_recommendations": False
            },
            ReportAudience.PUBLIC: {
                "summary": True,
                "key_findings": True,
                "about_the_tiger": False,
                "what_this_means": True
            }
        }
        return sections.get(audience, {})

    async def _handle_generate_report(
        self,
        investigation_id: str,
        investigation_data: Dict[str, Any],
        audience: str = "internal",
        format: str = "markdown",
        classification: str = "restricted",
        include_methodology: bool = True
    ) -> Dict[str, Any]:
        """Handle report generation."""
        try:
            import uuid
            report_id = str(uuid.uuid4())[:8]
            audience_enum = ReportAudience(audience)
            format_enum = ReportFormat(format)

            # Get required sections
            sections = self._get_audience_sections(audience_enum)

            # Build report structure based on audience
            report_content = self._build_report_content(
                investigation_id=investigation_id,
                investigation_data=investigation_data,
                audience=audience_enum,
                sections=sections,
                classification=classification,
                include_methodology=include_methodology
            )

            # Format output
            if format_enum == ReportFormat.JSON:
                output = json.dumps(report_content, indent=2)
            elif format_enum == ReportFormat.HTML:
                output = self._to_html(report_content)
            else:  # markdown
                output = self._to_markdown(report_content)

            # Calculate word count
            word_count = len(output.split())

            # Store report
            self._reports[report_id] = {
                "report_id": report_id,
                "investigation_id": investigation_id,
                "audience": audience,
                "format": format,
                "classification": classification,
                "generated_at": datetime.now().isoformat(),
                "content": output,
                "word_count": word_count,
                "sections": list(sections.keys())
            }

            logger.info(f"Generated {audience} report {report_id} for investigation {investigation_id}")

            return {
                "success": True,
                "report_id": report_id,
                "investigation_id": investigation_id,
                "audience": audience,
                "format": format,
                "content": output,
                "word_count": word_count,
                "sections_included": [s for s, required in sections.items() if required],
                "generated_at": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            return {"error": str(e), "success": False}

    def _build_report_content(
        self,
        investigation_id: str,
        investigation_data: Dict[str, Any],
        audience: ReportAudience,
        sections: Dict[str, bool],
        classification: str,
        include_methodology: bool
    ) -> Dict[str, Any]:
        """Build structured report content."""
        content = {
            "metadata": {
                "investigation_id": investigation_id,
                "audience": audience.value,
                "classification": classification.upper(),
                "generated_at": datetime.now().isoformat()
            },
            "sections": {}
        }

        # Extract relevant data based on audience
        if audience == ReportAudience.LAW_ENFORCEMENT:
            content["sections"] = self._build_law_enforcement_sections(
                investigation_data, sections, include_methodology
            )
        elif audience == ReportAudience.CONSERVATION:
            content["sections"] = self._build_conservation_sections(
                investigation_data, sections
            )
        elif audience == ReportAudience.INTERNAL:
            content["sections"] = self._build_internal_sections(
                investigation_data, sections, include_methodology
            )
        else:  # PUBLIC
            content["sections"] = self._build_public_sections(
                investigation_data, sections
            )

        return content

    def _build_law_enforcement_sections(
        self,
        data: Dict[str, Any],
        sections: Dict[str, bool],
        include_methodology: bool
    ) -> Dict[str, Any]:
        """Build sections for law enforcement report."""
        result = {}

        if sections.get("executive_summary"):
            result["executive_summary"] = {
                "title": "Executive Summary",
                "content": self._generate_executive_summary(data)
            }

        if sections.get("subject_identification"):
            result["subject_identification"] = {
                "title": "Subject Identification",
                "tiger_id": data.get("identification", {}).get("tiger_id", "Unknown"),
                "tiger_name": data.get("identification", {}).get("tiger_name", "Unknown"),
                "confidence": data.get("identification", {}).get("confidence", 0),
                "model_consensus": data.get("model_results", {})
            }

        if sections.get("evidence_chain"):
            result["evidence_chain"] = {
                "title": "Evidence Chain",
                "items": self._format_evidence_chain(data.get("evidence", []))
            }

        if sections.get("methodology") and include_methodology:
            result["methodology"] = {
                "title": "Methodology",
                "steps": data.get("reasoning_steps", [])
            }

        if sections.get("potential_violations"):
            result["potential_violations"] = {
                "title": "Potential Violations",
                "violations": self._identify_potential_violations(data)
            }

        if sections.get("recommended_actions"):
            result["recommended_actions"] = {
                "title": "Recommended Actions",
                "actions": self._generate_recommendations(data, "law_enforcement")
            }

        return result

    def _build_conservation_sections(
        self,
        data: Dict[str, Any],
        sections: Dict[str, bool]
    ) -> Dict[str, Any]:
        """Build sections for conservation report."""
        result = {}

        if sections.get("tiger_overview"):
            result["tiger_overview"] = {
                "title": "Tiger Overview",
                "identity": data.get("identification", {}),
                "history": data.get("history", "Unknown")
            }

        if sections.get("current_status"):
            result["current_status"] = {
                "title": "Current Welfare Status",
                "status": data.get("welfare_status", "Unknown"),
                "conditions": data.get("conditions", [])
            }

        if sections.get("recommendations"):
            result["recommendations"] = {
                "title": "Conservation Recommendations",
                "actions": self._generate_recommendations(data, "conservation")
            }

        if sections.get("urgency_assessment"):
            result["urgency_assessment"] = {
                "title": "Urgency Assessment",
                "level": self._assess_urgency(data),
                "factors": data.get("urgency_factors", [])
            }

        return result

    def _build_internal_sections(
        self,
        data: Dict[str, Any],
        sections: Dict[str, bool],
        include_methodology: bool
    ) -> Dict[str, Any]:
        """Build sections for internal report."""
        result = {}

        if sections.get("investigation_summary"):
            result["investigation_summary"] = {
                "title": "Investigation Summary",
                "id": data.get("investigation_id", "Unknown"),
                "status": data.get("status", "Unknown"),
                "phases_completed": data.get("phases_completed", [])
            }

        if sections.get("model_performance"):
            result["model_performance"] = {
                "title": "Model Performance",
                "models": data.get("model_results", {}),
                "ensemble_weights": data.get("ensemble_weights", {})
            }

        if sections.get("reasoning_chain") and include_methodology:
            result["reasoning_chain"] = {
                "title": "Reasoning Chain",
                "steps": data.get("reasoning_steps", [])
            }

        if sections.get("errors_warnings"):
            result["errors_warnings"] = {
                "title": "Errors and Warnings",
                "errors": data.get("errors", []),
                "warnings": data.get("warnings", [])
            }

        return result

    def _build_public_sections(
        self,
        data: Dict[str, Any],
        sections: Dict[str, bool]
    ) -> Dict[str, Any]:
        """Build sections for public report."""
        return {
            "summary": {
                "title": "Summary",
                "content": self._generate_public_summary(data)
            },
            "key_findings": {
                "title": "Key Findings",
                "findings": data.get("key_findings", [])
            }
        }

    def _generate_executive_summary(self, data: Dict[str, Any]) -> str:
        """Generate executive summary text."""
        identification = data.get("identification", {})
        tiger_name = identification.get("tiger_name", "Unknown tiger")
        confidence = identification.get("confidence", 0)

        return f"Investigation identified {tiger_name} with {confidence:.0%} confidence."

    def _generate_public_summary(self, data: Dict[str, Any]) -> str:
        """Generate public-friendly summary."""
        return "This investigation used advanced AI technology to identify an individual tiger."

    def _format_evidence_chain(self, evidence: List[Dict]) -> List[Dict]:
        """Format evidence chain for law enforcement."""
        formatted = []
        for i, item in enumerate(evidence, 1):
            formatted.append({
                "item_number": i,
                "type": item.get("type", "Unknown"),
                "description": item.get("description", ""),
                "source": item.get("source", ""),
                "confidence": item.get("confidence", 0)
            })
        return formatted

    def _identify_potential_violations(self, data: Dict[str, Any]) -> List[Dict]:
        """Identify potential legal violations from data."""
        violations = []

        # Check for common violation indicators
        if data.get("no_usda_license"):
            violations.append({
                "regulation": "Animal Welfare Act",
                "violation": "Operating without USDA license",
                "severity": "high"
            })

        if data.get("cites_concerns"):
            violations.append({
                "regulation": "CITES",
                "violation": "Potential international trade violation",
                "severity": "high"
            })

        return violations

    def _generate_recommendations(self, data: Dict[str, Any], audience: str) -> List[str]:
        """Generate audience-appropriate recommendations."""
        if audience == "law_enforcement":
            return [
                "Recommend investigation by USFWS",
                "Preserve digital evidence",
                "Interview facility personnel"
            ]
        elif audience == "conservation":
            return [
                "Monitor tiger welfare",
                "Consider sanctuary placement",
                "Document current conditions"
            ]
        else:
            return ["Continue monitoring"]

    def _assess_urgency(self, data: Dict[str, Any]) -> str:
        """Assess urgency level for conservation report."""
        if data.get("welfare_concerns"):
            return "high"
        elif data.get("unknown_location"):
            return "medium"
        return "low"

    def _to_markdown(self, content: Dict[str, Any]) -> str:
        """Convert report content to markdown."""
        lines = []

        # Header
        meta = content.get("metadata", {})
        lines.append(f"# Investigation Report")
        lines.append(f"")
        lines.append(f"**Investigation ID:** {meta.get('investigation_id', 'N/A')}")
        lines.append(f"**Classification:** {meta.get('classification', 'RESTRICTED')}")
        lines.append(f"**Generated:** {meta.get('generated_at', 'N/A')}")
        lines.append(f"")
        lines.append("---")
        lines.append("")

        # Sections
        for section_key, section_data in content.get("sections", {}).items():
            title = section_data.get("title", section_key.replace("_", " ").title())
            lines.append(f"## {title}")
            lines.append("")

            # Handle different section types
            if "content" in section_data:
                lines.append(section_data["content"])
            elif "items" in section_data:
                for item in section_data["items"]:
                    lines.append(f"- {item}")
            elif "steps" in section_data:
                for step in section_data["steps"]:
                    lines.append(f"**Step {step.get('step', '?')}:** {step.get('action', '')}")
                    lines.append(f"  - Conclusion: {step.get('conclusion', '')}")
                    lines.append(f"  - Confidence: {step.get('confidence', 0)}%")
            else:
                # Generic key-value output
                for key, value in section_data.items():
                    if key != "title":
                        lines.append(f"**{key.replace('_', ' ').title()}:** {value}")

            lines.append("")

        return "\n".join(lines)

    def _to_html(self, content: Dict[str, Any]) -> str:
        """Convert report content to HTML."""
        # Simple HTML conversion
        md = self._to_markdown(content)
        # Basic markdown to HTML
        html = md.replace("# ", "<h1>").replace("\n## ", "</p>\n<h2>")
        html = html.replace("**", "<strong>").replace("</strong>:", ":</strong>")
        return f"<html><body>{html}</body></html>"

    async def _handle_get_template(self, audience: str) -> Dict[str, Any]:
        """Handle getting report template."""
        try:
            audience_enum = ReportAudience(audience)
            sections = self._get_audience_sections(audience_enum)

            return {
                "success": True,
                "audience": audience,
                "required_sections": [s for s, req in sections.items() if req],
                "optional_sections": [s for s, req in sections.items() if not req],
                "template_structure": sections
            }

        except Exception as e:
            logger.error(f"Failed to get template: {e}")
            return {"error": str(e), "success": False}

    async def _handle_validate_completeness(
        self,
        report_content: str,
        audience: str
    ) -> Dict[str, Any]:
        """Handle validating report completeness."""
        try:
            audience_enum = ReportAudience(audience)
            sections = self._get_audience_sections(audience_enum)

            missing = []
            found = []

            content_lower = report_content.lower()

            for section, required in sections.items():
                section_name = section.replace("_", " ")
                if section_name in content_lower:
                    found.append(section)
                elif required:
                    missing.append(section)

            is_complete = len(missing) == 0

            return {
                "success": True,
                "is_complete": is_complete,
                "found_sections": found,
                "missing_required_sections": missing,
                "completeness_score": len(found) / len(sections) if sections else 1.0
            }

        except Exception as e:
            logger.error(f"Validation failed: {e}")
            return {"error": str(e), "success": False}

    async def _handle_export_pdf(
        self,
        report_content: str,
        output_path: str,
        title: str = "Investigation Report"
    ) -> Dict[str, Any]:
        """Handle PDF export."""
        try:
            if not HAS_REPORTLAB:
                return {
                    "success": False,
                    "error": "PDF export not available. Install: pip install reportlab"
                }

            doc = SimpleDocTemplate(output_path, pagesize=letter)
            styles = getSampleStyleSheet()
            story = []

            # Add title
            story.append(Paragraph(title, styles['Title']))
            story.append(Spacer(1, 12))

            # Convert markdown to paragraphs (simplified)
            for line in report_content.split('\n'):
                if line.startswith('# '):
                    story.append(Paragraph(line[2:], styles['Heading1']))
                elif line.startswith('## '):
                    story.append(Paragraph(line[3:], styles['Heading2']))
                elif line.strip():
                    story.append(Paragraph(line, styles['Normal']))
                story.append(Spacer(1, 6))

            doc.build(story)

            logger.info(f"Exported PDF to {output_path}")

            return {
                "success": True,
                "output_path": output_path,
                "message": f"PDF exported successfully to {output_path}"
            }

        except Exception as e:
            logger.error(f"PDF export failed: {e}")
            return {"error": str(e), "success": False}

    async def _handle_get_report(self, report_id: str) -> Dict[str, Any]:
        """Handle retrieving a generated report."""
        try:
            if report_id not in self._reports:
                return {"error": f"Report {report_id} not found", "success": False}

            return {
                "success": True,
                "report": self._reports[report_id]
            }

        except Exception as e:
            logger.error(f"Failed to get report: {e}")
            return {"error": str(e), "success": False}

    # Convenience methods for direct workflow integration
    async def generate_report(
        self,
        investigation_id: str,
        audience: str = "law_enforcement",
        format: str = "markdown",
        investigation_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Convenience method to generate a report.
        Wraps _handle_generate_report for direct workflow use.

        Args:
            investigation_id: The investigation ID
            audience: Target audience (law_enforcement, conservation, internal, public)
            format: Output format (markdown, json, pdf)
            investigation_data: Optional investigation data to include

        Returns:
            Generated report with content and metadata
        """
        return await self._handle_generate_report(
            investigation_id=investigation_id,
            audience=audience,
            format=format,
            investigation_data=investigation_data
        )


# Singleton instance
_server_instance: Optional[ReportGenerationMCPServer] = None


def get_report_generation_server() -> ReportGenerationMCPServer:
    """Get or create the singleton server instance."""
    global _server_instance
    if _server_instance is None:
        _server_instance = ReportGenerationMCPServer()
    return _server_instance
