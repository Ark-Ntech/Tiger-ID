"""Service for exporting investigation data in various formats"""

from typing import Dict, Any, List, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
import json
try:
    import markdown
    MARKDOWN_AVAILABLE = True
except ImportError:
    MARKDOWN_AVAILABLE = False
    markdown = None

from backend.database import get_db_session, Investigation, Evidence, InvestigationStep, Facility, Tiger
from backend.utils.logging import get_logger

logger = get_logger(__name__)


class ExportService:
    """Service for exporting investigations in various formats"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def export_investigation_json(
        self,
        investigation_id: UUID,
        include_evidence: bool = True,
        include_steps: bool = True,
        include_metadata: bool = True
    ) -> Dict[str, Any]:
        """
        Export investigation as JSON
        
        Args:
            investigation_id: Investigation ID
            include_evidence: Include evidence items
            include_steps: Include investigation steps
            include_metadata: Include metadata
        
        Returns:
            JSON-serializable dictionary
        """
        # Convert UUID to string for SQLite comparison
        investigation_id_str = str(investigation_id)
        investigation = self.session.query(Investigation).filter(
            Investigation.investigation_id == investigation_id_str
        ).first()
        
        if not investigation:
            return {"error": "Investigation not found"}
        
        export_data = {
            "investigation_id": str(investigation.investigation_id),
            "title": investigation.title,
            "description": investigation.description,
            "status": investigation.status,
            "priority": investigation.priority,
            "created_at": investigation.created_at.isoformat() if investigation.created_at else None,
            "updated_at": investigation.updated_at.isoformat() if hasattr(investigation, 'updated_at') and investigation.updated_at else None,
        }
        
        if include_metadata:
            export_data["metadata"] = investigation.summary or {}
        
        if include_evidence:
            evidence_items = self.session.query(Evidence).filter(
                Evidence.investigation_id == investigation_id_str
            ).all()
            
            export_data["evidence"] = [
                {
                    "evidence_id": str(ev.evidence_id),
                    "source_type": ev.source_type,
                    "source_url": ev.source_url,
                    "extracted_text": ev.extracted_text,
                    "relevance_score": float(ev.relevance_score) if ev.relevance_score else None,
                    "content": ev.content or {},
                    "created_at": ev.created_at.isoformat() if ev.created_at else None
                }
                for ev in evidence_items
            ]
        
        if include_steps:
            steps = self.session.query(InvestigationStep).filter(
                InvestigationStep.investigation_id == investigation_id_str
            ).order_by(InvestigationStep.timestamp).all()
            
            export_data["steps"] = [
                {
                    "step_id": str(step.step_id),
                    "step_type": step.step_type,
                    "agent_name": step.agent_name,
                    "status": step.status,
                    "result": step.result or {},
                    "timestamp": step.timestamp.isoformat() if step.timestamp else None
                }
                for step in steps
            ]
        
        return export_data
    
    def export_investigation_markdown(
        self,
        investigation_id: UUID,
        include_evidence: bool = True,
        include_steps: bool = True
    ) -> str:
        """
        Export investigation as Markdown
        
        Args:
            investigation_id: Investigation ID
            include_evidence: Include evidence items
            include_steps: Include investigation steps
        
        Returns:
            Markdown string
        """
        json_data = self.export_investigation_json(
            investigation_id,
            include_evidence=include_evidence,
            include_steps=include_steps,
            include_metadata=True
        )
        
        if "error" in json_data:
            return f"# Error\n\n{json_data['error']}"
        
        md_lines = []
        
        # Header
        md_lines.append(f"# {json_data['title']}\n")
        
        # Metadata
        md_lines.append(f"**Status:** {json_data['status']}")
        md_lines.append(f"**Priority:** {json_data['priority']}")
        md_lines.append(f"**Created:** {json_data.get('created_at', 'Unknown')}\n")
        
        # Description
        if json_data.get('description'):
            md_lines.append(f"## Description\n\n{json_data['description']}\n")
        
        # Steps
        if include_steps and json_data.get('steps'):
            md_lines.append("## Investigation Steps\n")
            for idx, step in enumerate(json_data['steps'], 1):
                md_lines.append(f"### Step {idx}: {step['step_type'].replace('_', ' ').title()}")
                md_lines.append(f"- **Agent:** {step.get('agent_name', 'System')}")
                md_lines.append(f"- **Status:** {step['status']}")
                md_lines.append(f"- **Timestamp:** {step.get('timestamp', 'Unknown')}")
                if step.get('result'):
                    md_lines.append(f"- **Result:** {json.dumps(step['result'], indent=2)}")
                md_lines.append("")
        
        # Evidence
        if include_evidence and json_data.get('evidence'):
            md_lines.append("## Evidence\n")
            for idx, ev in enumerate(json_data['evidence'], 1):
                md_lines.append(f"### Evidence {idx}: {ev['source_type'].replace('_', ' ').title()}")
                md_lines.append(f"- **Source URL:** {ev.get('source_url', 'N/A')}")
                md_lines.append(f"- **Relevance Score:** {ev.get('relevance_score', 0):.2f}")
                if ev.get('extracted_text'):
                    md_lines.append(f"- **Extracted Text:** {ev['extracted_text'][:200]}...")
                md_lines.append("")
        
        return "\n".join(md_lines)
    
    def export_investigation_pdf(
        self,
        investigation_id: UUID,
        include_evidence: bool = True,
        include_steps: bool = True
    ) -> bytes:
        """
        Export investigation as PDF
        
        Args:
            investigation_id: Investigation ID
            include_evidence: Include evidence items
            include_steps: Include investigation steps
        
        Returns:
            PDF bytes
        """
        try:
            from weasyprint import HTML, CSS
            from io import BytesIO
            
            # Get markdown content
            md_content = self.export_investigation_markdown(
                investigation_id,
                include_evidence=include_evidence,
                include_steps=include_steps
            )
            
            # Convert markdown to HTML
            if not MARKDOWN_AVAILABLE or markdown is None:
                # Fallback: just use the markdown content as-is wrapped in HTML
                html_content = md_content.replace('\n', '<br>\n')
            else:
                html_content = markdown.markdown(md_content, extensions=['tables', 'fenced_code'])
            
            # Wrap in styled HTML
            full_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        margin: 40px;
                        line-height: 1.6;
                    }}
                    h1 {{
                        color: #2c3e50;
                        border-bottom: 3px solid #3498db;
                        padding-bottom: 10px;
                    }}
                    h2 {{
                        color: #34495e;
                        margin-top: 30px;
                    }}
                    h3 {{
                        color: #7f8c8d;
                    }}
                    table {{
                        border-collapse: collapse;
                        width: 100%;
                        margin: 20px 0;
                    }}
                    th, td {{
                        border: 1px solid #ddd;
                        padding: 12px;
                        text-align: left;
                    }}
                    th {{
                        background-color: #3498db;
                        color: white;
                    }}
                    code {{
                        background-color: #f4f4f4;
                        padding: 2px 6px;
                        border-radius: 3px;
                    }}
                </style>
            </head>
            <body>
                {html_content}
            </body>
            </html>
            """
            
            # Generate PDF
            pdf_bytes = BytesIO()
            HTML(string=full_html).write_pdf(pdf_bytes)
            pdf_bytes.seek(0)
            
            return pdf_bytes.getvalue()
            
        except ImportError:
            logger.error("WeasyPrint not available - cannot generate PDF")
            raise ValueError("PDF export requires WeasyPrint library")
    
    def export_investigation_csv(
        self,
        investigation_id: UUID,
        data_type: str = "evidence"
    ) -> str:
        """
        Export investigation data as CSV
        
        Args:
            investigation_id: Investigation ID
            data_type: Type of data to export ('evidence', 'steps', or 'summary')
        
        Returns:
            CSV string
        """
        import csv
        from io import StringIO
        
        # Convert UUID to string for SQLite comparison
        investigation_id_str = str(investigation_id)
        investigation = self.session.query(Investigation).filter(
            Investigation.investigation_id == investigation_id_str
        ).first()
        
        if not investigation:
            return "Error: Investigation not found"
        
        output = StringIO()
        
        if data_type == "evidence":
            evidence_items = self.session.query(Evidence).filter(
                Evidence.investigation_id == investigation_id_str
            ).all()
            
            writer = csv.writer(output)
            writer.writerow([
                "Evidence ID", "Source Type", "Source URL", "Relevance Score",
                "Extracted Text", "Created At"
            ])
            
            for ev in evidence_items:
                writer.writerow([
                    str(ev.evidence_id),
                    ev.source_type,
                    ev.source_url or "",
                    ev.relevance_score or "",
                    (ev.extracted_text or "")[:500],
                    ev.created_at.isoformat() if ev.created_at else ""
                ])
        
        elif data_type == "steps":
            steps = self.session.query(InvestigationStep).filter(
                InvestigationStep.investigation_id == investigation_id_str
            ).order_by(InvestigationStep.timestamp).all()
            
            writer = csv.writer(output)
            writer.writerow([
                "Step ID", "Step Type", "Agent Name", "Status", "Timestamp", "Result"
            ])
            
            for step in steps:
                writer.writerow([
                    str(step.step_id),
                    step.step_type,
                    step.agent_name or "",
                    step.status,
                    step.timestamp.isoformat() if step.timestamp else "",
                    json.dumps(step.result or {})
                ])
        
        elif data_type == "summary":
            writer = csv.writer(output)
            writer.writerow(["Field", "Value"])
            writer.writerow(["Investigation ID", str(investigation.investigation_id)])
            writer.writerow(["Title", investigation.title])
            writer.writerow(["Description", investigation.description or ""])
            writer.writerow(["Status", investigation.status])
            writer.writerow(["Priority", investigation.priority])
            writer.writerow(["Created At", investigation.created_at.isoformat() if investigation.created_at else ""])
        
        return output.getvalue()


def get_export_service(session: Session) -> ExportService:
    """Get export service instance"""
    return ExportService(session)

