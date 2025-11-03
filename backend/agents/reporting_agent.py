"""Reporting Agent for compiling investigation results"""

from typing import Dict, Any, List, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session

from backend.services.investigation_service import InvestigationService
from backend.database import get_db_session
from backend.utils.logging import get_logger

logger = get_logger(__name__)


class ReportingAgent:
    """Agent specialized in compiling investigation results into reports"""
    
    def __init__(
        self, 
        db: Optional[Session] = None,
        investigation_service: Optional[InvestigationService] = None
    ):
        """
        Initialize Reporting Agent
        
        Args:
            db: Database session (optional, will create if not provided)
            investigation_service: InvestigationService instance (optional, for testing)
        """
        self.db = db
        # Allow dependency injection for testing
        if investigation_service:
            self.investigation_service = investigation_service
        else:
            self.investigation_service = InvestigationService(db) if db else None
    
    async def compile_report(
        self,
        investigation_id: UUID,
        evidence_items: List[Dict[str, Any]],
        analysis: Dict[str, Any],
        validation: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Compile investigation results into structured report
        
        Args:
            investigation_id: Investigation ID
            evidence_items: List of evidence items
            analysis: Analysis results
            validation: Validation results (optional)
            
        Returns:
            Compiled investigation report
        """
        if not self.db:
            with get_db_session() as session:
                self.db = session
                self.investigation_service = InvestigationService(session)
        
        investigation = self.investigation_service.get_investigation(investigation_id)
        
        if not investigation:
            raise ValueError(f"Investigation {investigation_id} not found")
        
        # Extract key information
        tigers = []
        facilities = []
        
        for item in evidence_items:
            if "tiger" in item:
                tigers.append(item["tiger"])
            if "facility" in item:
                facilities.append(item["facility"])
        
        # Build report structure
        report = {
            "investigation_id": str(investigation_id),
            "title": investigation.title,
            "summary": self._generate_summary(analysis, evidence_items),
            "subject": self._format_subject(tigers),
            "evidence": self._format_evidence(evidence_items),
            "findings": self._format_findings(analysis),
            "legal_implications": analysis.get("legal_implications", []),
            "recommendations": self._generate_recommendations(analysis, validation),
            "next_steps": self._generate_next_steps(analysis),
            "sources": self._extract_sources(evidence_items),
            "generated_at": datetime.utcnow().isoformat(),
            "confidence": analysis.get("confidence", 0.0)
        }
        
        return report
    
    def _generate_summary(
        self,
        analysis: Dict[str, Any],
        evidence_items: List[Dict[str, Any]]
    ) -> str:
        """Generate investigation summary"""
        indicators = analysis.get("trafficking_indicators", [])
        
        if not indicators:
            return "Investigation found no strong evidence of trafficking. Continue monitoring."
        
        # Build summary from indicators
        summary_parts = []
        
        for indicator in indicators[:3]:  # Top 3 indicators
            if indicator["type"] == "interstate_transfer":
                summary_parts.append(
                    f"Detected interstate transfer from {indicator.get('from', 'unknown')} "
                    f"to {indicator.get('to', 'unknown')}."
                )
            elif indicator["type"] == "location_mismatch":
                summary_parts.append("Location mismatch detected for tiger.")
            elif indicator["type"] == "unlicensed_facility":
                summary_parts.append(
                    f"Tiger found at unlicensed facility: {indicator.get('facility_name', 'unknown')}."
                )
        
        strength = analysis.get("evidence_strength", "weak")
        if strength == "strong":
            return " ".join(summary_parts) + " Strong evidence suggests trafficking occurred."
        elif strength == "moderate":
            return " ".join(summary_parts) + " Moderate evidence of potential trafficking."
        else:
            return " ".join(summary_parts) + " Weak evidence - requires further investigation."
    
    def _format_subject(self, tigers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Format subject information"""
        if not tigers:
            return {"description": "Unknown tiger(s)"}
        
        tiger = tigers[0]  # Primary subject
        return {
            "tiger_id": tiger.get("tiger_id"),
            "name": tiger.get("name"),
            "alias": tiger.get("alias"),
            "description": f"Tiger {tiger.get('name', tiger.get('tiger_id', 'unknown'))}"
        }
    
    def _format_evidence(self, evidence_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format evidence for report"""
        formatted = []
        
        for item in evidence_items:
            formatted_item = {
                "type": item.get("source_type", "unknown"),
                "source": item.get("source_url"),
                "summary": item.get("extracted_text", "")[:200] + "..." if len(item.get("extracted_text", "")) > 200 else item.get("extracted_text", ""),
                "relevance": item.get("relevance_score", 0.0),
                "verified": item.get("verified", False)
            }
            
            if "tiger" in item:
                formatted_item["tiger"] = item["tiger"].get("name", item["tiger"].get("tiger_id"))
            
            if "facility" in item:
                formatted_item["facility"] = item["facility"].get("exhibitor_name")
            
            formatted.append(formatted_item)
        
        return formatted
    
    def _format_findings(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Format findings for report"""
        findings = []
        
        indicators = analysis.get("trafficking_indicators", [])
        for indicator in indicators:
            findings.append({
                "type": indicator["type"],
                "description": indicator.get("description", ""),
                "severity": indicator.get("severity", "medium"),
                "evidence": indicator  # Include full indicator data
            })
        
        return findings
    
    def _generate_recommendations(
        self,
        analysis: Dict[str, Any],
        validation: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Generate recommendations"""
        recommendations = []
        
        # Add recommendations from analysis
        recommendations.extend(analysis.get("recommendations", []))
        
        # Add validation recommendations if provided
        if validation:
            recommendations.extend(validation.get("recommendations", []))
        
        # Add default recommendations based on evidence strength
        strength = analysis.get("evidence_strength", "weak")
        if strength == "strong":
            recommendations.append({
                "action": "Notify authorities",
                "priority": "high",
                "description": "Strong evidence - notify law enforcement immediately"
            })
        
        return recommendations
    
    def _generate_next_steps(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate next steps"""
        next_steps = []
        
        strength = analysis.get("evidence_strength", "weak")
        
        if strength == "strong":
            next_steps.append("Notify relevant law enforcement agencies")
            next_steps.append("Prepare legal documentation")
            next_steps.append("Coordinate with facility authorities")
        elif strength == "moderate":
            next_steps.append("Gather additional evidence")
            next_steps.append("Cross-reference with other investigations")
            next_steps.append("Monitor facilities involved")
        else:
            next_steps.append("Continue investigation")
            next_steps.append("Monitor for additional evidence")
        
        return next_steps
    
    def _extract_sources(self, evidence_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract and format sources"""
        sources = []
        seen_urls = set()
        
        for item in evidence_items:
            source_url = item.get("source_url")
            if source_url and source_url not in seen_urls:
                sources.append({
                    "url": source_url,
                    "type": item.get("source_type", "unknown"),
                    "verified": item.get("verified", False)
                })
                seen_urls.add(source_url)
        
        return sources
    
    async def export_report(
        self,
        report: Dict[str, Any],
        format: str = "markdown"
    ) -> str:
        """
        Export report in specified format
        
        Args:
            report: Report data
            format: Export format (markdown, json, pdf)
            
        Returns:
            Formatted report string
        """
        if format == "markdown":
            return self._export_markdown(report)
        elif format == "json":
            import json
            return json.dumps(report, indent=2)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _export_markdown(self, report: Dict[str, Any]) -> str:
        """Export report as Markdown"""
        md = f"""# {report['title']}

## Investigation Summary

{report['summary']}

## Subject

- **Tiger ID**: {report['subject'].get('tiger_id', 'Unknown')}
- **Name**: {report['subject'].get('name', 'Unknown')}
- **Description**: {report['subject'].get('description', 'Unknown')}

## Evidence

"""
        
        for i, evidence in enumerate(report['evidence'], 1):
            md += f"""### Evidence {i}

- **Type**: {evidence['type']}
- **Source**: {evidence['source']}
- **Summary**: {evidence['summary']}
- **Relevance**: {evidence['relevance']:.2f}
- **Verified**: {'Yes' if evidence['verified'] else 'No'}

"""
        
        md += """## Findings

"""
        
        for finding in report['findings']:
            md += f"""- **{finding['type']}**: {finding['description']} (Severity: {finding['severity']})

"""
        
        md += """## Legal Implications

"""
        
        for legal in report['legal_implications']:
            md += f"""- **{legal['law']}**: {legal['violation']} (Severity: {legal['severity']})

"""
        
        md += """## Recommendations

"""
        
        for rec in report['recommendations']:
            md += f"""- **{rec['action']}** ({rec['priority']}): {rec['description']}

"""
        
        md += """## Next Steps

"""
        
        for step in report['next_steps']:
            md += f"""- {step}

"""
        
        md += f"""## Sources

"""
        
        for source in report['sources']:
            md += f"""- [{source['url']}]({source['url']}) ({source['type']})

"""
        
        md += f"""
---

*Report generated on {report['generated_at']}*
*Confidence: {report['confidence']:.2f}*
"""
        
        return md
